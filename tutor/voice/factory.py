from django.conf import settings

from tutor.transcription.factory import transcribe as transcribe_impl

from tutor.voice.base import TranscriptionProvider, TTSProvider
from tutor.voice.providers.browser_tts import BrowserTTSProvider
from tutor.voice.providers.local_whisper import LocalWhisperProvider
from tutor.voice.providers.openai_voice import OpenAITTSProvider, OpenAIWhisperProvider

_TRANSCRIPTION_PROVIDERS: dict[str, type[TranscriptionProvider]] = {
    "openai_whisper": OpenAIWhisperProvider,
    "local_whisper": LocalWhisperProvider,
}

_TTS_PROVIDERS: dict[str, type[TTSProvider]] = {
    "browser_tts": BrowserTTSProvider,
    "openai_tts": OpenAITTSProvider,
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


def get_tts_provider(name: str | None = None) -> TTSProvider:
    key = (name or settings.TTS_PROVIDER).lower().strip()
    provider_cls = _TTS_PROVIDERS.get(key)
    if provider_cls is None:
        supported = ", ".join(sorted(_TTS_PROVIDERS))
        raise ValueError(f"Unknown TTS provider '{name}'. Supported: {supported}")
    return provider_cls()


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    provider: str | None = None,
) -> str:
    return transcribe_impl(audio_bytes, filename, provider=provider)


def synthesize_speech(text: str, provider: str | None = None) -> bytes:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("text is required for TTS")
    return get_tts_provider(provider).synthesize(cleaned)
