from abc import ABC, abstractmethod


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        """Return transcribed text from raw audio bytes."""
