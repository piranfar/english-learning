"""TOEFL-oriented speaking evaluation pipeline and JSON contract."""

from __future__ import annotations

import json
import re
from typing import Any

from django.conf import settings

from tutor.models import Message, PracticeSession, PromptTemplate
from tutor.services import (
    call_provider,
    format_speaking_message,
    get_prompt_template,
    persist_speaking_feedback_mistakes,
)

SPEAKING_EVALUATOR_SYSTEM_PROMPT = """You are a TOEFL iBT Speaking reviewer and supportive English speaking coach.

Evaluate the user's spoken response based on:
1. Delivery (fluency, pace, pauses, pronunciation clarity, word stress, sentence stress, intonation)
2. Language use (grammar range, grammar accuracy, vocabulary precision, academic phrasing)
3. Topic development (answer relevance, organization, examples/details, coherence, completion within time)

Rules:
- Do not judge accent by nationality or native-likeness.
- Judge only intelligibility, clarity, pronunciation, stress, rhythm, intonation, fluency, grammar, vocabulary, organization, and task relevance.
- If audio-derived delivery information is unavailable (typed input), clearly note that pronunciation and intonation scoring is limited.
- Give practical correction, not only a score.
- Always include one next_drill object.
- Return valid JSON only — no markdown, no prose outside JSON.

Mode-specific scoring:
- beginner: Score mainly task completion, understandable meaning, basic grammar, basic vocabulary, and answer length. Do not strongly penalize accent, small pronunciation errors, imperfect intonation, or hesitations. Feedback should be simple with one grammar correction, one vocabulary improvement, and one sentence to repeat.
- normal: B1/B2 speaking practice. Score task completion, organization, grammar accuracy, vocabulary appropriateness, fluency, pronunciation clarity, and basic intonation. Provide TOEFL-lite scoring and 2–3 improvement points.
- advanced: Strict TOEFL-style review with delivery, language use, and topic development categories. Include estimated_toefl_speaking (0–30 scale) and rubric_score_0_4 (0–4).

Required JSON schema:
{
  "mode": "beginner|normal|advanced",
  "estimated_toefl_speaking": 18,
  "rubric_score_0_4": 2.5,
  "overall_score": 62,
  "overall_feedback": "...",
  "scores": {
    "delivery": 58,
    "fluency": 55,
    "pronunciation_clarity": 62,
    "intonation": 50,
    "language_use": 60,
    "grammar": 57,
    "vocabulary": 63,
    "topic_development": 52,
    "organization": 54
  },
  "strengths": ["..."],
  "priority_corrections": [
    {
      "type": "grammar|vocabulary|organization|delivery",
      "original": "...",
      "corrected": "...",
      "explanation": "..."
    }
  ],
  "delivery_notes": {
    "pace": "...",
    "pronunciation": "...",
    "intonation": "..."
  },
  "corrected_answer": "...",
  "transcript": "...",
  "next_drill": {
    "title": "...",
    "instruction": "...",
    "target": "..."
  },
  "retry_recommendation": "..."
}

All score values in "scores" are 0–100 integers. Omit estimated_toefl_speaking and rubric_score_0_4 for beginner mode unless helpful."""

JSON_BLOCK_PATTERN = re.compile(
    r"---SPEAKING_FEEDBACK---\s*(\{[\s\S]*?\})\s*---END_SPEAKING_FEEDBACK---",
    re.DOTALL,
)


def resolve_transcription_model(evaluation_mode: str) -> str | None:
    mode = (evaluation_mode or "normal").lower().strip()
    if mode == "advanced":
        return getattr(settings, "WHISPER_MODEL_QUALITY", None) or settings.WHISPER_MODEL
    return getattr(settings, "WHISPER_MODEL_FAST", None) or settings.WHISPER_MODEL


def resolve_evaluator_model(evaluation_mode: str, template: PromptTemplate) -> str:
    mode = (evaluation_mode or "normal").lower().strip()
    if mode == "advanced":
        return getattr(settings, "SPEAKING_EVAL_MODEL_ADVANCED", None) or template.model_name
    return getattr(settings, "SPEAKING_EVAL_MODEL_STANDARD", None) or template.model_name


def build_evaluator_user_message(
    *,
    evaluation_mode: str,
    task_prompt: str,
    transcript: str,
    input_mode: str = "voice",
    speaking_level: str = "normal",
    speaking_time: int | None = None,
    prep_time: int | None = None,
    practice_type: str = "",
    task_title: str = "",
    article_text: str = "",
    evaluation_focus: list[str] | None = None,
    weakness_hint: str = "",
) -> str:
    lines = [
        f"User mode: {evaluation_mode}",
        f"Speaking level: {speaking_level}",
        f"Practice type: {practice_type or 'general'}",
        f"Task title: {task_title or 'Speaking task'}",
        f"Speaking task prompt: {task_prompt}",
        f"Input mode: {input_mode}",
    ]
    if speaking_time is not None:
        lines.append(f"Expected speaking time: {speaking_time} seconds")
    if prep_time is not None:
        lines.append(f"Preparation time: {prep_time} seconds")
    if evaluation_focus:
        lines.append(f"Evaluation focus: {', '.join(evaluation_focus)}")
    if weakness_hint:
        lines.append(f"Recent weakness history: {weakness_hint}")
    if input_mode == "typed":
        lines.append(
            "Note: Typed input only — pronunciation and intonation scoring is limited."
        )
    else:
        lines.append(
            "Note: Response was transcribed from audio. Delivery scoring is transcript-based."
        )
    if article_text.strip():
        lines.extend(["", "Article context:", article_text.strip()])
    lines.extend(["", "Transcript:", transcript.strip()])
    lines.append("")
    lines.append("Return JSON only matching the required schema.")
    return "\n".join(lines)


def _coerce_scores(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    scores: dict[str, int] = {}
    for key, value in raw.items():
        try:
            scores[str(key)] = max(0, min(100, int(round(float(value)))))
        except (TypeError, ValueError):
            continue
    return scores


def _scores_to_rubric(scores: dict[str, int]) -> dict:
    mapping = {
        "fluency": "fluency",
        "grammar": "grammar",
        "vocabulary": "vocabulary",
        "organization": "organization",
        "pronunciation_clarity": "fluency",
        "delivery": "fluency",
        "topic_development": "organization",
        "language_use": "grammar",
        "intonation": "fluency",
    }
    rubric: dict = {}
    for key, score in scores.items():
        rubric_key = mapping.get(key, key)
        if rubric_key in rubric:
            continue
        rubric_score = max(0, min(4, round(score / 25)))
        rubric[rubric_key] = {
            "score": rubric_score,
            "max": 4,
            "reason": f"Score {score}/100",
            "next_step": "",
        }
    return rubric


def _priority_to_mistakes(corrections: list) -> list[dict]:
    rows = []
    for item in corrections or []:
        if not isinstance(item, dict):
            continue
        original = (item.get("original") or item.get("wrong") or "").strip()
        corrected = (item.get("corrected") or item.get("correct") or "").strip()
        explanation = (item.get("explanation") or item.get("reason") or "").strip()
        area = (item.get("type") or item.get("area") or "grammar").strip().lower()
        if original:
            rows.append(
                {
                    "area": area,
                    "wrong": original,
                    "correct": corrected,
                    "reason": explanation,
                }
            )
    return rows


def _delivery_notes_text(notes: dict | None) -> str:
    if not isinstance(notes, dict):
        return ""
    parts = []
    for key in ("pace", "pronunciation", "intonation"):
        value = (notes.get(key) or "").strip()
        if value:
            parts.append(f"{key.replace('_', ' ').title()}: {value}")
    return " ".join(parts)


def normalize_evaluator_json(data: dict, *, input_mode: str = "voice") -> dict:
    scores = _coerce_scores(data.get("scores"))
    strengths = [str(s).strip() for s in data.get("strengths", []) if str(s).strip()]
    priority_corrections = data.get("priority_corrections") or []
    legacy_mistakes = data.get("main_mistakes") or []
    delivery_notes = data.get("delivery_notes") if isinstance(data.get("delivery_notes"), dict) else {}
    next_drill = data.get("next_drill") if isinstance(data.get("next_drill"), dict) else {}
    overall_feedback = (data.get("overall_feedback") or "").strip()
    corrected = (data.get("corrected_answer") or data.get("corrected_version") or "").strip()
    retry = (data.get("retry_recommendation") or "").strip()

    overall_score = data.get("overall_score")
    if overall_score is None and scores:
        overall_score = round(sum(scores.values()) / len(scores))
    try:
        overall_score = int(round(float(overall_score))) if overall_score is not None else None
    except (TypeError, ValueError):
        overall_score = None

    rubric = _scores_to_rubric(scores)
    if not rubric and isinstance(data.get("rubric"), dict):
        rubric = data.get("rubric") or {}
        breakdown = {}
        for key, item in rubric.items():
            if isinstance(item, dict) and item.get("score") is not None:
                breakdown[key] = item["score"]
            elif isinstance(item, (int, float)):
                breakdown[key] = int(item)
    else:
        breakdown = {key: item["score"] for key, item in rubric.items()}
    main_mistakes = _priority_to_mistakes(priority_corrections)
    if not main_mistakes and legacy_mistakes:
        main_mistakes = _priority_to_mistakes(legacy_mistakes)
    pronunciation_notes = _delivery_notes_text(delivery_notes)

    return {
        "mode": (data.get("mode") or "normal").strip(),
        "overall_score": overall_score,
        "estimated_toefl_speaking": data.get("estimated_toefl_speaking"),
        "rubric_score_0_4": data.get("rubric_score_0_4"),
        "overall_feedback": overall_feedback,
        "scores": scores,
        "strengths": strengths,
        "priority_corrections": priority_corrections,
        "delivery_notes": delivery_notes,
        "input_mode": input_mode,
        "pronunciation_limited": input_mode == "typed" or bool(data.get("pronunciation_limited", True)),
        "pronunciation_notes": pronunciation_notes,
        "rubric": rubric,
        "breakdown": breakdown,
        "corrected_version": corrected,
        "model_answer": corrected,
        "natural_version": corrected,
        "repeat_answer": (next_drill.get("instruction") or "").strip(),
        "next_drill": next_drill,
        "follow_up_question": "",
        "recommended_next_task": retry,
        "repeat_task_recommendation": retry,
        "positive_comment": strengths[0] if strengths else overall_feedback,
        "main_issues": [
            c.get("explanation", "") for c in priority_corrections if isinstance(c, dict)
        ][:3],
        "main_mistakes": main_mistakes,
        "vocabulary_upgrades": [],
        "transcript": (data.get("transcript") or "").strip(),
    }


def _extract_json_payload(raw_reply: str) -> dict | None:
    text = (raw_reply or "").strip()
    if not text:
        return None

    match = JSON_BLOCK_PATTERN.search(text)
    if match:
        text = match.group(1).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            data = json.loads(brace_match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
    return None


def _is_new_evaluator_contract(data: dict) -> bool:
    return bool(data.get("scores") or data.get("mode") or data.get("priority_corrections"))


def parse_evaluator_response(raw_reply: str, *, input_mode: str = "voice") -> tuple[str, dict | None]:
    data = _extract_json_payload(raw_reply)
    if not data or not _is_new_evaluator_contract(data):
        return raw_reply.strip(), None

    normalized = normalize_evaluator_json(data, input_mode=input_mode)
    reply = normalized.get("overall_feedback") or "Evaluation complete."
    return reply, normalized


def call_speaking_evaluator(
    template: PromptTemplate,
    messages: list[dict],
    *,
    evaluation_mode: str,
) -> str:
    from tutor.ai.providers.openai import OpenAIProvider

    model_name = resolve_evaluator_model(evaluation_mode, template)
    ai_provider = OpenAIProvider() if template.provider == "openai" else None

    if ai_provider and template.provider == "openai":
        from tutor.ai.openai_client import call_openai_chat

        user_parts = [
            str(message.get("content", "")).strip()
            for message in messages
            if str(message.get("content", "")).strip()
        ]
        prompt = "\n\n".join(user_parts)
        result = call_openai_chat(
            prompt,
            system_prompt=template.system_prompt or SPEAKING_EVALUATOR_SYSTEM_PROMPT,
            model=model_name,
            json_mode=True,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
        )
        return result["content"]

    return call_provider(template, messages)


def run_speaking_evaluation(
    *,
    user,
    session: PracticeSession,
    eval_message: str,
    provider: str | None,
    scenario: str | None,
    evaluation_mode: str = "normal",
    input_mode: str = "voice",
) -> dict:
    template = get_prompt_template("speaking_coach", provider)
    if not template.system_prompt or "Return valid JSON only" not in template.system_prompt:
        template = PromptTemplate(
            task_type=template.task_type,
            provider=template.provider,
            model_name=template.model_name,
            system_prompt=SPEAKING_EVALUATOR_SYSTEM_PROMPT,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            is_active=True,
        )

    history = [
        {"role": message.role, "content": message.content}
        for message in session.messages.order_by("created_at")
        if message.role in ("user", "assistant")
    ]
    content = format_speaking_message(scenario, eval_message)
    messages = [*history, {"role": "user", "content": content}]

    raw_reply = call_speaking_evaluator(
        template,
        messages,
        evaluation_mode=evaluation_mode,
    )
    reply, speaking_feedback = parse_evaluator_response(raw_reply, input_mode=input_mode)

    Message.objects.create(session=session, role="user", content=eval_message)
    Message.objects.create(session=session, role="assistant", content=reply)

    if speaking_feedback:
        persist_speaking_feedback_mistakes(user, session.track, speaking_feedback)

    return {
        "reply": reply,
        "corrections": [],
        "speaking_feedback": speaking_feedback,
    }
