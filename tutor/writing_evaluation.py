"""TOEFL-oriented writing evaluation pipeline and JSON contract."""

from __future__ import annotations

import json
import re
from typing import Any

from django.conf import settings

from tutor.models import Message, PracticeSession, PromptTemplate
from tutor.services import (
    call_provider,
    get_prompt_template,
    persist_writing_feedback_mistakes,
)

WRITING_EVALUATOR_SYSTEM_PROMPT = """You are a TOEFL iBT Writing reviewer and supportive English writing coach.

Evaluate the learner draft based on task response, organization, grammar, vocabulary, cohesion, and sentence control.

Rules:
- Do not judge the writer by nationality or native-likeness.
- Judge clarity, task relevance, organization, grammar range/accuracy, vocabulary precision, cohesion, and academic tone.
- Give practical correction, not only a score.
- Always include one next_rewrite_drill object.
- Return valid JSON only — no markdown, no prose outside JSON.

Mode-specific scoring:
- beginner: More structure, simple corrections, focus on meaning and basic grammar. Include sentence starters in feedback tone.
- normal: B1/B2 correction across grammar, vocabulary, organization, and clarity. Provide corrected paragraph and one rewrite drill.
- toefl_reviewer: Strict TOEFL-style scoring with estimated_toefl_writing (0-30), task response, development, coherence, grammar range, vocabulary precision, and academic tone.

Required JSON schema:
{
  "mode": "beginner|normal|toefl_reviewer",
  "estimated_toefl_writing": null,
  "overall_score": 0,
  "overall_feedback": "...",
  "scores": {
    "task_response": 0,
    "organization": 0,
    "grammar": 0,
    "vocabulary": 0,
    "cohesion": 0,
    "sentence_control": 0
  },
  "strengths": ["..."],
  "priority_corrections": [
    {"type": "grammar", "original": "...", "corrected": "...", "explanation": "..."}
  ],
  "corrected_version": "...",
  "next_rewrite_drill": {
    "title": "...",
    "instruction": "...",
    "target": "..."
  }
}

All score values in "scores" are 0–100 integers."""

JSON_BLOCK_PATTERN = re.compile(
    r"---(?:WRITING|TOEFL_WRITING)_FEEDBACK---\s*(\{[\s\S]*?\})\s*---END_(?:WRITING|TOEFL_WRITING)_FEEDBACK---",
    re.DOTALL,
)


def build_writing_evaluator_message(
    *,
    evaluation_mode: str,
    level: str,
    mode: str,
    prompt: str,
    draft: str,
    word_count: int,
    word_min: int,
    word_max: int,
    time_minutes: int,
    goal: str = "",
) -> str:
    lines = [
        f"User mode: {evaluation_mode}",
        f"Writing level: {level}",
        f"Writing type: {mode}",
        f"Prompt: {prompt}",
        f"Target word count: {word_min}–{word_max}",
        f"Student word count: {word_count}",
        f"Recommended time: {time_minutes} minutes",
    ]
    if goal:
        lines.append(f"Writing goal: {goal}")
    if word_count < word_min:
        lines.append("Note: Answer is shorter than target range.")
    elif word_count > word_max:
        lines.append("Note: Answer is longer than target range.")
    lines.extend(["", "Student answer:", draft.strip(), "", "Return JSON only matching the required schema."])
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


def _priority_to_mistakes(corrections: list) -> list[dict]:
    rows = []
    for item in corrections or []:
        if not isinstance(item, dict):
            continue
        original = (item.get("original") or item.get("wrong") or "").strip()
        corrected = (item.get("corrected") or item.get("correct") or "").strip()
        explanation = (item.get("explanation") or item.get("reason") or "").strip()
        if original:
            rows.append({"wrong": original, "correct": corrected, "reason": explanation})
    return rows


def normalize_writing_json(data: dict) -> dict:
    scores = _coerce_scores(data.get("scores"))
    priority_corrections = data.get("priority_corrections") or []
    next_drill = data.get("next_rewrite_drill") if isinstance(data.get("next_rewrite_drill"), dict) else {}
    strengths = [str(s).strip() for s in data.get("strengths", []) if str(s).strip()]
    corrected = (data.get("corrected_version") or "").strip()
    overall_feedback = (data.get("overall_feedback") or "").strip()

    overall_score = data.get("overall_score")
    if overall_score is None and scores:
        overall_score = round(sum(scores.values()) / len(scores))
    try:
        overall_score = int(round(float(overall_score))) if overall_score is not None else None
    except (TypeError, ValueError):
        overall_score = None

    rubric = {}
    for key, score in scores.items():
        rubric[key] = {
            "score": max(0, min(4, round(score / 25))),
            "max": 4,
            "reason": f"Score {score}/100",
            "next_step": "",
        }

    revision_task = (next_drill.get("instruction") or "").strip()

    return {
        "mode": (data.get("mode") or "normal").strip(),
        "overall_score": overall_score,
        "estimated_toefl_writing": data.get("estimated_toefl_writing"),
        "overall_feedback": overall_feedback,
        "scores": scores,
        "strengths": strengths,
        "priority_corrections": priority_corrections,
        "rubric": rubric,
        "main_mistakes": _priority_to_mistakes(priority_corrections),
        "corrected_version": corrected,
        "natural_version": corrected,
        "recommended_revision_task": revision_task,
        "next_rewrite_drill": next_drill,
        "positive_comment": strengths[0] if strengths else overall_feedback,
        "useful_phrases": strengths,
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


def _is_new_writing_contract(data: dict) -> bool:
    return bool(data.get("scores") or data.get("mode") or data.get("priority_corrections"))


def parse_writing_evaluator_response(raw_reply: str) -> tuple[str, dict | None]:
    data = _extract_json_payload(raw_reply)
    if not data or not _is_new_writing_contract(data):
        return raw_reply.strip(), None

    normalized = normalize_writing_json(data)
    reply = normalized.get("overall_feedback") or "Evaluation complete."
    return reply, normalized


def resolve_writing_evaluator_model(evaluation_mode: str, template: PromptTemplate) -> str:
    if evaluation_mode == "toefl_reviewer":
        return getattr(settings, "WRITING_EVAL_MODEL_ADVANCED", None) or template.model_name
    return getattr(settings, "WRITING_EVAL_MODEL_STANDARD", None) or template.model_name


def call_writing_evaluator(
    template: PromptTemplate,
    messages: list[dict],
    *,
    evaluation_mode: str,
) -> str:
    if template.provider == "openai":
        from tutor.ai.openai_client import call_openai_chat

        user_parts = [
            str(message.get("content", "")).strip()
            for message in messages
            if str(message.get("content", "")).strip()
        ]
        prompt = "\n\n".join(user_parts)
        result = call_openai_chat(
            prompt,
            system_prompt=template.system_prompt or WRITING_EVALUATOR_SYSTEM_PROMPT,
            model=resolve_writing_evaluator_model(evaluation_mode, template),
            json_mode=True,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
        )
        return result["content"]

    return call_provider(template, messages)


def run_writing_evaluation(
    *,
    user,
    session: PracticeSession,
    eval_message: str,
    provider: str | None,
    task_type: str,
    evaluation_mode: str = "normal",
) -> dict:
    template = get_prompt_template(task_type, provider)
    if not template.system_prompt or "Return valid JSON only" not in template.system_prompt:
        template = PromptTemplate(
            task_type=template.task_type,
            provider=template.provider,
            model_name=template.model_name,
            system_prompt=WRITING_EVALUATOR_SYSTEM_PROMPT,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            is_active=True,
        )

    history = [
        {"role": message.role, "content": message.content}
        for message in session.messages.order_by("created_at")
        if message.role in ("user", "assistant")
    ]
    messages = [*history, {"role": "user", "content": eval_message}]

    raw_reply = call_writing_evaluator(
        template,
        messages,
        evaluation_mode=evaluation_mode,
    )
    reply, writing_feedback = parse_writing_evaluator_response(raw_reply)

    if not writing_feedback:
        from tutor.services import parse_toefl_writing_feedback, parse_writing_feedback

        if task_type == "toefl_writing":
            reply, writing_feedback = parse_toefl_writing_feedback(raw_reply)
        else:
            reply, writing_feedback = parse_writing_feedback(raw_reply)

    Message.objects.create(session=session, role="user", content=eval_message)
    Message.objects.create(session=session, role="assistant", content=reply)

    if writing_feedback:
        persist_writing_feedback_mistakes(user, session.track, writing_feedback)

    result = {
        "reply": reply,
        "corrections": [],
    }
    if task_type == "toefl_writing":
        if writing_feedback:
            result["toefl_feedback"] = {
                "estimated_toefl_score": writing_feedback.get("estimated_toefl_writing"),
                "scores": {k: v.get("score") if isinstance(v, dict) else v for k, v in writing_feedback.get("rubric", {}).items()},
                "rubric_details": writing_feedback.get("rubric"),
                "feedback": writing_feedback.get("overall_feedback"),
                "strengths": writing_feedback.get("strengths"),
                "main_mistakes": writing_feedback.get("main_mistakes"),
                "corrected_version": writing_feedback.get("corrected_version"),
                "recommended_revision_task": writing_feedback.get("recommended_revision_task"),
            }
        result["writing_feedback"] = writing_feedback
    else:
        result["writing_feedback"] = writing_feedback

    from tutor.plan_completion import auto_complete_plan_items

    result["plan_items_completed"] = auto_complete_plan_items(user, track="writing")
    return result
