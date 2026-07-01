"""Local-first AI provider resolution with safe fallbacks."""

from __future__ import annotations

from django.conf import settings

from tutor.ai.exceptions import ProviderUnavailableError


def is_ai_provider_configured(provider: str) -> bool:
    """Return True when the provider can be invoked (API key present if required)."""
    key = (provider or "").lower().strip()
    if not key:
        return False
    if key == "ollama":
        return True
    if key == "openai":
        return bool(getattr(settings, "OPENAI_API_KEY", ""))
    if key == "anthropic":
        return bool(getattr(settings, "ANTHROPIC_API_KEY", ""))
    if key == "gemini":
        return bool(getattr(settings, "GEMINI_API_KEY", ""))
    return False


def build_provider_attempt_order(requested_provider: str | None) -> list[str]:
    """Priority: explicit request → DEFAULT_AI_PROVIDER → Ollama."""
    order: list[str] = []
    for candidate in (
        requested_provider,
        getattr(settings, "DEFAULT_AI_PROVIDER", "ollama"),
        "ollama",
    ):
        if not candidate:
            continue
        normalized = str(candidate).lower().strip()
        if normalized and normalized not in order:
            order.append(normalized)
    return order


def is_provider_error(exc: BaseException) -> bool:
    """True for missing keys, connectivity, or provider failures — not parse errors."""
    if isinstance(exc, (RuntimeError, ProviderUnavailableError)):
        return True
    if isinstance(exc, ValueError):
        message = str(exc).lower()
        if "parse" in message or "too short" in message or "must include" in message:
            return False
        if "no active prompt" in message:
            return True
        return False
    return False
