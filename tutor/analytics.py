from datetime import date, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate

from tutor.models import DailyProgress, Mistake, VocabularyItem
from tutor.plan import calculate_streak
from tutor.utils.text_validation import is_meaningful_mistake


def get_progress_analytics(user, today: date | None = None) -> dict:
    today = today or date.today()
    since = today - timedelta(days=29)

    mistakes_by_track = list(
        Mistake.objects.filter(user=user, created_at__date__gte=since)
        .values("track")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    category_counts: dict[str, int] = {}
    for mistake in Mistake.objects.filter(user=user, created_at__date__gte=since).iterator():
        if not is_meaningful_mistake(mistake.wrong_text, mistake.correct_text):
            continue
        category = mistake.category or "other"
        category_counts[category] = category_counts.get(category, 0) + 1

    from tutor.dashboard_coach import mistakes_by_area_last_30_days, track_label
    from tutor.plan_tasks import CATEGORY_LABELS

    mistakes_by_category = [
        {
            "category": category,
            "label": CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"]),
            "count": count,
        }
        for category, count in sorted(
            category_counts.items(),
            key=lambda row: (-row[1], row[0]),
        )
    ]

    mistakes_by_area = mistakes_by_area_last_30_days(user, days=30)

    mistakes_over_time = list(
        Mistake.objects.filter(user=user, created_at__date__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day", "track")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    timeline: dict[str, dict[str, int]] = {}
    for row in mistakes_over_time:
        day_key = row["day"].isoformat()
        timeline.setdefault(day_key, {})[track_label(row["track"])] = row["count"]

    vocab_learned = VocabularyItem.objects.filter(user=user).count()
    days_completed = DailyProgress.objects.filter(user=user, completed=True).count()

    return {
        "streak": calculate_streak(user, today),
        "vocab_learned": vocab_learned,
        "mistakes_total": Mistake.objects.filter(user=user).count(),
        "mistakes_by_track": [
            {"track": track_label(row["track"]), "count": row["count"]}
            for row in mistakes_by_track
        ],
        "mistakes_by_category": mistakes_by_category,
        "mistakes_by_area": mistakes_by_area,
        "mistakes_timeline": [
            {"date": day, "tracks": tracks}
            for day, tracks in sorted(timeline.items())
        ],
        "days_completed": days_completed,
    }
