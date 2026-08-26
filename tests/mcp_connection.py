#!/usr/bin/env python3
"""
Complete MCP test - establishes connection and sends commands.

Uses the FastMCP client with StreamableHttpTransport to connect to the
MCP server in multi-user mode, passing QRadar credentials via headers.
"""

import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def test_mcp_complete():
    """Test MCP server with actual commands."""

    base_url = "http://localhost:5001"
    mcp_endpoint = f"{base_url}/mcp"

    # Replace with your actual tokens
    headers = {
        "SEC": "",
    }

    print("QRadar MCP Server - Complete Test")
    print("=" * 50)
    print(f"Endpoint: {mcp_endpoint}\n")

    transport = StreamableHttpTransport(url=mcp_endpoint, headers=headers)

    try:
        async with Client(transport) as client:
            # Step 1: List tools
            print("Step 1: Listing available tools...")
            tools = await client.list_tools()
            print(f"\n✅ Found {len(tools)} tools")
            print("\nFirst 10 tools:")
            for i, tool in enumerate(tools[:10], 1):
                desc = tool.description.split('\n')[0][:60] if tool.description else ""
                print(f"  {i}. {tool.name}: {desc}...")

            # Step 2: List resources
            print("\nStep 2: Listing available resources...")
            resources = await client.list_resources()
            print(f"\n✅ Found {len(resources)} resources")
            for resource in resources:
                print(f"  - {resource.uri}")

        print("\n" + "=" * 50)
        print("✅ MCP Server is fully operational in multi-user mode!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_complete())
