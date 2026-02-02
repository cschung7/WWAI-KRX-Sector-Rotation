import asyncio
import os
import sys

# Ensure we can find the installed packages
# The previous install was in the base environment provided by 'python' in the path, 
# or specific pip install. 
# We saw 'miniconda3/bin/pip' used implicitly or explicitly?
# The output of step 12 showed install in /home/chae/miniconda3/lib/python3.12/site-packages
# So running with /home/chae/miniconda3/bin/python should work.

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_path = "/home/chae/miniconda3/bin/notebooklm-mcp"
    
    print(f"Connecting to {server_path}...")
    
    server_params = StdioServerParameters(
        command=server_path,
        args=[],
        env=os.environ.copy()
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("\n--- Connected! ---")
                
                # List Resources
                try:
                    resources = await session.list_resources()
                    print(f"\nResources ({len(resources.resources)}):")
                    for res in resources.resources:
                        print(f"- {res.name} ({res.uri})")
                except Exception as e:
                    print(f"Error listing resources: {e}")

                # List Tools
                try:
                    tools = await session.list_tools()
                    print(f"\nTools ({len(tools.tools)}):")
                    for tool in tools.tools:
                        print(f"- {tool.name}: {tool.description[:100]}...")
                except Exception as e:
                    print(f"Error listing tools: {e}")
                    
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
