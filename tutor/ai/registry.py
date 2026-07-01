"""Central AI provider registry — metadata for all supported providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderSpec:
    id: str
    display_name: str
    required_env: str | None
    default_model_setting: str | None
    cloud: bool
    supported_tasks: tuple[str, ...]


AI_PROVIDER_REGISTRY: dict[str, AIProviderSpec] = {
    "ollama": AIProviderSpec(
        id="ollama",
        display_name="Ollama (local)",
        required_env=None,
        default_model_setting="DEFAULT_OLLAMA_MODEL",
        cloud=False,
        supported_tasks=(
            "grammar",
            "writing",
            "speaking",
            "reading",
            "listening",
            "vocabulary",
            "lesson_generation",
        ),
    ),
    "openai": AIProviderSpec(
        id="openai",
        display_name="OpenAI GPT",
        required_env="OPENAI_API_KEY",
        default_model_setting="OPENAI_MODEL",
        cloud=True,
        supported_tasks=(
            "grammar",
            "writing",
            "speaking",
            "reading",
            "listening",
            "vocabulary",
            "lesson_generation",
        ),
    ),
    "anthropic": AIProviderSpec(
        id="anthropic",
        display_name="Anthropic Claude",
        required_env="ANTHROPIC_API_KEY",
        default_model_setting="ANTHROPIC_MODEL",
        cloud=True,
        supported_tasks=(
            "grammar",
            "writing",
            "speaking",
            "reading",
            "listening",
            "vocabulary",
            "lesson_generation",
        ),
    ),
    "gemini": AIProviderSpec(
        id="gemini",
        display_name="Google Gemini",
        required_env="GEMINI_API_KEY",
        default_model_setting="GEMINI_MODEL",
        cloud=True,
        supported_tasks=(
            "grammar",
            "writing",
            "speaking",
            "reading",
            "listening",
            "vocabulary",
            "lesson_generation",
        ),
    ),
}


def list_ai_providers() -> list[AIProviderSpec]:
    return [AI_PROVIDER_REGISTRY[key] for key in sorted(AI_PROVIDER_REGISTRY)]


def get_ai_provider_spec(provider_id: str) -> AIProviderSpec | None:
    return AI_PROVIDER_REGISTRY.get((provider_id or "").lower().strip())
