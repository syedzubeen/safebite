import os
from google import genai

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_MODEL = "gemini-2.5-flash"


def ask(prompt: str) -> str:
    response = _client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text.strip()
