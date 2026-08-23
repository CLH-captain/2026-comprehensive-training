"""Run one safe, representative call against each course MCP server."""

import asyncio
import base64
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
POWERSHELL = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
NPX = Path(r"D:\npx.cmd")

SERVERS = {
    "filesystem": (NPX, ["-y", "@modelcontextprotocol/server-filesystem", str(ROOT)]),
    "fetch": (PYTHON, ["-m", "mcp_server_fetch"]),
    "playwright": (NPX, ["-y", "@playwright/mcp", "--headless", "--browser", "chromium", "--allowed-hosts", "127.0.0.1:5173", "--output-dir", str(ROOT / "artifacts" / "playwright-mcp-output")]),
    "git": (PYTHON, ["-m", "mcp_server_git", "--repository", str(ROOT)]),
    "mysql": (POWERSHELL, ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / "mcp" / "mysql-wrapper.ps1")]),
    "memory": (NPX, ["-y", "@modelcontextprotocol/server-memory"]),
    "sequential_thinking": (NPX, ["-y", "@modelcontextprotocol/server-sequential-thinking"]),
}


def text_from(result) -> str:
    return " ".join(getattr(item, "text", str(item)) for item in result.content)


async def main() -> None:
    calls = {
        "filesystem": ("read_text_file", {"path": str(ROOT / "README.md")}),
        "fetch": ("fetch", {"url": "https://playwright.dev/docs/intro"}),
        "playwright": ("browser_navigate", {"url": "http://127.0.0.1:5173"}),
        "git": ("git_status", {"repo_path": str(ROOT)}),
        "mysql": ("mysql_query", {"sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() LIMIT 20"}),
        "memory": ("create_entities", {"entities": [{"name": "SZUT MCP homework", "entityType": "course_demo", "observations": ["Seven MCP servers configured locally"]}]}),
        "sequential_thinking": ("sequentialthinking", {"thought": "Filesystem, Fetch, Playwright, Git, MySQL, Memory and Sequential Thinking form a complete local course demonstration.", "nextThoughtNeeded": False, "thoughtNumber": 1, "totalThoughts": 1}),
    }
    results = []
    for name, (command, args) in SERVERS.items():
        tool_name, tool_args = calls[name]
        params = StdioServerParameters(command=str(command), args=args, env=None)
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, tool_args)
                    if name == "playwright":
                        screenshot = await session.call_tool("browser_take_screenshot", {})
                        for item in screenshot.content:
                            if getattr(item, "type", None) == "image" and getattr(item, "data", None):
                                (ROOT.parent / "artifacts" / "playwright-home.png").write_bytes(base64.b64decode(item.data))
                                break
                    preview = text_from(result).replace("\n", " ")[:500]
                    results.append({"name": name, "tool": tool_name, "status": "ok", "preview": preview})
        except Exception as exc:
            results.append({"name": name, "tool": tool_name, "status": "error", "error": type(exc).__name__ + ": " + str(exc)[:240]})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())






