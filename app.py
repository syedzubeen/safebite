import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from db.user_profiles import has_profile, get_profile
from handlers.onboarding import send_onboarding, register as register_onboarding
from handlers.silent_guardian import process_channel_message
from handlers.food_query import analyse_food_query
from handlers.restaurant_scan import register as register_restaurant_scan
from handlers.photo_handler import process_photo
from handlers.weekly_digest import register as register_digest
from handlers.assistant import register as register_assistant
from handlers.app_home import register as register_app_home
from utils.slack_search import search_workspace_food_context
from utils.block_builder import food_query_blocks

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

register_assistant(app)
register_app_home(app)
register_onboarding(app)
register_restaurant_scan(app)
register_digest(app)


@app.event("message")
def handle_message(event, client, say, logger):
    if event.get("bot_id"):
        return

    subtype = event.get("subtype")
    if subtype and subtype != "file_share":
        return

    channel_type = event.get("channel_type")
    user_id = event.get("user")

    # --- Channel messages: Silent Guardian ---
    if channel_type in ("channel", "group"):
        process_channel_message(event, client, logger)
        return

    # --- DMs only below ---
    if channel_type != "im":
        return

    # Photo upload in DM
    if event.get("files"):
        process_photo(event, client, say, logger)
        return

    # First-time user: onboarding
    if not has_profile(user_id):
        send_onboarding(client, user_id, event["channel"])
        return

    # Food query
    query = event.get("text", "").strip()
    if not query:
        return

    profile = get_profile(user_id)
    conditions = profile["conditions"]

    say("_Checking food safety for you..._")
    try:
        action_token = event.get("action_token")
        workspace_context = search_workspace_food_context(client, query, action_token)
        result = analyse_food_query(query, conditions, workspace_context)
        blocks, attachments = food_query_blocks(
            query=query,
            verdict=result.get("verdict", "Use Caution"),
            analysis=result.get("analysis", ""),
            alternatives=result.get("alternatives") or "No substitutions needed.",
            workspace_note=result.get("workspace_note") or "",
        )
        say(blocks=blocks, attachments=attachments, text=f"Food Safety: {result.get('verdict', '')}")
    except Exception as e:
        say(f"Sorry, I ran into an error analysing that. Please try again.\n`{e}`")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
