# Windows QA Engineer Skill

AI-powered manual QA copilot for Windows 11 desktop apps (WinForms/WPF/UWP) using [Microsoft UFO](https://github.com/microsoft/UFO) UIA/Win32 automation via MCP.

## What it does

Turns Claude Code into a QA operator that can discover windows, inspect UI controls, click buttons, fill forms, assert text, and capture screenshots — all on your real Windows desktop using UFO's actual automation stack (no mocks).

## Workflow

```
Discover windows → Select SUT → Collect controls → Interact by id/name → Assert → Report
```

## Requirements

- Windows 11
- Python 3.10+ (3.11 recommended)
- [Microsoft UFO](https://github.com/microsoft/UFO) installed
- [FastMCP](https://pypi.org/project/fastmcp/)

## Install

### Via Skills CLI (recommended)

```bash
npx skills add CodeAlive-AI/windows-qa-engineer@windows-qa-engineer -g -y
```

### Manual

1. Clone this repo
2. Copy the `windows-qa-engineer/` folder to `~/.claude/skills/`
3. Add the MCP server to your project `.mcp.json` (see `windows-qa-engineer/references/setup.md`)
4. Restart Claude Code

## MCP Server Setup

The skill includes a FastMCP server (`scripts/ufo_windows_qa_mcp_server.py`) that composes UFO's three MCP servers (UICollector, HostUIExecutor, AppUIExecutor) into a single stdio endpoint.

Add to your project `.mcp.json`:

```json
{
  "mcpServers": {
    "ufo-windows-qa": {
      "type": "stdio",
      "command": "python",
      "args": [".claude/skills/windows-qa-engineer/scripts/ufo_windows_qa_mcp_server.py"],
      "env": {
        "CONTROL_BACKEND": "uia"
      }
    }
  }
}
```

## Usage

```
/windows-qa-engineer Calculator "verify 2+2=4"
```

Or just describe what you want to test:

> "Test the login flow on MyApp — enter admin/password, click Login, verify the welcome screen"

## License

MIT
