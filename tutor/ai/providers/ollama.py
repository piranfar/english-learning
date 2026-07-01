import json
import re
import urllib.error
import urllib.request

from django.conf import settings

from tutor.ai.base import AIProvider
from tutor.ai.ollama_client import fetch_ollama_tags, ollama_base_url


def _parse_model_not_found(body: str) -> str | None:
    match = re.search(r"model ['\"]([^'\"]+)['\"] not found", body, re.IGNORECASE)
    if match:
        return match.group(1)
    try:
        data = json.loads(body)
        error = data.get("error", "")
        match = re.search(r"model ['\"]([^'\"]+)['\"] not found", error, re.IGNORECASE)
        if match:
            return match.group(1)
    except json.JSONDecodeError:
        pass
    return None


def _format_model_not_found_error(requested_model: str) -> str:
    host = ollama_base_url()
    ok, installed, _error = fetch_ollama_tags()
    if ok and installed:
        sample = ", ".join(installed[:6])
        suffix = "..." if len(installed) > 6 else ""
        return (
            f"Ollama model not found: {requested_model}. "
            f"Host: {host}. "
            f"Installed models include {sample}{suffix}. "
            "Update the PromptTemplate model_name to match an installed tag "
            "(for example qwen2.5:7b or llama3.2:3b)."
        )
    return (
        f"Ollama model not found: {requested_model}. "
        f"Host: {host}. "
        "Run `ollama list` and update the PromptTemplate model_name to match "
        "an installed model tag (for example qwen2.5:7b or llama3.2:3b)."
    )


class OllamaProvider(AIProvider):
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        model_name: str,
    ) -> str:
        payload = {
            "model": model_name,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        url = f"{ollama_base_url()}/api/chat"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 404 and _parse_model_not_found(body):
                raise RuntimeError(_format_model_not_found_error(model_name)) from exc
            raise RuntimeError(
                f"Ollama request failed ({exc.code}) at {ollama_base_url()}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Ollama unreachable at {ollama_base_url()}: {exc.reason}"
            ) from exc

        message = data.get("message", {})
        content = message.get("content", "")
        if not content:
            raise RuntimeError("Ollama returned an empty response")
        return content
