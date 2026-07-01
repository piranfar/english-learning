"""Provider-independent reading generation with OpenAI default and strict JSON."""

from __future__ import annotations

import json
import re
from typing import Any

from django.conf import settings

from tutor.ai.provider_resolution import is_ai_provider_configured
from tutor.ai_providers.openai_provider import OpenAIReadingProvider
from tutor.reading_practice import (
    build_reading_generate_user_message,
    gather_reading_context,
    parse_reading_json_payload,
    resolve_lesson_focus,
)

READING_SYSTEM_PROMPT = """You are an expert English reading test designer and TOEFL reading coach.

Generate an original reading practice task.

Rules:
- Do not copy copyrighted TOEFL passages or questions.
- Create original text only.
- Match the requested level, stage, topic, lesson focus, length, and mode.
- For TOEFL 2026 mode, use these task styles:
  1. Complete the Words
  2. Read in Daily Life
  3. Read an Academic Passage
- For Classic TOEFL Academic mode, use academic passage questions such as main idea, detail, inference, vocabulary in context, reference, rhetorical purpose, sentence simplification, insert sentence, and summary.
- For General mode, use B1/B2 comprehension: main idea, detail, vocabulary in context, inference, sentence meaning.
- The passage must contain enough information to answer every question.
- Do not require outside knowledge.
- Return valid JSON only — no markdown, no prose outside JSON.
- Include answer_key and explanations for every question.
- Include one next_drill object.

Required JSON schema:
{
  "mode": "general|toefl_2026|classic_toefl",
  "level": "B1",
  "stage": "...",
  "lesson_focus": "...",
  "topic": "...",
  "title": "",
  "estimated_reading_time_minutes": 3,
  "passage": "",
  "vocabulary": [{"word": "", "meaning": "", "example": ""}],
  "questions": [{
    "id": "q1",
    "type": "main_idea",
    "question": "",
    "choices": [{"id": "A", "text": ""}, {"id": "B", "text": ""}, {"id": "C", "text": ""}, {"id": "D", "text": ""}],
    "correct_answer": "A",
    "explanation": "",
    "skill": "main_idea",
    "difficulty": "B1"
  }],
  "answer_key": {"q1": "A"},
  "skills_tested": ["main_idea", "detail"],
  "next_drill": {"title": "", "instruction": "", "target_skill": ""}
}

For complete_the_words questions include text_with_blank instead of question when helpful."""

READING_NOT_CONFIGURED_MSG = (
    "AI reading generation is not configured. Add OPENAI_API_KEY to enable generated reading practice."
)


class ReadingNotConfiguredError(Exception):
    pass


def resolve_reading_provider(requested: str | None = None) -> str | None:
    """OpenAI-first provider resolution for reading; never requires Anthropic."""
    if requested:
        cleaned = str(requested).lower().strip()
        if is_ai_provider_configured(cleaned):
            return cleaned

    preferred = getattr(settings, "READING_AI_PROVIDER", "openai").lower().strip()
    for candidate in (preferred, "openai", "ollama"):
        if candidate and is_ai_provider_configured(candidate):
            return candidate
    return None


def resolve_reading_model(reading_mode: str, provider: str) -> str:
    if provider == "openai":
        if reading_mode in ("toefl_2026", "classic_toefl"):
            return getattr(settings, "READING_GENERATION_MODEL", None) or getattr(
                settings, "OPENAI_MODEL", "gpt-4o"
            )
        return getattr(settings, "READING_FAST_MODEL", None) or getattr(
            settings, "OPENAI_MODEL", "gpt-4o-mini"
        )
    return ""


def friendly_reading_error(exc: BaseException) -> str:
    message = str(exc).lower()
    if isinstance(exc, ReadingNotConfiguredError) or "openai_not_configured" in message:
        return READING_NOT_CONFIGURED_MSG
    if "api_key" in message or "not configured" in message:
        return READING_NOT_CONFIGURED_MSG
    if "parse" in message or "too short" in message or "json" in message:
        return "Could not generate reading practice. Please try again with different filters."
    if "unsupported parameter" in message or "model" in message and "does not exist" in message:
        return "Reading AI model configuration error. Check READING_GENERATION_MODEL and READING_FAST_MODEL in .env."
    if "no active prompt" in message:
        return READING_NOT_CONFIGURED_MSG
    return "Could not generate reading practice right now. Please try again."


def _call_ollama_json(system_prompt: str, user_prompt: str) -> str:
    from tutor.services import generate_from_template

    combined = f"{system_prompt}\n\n{user_prompt}\n\nReturn valid JSON only."
    return generate_from_template("reading_generate", combined, provider="ollama")


def _generate_raw_json(
    *,
    system_prompt: str,
    user_prompt: str,
    provider: str,
    model: str,
) -> str:
    if provider == "openai":
        result = OpenAIReadingProvider().generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
        )
        return result.raw_text

    return _call_ollama_json(system_prompt, user_prompt)


def _extract_json_object(text: str) -> dict:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Empty AI response")

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data

    raise ValueError("Could not parse reading JSON from AI response")


def generate_reading_practice_ai(
    user,
    *,
    level: str = "B1",
    stage: str = "b2_toefl_80",
    topic: str = "Academic",
    lesson_focus: str = "current_lesson",
    question_focus: str = "mixed",
    length: str = "medium",
    reading_mode: str = "general",
    simulation_type: str = "",
    provider: str | None = None,
) -> dict:
    resolved_provider = resolve_reading_provider(provider)
    if not resolved_provider:
        raise ReadingNotConfiguredError(READING_NOT_CONFIGURED_MSG)

    context = gather_reading_context(user)
    if stage not in ("b2_toefl_80", "academic_toefl_100"):
        stage = context["stage"]

    resolve_lesson_focus(lesson_focus, context)
    user_message = build_reading_generate_user_message(
        level=level,
        stage=stage,
        topic=topic,
        lesson_focus=lesson_focus,
        question_focus=question_focus,
        length=length,
        context=context,
        simulation_type=simulation_type,
        reading_mode=reading_mode,
    )

    model = resolve_reading_model(reading_mode, resolved_provider)
    raw = _generate_raw_json(
        system_prompt=READING_SYSTEM_PROMPT,
        user_prompt=user_message,
        provider=resolved_provider,
        model=model,
    )

    try:
        payload = _extract_json_object(raw)
        return parse_reading_json_payload(payload, level=level, stage=stage)
    except (ValueError, json.JSONDecodeError):
        raw_retry = _generate_raw_json(
            system_prompt=READING_SYSTEM_PROMPT + "\nYour previous response was invalid JSON. Return only valid JSON.",
            user_prompt=user_message,
            provider=resolved_provider,
            model=model,
        )
        payload = _extract_json_object(raw_retry)
        return parse_reading_json_payload(payload, level=level, stage=stage)
