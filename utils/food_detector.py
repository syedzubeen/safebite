import json
import re

from utils.ai_client import ask

FOOD_DETECTION_PROMPT = """You are a food mention detector. Given a Slack message, determine if it contains any reference to food, drinks, restaurants, ordering food, or eating plans.

Respond with ONLY this JSON format (no markdown, no explanation):
{"is_food_mention": true/false, "food_items": ["item1", "item2"], "context": "one sentence summary of what food situation is being discussed"}

Examples:
- "Let's grab lunch at Karim's" → {"is_food_mention": true, "food_items": ["lunch", "Karim's restaurant"], "context": "Team planning lunch at Karim's restaurant"}
- "Ordering Dominos, who's in?" → {"is_food_mention": true, "food_items": ["Dominos pizza"], "context": "Someone ordering Dominos pizza for the team"}
- "The meeting is at 3pm" → {"is_food_mention": false, "food_items": [], "context": ""}
- "biryani from Paradise restaurant today!" → {"is_food_mention": true, "food_items": ["biryani", "Paradise restaurant"], "context": "Team ordering biryani from Paradise restaurant"}

Message: {message}"""


def detect_food(message: str) -> dict:
    prompt = FOOD_DETECTION_PROMPT.replace("{message}", message)
    response = ask(prompt)

    match = re.search(r'\{.*?\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"is_food_mention": False, "food_items": [], "context": ""}
