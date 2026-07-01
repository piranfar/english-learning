"""Learner-friendly daily plan task content and routing."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import quote

from django.utils import timezone

from tutor.models import Mistake, VocabularyItem
from tutor.utils.text_validation import is_meaningful_mistake

GRAMMAR_CATEGORIES = {
    "article",
    "preposition",
    "tense",
    "subject_verb_agreement",
    "word_order",
    "fragment",
    "run_on_sentence",
    "collocation",
    "direct_translation",
}

WRITING_CATEGORIES = {
    "spelling",
    "sentence_structure",
    "academic_tone",
    "run_on_sentence",
    "fragment",
}

VOCAB_CATEGORIES = {"vocabulary_precision"}

SPEAKING_CATEGORIES = {"speaking_organization", "pronunciation_fluency"}

READING_CATEGORIES = {"reading_comprehension"}

LISTENING_CATEGORIES = {"listening_comprehension"}

CATEGORY_LABELS = {
    "article": "Article errors",
    "preposition": "Preposition errors",
    "tense": "Verb tense",
    "subject_verb_agreement": "Subject-verb agreement",
    "word_order": "Word order",
    "spelling": "Spelling",
    "sentence_structure": "Sentence structure",
    "fragment": "Sentence fragments",
    "run_on_sentence": "Run-on sentences",
    "collocation": "Collocation",
    "vocabulary_precision": "Vocabulary precision",
    "academic_tone": "Academic tone",
    "direct_translation": "Direct translation",
    "speaking_organization": "Speaking organization",
    "pronunciation_fluency": "Pronunciation and fluency",
    "reading_comprehension": "Reading comprehension",
    "listening_comprehension": "Listening comprehension",
    "other": "Mixed grammar patterns",
}

CATEGORY_WHY_IT_MATTERS = {
    "article": "Article mistakes show up in almost every TOEFL speaking and writing answer.",
    "preposition": "Prepositions change meaning quickly, especially in academic sentences.",
    "tense": "Consistent verb tense helps you sound clear and confident on timed tasks.",
    "subject_verb_agreement": "Agreement errors are easy to fix once you notice the pattern.",
    "word_order": "Natural word order makes your ideas easier to follow under pressure.",
    "spelling": "Spelling fixes improve clarity in essays and typed responses.",
    "sentence_structure": "Strong sentence structure makes your main idea easier to understand.",
    "fragment": "Complete sentences help you score higher on grammar and coherence.",
    "run_on_sentence": "Controlled sentence length keeps academic writing readable.",
    "collocation": "Natural word combinations make your English sound more fluent.",
    "vocabulary_precision": "Precise vocabulary helps you say exactly what you mean on test day.",
    "academic_tone": "Academic tone matters for essays, summaries, and integrated tasks.",
    "direct_translation": "English word order is different from Persian — small shifts help a lot.",
    "speaking_organization": "Clear organization helps you finish speaking tasks on time.",
    "pronunciation_fluency": "Fluency practice makes your speaking sound smoother and more natural.",
    "reading_comprehension": "Reading inference is important for TOEFL.",
    "listening_comprehension": "Listening for main ideas and details is essential for lecture questions.",
    "other": "Reviewing your recent mistakes helps you stop repeating the same errors.",
}

CATEGORY_LESSON_TOPICS = {
    "article": "articles-a-an-the",
    "preposition": "prepositions-of-time-and-place",
    "tense": "present-perfect",
    "subject_verb_agreement": "common-persian-speaker-grammar-mistakes",
    "word_order": "common-persian-speaker-grammar-mistakes",
    "fragment": "relative-clauses",
    "run_on_sentence": "relative-clauses",
    "collocation": "common-persian-speaker-grammar-mistakes",
    "direct_translation": "common-persian-speaker-grammar-mistakes",
}

SKILL_LABELS = {
    "grammar": "Grammar",
    "reading": "Reading",
    "writing": "Writing",
    "listening": "Listening",
    "speaking": "Speaking",
    "shadowing": "Shadowing",
    "vocabulary": "Vocabulary",
    "mistakes": "Mistake review",
}

TRACK_PRACTICE_REASONS = {
    "grammar": "A short grammar tune-up keeps your sentences accurate under pressure.",
    "reading": "Reading inference is important for TOEFL.",
    "writing": "Writing practice helps you fix patterns you repeat in essays.",
    "listening": "Listening practice trains you to catch key details quickly.",
    "speaking": "Speaking practice improves fluency and organization.",
    "shadowing": "Shadowing builds natural rhythm and pronunciation.",
}

TRACK_ROUTES = {
    "grammar": "/lesson",
    "reading": "/reading",
    "writing": "/writing",
    "listening": "/listening",
    "speaking": "/speaking",
    "shadowing": "/shadowing",
    "vocabulary": "/vocab",
}


def _status_from_completed(completed: bool) -> str:
    return "done" if completed else "not_started"


def _skill_for_mistake(mistake: Mistake) -> str:
    category = mistake.category or "other"
    if category in VOCAB_CATEGORIES or mistake.track == "vocab_quiz":
        return "vocabulary"
    if category in WRITING_CATEGORIES or "writing" in mistake.track:
        return "writing"
    if category in SPEAKING_CATEGORIES or mistake.track == "speaking_coach":
        return "speaking"
    if category in READING_CATEGORIES or mistake.track == "reading_coach":
        return "reading"
    if category in LISTENING_CATEGORIES or mistake.track == "listening_coach":
        return "listening"
    if category in GRAMMAR_CATEGORIES or mistake.track == "grammar_coach":
        return "grammar"
    return "mistakes"


def count_recent_mistakes_by_category(user, days: int = 7) -> dict[str, int]:
    since = timezone.now() - timedelta(days=days)
    counts: dict[str, int] = {}
    for mistake in Mistake.objects.filter(user=user, created_at__gte=since).iterator():
        if not is_meaningful_mistake(mistake.wrong_text, mistake.correct_text):
            continue
        category = mistake.category or "other"
        counts[category] = counts.get(category, 0) + 1
    return counts


def _mistake_category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"])


def build_mistake_reason(mistake: Mistake, category_counts: dict[str, int]) -> str:
    category = mistake.category or "other"
    count = category_counts.get(category, 0)
    label = _mistake_category_label(category).lower()
    if count >= 2:
        return f"You made {count} {label} recently."
    if mistake.reason:
        return mistake.reason[:180]
    return f"Review this {label} mistake before it becomes a habit."


def build_vocab_reason(vocab: VocabularyItem) -> str:
    return f'"{vocab.word}" is due for review today.'


def build_track_reason(track: str) -> str:
    return TRACK_PRACTICE_REASONS.get(track, "Daily practice keeps your skills moving forward.")


def route_for_mistake(mistake: Mistake) -> str:
    category = mistake.category or "other"
    if category in VOCAB_CATEGORIES or mistake.track == "vocab_quiz":
        word = mistake.correct_text.strip()
        if word:
            return f"/vocab?word={quote(word)}"
        return "/vocab?mode=review_mistakes"

    if category in WRITING_CATEGORIES or "writing" in mistake.track:
        return f"/writing?tab=editing"

    if category in SPEAKING_CATEGORIES or mistake.track == "speaking_coach":
        return "/speaking"

    if category in READING_CATEGORIES or mistake.track == "reading_coach":
        return "/reading"

    if category in LISTENING_CATEGORIES or mistake.track == "listening_coach":
        return "/listening"

    topic = CATEGORY_LESSON_TOPICS.get(category)
    if topic:
        return f"/lesson?topic={topic}"

    return f"/mistakes?focus={mistake.id}"


def title_for_mistake(mistake: Mistake) -> str:
    category = mistake.category or "other"
    label = _mistake_category_label(category)
    snippet = mistake.wrong_text.strip()
    if len(snippet) > 42:
        snippet = f"{snippet[:42]}…"
    return f"Review {label.lower()}: {snippet}"


def build_vocab_plan_item(vocab: VocabularyItem, completed: bool = False) -> dict:
    skill = "vocabulary"
    return {
        "id": f"vocab-{vocab.id}",
        "type": "vocab",
        "track": skill,
        "skill": SKILL_LABELS[skill],
        "title": f'Review vocabulary: "{vocab.word}"',
        "minutes": 3,
        "status": _status_from_completed(completed),
        "completed": completed,
        "reason": build_vocab_reason(vocab),
        "route": f"/vocab?word={vocab.id}",
        "ref_id": vocab.id,
        "metadata": {
            "vocab_id": vocab.id,
            "word": vocab.word,
        },
    }


def build_mistake_plan_item(
    mistake: Mistake,
    category_counts: dict[str, int],
    completed: bool = False,
) -> dict:
    skill = _skill_for_mistake(mistake)
    return {
        "id": f"mistake-{mistake.id}",
        "type": "mistake",
        "track": skill,
        "skill": SKILL_LABELS.get(skill, "Mistake review"),
        "title": title_for_mistake(mistake),
        "minutes": 5,
        "status": _status_from_completed(completed),
        "completed": completed,
        "reason": build_mistake_reason(mistake, category_counts),
        "route": route_for_mistake(mistake),
        "ref_id": mistake.id,
        "metadata": {
            "mistake_id": mistake.id,
            "category": mistake.category or "other",
            "source_track": mistake.track,
        },
    }


def build_track_plan_item(
    track: str,
    minutes: int,
    completed: bool = False,
    *,
    reason: str | None = None,
) -> dict:
    skill = track if track in SKILL_LABELS else "grammar"
    return {
        "id": f"track-{track}",
        "type": "track",
        "track": track,
        "skill": SKILL_LABELS.get(skill, track.capitalize()),
        "title": f"{SKILL_LABELS.get(skill, track.capitalize())} practice",
        "minutes": minutes,
        "status": _status_from_completed(completed),
        "completed": completed,
        "reason": reason or build_track_reason(track),
        "route": TRACK_ROUTES.get(track, "/dashboard"),
        "metadata": {"practice_track": track},
    }


def build_plan_summary(user, items: list[dict]) -> dict:
    category_counts = count_recent_mistakes_by_category(user)
    recommended_order = [item["id"] for item in items if not item.get("completed")]

    if category_counts:
        top_category = max(category_counts, key=category_counts.get)
        weakness = _mistake_category_label(top_category)
        why = CATEGORY_WHY_IT_MATTERS.get(top_category, CATEGORY_WHY_IT_MATTERS["other"])
    else:
        mistake_items = [item for item in items if item.get("type") == "mistake"]
        if mistake_items:
            top_category = mistake_items[0].get("metadata", {}).get("category", "other")
            weakness = _mistake_category_label(top_category)
            why = CATEGORY_WHY_IT_MATTERS.get(top_category, CATEGORY_WHY_IT_MATTERS["other"])
        else:
            weakness = "Balanced daily practice"
            why = "Steady practice across skills builds confidence for TOEFL and real-life English."

    return {
        "main_focus": weakness,
        "why_it_matters": why,
        "recommended_order": recommended_order,
    }


def enrich_plan_item(item: dict, user, category_counts: dict[str, int] | None = None) -> dict | None:
    category_counts = category_counts or count_recent_mistakes_by_category(user)
    completed = bool(item.get("completed"))
    item_type = item.get("type")

    if item_type == "mistake":
        ref_id = item.get("ref_id")
        if not ref_id:
            return None
        try:
            mistake = Mistake.objects.get(id=ref_id, user=user)
        except Mistake.DoesNotExist:
            return None
        if not is_meaningful_mistake(mistake.wrong_text, mistake.correct_text):
            return None
        enriched = build_mistake_plan_item(mistake, category_counts, completed=completed)
        enriched["completed"] = completed
        enriched["status"] = _status_from_completed(completed)
        return enriched

    if item_type == "vocab":
        ref_id = item.get("ref_id")
        if not ref_id:
            return None
        try:
            vocab = VocabularyItem.objects.get(id=ref_id, user=user)
        except VocabularyItem.DoesNotExist:
            return None
        enriched = build_vocab_plan_item(vocab, completed=completed)
        enriched["completed"] = completed
        enriched["status"] = _status_from_completed(completed)
        return enriched

    if item_type == "track":
        track = item.get("track") or item.get("metadata", {}).get("practice_track") or "grammar"
        minutes = item.get("minutes", 10)
        enriched = build_track_plan_item(track, minutes, completed=completed)
        enriched["completed"] = completed
        enriched["status"] = _status_from_completed(completed)
        return enriched

    return item


def prepare_plan_items_for_response(items: list[dict], user) -> list[dict]:
    category_counts = count_recent_mistakes_by_category(user)
    prepared: list[dict] = []
    for item in items:
        if item.get("type") in ("reading", "listening"):
            prepared.append(item)
            continue
        enriched = enrich_plan_item(item, user, category_counts)
        if enriched:
            prepared.append(enriched)
    return prepared
