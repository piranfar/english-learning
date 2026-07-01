from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        model_name: str,
    ) -> str:
        """Return the assistant's text response."""
