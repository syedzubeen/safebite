import asyncio
import os
import threading

from db.user_profiles import get_all_profiles
from utils.ai_client import ask

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
}

DIGEST_PROMPT = """You are SafeBite, a personal food safety assistant for someone with celiac disease.

Write a warm, informative weekly digest. Structure it clearly with these sections:

1. A friendly greeting (1 sentence)

2. *This Week's Gluten Watch* — 2-3 specific hidden gluten risks to be aware of this week, focused on everyday situations (restaurant meals, packaged foods, team lunches). Be specific and practical, not generic.

3. *Indian Cuisine Spotlight* — one Indian dish or ingredient explained in depth. Cover whether it is safe, what the hidden risks are, and what to ask for at a restaurant. Examples: nihari, hing, biryani, korma, pav bhaji, samosa, dhokla, idli, dosa, seekh kebab.

4. *Safe Swap of the Week* — one specific unsafe food and its gluten-free alternative. Keep it practical and real.

5. *Quick Tips* — 2 bullet points of actionable advice for the week.

6. A warm closing line.

Conditions: {conditions}

Formatting rules:
- Use *bold* for section headers and key terms (Slack markdown, single asterisks)
- No em dashes. Use commas or periods instead.
- Bullet points with a hyphen (-)
- No extra emojis beyond 💡 for tips
- Write conversationally, not clinically
- Total length: 200-250 words"""


async def _send_via_gmail_mcp(to_address: str, subject: str, body: str) -> str:
    """Connect to SafeBite's Gmail MCP server and send an email."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    python_exe = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".venv", "Scripts", "python.exe"
    )
    server_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mcp_server", "gmail_server.py"
    )

    server_params = StdioServerParameters(
        command=python_exe,
        args=[server_script],
        env={**os.environ},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "send_email",
                {"to_address": to_address, "subject": subject, "body": body},
            )
            if result and result.content:
                return result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
            return "Sent"


def send_digest_email(to_address: str, subject: str, body: str) -> str:
    """Run the async MCP call in a separate thread to avoid event loop conflicts."""
    result = [None]
    error = [None]

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(_send_via_gmail_mcp(to_address, subject, body))
        except Exception as e:
            error[0] = e
        finally:
            loop.close()

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=30)

    if error[0]:
        return f"Error: {error[0]}"
    return result[0] or "Sent"


def send_weekly_digest(client, logger):
    all_profiles = get_all_profiles()

    if not all_profiles:
        logger.info("Weekly digest: no profiles found, skipping.")
        return

    for user_id, profile in all_profiles.items():
        conditions = profile.get("conditions", [])
        if not conditions:
            continue

        condition_str = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)

        try:
            prompt = DIGEST_PROMPT.replace("{conditions}", condition_str)
            digest_text = ask(prompt)

            # Get user's email from Slack profile
            user_info = client.users_info(user=user_id)
            profile = user_info.get("user", {}).get("profile", {})
            email = profile.get("email", "")
            print(f"[digest] user={user_id} email={email} profile_keys={list(profile.keys())}")

            subject = "Your SafeBite Weekly Digest"
            body = f"SafeBite Weekly Digest\n\n{digest_text}\n\nStay safe this week."

            if email:
                # Send via Gmail MCP server
                mcp_result = send_digest_email(email, subject, body)
                logger.info(f"Gmail MCP: {mcp_result}")
            else:
                logger.warning(f"No email found for {user_id}, falling back to Slack DM")

            # Also send in Slack DM as backup
            dm = client.conversations_open(users=user_id)
            dm_channel = dm["channel"]["id"]
            client.chat_postMessage(
                channel=dm_channel,
                text=f"📅 *Your SafeBite Weekly Digest*\n\n{digest_text}",
            )
            logger.info(f"Weekly digest sent to {user_id}")

        except Exception as e:
            logger.error(f"Failed to send digest to {user_id}: {e}")


def register(app):
    @app.command("/safebite-digest")
    def trigger_digest(ack, body, client, respond, logger):
        ack()
        respond("_Sending weekly digest via email and Slack..._")
        send_weekly_digest(client, logger)
        respond("✅ Weekly digest sent to all registered users via Gmail and Slack DM.")
