from abc import ABC, abstractmethod


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        """Return transcribed text from audio bytes."""


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Return audio bytes (MP3)."""
