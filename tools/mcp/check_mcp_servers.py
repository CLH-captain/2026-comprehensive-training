"""Initialize each configured course MCP server and print its advertised tools."""

import asyncio
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
    "playwright": (NPX, ["-y", "@playwright/mcp", "--headless", "--browser", "chromium", "--allowed-hosts", "127.0.0.1:5173"]),
    "git": (PYTHON, ["-m", "mcp_server_git", "--repository", str(ROOT)]),
    "mysql": (POWERSHELL, ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / "mcp" / "mysql-wrapper.ps1")]),
    "memory": (NPX, ["-y", "@modelcontextprotocol/server-memory"]),
    "sequential_thinking": (NPX, ["-y", "@modelcontextprotocol/server-sequential-thinking"]),
}


async def probe(name: str, command: Path, args: list[str]) -> dict:
    params = StdioServerParameters(command=str(command), args=args, env=None)
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return {"name": name, "status": "ok", "tools": [tool.name for tool in result.tools]}
    except Exception as exc:  # evidence script: report, do not hide unavailable servers
        return {"name": name, "status": "error", "error": type(exc).__name__ + ": " + str(exc)[:240]}


async def main() -> None:
    results = [await probe(name, command, args) for name, (command, args) in SERVERS.items()]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
