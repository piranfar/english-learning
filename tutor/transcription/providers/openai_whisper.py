import io

from django.conf import settings
from openai import OpenAI

from tutor.transcription.base import TranscriptionProvider


class OpenAIWhisperProvider(TranscriptionProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it in .env for openai_whisper."
            )
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL

    def transcribe(self, audio_bytes: bytes, filename: str, model: str | None = None) -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename or "audio.webm"
        transcription_model = model or self.model
        try:
            response = self.client.audio.transcriptions.create(
                model=transcription_model,
                file=audio_file,
                language="en",
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI Whisper transcription failed: {exc}") from exc

        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Whisper returned an empty transcription")
        return text
