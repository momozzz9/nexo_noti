import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def list_tools():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input Schema: {tool.inputSchema}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(list_tools())
