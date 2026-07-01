from django.conf import settings
from anthropic import Anthropic

from tutor.ai.base import AIProvider


class AnthropicProvider(AIProvider):
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        model_name: str,
    ) -> str:
        response = self.client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text_blocks = [
            block.text for block in response.content if block.type == "text"
        ]
        content = "".join(text_blocks).strip()
        if not content:
            raise RuntimeError("Anthropic returned an empty response")
        return content
