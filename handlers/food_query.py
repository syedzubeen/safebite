import json
import re
from utils.ai_client import ask

CONDITION_LABELS = {
    "celiac": "Celiac Disease (strict gluten-free required)",
}

SYSTEM_PROMPT = """You are SafeBite, a food safety assistant specialising in celiac disease.
You have deep knowledge of Indian cuisine (dal, biryani, nihari, rajma, kadhi, korma, roti, naan, etc.)
as well as global cuisines.

Respond with ONLY valid JSON in this exact structure (no markdown, no explanation):
{
  "verdict": "Safe" or "Use Caution" or "Unsafe",
  "analysis": "2-3 sentences explaining why, mentioning specific ingredients of concern. For Indian dishes include knowledge of hidden risks like hing with wheat filler, maida thickeners, etc.",
  "alternatives": "1-2 specific safer alternatives if unsafe or caution. Write null if safe.",
  "workspace_note": "If workspace context is provided and relevant, one sentence referencing it. Otherwise null."
}"""


def analyse_food_query(query: str, conditions: list[str], workspace_context: str = "") -> dict:
    condition_str = "\n".join(f"- {CONDITION_LABELS[c]}" for c in conditions if c in CONDITION_LABELS)

    prompt = f"""{SYSTEM_PROMPT}

User conditions:
{condition_str}

User question: {query}"""

    if workspace_context:
        prompt += f"\n\nWorkspace context (use if relevant): {workspace_context}"

    response = ask(prompt)

    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "verdict": "Use Caution",
        "analysis": response,
        "alternatives": None,
        "workspace_note": None,
    }
