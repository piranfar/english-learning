"""Aggregate real coach scores for readiness and dashboard."""

from __future__ import annotations

import json
import re
from datetime import timedelta

from django.utils import timezone

from tutor.models import Message, Mistake, PracticeSession, ShadowingAttempt, VocabularyItem

WRITING_TRACKS = {
    "writing_coach",
    "writing_edit_coach",
    "writing_lesson_coach",
    "writing_paraphrase_coach",
    "writing_paraphrase_generate",
    "writing_paraphrase_check",
    "sentence_builder_coach",
    "paragraph_builder_coach",
}

SPEAKING_TRACKS = {"speaking_coach", "toefl_speaking_coach"}


def _average(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _coerce_score(value) -> int | None:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if 0 <= score <= 100:
        return score
    return None


def _extract_overall_score_from_content(content: str) -> int | None:
    from tutor.services import (
        parse_speaking_feedback,
        parse_toefl_writing_feedback,
        parse_writing_feedback,
    )
    from tutor.speaking_evaluation import parse_evaluator_response
    from tutor.writing_evaluation import parse_writing_evaluator_response

    text = (content or "").strip()
    if not text:
        return None

    for parser in (
        lambda: parse_evaluator_response(text),
        lambda: parse_speaking_feedback(text),
        lambda: parse_writing_evaluator_response(text),
        lambda: parse_toefl_writing_feedback(text),
        lambda: parse_writing_feedback(text),
    ):
        try:
            _, feedback = parser()
        except Exception:
            continue
        if feedback:
            score = _coerce_score(feedback.get("overall_score"))
            if score is not None:
                return score

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            score = _coerce_score(data.get("overall_score"))
            if score is not None:
                return score
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                score = _coerce_score(data.get("overall_score"))
                if score is not None:
                    return score
        except json.JSONDecodeError:
            pass

    return None


def _session_track_scores(user, tracks: set[str], *, limit: int = 8) -> list[int]:
    scores: list[int] = []
    sessions = (
        PracticeSession.objects.filter(user=user, track__in=tracks)
        .order_by("-created_at")[:limit]
    )
    for session in sessions:
        messages = session.messages.filter(role="assistant").order_by("-created_at")[:2]
        for message in messages:
            score = _extract_overall_score_from_content(message.content)
            if score is not None:
                scores.append(score)
                break
    return scores


def speaking_score_for_user(user, stage_slug: str = "") -> int:
    del stage_slug
    scores = _session_track_scores(user, SPEAKING_TRACKS)
    if scores:
        return _average(scores)

    shadowing = (
        ShadowingAttempt.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("similarity_score", flat=True)[:5]
    )
    shadowing_scores = [int(value) for value in shadowing if value]
    return _average(shadowing_scores)


def writing_score_for_user(user, stage_slug: str = "") -> int:
    del stage_slug
    return _average(_session_track_scores(user, WRITING_TRACKS))


def vocabulary_score_for_user(user, stage_slug: str = "") -> int:
    del stage_slug
    items = VocabularyItem.objects.filter(user=user)
    total = items.count()
    if not total:
        return 0

    reviewed = items.filter(repetitions__gt=0).count()
    mastery_ratio = reviewed / total

    since = timezone.now() - timedelta(days=14)
    recent_mistakes = Mistake.objects.filter(
        user=user,
        track="vocab_quiz",
        created_at__gte=since,
    ).count()

    base = 50 + mastery_ratio * 40
    penalty = min(25, recent_mistakes * 4)
    return max(0, min(100, round(base - penalty)))


def coach_score_for_user(user, skill: str, stage_slug: str) -> int:
    if skill == "reading":
        from tutor.reading_practice import reading_score_for_user

        return reading_score_for_user(user, stage_slug)
    if skill == "listening":
        from tutor.listening_practice import listening_score_for_user

        return listening_score_for_user(user, stage_slug)
    if skill == "speaking":
        return speaking_score_for_user(user, stage_slug)
    if skill == "writing":
        return writing_score_for_user(user, stage_slug)
    if skill == "vocabulary":
        return vocabulary_score_for_user(user, stage_slug)
    return 0


def estimated_toefl_total(
    user,
    stage_slug: str,
    *,
    mastery_ratio: float = 0,
    grammar_score: int = 0,
) -> tuple[int, str]:
    """Practice TOEFL total (0–120) from recent coach section scores."""
    section_scores: list[int] = []
    for skill in ("reading", "listening", "speaking", "writing"):
        score = coach_score_for_user(user, skill, stage_slug)
        if score:
            section_scores.append(max(0, min(30, round(score / 100 * 30))))

    if len(section_scores) >= 2:
        total_120 = sum(section_scores)
        if len(section_scores) < 4:
            total_120 = round(total_120 / len(section_scores) * 4)
        blended = round(total_120 * 0.9 + mastery_ratio * 8 + grammar_score * 0.05)
        return min(120, max(40, blended)), "practice estimate from recent coach scores"

    progress = 0
    try:
        from tutor.learning_journey import goal_progress_percent

        progress = goal_progress_percent(user, stage_slug)
    except Exception:
        pass

    fallback = min(
        110 if stage_slug == "academic_toefl_100" else 95,
        round(55 + mastery_ratio * 20 + progress // 4),
    )
    return fallback, "practice estimate from lesson progress"
