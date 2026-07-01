"""DRF throttle classes for auth and AI endpoints."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class AIUserRateThrottle(UserRateThrottle):
    scope = "ai"
