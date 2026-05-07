import os
import anthropic
from .base import LLMProvider

_SYSTEM_PROMPT = "You are a MySQL SQL generator. Return ONLY a single valid SQL query with no markdown, no explanation."


class ClaudeProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=500,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text.strip()
