from datetime import date, timedelta

from django.conf import settings
from django.db.models import Q

from tutor.learning_journey import plan_minutes_for_user, plan_track_reason
from tutor.models import DailyProgress, Mistake, StudyPlan, VocabularyItem
from tutor.plan_tasks import (
    build_mistake_plan_item,
    build_plan_summary,
    build_track_plan_item,
    build_vocab_plan_item,
    count_recent_mistakes_by_category,
    prepare_plan_items_for_response,
)
from tutor.utils.text_validation import is_meaningful_mistake


def get_plan_config() -> dict:
    return getattr(settings, "STUDY_PLAN_DEFAULTS", {})


def due_mistakes_queryset(user, today: date | None = None):
    today = today or date.today()
    return Mistake.objects.filter(user=user).filter(
        Q(next_review_date__isnull=True) | Q(next_review_date__lte=today)
    )


def is_reviewable_mistake(mistake: Mistake) -> bool:
    return is_meaningful_mistake(mistake.wrong_text, mistake.correct_text)


def due_reviewable_mistakes(user, today: date | None = None) -> list[Mistake]:
    return [
        mistake
        for mistake in due_mistakes_queryset(user, today).order_by(
            "next_review_date", "created_at"
        )
        if is_reviewable_mistake(mistake)
    ]


def count_due_reviewable_mistakes(user, today: date | None = None) -> int:
    return len(due_reviewable_mistakes(user, today))


def due_vocab_queryset(user, today: date | None = None):
    today = today or date.today()
    return VocabularyItem.objects.filter(
        user=user,
        next_review_date__lte=today,
    )


def build_plan_items(user, today: date | None = None) -> list[dict]:
    today = today or date.today()
    config = get_plan_config()
    vocab_count = config.get("vocab_count", 5)
    mistake_count = config.get("mistake_count", 3)
    minutes_per_track = plan_minutes_for_user(user) or config.get(
        "minutes_per_track",
        {
            "grammar": 15,
            "reading": 15,
            "writing": 15,
            "listening": 10,
            "speaking": 10,
            "shadowing": 10,
        },
    )

    items = []
    category_counts = count_recent_mistakes_by_category(user)

    for vocab in due_vocab_queryset(user, today).order_by(
        "next_review_date", "created_at"
    )[:vocab_count]:
        items.append(build_vocab_plan_item(vocab))

    for mistake in due_reviewable_mistakes(user, today)[:mistake_count]:
        items.append(build_mistake_plan_item(mistake, category_counts))

    from tutor.reading_practice import build_reading_plan_items_for_user

    for reading_item in build_reading_plan_items_for_user(user, today):
        items.append(reading_item)

    from tutor.listening_practice import build_listening_plan_items_for_user

    for listening_item in build_listening_plan_items_for_user(user, today):
        items.append(listening_item)

    for track, minutes in minutes_per_track.items():
        stage_reason = plan_track_reason(user, track)
        items.append(build_track_plan_item(track, minutes, reason=stage_reason))

    return items


def minutes_per_track_from_items(items: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for item in items:
        track = item.get("track", "other")
        totals[track] = totals.get(track, 0) + item.get("minutes", 0)
    return totals


def get_today_plan(user, today: date | None = None) -> tuple[StudyPlan | None, DailyProgress | None]:
    today = today or date.today()
    try:
        plan = StudyPlan.objects.get(user=user, date=today)
    except StudyPlan.DoesNotExist:
        return None, None

    progress, _ = DailyProgress.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            "minutes_per_track": minutes_per_track_from_items(plan.items),
            "completed": False,
        },
    )
    return plan, progress


def generate_today_plan(user, today: date | None = None) -> tuple[StudyPlan, DailyProgress]:
    today = today or date.today()
    if StudyPlan.objects.filter(user=user, date=today).exists():
        raise ValueError("A plan already exists for today.")

    items = build_plan_items(user, today)
    plan = StudyPlan.objects.create(user=user, date=today, items=items)
    progress_minutes = minutes_per_track_from_items(items)
    progress, _ = DailyProgress.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            "minutes_per_track": progress_minutes,
            "completed": False,
        },
    )
    if not progress.minutes_per_track:
        progress.minutes_per_track = progress_minutes
        progress.save(update_fields=["minutes_per_track"])
    return plan, progress


def filter_reviewable_plan_items(items: list[dict], user) -> list[dict]:
    """Drop invalid mistake tasks and enrich legacy items for the API."""
    return prepare_plan_items_for_response(items, user)


def plan_response_payload(plan: StudyPlan, progress: DailyProgress, user, today: date | None = None) -> dict:
    today = today or date.today()
    items = filter_reviewable_plan_items(plan.items, user)
    completed_count = sum(1 for item in items if item.get("completed"))
    summary = build_plan_summary(user, items)
    return {
        "exists": True,
        "date": plan.date.isoformat(),
        "items": items,
        "summary": summary,
        "completed_count": completed_count,
        "total_count": len(items),
        "vocab_due": due_vocab_queryset(user, today).count(),
        "mistakes_due": count_due_reviewable_mistakes(user, today),
        "progress": {
            "completed": progress.completed,
            "minutes_per_track": progress.minutes_per_track,
        },
    }


def empty_plan_response(user, today: date | None = None) -> dict:
    today = today or date.today()
    return {
        "exists": False,
        "date": today.isoformat(),
        "items": [],
        "summary": {
            "main_focus": "Balanced daily practice",
            "why_it_matters": "Generate a plan to see what matters most for you today.",
            "recommended_order": [],
        },
        "completed_count": 0,
        "total_count": 0,
        "vocab_due": due_vocab_queryset(user, today).count(),
        "mistakes_due": count_due_reviewable_mistakes(user, today),
        "progress": {
            "completed": False,
            "minutes_per_track": {},
        },
    }


def get_or_create_today_plan(user, today: date | None = None) -> tuple[StudyPlan, DailyProgress]:
    today = today or date.today()
    plan, created = StudyPlan.objects.get_or_create(
        user=user,
        date=today,
        defaults={"items": build_plan_items(user, today)},
    )
    if created:
        progress_minutes = minutes_per_track_from_items(plan.items)
    else:
        progress_minutes = {}

    progress, _ = DailyProgress.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            "minutes_per_track": progress_minutes,
            "completed": False,
        },
    )

    if created and not progress.minutes_per_track:
        progress.minutes_per_track = progress_minutes
        progress.save(update_fields=["minutes_per_track"])

    return plan, progress


def update_plan_item(plan: StudyPlan, item_id: str, completed: bool) -> StudyPlan:
    items = list(plan.items)
    updated = False
    for item in items:
        if item.get("id") == item_id:
            item["completed"] = completed
            item["status"] = "done" if completed else "not_started"
            updated = True
            break

    if not updated:
        raise ValueError(f"Plan item '{item_id}' not found")

    plan.items = items
    plan.save(update_fields=["items"])
    return plan


def sync_progress_completion(plan: StudyPlan, progress: DailyProgress) -> DailyProgress:
    all_done = bool(plan.items) and all(item.get("completed") for item in plan.items)
    progress.completed = all_done
    progress.minutes_per_track = minutes_per_track_from_items(plan.items)
    progress.save(update_fields=["completed", "minutes_per_track"])
    return progress


def calculate_streak(user, today: date | None = None) -> int:
    today = today or date.today()
    streak = 0
    current = today

    if not DailyProgress.objects.filter(user=user, date=current, completed=True).exists():
        current -= timedelta(days=1)

    while DailyProgress.objects.filter(user=user, date=current, completed=True).exists():
        streak += 1
        current -= timedelta(days=1)

    return streak
