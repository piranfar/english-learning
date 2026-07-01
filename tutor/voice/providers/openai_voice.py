import io

from django.conf import settings
from openai import OpenAI

from tutor.voice.base import TranscriptionProvider, TTSProvider


class OpenAIWhisperProvider(TranscriptionProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL

    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename or "audio.webm"
        response = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,
            language="en",
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Whisper returned an empty transcription")
        return text


class OpenAITTSProvider(TTSProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_TTS_MODEL
        self.voice = settings.OPENAI_TTS_VOICE

    def synthesize(self, text: str) -> bytes:
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        return response.content
