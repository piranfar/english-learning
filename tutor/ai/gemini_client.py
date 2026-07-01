"""Google Gemini chat helper — optional cloud provider via google-genai."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from tutor.ai.exceptions import ProviderUnavailableError


def call_gemini_chat(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    json_mode: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Call Gemini and return normalized provider metadata + content."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise ProviderUnavailableError("gemini", "api_key_missing")

    model_name = model or getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")

    from google import genai
    from google.genai import types

    config_kwargs: dict[str, Any] = {}
    if system_prompt:
        config_kwargs["system_instruction"] = system_prompt
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    if max_tokens is not None:
        config_kwargs["max_output_tokens"] = max_tokens

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )

    content = (getattr(response, "text", None) or "").strip()
    if not content:
        raise RuntimeError("Gemini returned an empty response")

    result: dict[str, Any] = {
        "provider": "gemini",
        "model": model_name,
        "content": content,
    }
    if hasattr(response, "model_dump"):
        try:
            result["raw"] = response.model_dump()
        except Exception:
            pass
    return result
