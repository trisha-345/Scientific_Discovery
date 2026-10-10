import json
import re
from groq import Groq
from app.config import settings


_client = None

def get_client():
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def call_llm_json(system_prompt: str, user_prompt: str) -> dict | list:
    """Call Groq and parse JSON response. Retries once on parse failure."""
    client = get_client()

    for attempt in range(2):
        resp = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        content = resp.choices[0].message.content or ""

        # Strip markdown fences if model wrapped them
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt == 1:
                raise
            # On retry, ask more explicitly
            user_prompt = user_prompt + "\n\nReturn ONLY valid JSON. No markdown, no explanation."

    return {}