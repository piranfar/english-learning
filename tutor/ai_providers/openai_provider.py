"""OpenAI provider for reading generation (JSON output)."""

from __future__ import annotations

from django.conf import settings

from tutor.ai_providers.base import ReadingGenerationResult


class OpenAIReadingProvider:
    def generate_json(self, *, system_prompt: str, user_prompt: str, model: str) -> ReadingGenerationResult:
        from tutor.ai.openai_client import ProviderUnavailableError, call_openai_chat

        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("openai_not_configured")

        model_name = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        try:
            result = call_openai_chat(
            user_prompt,
            system_prompt=system_prompt,
            model=model_name,
            json_mode=True,
            temperature=0.6,
            max_tokens=4000,
            )
        except ProviderUnavailableError as exc:
            raise RuntimeError("openai_not_configured") from exc
        return ReadingGenerationResult(
            raw_text=result["content"],
            provider="openai",
            model=model_name,
        )
