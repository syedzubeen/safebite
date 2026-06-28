"""Run this once to discover available Slack MCP server tools."""
import asyncio
import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

async def discover():
    import json, glob
    # Find the bot token from slack CLI credentials
    cred_files = glob.glob(os.path.expanduser("~/.slack/credentials.json"))
    token = None
    if cred_files:
        with open(cred_files[0]) as f:
            creds = json.load(f)
            # Get first available token
            for team in creds.values():
                if isinstance(team, dict):
                    token = team.get("token") or team.get("bot_access_token")
                    if token:
                        break
    if not token:
        print("Could not find bot token. Check ~/.slack/credentials.json")
        return
    print(f"Using token: {token[:20]}...")
    token = os.environ.get("SLACK_BOT_TOKEN", token)
    headers = {"Authorization": f"Bearer {token}"}
    async with streamablehttp_client("https://mcp.slack.com/mcp", headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"Tool: {tool.name}")
                print(f"  Description: {tool.description[:100]}")
                print()

asyncio.run(discover())
