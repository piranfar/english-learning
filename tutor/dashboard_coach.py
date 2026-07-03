"""Deterministic coach focus for the learner dashboard."""

from __future__ import annotations

from datetime import date

from tutor.models import Mistake, StudyPlan, VocabularyItem
from tutor.plan_tasks import (
    CATEGORY_LABELS,
    CATEGORY_LESSON_TOPICS,
    CATEGORY_WHY_IT_MATTERS,
    SKILL_LABELS,
    build_plan_summary,
    count_recent_mistakes_by_category,
    prepare_plan_items_for_response,
)
from tutor.utils.text_validation import is_meaningful_mistake

TRACK_LABELS = {
    "writing_edit_coach": "Writing correction",
    "grammar_coach": "Grammar",
    "writing_lesson_coach": "Writing lesson",
    "vocab_quiz": "Vocabulary quiz",
    "writing_coach": "Writing practice",
    "speaking_coach": "Speaking practice",
    "reading_coach": "Reading practice",
    "listening_coach": "Listening practice",
    "writing_paraphrase_coach": "Paraphrasing practice",
    "writing_paraphrase_generate": "Paraphrasing practice",
    "writing_paraphrase_check": "Paraphrasing practice",
    "sentence_builder_coach": "Sentence builder",
    "paragraph_builder_coach": "Paragraph builder",
}

CATEGORY_FOCUS_ROUTES = {
    "article": "/mistakes?category=article",
    "preposition": "/mistakes?category=preposition",
    "spelling": "/mistakes?category=spelling",
    "sentence_structure": "/mistakes?category=sentence_structure",
    "vocabulary_precision": "/vocab",
    "reading_comprehension": "/reading",
    "listening_comprehension": "/listening",
    "speaking_organization": "/speaking",
    "pronunciation_fluency": "/speaking",
    "academic_tone": "/writing",
}

CATEGORY_TRACK_MATCH = {
    "article": "grammar",
    "preposition": "grammar",
    "tense": "grammar",
    "subject_verb_agreement": "grammar",
    "word_order": "grammar",
    "fragment": "grammar",
    "run_on_sentence": "grammar",
    "collocation": "grammar",
    "direct_translation": "grammar",
    "spelling": "writing",
    "sentence_structure": "writing",
    "vocabulary_precision": "vocabulary",
    "reading_comprehension": "reading",
    "listening_comprehension": "listening",
    "speaking_organization": "speaking",
    "pronunciation_fluency": "speaking",
    "academic_tone": "writing",
}


def track_label(track: str) -> str:
    if not track:
        return "Practice"
    if track in TRACK_LABELS:
        return TRACK_LABELS[track]
    if track in SKILL_LABELS:
        return SKILL_LABELS[track]
    return track.replace("_", " ").title()


def route_for_focus_category(category: str) -> str:
    route = CATEGORY_FOCUS_ROUTES.get(category)
    if route:
        return route
    lesson_topic = CATEGORY_LESSON_TOPICS.get(category)
    if lesson_topic:
        return f"/lesson?topic={lesson_topic}"
    return "/today"


def focus_action_title(category: str | None, *, vocab_due: int = 0) -> str:
    if category == "vocabulary_precision" or (category is None and vocab_due > 0):
        count = vocab_due
        return (
            f"Review {count} due vocabulary item{'s' if count != 1 else ''}"
            if count > 0
            else "Review due vocabulary"
        )
    if category:
        label = CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"])
        return f"Practice {label.lower()}"
    return "Open today's study plan"


def mistakes_by_category_last_30_days(user, days: int = 30) -> list[dict]:
    since_days = count_recent_mistakes_by_category(user, days=days)
    return [
        {
            "category": category,
            "label": CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"]),
            "count": count,
        }
        for category, count in sorted(
            since_days.items(),
            key=lambda row: (-row[1], row[0]),
        )
    ]


def mistakes_by_area_last_30_days(user, days: int = 30) -> list[dict]:
    from datetime import timedelta

    from django.utils import timezone

    since = timezone.now() - timedelta(days=days)
    counts: dict[str, int] = {}
    for mistake in Mistake.objects.filter(user=user, created_at__gte=since).iterator():
        if not is_meaningful_mistake(mistake.wrong_text, mistake.correct_text):
            continue
        area = track_label(mistake.track)
        counts[area] = counts.get(area, 0) + 1
    return [
        {"area": area, "count": count}
        for area, count in sorted(counts.items(), key=lambda row: (-row[1], row[0]))
    ]


def progress_by_skill(minutes_per_track: dict) -> list[dict]:
    rows = []
    for track, minutes in minutes_per_track.items():
        rows.append(
            {
                "skill": track_label(track),
                "minutes": minutes,
            }
        )
    return sorted(rows, key=lambda row: (-row["minutes"], row["skill"]))


def _first_incomplete_task(items: list[dict]) -> dict | None:
    for item in items:
        if not item.get("completed"):
            return item
    return None


def _serialize_plan_task(task: dict | None) -> dict | None:
    if not task:
        return None
    return {
        "title": task.get("title", ""),
        "route": task.get("route", "/today"),
        "type": task.get("type"),
        "skill": task.get("skill"),
        "category": (task.get("metadata") or {}).get("category"),
    }


def _task_matches_focus_category(task: dict | None, category: str | None) -> bool:
    if not task or not category:
        return False
    task_type = task.get("type")
    if task_type == "vocab":
        return category == "vocabulary_precision"
    if task_type == "mistake":
        return (task.get("metadata") or {}).get("category") == category
    if task_type == "track":
        return CATEGORY_TRACK_MATCH.get(category) == task.get("track")
    return False


def _top_focus_category(category_counts: dict[str, int]) -> str | None:
    if not category_counts:
        return None
    return max(category_counts, key=category_counts.get)


def _vocab_due_message(vocab_due: int) -> str:
    if vocab_due <= 0:
        return "No vocabulary due right now."
    suffix = "is" if vocab_due == 1 else "are"
    noun = "item" if vocab_due == 1 else "items"
    return f"{vocab_due} vocabulary {noun} {suffix} due."


def _build_focus_payload(
    *,
    title: str,
    why: str,
    category: str | None,
    vocab_due: int,
    route_fallback: str = "/today",
) -> tuple[dict, dict]:
    today_focus = {
        "title": title,
        "why_it_matters": why,
        "category": category,
    }
    action_route = route_for_focus_category(category) if category else route_fallback
    if category is None and vocab_due > 0:
        action_route = "/vocab"
    focus_action = {
        "title": focus_action_title(category, vocab_due=vocab_due),
        "route": action_route,
        "label": "Start focus task",
    }
    return today_focus, focus_action


def build_coach_focus(
    user,
    today: date,
    plan_summary: dict,
    profile,
    vocab_due: int,
    mistakes_due: int,
    plan: StudyPlan | None = None,
) -> dict:
    category_counts = count_recent_mistakes_by_category(user, days=30)
    mistakes_recorded_30d = sum(category_counts.values())
    mistakes_total = Mistake.objects.filter(user=user).count()
    has_vocab_deck = VocabularyItem.objects.filter(user=user).exists()

    plan_items = []
    plan_focus = None
    if plan is not None:
        plan_items = prepare_plan_items_for_response(plan.items, user)
        plan_focus = build_plan_summary(user, plan_items)

    next_task = _first_incomplete_task(plan_items)
    next_plan_task = _serialize_plan_task(next_task)

    top_category = _top_focus_category(category_counts)
    vocab_due_message = _vocab_due_message(vocab_due)

    empty_states = {
        "no_mistakes_yet": mistakes_total == 0,
        "no_vocab_due": vocab_due == 0,
        "needs_diagnostic": (
            mistakes_total == 0
            and vocab_due == 0
            and not plan_summary.get("exists")
            and not has_vocab_deck
        ),
        "vocab_due_message": vocab_due_message,
    }

    plan_exists = bool(plan_summary.get("exists") and plan_summary.get("total_count", 0) > 0)
    plan_completed = bool(plan_summary.get("completed"))

    if plan_completed:
        title = plan_focus["main_focus"] if plan_focus else "Daily plan complete"
        why = (
            plan_focus["why_it_matters"]
            if plan_focus
            else "You finished today's assigned work. Extra practice still helps retention."
        )
        today_focus, focus_action = _build_focus_payload(
            title=title,
            why=why,
            category=top_category,
            vocab_due=0,
            route_fallback="/speaking",
        )
        if top_category is None:
            focus_action = {
                "title": "Keep momentum with a quick speaking session",
                "route": "/speaking",
                "label": "Start focus task",
            }
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=None,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=True,
        )

    if top_category:
        weakness = CATEGORY_LABELS.get(top_category, CATEGORY_LABELS["other"])
        why = CATEGORY_WHY_IT_MATTERS.get(top_category, CATEGORY_WHY_IT_MATTERS["other"])
        today_focus, focus_action = _build_focus_payload(
            title=weakness,
            why=why,
            category=top_category,
            vocab_due=0 if top_category != "vocabulary_precision" else vocab_due,
        )
        if (
            next_task
            and _task_matches_focus_category(next_task, top_category)
            and top_category != "vocabulary_precision"
        ):
            focus_action = {
                "title": next_task.get("title", focus_action["title"]),
                "route": next_task.get("route", focus_action["route"]),
                "label": "Start focus task",
            }
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=next_plan_task if next_task and not _task_matches_focus_category(next_task, top_category) else None,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=False,
        )

    if mistakes_due > 0:
        today_focus, focus_action = _build_focus_payload(
            title="Mistake review",
            why="Reviewing due mistakes stops small errors from becoming habits.",
            category=None,
            vocab_due=0,
            route_fallback="/today" if plan_exists else "/mistakes",
        )
        focus_action["title"] = (
            f"Review {mistakes_due} due mistake{'s' if mistakes_due != 1 else ''}"
        )
        if not plan_exists:
            focus_action["title"] = "Generate today's study plan"
            focus_action["route"] = "/today"
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=next_plan_task,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=False,
        )

    if vocab_due > 0:
        today_focus, focus_action = _build_focus_payload(
            title="Vocabulary review",
            why="Spaced review helps you remember words when you need them on test day.",
            category="vocabulary_precision",
            vocab_due=vocab_due,
        )
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=next_plan_task if next_task and next_task.get("type") != "vocab" else None,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=False,
        )

    weak_areas = profile.weak_areas or []
    if weak_areas:
        weakness = weak_areas[0].replace("_", " ").strip().title()
        today_focus, focus_action = _build_focus_payload(
            title=weakness,
            why="You marked this as a weak area — targeted practice will help most.",
            category=None,
            vocab_due=0,
            route_fallback="/today",
        )
        focus_action = {
            "title": (
                "Generate today's study plan" if not plan_exists else f"Practice {weakness.lower()}"
            ),
            "route": "/today",
            "label": "Start focus task",
        }
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=next_plan_task,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=False,
        )

    if empty_states["needs_diagnostic"]:
        today_focus = {
            "title": "Getting started",
            "why_it_matters": (
                "Complete a short diagnostic activity to personalize your plan."
            ),
            "category": None,
        }
        focus_action = {
            "title": "Start a short diagnostic activity",
            "route": "/lesson",
            "label": "Start focus task",
        }
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=next_plan_task,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=plan_exists,
            plan_completed=False,
        )

    if not plan_exists:
        today_focus = {
            "title": "Balanced daily practice",
            "why_it_matters": (
                "Regular practice across skills keeps you ready for TOEFL and real-life English."
            ),
            "category": None,
        }
        focus_action = {
            "title": "Generate today's study plan",
            "route": "/today",
            "label": "Start focus task",
        }
        return _assemble_coach_focus(
            today_focus,
            focus_action,
            next_plan_task=None,
            vocab_due=vocab_due,
            empty_states=empty_states,
            plan_exists=False,
            plan_completed=False,
        )

    title = plan_focus["main_focus"] if plan_focus else "Today's practice"
    why = plan_focus["why_it_matters"] if plan_focus else "Continue with your assigned tasks for today."
    today_focus, focus_action = _build_focus_payload(
        title=title,
        why=why,
        category=None,
        vocab_due=0,
        route_fallback="/today",
    )
    focus_action = {
        "title": "Work through today's plan tasks",
        "route": "/today",
        "label": "Start focus task",
    }
    return _assemble_coach_focus(
        today_focus,
        focus_action,
        next_plan_task=next_plan_task,
        vocab_due=vocab_due,
        empty_states=empty_states,
        plan_exists=plan_exists,
        plan_completed=False,
    )


def _assemble_coach_focus(
    today_focus: dict,
    focus_action: dict,
    *,
    next_plan_task: dict | None,
    vocab_due: int,
    empty_states: dict,
    plan_exists: bool,
    plan_completed: bool,
) -> dict:
    focus_category = today_focus.get("category")
    if vocab_due == 0 and focus_category != "vocabulary_precision":
        if focus_action.get("route", "").startswith("/vocab"):
            focus_action = {
                "title": focus_action_title(focus_category, vocab_due=0),
                "route": route_for_focus_category(focus_category) if focus_category else "/today",
                "label": "Start focus task",
            }
        if "vocabulary" in focus_action.get("title", "").lower() and "due" in focus_action.get("title", "").lower():
            focus_action = {
                "title": focus_action_title(focus_category, vocab_due=0),
                "route": route_for_focus_category(focus_category) if focus_category else "/today",
                "label": "Start focus task",
            }

    if vocab_due == 0 and next_plan_task and next_plan_task.get("type") == "vocab":
        next_plan_task = None

    return {
        "today_focus": today_focus,
        "focus_action": focus_action,
        "next_plan_task": next_plan_task,
        "vocab_due_count": vocab_due,
        "plan_exists": plan_exists,
        "plan_completed": plan_completed,
        "main_weakness": today_focus["title"],
        "why_it_matters": today_focus["why_it_matters"],
        "recommended_action": focus_action["title"],
        "action_route": focus_action["route"],
        "action_label": focus_action["label"],
        "empty_states": empty_states,
    }
