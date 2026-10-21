"""Inspector: dumps the FULL tool definitions the server publishes --
names, descriptions, and every parameter's type/description/constraints.
This is the config surface the agent reasons about."""

import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "distributor_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("SERVER:", init.serverInfo.name, "| version:", init.serverInfo.version)
            print("INSTRUCTIONS:", (init.instructions or "(none)")[:200])
            print("=" * 60)
            tools = await session.list_tools()
            for t in tools.tools:
                print("TOOL:", t.name)
                print("  description:", t.description)
                print("  parameters:", json.dumps(t.inputSchema, indent=2))
                print("-" * 60)
            res = await session.list_resources()
            if res.resources:
                print("RESOURCES:")
                for r in res.resources:
                    print("  ", r.uri, "-", (r.description or "(no description)"))


asyncio.run(main())
