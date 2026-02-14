import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to the report file
REPORT_FILE = "/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/reports/US_FINANCIAL_NEWS_20260202.md"

async def run():
    # 1. Read the report content
    print(f"Reading report from {REPORT_FILE}...")
    try:
        with open(REPORT_FILE, 'r') as f:
            report_content = f.read()
    except FileNotFoundError:
        print("Report file not found!")
        return

    server_path = "/home/chae/miniconda3/bin/notebooklm-mcp"
    server_params = StdioServerParameters(
        command=server_path,
        args=[],
        env=os.environ.copy()
    )

    print("Connecting to NotebookLM MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 2. Create Notebook
            print("Creating new Notebook...")
            try:
                # The tool 'notebook_create' returns the notebook object/ID
                result = await session.call_tool("notebook_create", arguments={"title": "US Financial News & Market Outlook 2026"})
                
                # Parse result to extracting notebook ID is tricky without knowing the exact structure
                # The MCP result is typically a list of Content objects (TextContent, ImageContent, etc.)
                # We'll print it to debug and try to parse it.
                # Assuming the output text contains the ID or we can list notebooks to find it.
                
                print(f"Create Result: {result}")
                
                # Check text content for ID
                output_text = result.content[0].text
                # Typical output might be "Created notebook: US Financial News ... (ID: xxxxx)"
                # Let's try to extract it or just fetch the list of notebooks (most recent)
                
            except Exception as e:
                print(f"Error creating notebook: {e}")
                return

            # Wait a moment for propagation
            await asyncio.sleep(2)

            # 3. Find the new notebook ID (robust method)
            print("Listing notebooks to find the ID...")
            list_res = await session.call_tool("notebook_list", arguments={"max_results": 1})
            # Assuming the newest is first? Or we search by title.
            
            # We need to parse the list output. It's returned as text or JSON?
            # Likely Markdown text in a TextContent block.
            # "notebook_list" usually returns a JSON structure in the text or structured data? 
            # MCP tools return `CallToolResult` which has `content` list.
            
            # Let's dump the list content to see.
            list_text = list_res.content[0].text
            print(f"List Result: {list_text}")
            
            # Simple heuristic parsing (assuming the recent one is at the top or we regex for ID)
            # If we struggle to parse, we can't proceed. 
            # But let's assume we can interactively see it in the logs if this fails.
            
            # However, for this script to be autonomous, we'll try to grep the ID.
            # If the tool returns JSON, we parse it. If text, we might need regex.
            import re
            # Regex for UUID-like strings or "id": "..."
            # NotebookLM IDs are often long UUIDs.
            
            # For now, let's just Try to add source to the MOST RECENT notebook if we can find it.
            # We will use the output of 'notebook_create' if it yielded an ID.
            
            # Let's try to extract ID from the create result first if possible.
            notebook_id = None
            
            # Looking for 32+ char hex or similar ID
            match = re.search(r'\b[a-zA-Z0-9_-]{15,}\b', output_text) # Simple generic ID matcher
            # NotebookLM IDs look like: 1A2B3C... (often shorter than UUID, e.g. 12 chars or long UUID)
            
            # If we assume the tool returns the ID as a key part of the message.
            if "ID:" in output_text:
                 # Extract standard format "ID: <id>"
                 parts = output_text.split("ID:")
                 if len(parts) > 1:
                     notebook_id = parts[1].strip().strip('()').split()[0]
            
            if not notebook_id:
                # Fallback to list
                 match = re.search(r'\b[a-zA-Z0-9_-]{10,}\b', list_text)
                 # This is risky. 
                 pass

            # If we really can't get the ID automatically, we'll stop and report.
            # But let's try to be smart.
            
            # Actually, I'll rely on the output logs to give me the ID if I can't parse it, 
            # and then I can run a second command.
            # BUT I want to do it in one go.
            
            # Let's assume we get the ID.
            if notebook_id: 
                print(f"Found Notebook ID: {notebook_id}")
                
                # 4. Add the Source
                print("Adding source text...")
                await session.call_tool("notebook_add_text", arguments={
                    "notebook_id": notebook_id,
                    "text": report_content,
                    "title": "US Financial News Summary (Feb 2026)"
                })
                print("Source added successfully!")
                
                # 5. Query
                print("Querying the notebook...")
                query_res = await session.call_tool("notebook_query", arguments={
                    "notebook_id": notebook_id,
                    "query": "Summarize the key market risks for 2026 mentioned in the source."
                })
                print(f"Query Answer:\n{query_res.content[0].text}")
                
            else:
                print("Could not automatically determine Notebook ID from output. Please check logs.")

if __name__ == "__main__":
    asyncio.run(run())
