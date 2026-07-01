"""Base types for reading AI providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ReadingGenerationResult:
    raw_text: str
    provider: str
    model: str


class ReadingAIProvider(Protocol):
    def generate_json(self, *, system_prompt: str, user_prompt: str, model: str) -> ReadingGenerationResult:
        ...
