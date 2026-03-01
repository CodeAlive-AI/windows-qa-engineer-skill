# Setup: UFO + MCP Server

## Prerequisites
- **OS**: Windows 11
- **Python**: 3.10+ (Verified on 3.11.6)

## 1. Install Microsoft UFO
Clone the repository and install dependencies. Note that UFO's `requirements.txt` may be missing some core automation libraries.

```powershell
# Clone UFO
cd C:\
git clone https://github.com/microsoft/UFO.git
cd UFO

# Install verified dependencies
pip install -r requirements.txt
pip install fastmcp uiautomation flask pyautogui html2text fastapi uvicorn
```

## 2. Configure Configuration
UFO expects a configuration directory. If you encounter `FileNotFoundError: No configuration found for 'ufo'`, ensure the following structure exists in your UFO root:

```powershell
# Create basic config if missing
mkdir config/ufo
New-Item -Path "config/ufo/system.yaml" -ItemType File -Value "MAX_STEP: 50`nCONTROL_BACKEND: ['uia']"
New-Item -Path "config/ufo/mcp.yaml" -ItemType File -Value "{}"
```

## 3. Register MCP Server
Add the server to your Gemini CLI or Claude Code config (usually `.mcp.json` in project root or global config).

```json
{
  "mcpServers": {
    "ufo-windows-qa": {
      "type": "stdio",
      "command": "python",
      "args": [
        "C:/Users/YOUR_USER/.agents/skills/windows-qa-engineer/scripts/ufo_windows_qa_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/UFO",
        "CONTROL_BACKEND": "uia"
      }
    }
  }
}
```

## Troubleshooting

### "Invalid JSON: EOF while parsing"
This happens when UFO or one of its dependencies prints a warning or error to `stdout` during startup, corrupting the JSON-RPC stream. 
**Fix**: The improved `ufo_windows_qa_mcp_server.py` redirects modules' `stdout` to `stderr` during loading. Ensure you are using the latest version of the script.

### "ModuleNotFoundError: No module named 'langchain.docstore'"
UFO's `constellation_mcp_server` depends on specific LangChain versions. 
**Fix**: The improved MCP server allows partial loading; if `UICollector` is registered, the core QA tools will still work even if other sub-servers fail to load.

### "No configuration found for 'ufo'"
UFO's `ConfigLoader` is sensitive to the current working directory.
**Fix**: The MCP server script now automatically `os.chdir()` to the detected `ufo_root` before initializing.
