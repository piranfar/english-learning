from tutor.ai.base import AIProvider
from tutor.ai.providers.anthropic import AnthropicProvider
from tutor.ai.providers.gemini import GeminiProvider
from tutor.ai.providers.ollama import OllamaProvider
from tutor.ai.providers.openai import OpenAIProvider

_PROVIDERS: dict[str, type[AIProvider]] = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str) -> AIProvider:
    key = name.lower().strip()
    provider_cls = _PROVIDERS.get(key)
    if provider_cls is None:
        supported = ", ".join(sorted(_PROVIDERS))
        raise ValueError(f"Unknown AI provider '{name}'. Supported: {supported}")
    return provider_cls()
