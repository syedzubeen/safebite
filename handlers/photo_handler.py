import os
import httpx
from google import genai
from google.genai import types

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_MODEL = "gemini-2.5-flash"

CONDITION_LABELS = {
    "celiac": "Celiac Disease (strict gluten-free required)",
    "type1_diabetes": "Type 1 Diabetes (track GI, glycemic load, and carbs)",
    "type2_diabetes": "Type 2 Diabetes (manage blood sugar, prefer low GI foods)",
}

LABEL_SCAN_PROMPT = """You are SafeBite, a food safety expert for celiac disease and diabetes.

Analyse this ingredient label image for a user with: {conditions}

1. Assess image quality and label legibility
2. Extract ALL ingredients listed on the label
3. Flag any dangerous ingredients for their conditions

For Celiac: flag wheat, barley, rye, oats, maida, suji, atta, semolina, wheat starch, barley malt, modified starch (if wheat-based), hing/asafoetida (often contains wheat filler), malt vinegar, soy sauce (unless GF)
For Diabetes: flag sugar, glucose, dextrose, corn syrup, high-fructose corn syrup, refined flour, white rice flour, maltodextrin

Respond in this format:

*Ingredient Label Analysis*

*VERDICT:* [✅ Safe / ⚠️ Use Caution / ❌ Unsafe]

*CONFIDENCE:* [🟢 High (90-100%) / 🟡 Medium (60-89%) / 🔴 Low (below 60%)]

_Legend:_
_🟢 High: Label fully legible, all ingredients extracted with certainty._
_🟡 Medium: Partially obscured or blurry, some ingredients may be missed._
_🔴 Low: Label unclear, verdict may be unreliable. Retake the photo for best results._

*FLAGGED INGREDIENTS:*
[Use 🔴 before each flagged ingredient and explain why. If none, write "None detected."]

*FULL INGREDIENT LIST:*
[All ingredients extracted from the label, comma separated]

*VERDICT EXPLANATION:*
[1-2 sentences on overall safety]

Formatting rules: Slack markdown only (*bold* not **bold**), no em dashes, no extra emojis."""

FOOD_PHOTO_PROMPT = """You are SafeBite, a food safety expert for celiac disease and diabetes.

Analyse this food photo for a user with: {conditions}

Identify the dish and its likely ingredients, then assess safety.

Respond in this format:

*Food Photo Analysis*

IDENTIFIED DISH: [What you see]
CONFIDENCE: [High / Medium / Low]

*VERDICT:* [✅ Safe / ⚠️ Use Caution / ❌ Unsafe]

*CONFIDENCE:* [🟢 High (90-100%) / 🟡 Medium (60-89%) / 🔴 Low (below 60%)]

_Legend:_
_🟢 High: Dish clearly identified, ingredients well-known._
_🟡 Medium: Dish likely identified but ingredients inferred._
_🔴 Low: Dish unclear, verdict may be unreliable._

*INGREDIENTS OF CONCERN:*
[Use 🔴 before each risky ingredient. For Indian dishes, check for hing, maida thickeners, wheat-based spice mixes.]

*ANALYSIS:*
[2-3 sentences on overall safety]

*SAFE ALTERNATIVES:*
[If unsafe, suggest a safer swap. If safe, write "Enjoy!"]

_Note: Photo analysis is probabilistic. Always confirm with the restaurant or cook._

Formatting rules: Slack markdown only (*bold* not **bold**), no em dashes, no extra emojis."""


def _download_image(url: str, token: str) -> bytes:
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.content


def _analyse_image(image_bytes: bytes, mime_type: str, prompt: str) -> str:
    response = _client.models.generate_content(
        model=_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ],
    )
    return response.text.strip()


def process_photo(event, client, say, logger):
    files = event.get("files", [])
    if not files:
        return

    user_id = event.get("user")

    from db.user_profiles import get_profile, has_profile

    if not has_profile(user_id):
        say("Please set up your profile first by sending me a message.")
        return

    profile = get_profile(user_id)
    conditions = profile["conditions"]
    condition_str = ", ".join(CONDITION_LABELS.get(c, c) for c in conditions)

    bot_token = client.token

    for file in files:
        mime_type = file.get("mimetype", "image/jpeg")
        if not mime_type.startswith("image/"):
            continue

        url = file.get("url_private_download") or file.get("url_private")
        if not url:
            continue

        say("_Analysing your image..._")

        try:
            image_bytes = _download_image(url, bot_token)

            caption = (event.get("text") or event.get("message", {}).get("text") or "").lower()
            filename = file.get("name", "").lower()
            title = file.get("title", "").lower()

            is_label_scan = any(word in caption + filename + title for word in [
                "label", "ingredient", "packet", "package", "ingredients", "wrapper"
            ])

            prompt_template = LABEL_SCAN_PROMPT if is_label_scan else FOOD_PHOTO_PROMPT
            prompt = prompt_template.replace("{conditions}", condition_str)

            result = _analyse_image(image_bytes, mime_type, prompt)
            say(result)

        except Exception as e:
            logger.error(f"Photo analysis error: {e}")
            say(f"Sorry, I couldn't analyse that image. Please try again.\n`{e}`")
