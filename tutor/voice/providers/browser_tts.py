from tutor.voice.base import TTSProvider


class BrowserTTSProvider(TTSProvider):
    """Placeholder — listening practice uses client-side speechSynthesis."""

    def synthesize(self, text: str) -> bytes:
        raise RuntimeError(
            "Browser TTS is handled on the client. Use speechSynthesis in the browser, "
            "or pass provider=openai_tts for server-side audio."
        )
