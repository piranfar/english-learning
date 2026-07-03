"""Resolve which AI provider runs for each task type."""

from __future__ import annotations

from collections import defaultdict

from django.conf import settings

from tutor.ai.provider_resolution import is_ai_provider_configured
from tutor.models import PromptTemplate, TaskProviderSetting


def _default_provider_for_task(task_type: str) -> str:
    if task_type.startswith("reading_"):
        return getattr(settings, "READING_AI_PROVIDER", "openai").lower().strip()
    return getattr(settings, "DEFAULT_AI_PROVIDER", "ollama").lower().strip()


def _first_active_provider(task_type: str, preferred: str | None = None) -> str | None:
    active = list(
        PromptTemplate.objects.filter(task_type=task_type, is_active=True)
        .order_by("provider")
        .values_list("provider", flat=True)
    )
    if not active:
        return preferred
    if preferred and preferred in active:
        return preferred
    return active[0]


def resolve_task_provider(task_type: str, requested_provider: str | None = None) -> str:
    """Priority: explicit request → staff DB setting → env default → first active prompt."""
    if requested_provider:
        cleaned = str(requested_provider).lower().strip()
        if cleaned:
            return cleaned

    try:
        setting = TaskProviderSetting.objects.get(task_type=task_type)
        if PromptTemplate.objects.filter(
            task_type=task_type,
            provider=setting.provider,
            is_active=True,
        ).exists():
            return setting.provider
    except TaskProviderSetting.DoesNotExist:
        pass

    preferred = _default_provider_for_task(task_type)
    resolved = _first_active_provider(task_type, preferred)
    return resolved or preferred


def resolve_reading_provider(requested: str | None = None, task_type: str = "reading_generate") -> str | None:
    """Reading generation with configured provider and API-key checks."""
    if requested:
        cleaned = str(requested).lower().strip()
        if is_ai_provider_configured(cleaned):
            return cleaned

    preferred = resolve_task_provider(task_type, None)
    for candidate in (preferred, "openai", "ollama"):
        if candidate and is_ai_provider_configured(candidate):
            active = PromptTemplate.objects.filter(
                task_type=task_type,
                provider=candidate,
                is_active=True,
            ).exists()
            if active or task_type == "reading_generate":
                return candidate
    return None


def task_provider_admin_rows() -> list[dict]:
    settings_map = {
        row.task_type: row.provider for row in TaskProviderSetting.objects.all()
    }
    prompts_by_task: dict[str, list[dict]] = defaultdict(list)
    for prompt in PromptTemplate.objects.all().order_by("provider"):
        prompts_by_task[prompt.task_type].append(
            {
                "provider": prompt.provider,
                "model_name": prompt.model_name,
                "is_active": prompt.is_active,
                "prompt_id": prompt.id,
            }
        )

    rows = []
    for task_type in sorted(prompts_by_task):
        providers = prompts_by_task[task_type]
        active = [item for item in providers if item["is_active"]]
        selected = settings_map.get(task_type)
        if not selected or not any(
            item["provider"] == selected and item["is_active"] for item in providers
        ):
            selected = _first_active_provider(task_type, _default_provider_for_task(task_type))
        selected_meta = next(
            (item for item in providers if item["provider"] == selected),
            None,
        )
        rows.append(
            {
                "task_type": task_type,
                "selected_provider": selected,
                "model_name": selected_meta["model_name"] if selected_meta else "",
                "available_providers": active,
                "configured_in_db": task_type in settings_map,
            }
        )
    return rows


def set_task_provider(task_type: str, provider: str) -> TaskProviderSetting:
    cleaned = str(provider).lower().strip()
    if not PromptTemplate.objects.filter(
        task_type=task_type,
        provider=cleaned,
        is_active=True,
    ).exists():
        raise ValueError(
            f"No active prompt for task '{task_type}' with provider '{cleaned}'. "
            "Enable that provider in Prompt management first."
        )
    obj, _created = TaskProviderSetting.objects.update_or_create(
        task_type=task_type,
        defaults={"provider": cleaned},
    )
    return obj


def bulk_set_task_providers(settings_payload: list[dict]) -> list[TaskProviderSetting]:
    updated = []
    for entry in settings_payload:
        task_type = entry.get("task_type")
        provider = entry.get("provider")
        if not task_type or not provider:
            continue
        updated.append(set_task_provider(task_type, provider))
    return updated
