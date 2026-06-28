from slack_bolt import Assistant, BoltContext, Say
from slack_sdk import WebClient

from db.user_profiles import get_profile, has_profile, save_profile
from handlers.food_query import analyse_food_query
from handlers.restaurant_scan import scan_restaurant
from utils.slack_search import search_workspace_food_context
from utils.block_builder import food_query_blocks

SUGGESTED_PROMPTS = [
    {"title": "Check a dish", "message": "Is biryani safe for me?"},
    {"title": "Check an Indian dish", "message": "Is rajma chawal safe for me?"},
    {"title": "Scan a restaurant", "message": "Scan Karim's Delhi for safe dishes"},
    {"title": "My profile", "message": "Show my dietary profile"},
]

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
}


def register(app):
    assistant = Assistant()

    @assistant.thread_started
    def handle_thread_started(
        payload, set_suggested_prompts, say, context: BoltContext, client: WebClient
    ):
        user_id = payload.get("user", {}).get("id") if isinstance(payload.get("user"), dict) else context.get("user_id")

        if user_id and has_profile(user_id):
            profile = get_profile(user_id)
            conditions = profile["conditions"]
            labels = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)
            say(
                f"👋 Hi! I'm SafeBite, your food safety guardian.\n\n"
                f"I'm watching out for *{labels}*. Ask me anything about food safety, "
                f"or try one of the suggestions below."
            )
        else:
            from handlers.onboarding import WELCOME_BLOCKS
            say(blocks=WELCOME_BLOCKS, text="Welcome to SafeBite — let's set up your dietary profile.")

        set_suggested_prompts(prompts=SUGGESTED_PROMPTS)

    @assistant.user_message
    def handle_user_message(
        payload,
        set_status,
        say,
        context: BoltContext,
        client: WebClient,
    ):
        user_id = context.get("user_id")
        message_text = payload.get("text", "").strip()
        action_token = payload.get("action_token")
        channel_id = payload.get("channel_id") or payload.get("channel")
        thread_ts = payload.get("thread_ts") or payload.get("ts")

        # Handle photo uploads
        if payload.get("files"):
            if not has_profile(user_id):
                say("Please set up your profile first by sending me a message.")
                return
            set_status("Analysing your image...")
            from handlers.photo_handler import process_photo
            import logging
            process_photo(payload, client, say, logging.getLogger(__name__))
            return

        if not message_text:
            return

        # Handle "Reply" keyword — user wants nearby alternatives
        if message_text.strip().lower() in ("reply", "find nearby", "nearby alternatives", "alternatives"):
            set_status("Finding nearby gluten-free restaurants...")
            say("To find nearby gluten-free alternatives, use `/safebite scan [restaurant name]` or ask me: _find gluten-free restaurants near [place]_")
            return

        # Handle profile request
        if "profile" in message_text.lower():
            if not has_profile(user_id):
                say("You don't have a profile yet. Please DM me directly to set one up with your conditions.")
                return
            profile = get_profile(user_id)
            labels = [CONDITION_LABELS.get(c, c) for c in profile["conditions"]]
            say("*Your SafeBite Profile:*\n" + "\n".join(f"• {l}" for l in labels))
            return

        # Handle restaurant scan
        lower = message_text.lower()
        if lower.startswith("scan "):
            restaurant = message_text[5:].strip()
            if not restaurant:
                say("Please tell me which restaurant to scan. Example: *Scan Karim's Delhi*")
                return
            if not has_profile(user_id):
                say("Please set up your profile first by DMing me.")
                return

            set_status("Scanning restaurant menu...")
            profile = get_profile(user_id)
            try:
                from utils.block_builder import restaurant_scan_blocks, CONDITION_LABELS as BK_LABELS
                data = scan_restaurant(restaurant, profile["conditions"])
                condition_str = ", ".join(BK_LABELS.get(c, c) for c in profile["conditions"])
                tip = data.get("tip", "") or ""
                if isinstance(tip, list):
                    tip = " ".join(tip)
                elif not isinstance(tip, str):
                    tip = str(tip)
                blocks, attachments = restaurant_scan_blocks(
                    restaurant=restaurant,
                    safe=data.get("safe", []) or [],
                    modify=data.get("modify", []) or [],
                    avoid=data.get("avoid", []) or [],
                    tips=tip,
                    conditions=condition_str,
                )
                say(blocks=blocks, attachments=attachments, text=f"SafeBite scan: {restaurant}")
            except Exception as e:
                say(f"Sorry, I couldn't scan that restaurant. Try again?\n`{e}`")
            return

        # Default: food safety query
        if not has_profile(user_id):
            from handlers.onboarding import WELCOME_BLOCKS
            say(blocks=WELCOME_BLOCKS, text="Welcome to SafeBite — let's set up your dietary profile.")
            return

        set_status("Checking food safety...")

        conditions = get_profile(user_id)["conditions"] if has_profile(user_id) else ["celiac"]

        try:
            assistant_thread = payload.get("assistant_thread", {})
            action_token = payload.get("action_token") or (assistant_thread.get("action_token") if isinstance(assistant_thread, dict) else None)
            workspace_context = search_workspace_food_context(client, message_text, action_token)
            result = analyse_food_query(message_text, conditions, workspace_context)
            blocks, attachments = food_query_blocks(
                query=message_text,
                verdict=result.get("verdict", "Use Caution"),
                analysis=result.get("analysis", ""),
                alternatives=result.get("alternatives") or "No substitutions needed.",
                workspace_note=result.get("workspace_note") or "",
            )
            say(blocks=blocks, attachments=attachments, text=f"Food Safety: {result.get('verdict', '')}")
        except Exception as e:
            say(f"Sorry, I ran into an error. Please try again.\n`{e}`")

    app.use(assistant)
