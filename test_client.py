"""Smoke test: talks to distributor_server.py over MCP stdio, lists its tools,
then calls two of them. Proves the server actually speaks MCP."""

import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=sys.executable,  # use whatever Python is running this script
        args=[os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "distributor_server.py")],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            r1 = await session.call_tool("search_inventory", {"keyword": "flange"})
            print("SEARCH:", r1.content[0].text)
            r2 = await session.call_tool("get_quote", {"sku": "BRG-UCF205", "quantity": 500})
            print("QUOTE:", r2.content[0].text)


asyncio.run(main())
