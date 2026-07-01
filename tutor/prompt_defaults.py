"""Default prompt templates seeded from tutor.prompts.* modules."""

from tutor.prompts.grammar_coach import GRAMMAR_COACH_TEMPLATES
from tutor.prompts.listening_coach import LISTENING_COACH_TEMPLATES, LISTENING_QUIZ_TEMPLATES
from tutor.prompts.reading_coach import (
    READING_COACH_TEMPLATES,
    READING_GENERATE_TEMPLATES,
    READING_QUIZ_TEMPLATES,
    READING_SIMULATION_TEMPLATES,
)
from tutor.prompts.speaking_coach import SPEAKING_COACH_TEMPLATES
from tutor.prompts.toefl import TOEFL_TEMPLATES
from tutor.prompts.provider_variants import gemini_variant
from tutor.prompts.writing_coach import VOCAB_BUILDER_TEMPLATES, WRITING_COACH_TEMPLATES

_BASE_DEFAULT_TEMPLATES = [
    *GRAMMAR_COACH_TEMPLATES,
    *WRITING_COACH_TEMPLATES,
    *VOCAB_BUILDER_TEMPLATES,
    *READING_COACH_TEMPLATES,
    *READING_QUIZ_TEMPLATES,
    *READING_GENERATE_TEMPLATES,
    *READING_SIMULATION_TEMPLATES,
    *LISTENING_COACH_TEMPLATES,
    *LISTENING_QUIZ_TEMPLATES,
    *SPEAKING_COACH_TEMPLATES,
    *TOEFL_TEMPLATES,
]

GEMINI_DEFAULT_TEMPLATES = [
    gemini_variant(template, model_name="gemini-2.0-flash")
    for template in _BASE_DEFAULT_TEMPLATES
    if template["provider"] == "openai"
]

ALL_DEFAULT_TEMPLATES = [*_BASE_DEFAULT_TEMPLATES, *GEMINI_DEFAULT_TEMPLATES]

PROVIDER_NOTES = {
    "ollama": "Local Ollama. Use tagged model names (e.g. qwen2.5:7b, llama3.2:3b).",
    "openai": "OpenAI API. Requires OPENAI_API_KEY in Django .env.",
    "anthropic": "Anthropic API. Requires ANTHROPIC_API_KEY in Django .env.",
    "gemini": "Google Gemini API. Requires GEMINI_API_KEY in Django .env (optional).",
}


def get_default_template(task_type: str, provider: str) -> dict | None:
    for template in ALL_DEFAULT_TEMPLATES:
        if template["task_type"] == task_type and template["provider"] == provider:
            return dict(template)
    return None
