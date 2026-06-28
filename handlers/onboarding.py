from db.user_profiles import has_profile, save_profile


ONBOARDING_GIF_URL = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHpyeXZ4Y2M0a3NmOHA2cjU2M3NybnlmdW1zaGJrOWs5YmdvOGhnNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/oX1CAMyBNiYecoZV1r/giphy.gif"

WELCOME_BLOCKS = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "*Welcome to SafeBite* 🛡️\n\n"
                "I'm your silent food safety guardian. I'll privately alert you "
                "whenever food comes up in your Slack channels — checking it against "
                "your dietary conditions before you ever take a bite."
            ),
        },
    },
    {
        "type": "image",
        "image_url": ONBOARDING_GIF_URL,
        "alt_text": "SafeBite — your food safety guardian",
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*To get started, confirm your dietary condition:*",
        },
    },
    {
        "type": "actions",
        "block_id": "onboarding_conditions",
        "elements": [
            {
                "type": "checkboxes",
                "action_id": "condition_select",
                "options": [
                    {
                        "text": {"type": "mrkdwn", "text": "*Celiac Disease*, strict gluten-free required"},
                        "value": "celiac",
                    },
                    # Diabetes support coming in a future release
                    # {"text": {"type": "mrkdwn", "text": "*Type 1 Diabetes*"}, "value": "type1_diabetes"},
                    # {"text": {"type": "mrkdwn", "text": "*Type 2 Diabetes*"}, "value": "type2_diabetes"},
                ],
            }
        ],
    },
    {
        "type": "actions",
        "block_id": "onboarding_submit",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Save My Profile"},
                "style": "primary",
                "action_id": "save_profile",
            }
        ],
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🔒 Your conditions are private. Only you will ever see SafeBite's alerts.",
            }
        ],
    },
]


def send_onboarding(client, user_id: str, channel_id: str):
    client.chat_postMessage(
        channel=channel_id,
        blocks=WELCOME_BLOCKS,
        text="Welcome to SafeBite — let's set up your dietary profile.",
    )


def register(app):
    # Track checkbox state per user session
    _pending_conditions: dict[str, list[str]] = {}

    @app.action("condition_select")
    def handle_condition_select(ack, body):
        ack()
        user_id = body["user"]["id"]
        selected = body["actions"][0].get("selected_options", [])
        _pending_conditions[user_id] = [opt["value"] for opt in selected]

    @app.action("save_profile")
    def handle_save_profile(ack, body, client, say):
        ack()
        user_id = body["user"]["id"]
        conditions = _pending_conditions.get(user_id, [])

        if not conditions:
            say("Please select at least one condition before saving.")
            return

        save_profile(user_id, conditions)

        labels = {
            "celiac": "Celiac Disease",
            "type1_diabetes": "Type 1 Diabetes",
            "type2_diabetes": "Type 2 Diabetes",
        }
        condition_list = "\n".join(f"• {labels[c]}" for c in conditions)

        client.chat_postMessage(
            channel=body["channel"]["id"],
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"✅ *Profile saved!*\n\n"
                            f"I'll silently protect you from food that conflicts with:\n{condition_list}\n\n"
                            f"*What I'll do:*\n"
                            f"• Watch food mentions in your channels and DM you privately\n"
                            f"• Answer food safety questions anytime — just ask me here\n"
                            f"• Scan restaurant menus on request\n\n"
                            f"To update your profile anytime, type `/safebite profile`"
                        ),
                    },
                }
            ],
            text="Profile saved! SafeBite is now watching out for you.",
        )
