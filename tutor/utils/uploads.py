"""Upload validation helpers."""

from __future__ import annotations

from django.conf import settings


class AudioUploadTooLarge(Exception):
    def __init__(self, size: int, max_bytes: int):
        self.size = size
        self.max_bytes = max_bytes
        super().__init__(f"Audio upload exceeds maximum size of {max_bytes} bytes.")


def validate_audio_upload(uploaded_file) -> None:
    """Reject audio uploads larger than MAX_AUDIO_UPLOAD_BYTES."""
    max_bytes = getattr(settings, "MAX_AUDIO_UPLOAD_BYTES", 15 * 1024 * 1024)
    size = getattr(uploaded_file, "size", None)
    if size is None:
        return
    if size > max_bytes:
        raise AudioUploadTooLarge(size, max_bytes)
