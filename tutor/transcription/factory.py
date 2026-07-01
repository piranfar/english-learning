import os

from django.conf import settings

from tutor.transcription.base import TranscriptionProvider
from tutor.transcription.providers.local_whisper import LocalWhisperProvider
from tutor.transcription.providers.openai_whisper import OpenAIWhisperProvider

_TRANSCRIPTION_PROVIDERS: dict[str, type[TranscriptionProvider]] = {
    "openai_whisper": OpenAIWhisperProvider,
    "local_whisper": LocalWhisperProvider,
}

ALLOWED_AUDIO_EXTENSIONS = {
    ".webm",
    ".mp3",
    ".mp4",
    ".wav",
    ".m4a",
    ".ogg",
    ".mpeg",
    ".mpga",
}


def get_transcription_provider(name: str | None = None) -> TranscriptionProvider:
    key = (name or settings.TRANSCRIPTION_PROVIDER).lower().strip()
    provider_cls = _TRANSCRIPTION_PROVIDERS.get(key)
    if provider_cls is None:
        supported = ", ".join(sorted(_TRANSCRIPTION_PROVIDERS))
        raise ValueError(
            f"Unknown transcription provider '{name}'. Supported: {supported}"
        )
    return provider_cls()


def validate_audio_filename(filename: str) -> None:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext and ext not in ALLOWED_AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise ValueError(
            f"Unsupported audio type '{ext}'. Supported extensions: {supported}"
        )


def transcribe(
    audio_bytes: bytes,
    filename: str,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    if not audio_bytes:
        raise ValueError("Audio file is empty")
    validate_audio_filename(filename)
    transcription_provider = get_transcription_provider(provider)
    if model and hasattr(transcription_provider, "transcribe"):
        return transcription_provider.transcribe(audio_bytes, filename, model=model)
    return transcription_provider.transcribe(audio_bytes, filename)
