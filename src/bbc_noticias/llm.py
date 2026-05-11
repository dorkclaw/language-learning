"""
OpenRouter LLM client — wraps OpenAI-compatible API for BBC Noticias bot.
Uses openrouter/auto (or configured model) via the OpenAI SDK.
"""
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class LLM:
    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your .env file or set the environment variable."
            )
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE,
        )
        self.model = OPENROUTER_MODEL

    def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a chat completion and return the text response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    def complete_json(self, system: str, user: str, temperature: float = 0.3) -> dict:
        """Same as complete() but parses the response as JSON."""
        import json, re
        text = self.complete(system, user, temperature)
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        return json.loads(text)