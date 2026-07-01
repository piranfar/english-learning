"""Controlled AI provider errors — never expose raw secrets to learners."""


class ProviderUnavailableError(RuntimeError):
    """Raised when a provider cannot be invoked (missing key, misconfiguration, etc.)."""

    def __init__(self, provider: str, reason: str = "not configured"):
        self.provider = provider
        self.reason = reason
        super().__init__(f"{provider} provider unavailable")
