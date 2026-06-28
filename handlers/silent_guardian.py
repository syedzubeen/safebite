from db.user_profiles import get_all_profiles
from utils.food_detector import detect_food
from utils.ai_client import ask

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
}

GUARDIAN_ALERT_PROMPT = """You are SafeBite, a private food safety guardian.

A food mention was detected in a team Slack channel. Analyse it for a user with the conditions below and send them a private, concise safety alert.

Food context from channel: {context}
Food items mentioned: {food_items}
User conditions: {conditions}

Respond in this format:

*SafeBite Alert* — food mentioned in your channel

_{context}_

*VERDICT:* [✅ Safe / ⚠️ Use Caution / ❌ Unsafe]

*WATCH OUT FOR:*
[1-2 specific risks for their condition. If safe, write "Nothing flagged."]

*SUGGESTION:*
[One practical tip. What to order, avoid, or ask the restaurant. 1-2 sentences max.]

Keep it brief. This is a private DM nudge, not a full report.

Formatting rules (strictly follow):
- Slack markdown only: *bold* for key terms, never **double asterisks**
- No em dashes. Use commas or periods instead.
- No extra emojis beyond the verdict line
- Keep bold minimal"""

MENU_SCAN_PROMPT = """You are SafeBite, a food safety assistant for celiac disease.

A restaurant was mentioned in a Slack channel. Scan its menu and identify safe dishes.

Restaurant: {restaurant}
Menu information: {menu_info}
User conditions: {conditions}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "verdict": "Safe dishes available" or "Limited options" or "Nothing safe",
  "safe_dishes": ["dish1", "dish2"],
  "avoid": ["dish1 - reason", "dish2 - reason"],
  "tip": "One sentence tip for talking to staff or avoiding cross-contamination."
}}"""


def _extract_restaurant(food_items: list[str]) -> str | None:
    """Extract the most likely restaurant name from food items."""
    restaurant_keywords = ["restaurant", "cafe", "dhaba", "kitchen", "bistro", "grill",
                          "ramen", "pizza", "burger", "sushi", "biryani house"]
    for item in food_items:
        item_lower = item.lower()
        if any(kw in item_lower for kw in restaurant_keywords):
            return item
        # Capitalized multi-word items are likely restaurant names
        words = item.split()
        if len(words) >= 2 and item[0].isupper():
            return item
    return None


def _has_safe_dishes(verdict: str) -> bool:
    """Return True only if verdict clearly indicates safe options."""
    return "safe dishes available" in verdict.lower()


def build_guardian_alert(context: str, food_items: list, conditions: list) -> str:
    condition_str = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)
    food_str = ", ".join(food_items)

    prompt = GUARDIAN_ALERT_PROMPT.format(
        context=context,
        food_items=food_str,
        conditions=condition_str,
    )
    return ask(prompt)


def build_menu_alert(restaurant: str, menu_info: str, conditions: list) -> dict:
    import json, re
    condition_str = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)
    prompt = MENU_SCAN_PROMPT.replace("{restaurant}", restaurant) \
                             .replace("{menu_info}", menu_info) \
                             .replace("{conditions}", condition_str)
    response = ask(prompt)
    # Extract JSON object robustly — find first { and last }
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"verdict": "Use Caution", "safe_dishes": [], "avoid": [], "tip": ""}


def process_channel_message(event, client, logger):
    message_text = event.get("text", "").strip()
    if not message_text or len(message_text) < 5:
        return

    sender_id = event.get("user")

    try:
        detection = detect_food(message_text)
    except Exception as e:
        logger.error(f"Food detection error: {e}")
        return

    if not detection.get("is_food_mention"):
        return

    context = detection.get("context", message_text)
    food_items = detection.get("food_items", [])

    # Try to extract a restaurant name for menu scanning
    restaurant_name = _extract_restaurant(food_items)

    all_profiles = get_all_profiles()
    for user_id, profile in all_profiles.items():
        import os
        if os.environ.get("DEMO_MODE", "false").lower() != "true":
            if user_id == sender_id:
                continue

        conditions = profile.get("conditions", [])
        if not conditions:
            continue

        try:
            dm = client.conversations_open(users=user_id)
            dm_channel = dm["channel"]["id"]

            if restaurant_name:
                from handlers.restaurant_scan import fetch_menu
                from utils.nearby_restaurants import find_nearby_gluten_free, format_nearby_suggestions
                from utils.block_builder import restaurant_scan_blocks
                from utils.block_builder import CONDITION_LABELS as BK_LABELS

                menu_info = fetch_menu(restaurant_name)
                data = build_menu_alert(restaurant_name, menu_info, conditions)

                condition_str = ", ".join(BK_LABELS.get(c, c) for c in conditions)
                blocks, attachments = restaurant_scan_blocks(
                    restaurant=restaurant_name,
                    safe=data.get("safe_dishes", []),
                    modify=[],
                    avoid=data.get("avoid", []),
                    tips=data.get("tip", ""),
                    conditions=condition_str,
                )

                # Append nearby alternatives only when verdict is "Nothing safe"
                if data.get("verdict", "").lower() == "nothing safe":
                    nearby = find_nearby_gluten_free(restaurant_name, location_context=message_text)
                    suggestion = format_nearby_suggestions(restaurant_name, nearby)
                    attachments[0]["blocks"].append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": suggestion},
                    })

                client.chat_postMessage(channel=dm_channel, blocks=blocks, attachments=attachments,
                                        text=f"SafeBite Alert: {restaurant_name}")
            else:
                alert = build_guardian_alert(context, food_items, conditions)
                client.chat_postMessage(channel=dm_channel, text=alert)

        except Exception as e:
            logger.error(f"Failed to send guardian alert to {user_id}: {e}")
