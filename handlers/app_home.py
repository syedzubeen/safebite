from db.user_profiles import get_profile, has_profile

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
}


def build_home_view(user_id: str) -> dict:
    if not has_profile(user_id):
        return _build_unregistered_view()
    profile = get_profile(user_id)
    conditions = profile.get("conditions", [])
    condition_str = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)
    return _build_registered_view(condition_str)


def _build_unregistered_view() -> dict:
    return {
        "type": "home",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Welcome to SafeBite* 🛡️\n\nYour silent food safety guardian for celiac disease. I protect you privately whenever food comes up in your team channels.",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "You haven't set up your profile yet. DM me to get started — it takes 10 seconds.",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Set up my profile"},
                        "style": "primary",
                        "action_id": "home_open_dm",
                    }
                ],
            },
        ],
    }


def _build_registered_view(condition_str: str) -> dict:
    return {
        "type": "home",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your SafeBite Profile* 🛡️\n*Condition:* {condition_str}\n*Status:* 🟢 Active — monitoring all channels",
                },
            },
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Quick Actions", "emoji": True},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔍 Check a dish", "emoji": True},
                        "action_id": "home_check_dish",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🍽️ Scan a restaurant", "emoji": True},
                        "action_id": "home_scan_restaurant",
                    },
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📋 Analyse a label", "emoji": True},
                        "action_id": "home_analyse_label",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✏️ Update my profile", "emoji": True},
                        "action_id": "home_update_profile",
                        "style": "danger",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "How SafeBite protects you", "emoji": True},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "🛡️ *Silent Guardian*\nMonitors channels and DMs you privately when food is mentioned"},
                    {"type": "mrkdwn", "text": "🍽️ *Menu Scanner*\nScans live restaurant menus for safe dishes"},
                    {"type": "mrkdwn", "text": "📍 *Nearby Finder*\nFinds gluten-free alternatives when nothing is safe"},
                    {"type": "mrkdwn", "text": "📋 *Label Reader*\nAnalyses ingredient labels and food photos"},
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🔒 Your condition is private. SafeBite never shares it with your team or workspace admins.",
                    }
                ],
            },
        ],
    }


def register(app):
    @app.event("app_home_opened")
    def handle_app_home_opened(event, client, logger):
        user_id = event["user"]
        try:
            view = build_home_view(user_id)
            client.views_publish(user_id=user_id, view=view)
        except Exception as e:
            logger.error(f"App Home error: {e}")

    def _open_modal(client, trigger_id, title, text):
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": title},
                "close": {"type": "plain_text", "text": "Got it"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": text},
                    }
                ],
            },
        )

    @app.action("home_check_dish")
    def handle_check_dish(ack, client, body):
        ack()
        _open_modal(client, body["trigger_id"], "Check a dish",
            "Go to the *Chat* tab and ask me anything:\n\n"
            "• _Is biryani safe for me?_\n"
            "• _Can I eat rajma chawal?_\n"
            "• _Is nihari gluten-free?_\n"
            "• _What about pav bhaji?_\n\n"
            "I'll search your team's Slack history for past discussions about that food and give you a personalised verdict.")

    @app.action("home_scan_restaurant")
    def handle_scan_restaurant(ack, client, body):
        ack()
        _open_modal(client, body["trigger_id"], "Scan a restaurant",
            "Go to the *Chat* tab and type:\n\n"
            "`scan [restaurant name]`\n\n"
            "Examples:\n"
            "• _scan Karim's Delhi_\n"
            "• _scan Paradise Biryani_\n"
            "• _scan Dominos India_\n\n"
            "I'll fetch the live menu and tell you exactly what's safe, what to modify, and what to avoid.")

    @app.action("home_analyse_label")
    def handle_analyse_label(ack, client, body):
        ack()
        _open_modal(client, body["trigger_id"], "Analyse a label",
            "Go to the *Chat* tab and upload a photo of the ingredient label.\n\n"
            "Add the word *ingredients* or *label* in your caption so I know to run a label scan.\n\n"
            "I'll extract every ingredient and flag hidden gluten sources like *maida*, *suji*, *hing*, or *barley malt*.")

    @app.action("home_update_profile")
    def handle_update_profile(ack, client, body):
        ack()
        from handlers.onboarding import WELCOME_BLOCKS
        user_id = body["user"]["id"]
        dm = client.conversations_open(users=user_id)
        client.chat_postMessage(
            channel=dm["channel"]["id"],
            blocks=WELCOME_BLOCKS,
            text="Update your SafeBite profile.",
        )

    @app.action("home_open_dm")
    def handle_open_dm(ack, client, body):
        ack()
        from handlers.onboarding import WELCOME_BLOCKS
        user_id = body["user"]["id"]
        dm = client.conversations_open(users=user_id)
        client.chat_postMessage(
            channel=dm["channel"]["id"],
            blocks=WELCOME_BLOCKS,
            text="Welcome to SafeBite — let's set up your profile.",
        )
