"""Resolve whether a learner may override the AI provider."""

from __future__ import annotations

from django.conf import settings


def resolve_user_provider(request, requested_provider: str | None) -> str | None:
    """Staff (and optionally learners) may select provider; others use template default."""
    if not requested_provider:
        return None
    cleaned = str(requested_provider).strip()
    if not cleaned:
        return None
    allow_learner = getattr(settings, "ALLOW_LEARNER_PROVIDER_OVERRIDE", False)
    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_staff:
        return cleaned
    if allow_learner:
        return cleaned
    return None
