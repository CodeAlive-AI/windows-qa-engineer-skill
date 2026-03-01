"""
ufo_windows_qa_mcp_server.py

Stdio MCP server that exposes UFO's real Windows automation tools to Gemini CLI / Claude Code.
Composes UFO's UICollector, HostUIExecutor, AppUIExecutor into ONE server via FastMCP.mount().

Improvements:
- Robust JSON-RPC protection: Redirects ALL rogue prints to stderr during load.
- Automatic Path Discovery: Searches for UFO in common locations or via PYTHONPATH.
- Working Directory Management: Automatically switches to UFO root to satisfy config loader.
"""

from __future__ import annotations
import time
import sys
import os
import warnings
import logging
import pathlib
from typing import Annotated, Any, Dict, List, Optional

# 1. CRITICAL: Suppress all warnings and non-JSON output early
warnings.filterwarnings("ignore")

# Force all logging to stderr to avoid corrupting the MCP JSON-RPC stream on stdout
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
for logger_name in ["mcp", "fastmcp", "ufo", "galaxy", "aip", "langchain"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

from fastmcp import FastMCP
from pydantic import Field

def find_ufo_root() -> Optional[str]:
    """Identify the UFO root directory from environment or common paths."""
    # Priority 1: PYTHONPATH
    python_path = os.getenv("PYTHONPATH", "")
    for path in python_path.split(os.pathsep):
        if path and (pathlib.Path(path) / "ufo").exists():
            return path
            
    # Priority 2: Common installation locations
    user_home = str(pathlib.Path.home())
    common_paths = [
        os.path.join(user_home, "UFO"),
        os.path.join(os.getcwd(), "UFO"),
        "C:\\UFO"
    ]
    for path in common_paths:
        if os.path.exists(os.path.join(path, "ufo")):
            return path
            
    return None

ufo_root = find_ufo_root()
if ufo_root:
    # Satisfy UFO's ConfigLoader by ensuring we are in the root where 'config/' exists
    os.chdir(ufo_root)
    if ufo_root not in sys.path:
        sys.path.append(ufo_root)

# Delay imports that depend on UFO until path is set
try:
    from ufo.client.mcp.mcp_registry import MCPRegistry
    from ufo.client.mcp.local_servers import load_all_servers
except ImportError as e:
    print(f"Error: UFO framework not found. Please install UFO and set PYTHONPATH. {e}", file=sys.stderr)
    sys.exit(1)

def _get_ufo_server(namespace: str) -> FastMCP:
    """Load all UFO servers and fetch requested namespace, shielding stdout."""
    original_stdout = sys.stdout
    sys.stdout = sys.stderr  # Capture rogue prints during module init
    try:
        load_all_servers()
    finally:
        sys.stdout = original_stdout

    if not MCPRegistry.is_registered(namespace):
        # We don't crash here to allow partial server loads (e.g. if one sub-server has missing deps)
        print(f"Warning: UFO server '{namespace}' not registered.", file=sys.stderr)
        return None
    return MCPRegistry.get(namespace)

# Compose into one server
mcp = FastMCP("UFO Windows QA (UIA/Win32)")

# Mount core UI automation servers
for ns in ["UICollector", "HostUIExecutor", "AppUIExecutor"]:
    srv = _get_ufo_server(ns)
    if srv:
        mcp.mount(srv)

# QA helper tools (thin wrappers around UFO tools for common QA patterns)

@mcp.tool()
def qa_refresh_and_list_windows(
    remove_empty: Annotated[bool, Field(description="Drop empty/ghost windows.")] = True
) -> Annotated[List[Dict[str, Any]], Field(description="Window list.")]:
    """Refresh + list windows in one call. Wraps UICollector.get_desktop_app_info."""
    return mcp.call_tool_sync(
        "get_desktop_app_info",
        {"remove_empty": remove_empty, "refresh_app_windows": True},
    )

@mcp.tool()
def qa_refresh_controls(
    field_list: Annotated[List[str], Field(description="Fields to fetch per control.")] = ["label","control_text","control_type","automation_id","control_rect"],
) -> Annotated[List[Dict[str, Any]], Field(description="Controls for selected window.")]:
    """Refresh control map for the selected window. Wraps UICollector.get_app_window_controls_info."""
    return mcp.call_tool_sync(
        "get_app_window_controls_info", {"field_list": field_list}
    )

@mcp.tool()
def qa_wait_for_text_contains(
    id: Annotated[str, Field(description="Control id (label).")],
    name: Annotated[str, Field(description="Control name.")],
    expected_substring: Annotated[str, Field(description="Substring that must appear.")],
    timeout_s: Annotated[float, Field(description="Max wait seconds.")] = 10.0,
    poll_s: Annotated[float, Field(description="Poll interval seconds.")] = 0.5,
) -> Annotated[Dict[str, Any], Field(description="Result with ok flag and observed text.")]:
    """Poll texts(id,name) until expected_substring appears or timeout. Useful for async UI updates."""
    deadline = time.time() + max(0.1, timeout_s)
    last_text: Optional[str] = None

    while time.time() < deadline:
        try:
            res = mcp.call_tool_sync("texts", {"id": id, "name": name})
            last_text = str(res)
            if expected_substring in last_text:
                return {"ok": True, "text": last_text, "matched": expected_substring}
        except:
            pass # Control might not be ready yet
        time.sleep(max(0.05, poll_s))

    return {
        "ok": False,
        "text": last_text,
        "matched": expected_substring,
        "timeout_s": timeout_s,
    }

def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
