"""Helpers for adding provider-specific prompt template variants."""


def gemini_variant(template: dict, *, model_name: str = "gemini-2.0-flash") -> dict:
    """Clone a template for Google Gemini."""
    title = template["title"]
    for suffix in ("(Ollama)", "(OpenAI)", "(Anthropic)"):
        if suffix in title:
            title = title.replace(suffix, "(Gemini)")
            break
    else:
        if "(Gemini)" not in title:
            title = f"{title} (Gemini)"

    return {
        **template,
        "title": title,
        "provider": "gemini",
        "model_name": model_name,
    }
