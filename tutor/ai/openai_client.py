"""OpenAI chat helper — optional cloud provider via openai SDK."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from tutor.ai.exceptions import ProviderUnavailableError


def call_openai_chat(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    json_mode: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Call OpenAI chat completions and return normalized provider metadata + content."""
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise ProviderUnavailableError("openai", "api_key_missing")

    model_name = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    request_kwargs: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
    }
    if temperature is not None:
        request_kwargs["temperature"] = temperature
    if max_tokens is not None:
        # GPT-5+ and newer models reject max_tokens; max_completion_tokens works across models.
        request_kwargs["max_completion_tokens"] = max_tokens
    if json_mode:
        request_kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**request_kwargs)

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("OpenAI returned an empty response")

    result: dict[str, Any] = {
        "provider": "openai",
        "model": model_name,
        "content": content,
    }
    if hasattr(response, "model_dump"):
        try:
            result["raw"] = response.model_dump()
        except Exception:
            pass
    return result
