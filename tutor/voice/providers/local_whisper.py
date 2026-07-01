import os
import tempfile

from django.conf import settings

from tutor.voice.base import TranscriptionProvider


class LocalWhisperProvider(TranscriptionProvider):
    def __init__(self):
        self.model_name = settings.LOCAL_WHISPER_MODEL

    def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError(
                "Local Whisper requires: pip install openai-whisper (and ffmpeg on PATH)"
            ) from exc

        suffix = os.path.splitext(filename or "audio.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            model = whisper.load_model(self.model_name)
            result = model.transcribe(tmp_path, language="en")
        finally:
            os.unlink(tmp_path)

        text = (result.get("text") or "").strip()
        if not text:
            raise RuntimeError("Local Whisper returned an empty transcription")
        return text
