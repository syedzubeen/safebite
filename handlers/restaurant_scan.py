import os
import httpx
from utils.ai_client import ask

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")


def _search(query: str, num: int = 5) -> list[str]:
    """Run a single SerpAPI search and return text snippets."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num,
    }
    try:
        response = httpx.get("https://serpapi.com/search", params=params, timeout=15)
        data = response.json()
        snippets = []
        kg = data.get("knowledge_graph", {})
        if kg.get("title"):
            snippets.append(f"Restaurant: {kg.get('title')}, {kg.get('description', '')}")
        for result in data.get("organic_results", [])[:num]:
            snippet = result.get("snippet", "")
            if snippet:
                snippets.append(snippet)
        return snippets
    except Exception:
        return []


def fetch_menu(restaurant: str) -> str:
    """
    Run two searches for comprehensive menu coverage:
    1. General menu search
    2. Targeted search for rice/grilled/traditional dishes
    """
    general = _search(f"{restaurant} full menu dishes")
    targeted = _search(f"{restaurant} rice biryani grilled curry safe dishes")

    all_snippets = general + [s for s in targeted if s not in general]

    return "\n".join(all_snippets) if all_snippets else f"No menu information found for {restaurant}."


SCAN_PROMPT = """You are SafeBite, a food safety assistant for celiac disease.

You have been given real-time search results about a restaurant's menu.
Analyse the menu for a user with these conditions: {conditions}

Restaurant: {restaurant}
Menu search results:
{menu_info}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "safe": ["dish name", "dish name"],
  "modify": ["dish name - what to ask for"],
  "avoid": ["dish name - reason"],
  "tip": "1-2 sentence tip for talking to staff or avoiding cross-contamination."
}}

Keep each list to 5 items max. Be specific about dish names from the menu."""

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
    "type1_diabetes": "Type 1 Diabetes",
    "type2_diabetes": "Type 2 Diabetes",
}


def scan_restaurant(restaurant: str, conditions: list[str]) -> dict:
    import json, re
    menu_info = fetch_menu(restaurant)
    condition_labels = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)

    prompt = SCAN_PROMPT.replace("{restaurant}", restaurant) \
                        .replace("{conditions}", condition_labels) \
                        .replace("{menu_info}", menu_info)

    response = ask(prompt)
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"safe": [], "modify": [], "avoid": [], "tip": response}


def register(app):
    @app.command("/safebite")
    def handle_safebite_command(ack, body, client, respond):
        ack()

        user_id = body["user_id"]
        text = body.get("text", "").strip()

        from db.user_profiles import get_profile, has_profile

        if not text or text == "help":
            respond(
                "*SafeBite Commands:*\n"
                "• `/safebite scan [restaurant name]` — scan a restaurant menu for safe dishes\n"
                "• `/safebite profile` — view or update your dietary profile\n"
            )
            return

        if text == "profile":
            if not has_profile(user_id):
                respond("You don't have a profile yet. DM me to set one up!")
                return
            profile = get_profile(user_id)
            labels = [CONDITION_LABELS.get(c, c) for c in profile["conditions"]]
            respond(f"*Your SafeBite profile:*\n" + "\n".join(f"• {l}" for l in labels))
            return

        if text.lower().startswith("scan "):
            restaurant = text[5:].strip()
            if not restaurant:
                respond("Please provide a restaurant name. Example: `/safebite scan Karim's Delhi`")
                return

            if not has_profile(user_id):
                respond("Please set up your profile first by DMing me.")
                return

            profile = get_profile(user_id)
            conditions = profile["conditions"]

            # Respond ephemerally while scanning
            respond(f"_Scanning {restaurant} menu for you..._")

            try:
                from utils.block_builder import restaurant_scan_blocks, CONDITION_LABELS as BK_LABELS
                data = scan_restaurant(restaurant, conditions)
                condition_str = ", ".join(BK_LABELS.get(c, c) for c in conditions)
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
                client.chat_postEphemeral(
                    channel=body["channel_id"],
                    user=user_id,
                    blocks=blocks,
                    attachments=attachments,
                    text=f"SafeBite scan: {restaurant}",
                )
            except Exception as e:
                respond(f"Error scanning restaurant: `{e}`")
            return

        respond("Unknown command. Try `/safebite help`")
