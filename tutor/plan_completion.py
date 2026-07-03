"""Auto-complete today's plan items when the learner finishes coach activities."""

from __future__ import annotations

from datetime import date

from tutor.plan import get_today_plan, sync_progress_completion, update_plan_item


def _item_matches_activity(item: dict, *, track: str | None, metadata: dict) -> bool:
    if item.get("completed"):
        return False

    item_id = item.get("id") or ""
    item_type = item.get("type") or ""
    item_meta = item.get("metadata") or {}

    if track and item_id == f"track-{track}":
        return True

    if track == "reading" and item_type == "reading":
        focus = metadata.get("lesson_focus")
        if not focus or focus == "none":
            return True
        item_focus = item_meta.get("lesson_focus")
        if item_focus in (focus, "current_lesson"):
            return True

    if track == "listening" and item_type == "listening":
        listening_type = metadata.get("listening_type")
        focus = metadata.get("lesson_focus")
        if listening_type and item_meta.get("listening_type") == listening_type:
            if not focus or focus == "none" or item_meta.get("lesson_focus") in (focus, "current_lesson"):
                return True
        elif not listening_type:
            return True

    if track == "grammar" and item_type == "track" and item.get("track") == "grammar":
        return True

    if track == "vocabulary" and item_type == "vocab":
        vocab_id = metadata.get("vocab_id")
        if vocab_id and item_id == f"vocab-{vocab_id}":
            return True
        if not vocab_id:
            return True

    if track == "mistakes" and item_type == "mistake":
        mistake_id = metadata.get("mistake_id")
        if mistake_id and item_id == f"mistake-{mistake_id}":
            return True

    return False


def auto_complete_plan_items(
    user,
    *,
    track: str | None = None,
    metadata: dict | None = None,
    today: date | None = None,
) -> list[str]:
    """Mark matching incomplete plan items as done. Returns completed item ids."""
    plan, progress = get_today_plan(user, today)
    if not plan or not track:
        return []

    metadata = metadata or {}
    completed_ids: list[str] = []

    for item in plan.items:
        if not _item_matches_activity(item, track=track, metadata=metadata):
            continue
        item_id = item.get("id")
        if not item_id:
            continue
        try:
            update_plan_item(plan, item_id, True)
            completed_ids.append(item_id)
        except ValueError:
            continue

    if completed_ids and progress:
        sync_progress_completion(plan, progress)

    return completed_ids
