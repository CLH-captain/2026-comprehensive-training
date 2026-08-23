import asyncio
import base64
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
NPX = Path(r"D:\npx.cmd")


async def main() -> None:
    params = StdioServerParameters(
        command=str(NPX),
        args=["-y", "@playwright/mcp", "--headless", "--browser", "chromium", "--allowed-hosts", "127.0.0.1:8765"],
        env=None,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("browser_navigate", {"url": "http://127.0.0.1:8765/mcp-config.html"})
            result = await session.call_tool("browser_take_screenshot", {})
            for item in result.content:
                if getattr(item, "type", None) == "image":
                    (ROOT.parent / "artifacts" / "mcp-config.png").write_bytes(base64.b64decode(item.data))
                    return


if __name__ == "__main__":
    asyncio.run(main())
