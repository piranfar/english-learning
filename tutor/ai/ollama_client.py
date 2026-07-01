import json
import urllib.error
import urllib.request

from django.conf import settings


def ollama_base_url() -> str:
    return settings.OLLAMA_HOST.rstrip("/")


def fetch_ollama_tags() -> tuple[bool, list[str], str | None]:
    """Return (ok, model_names, error_message)."""
    url = f"{ollama_base_url()}/api/tags"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, [], f"Ollama returned HTTP {exc.code}: {body}"
    except urllib.error.URLError as exc:
        return False, [], f"Ollama unreachable at {url}: {exc.reason}"
    except json.JSONDecodeError as exc:
        return False, [], f"Invalid JSON from Ollama at {url}: {exc}"

    models = []
    for entry in data.get("models", []):
        name = entry.get("name")
        if name:
            models.append(name)
    return True, models, None


def missing_recommended_models(installed: list[str]) -> list[str]:
    from tutor.ai.ollama_config import RECOMMENDED_OLLAMA_MODELS

    missing = []
    for recommended in RECOMMENDED_OLLAMA_MODELS:
        if _model_is_available(recommended, installed):
            continue
        missing.append(recommended)
    return missing


def _model_is_available(recommended: str, installed: list[str]) -> bool:
    if recommended in installed:
        return True
    recommended_base = recommended.split(":")[0]
    for name in installed:
        if name.split(":")[0] == recommended_base:
            return True
    return False
