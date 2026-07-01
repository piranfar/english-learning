from datetime import date, timedelta

from django.utils import timezone

from tutor.learning_journey import (
    get_or_create_journey,
    next_lesson_for_stage,
)
from tutor.models import LessonProgress, LessonTopic, Message, Mistake, PracticeSession

GRAMMAR_TRACK = "grammar_coach"

TOPIC_KEYWORD_RULES = [
    {
        "slug": "articles-a-an-the",
        "keywords": [
            "article",
            "articles",
            " a ",
            " an ",
            " the ",
            "a/an",
            "determiner",
        ],
    },
    {
        "slug": "prepositions-of-time-and-place",
        "keywords": [
            "preposition",
            "prepositions",
            " in ",
            " on ",
            " at ",
            "into",
            "onto",
            "place",
            "time",
        ],
    },
    {
        "slug": "present-perfect",
        "keywords": [
            "present perfect",
            "have/has",
            " since ",
            " for ",
            "already",
            "yet",
            "just",
            "ever",
            "never",
        ],
    },
    {
        "slug": "present-perfect-continuous",
        "keywords": [
            "present perfect continuous",
            "have been",
            "has been",
            "for a long time",
            "how long",
        ],
    },
    {
        "slug": "past-simple",
        "keywords": [
            "past simple",
            "past tense",
            "yesterday",
            "ago",
            "last week",
            "finished time",
            "ed ",
        ],
    },
    {
        "slug": "past-perfect",
        "keywords": [
            "past perfect",
            "had ",
            "before ",
            "already",
            "by the time",
        ],
    },
    {
        "slug": "present-simple",
        "keywords": [
            "present simple",
            "every day",
            "usually",
            "always",
            "habit",
            "routine",
        ],
    },
    {
        "slug": "present-continuous",
        "keywords": [
            "present continuous",
            "continuous",
            "progressive",
            "-ing",
            "now",
            "currently",
            "at the moment",
        ],
    },
    {
        "slug": "past-simple-vs-present-perfect",
        "keywords": [
            "past simple vs present perfect",
        ],
    },
    {
        "slug": "present-simple-vs-present-continuous",
        "keywords": [
            "present simple vs present continuous",
        ],
    },
    {
        "slug": "used-to-be-used-to-get-used-to",
        "keywords": [
            "used to",
            "be used to",
            "get used to",
            "accustomed",
        ],
    },
    {
        "slug": "modal-verbs-should-must-have-to",
        "keywords": [
            "modal",
            "should",
            "must",
            "have to",
            "ought",
            "obligation",
        ],
    },
    {
        "slug": "conditionals-type-0-1-2",
        "keywords": [
            "conditional",
            "if clause",
            "would",
            "unless",
            "type 0",
            "type 1",
            "type 2",
        ],
    },
    {
        "slug": "passive-voice",
        "keywords": [
            "passive",
            "was/were",
            "been",
            "by the",
        ],
    },
    {
        "slug": "relative-clauses",
        "keywords": [
            "relative clause",
            "who ",
            "which ",
            "that ",
            "whose",
            "where ",
        ],
    },
    {
        "slug": "gerunds-and-infinitives",
        "keywords": [
            "gerund",
            "infinitive",
            "to verb",
            "-ing form",
            "enjoy",
            "want to",
        ],
    },
    {
        "slug": "common-persian-speaker-grammar-mistakes",
        "keywords": [
            "persian",
            "farsi",
            "word order",
            "native speaker",
        ],
    },
]


def topic_to_dict(topic: LessonTopic) -> dict:
    return {
        "id": topic.id,
        "title": topic.title,
        "slug": topic.slug,
        "level": topic.level,
        "category": topic.category,
        "stage_slug": topic.stage_slug,
        "description": topic.description,
        "order": topic.order,
    }


def mistake_to_review_item(mistake: Mistake) -> dict:
    return {
        "wrong_text": mistake.wrong_text,
        "correct_text": mistake.correct_text,
        "reason": mistake.reason,
        "persian_explanation": mistake.persian_explanation,
    }


def build_yesterday_summary(user) -> str:
    yesterday = date.today() - timedelta(days=1)
    grammar_sessions = PracticeSession.objects.filter(
        user=user,
        track=GRAMMAR_TRACK,
        created_at__date=yesterday,
    ).order_by("created_at")

    progress_rows = LessonProgress.objects.filter(
        user=user,
        last_practiced__date=yesterday,
    ).select_related("topic")

    parts = []
    if progress_rows.exists():
        titles = [row.topic.title for row in progress_rows]
        parts.append(f"Yesterday you studied: {', '.join(titles)}.")

    if grammar_sessions.exists():
        user_messages = Message.objects.filter(
            session__in=grammar_sessions,
            role="user",
        ).order_by("created_at")
        if user_messages.exists():
            snippets = [message.content.strip()[:100] for message in user_messages[:3]]
            parts.append(f"You practiced with prompts like: {'; '.join(snippets)}.")
        elif not parts:
            count = grammar_sessions.count()
            parts.append(
                f"You had {count} grammar session{'s' if count != 1 else ''} yesterday."
            )

    return " ".join(parts)


def recent_mistakes(user, days: int = 7, limit: int = 3):
    from tutor.utils.text_validation import is_meaningful_mistake

    since = timezone.now() - timedelta(days=days)
    mistakes = Mistake.objects.filter(user=user, created_at__gte=since).order_by(
        "-created_at"
    )
    filtered = [
        mistake
        for mistake in mistakes
        if is_meaningful_mistake(mistake.wrong_text, mistake.correct_text)
    ]
    return filtered[:limit]


def score_mistake_topics(mistakes) -> dict[str, int]:
    scores: dict[str, int] = {}
    for mistake in mistakes:
        blob = " ".join(
            [
                mistake.wrong_text.lower(),
                mistake.correct_text.lower(),
                mistake.reason.lower(),
            ]
        )
        for rule in TOPIC_KEYWORD_RULES:
            slug = rule["slug"]
            for keyword in rule["keywords"]:
                if keyword.lower() in blob:
                    scores[slug] = scores.get(slug, 0) + 1
    return scores


def get_topic_by_slug(slug: str) -> LessonTopic | None:
    return LessonTopic.objects.filter(slug=slug, is_active=True).first()


def next_curriculum_topic(user) -> LessonTopic | None:
    journey = get_or_create_journey(user)
    return next_lesson_for_stage(user, journey.current_goal.slug)


def build_starter_message(
    topic: LessonTopic,
    yesterday_summary: str,
    review_items: list[dict],
) -> str:
    lines = [
        f"Let's start today's B1 grammar lesson on: {topic.title}.",
        topic.description or "",
    ]
    if yesterday_summary:
        lines.append(f"Context from yesterday: {yesterday_summary}")
    if review_items:
        lines.append("Please briefly review these recent mistakes before teaching:")
        for index, item in enumerate(review_items, start=1):
            lines.append(
                f"{index}. Wrong: {item['wrong_text']} → Correct: {item['correct_text']} "
                f"({item['reason']})"
            )
    lines.append(
        "Teach this topic with clear explanations, Persian notes where helpful, "
        "academic/TOEFL-style examples, and one practice question to start."
    )
    return "\n\n".join(line for line in lines if line.strip())


def get_lesson_recommendation(user) -> dict:
    mistakes = recent_mistakes(user, days=7, limit=20)
    review_items = [mistake_to_review_item(m) for m in recent_mistakes(user, days=7, limit=3)]
    yesterday_summary = build_yesterday_summary(user)

    recommended_topic = None
    reason = ""

    topic_scores = score_mistake_topics(mistakes)
    if topic_scores:
        best_slug = max(topic_scores, key=topic_scores.get)
        recommended_topic = get_topic_by_slug(best_slug)
        if recommended_topic:
            reason = (
                f"Based on your recent mistakes, focus on {recommended_topic.title} "
                f"({topic_scores[best_slug]} related error pattern"
                f"{'s' if topic_scores[best_slug] != 1 else ''} this week)."
            )

    if recommended_topic is None:
        recommended_topic = next_curriculum_topic(user)
        if recommended_topic:
            reason = (
                f"Continue your B1 grammar path with {recommended_topic.title} "
                "(next topic in the curriculum)."
            )

    if recommended_topic is None:
        return {
            "recommended_topic": None,
            "reason": "No lesson topics are available yet. Run seed_lesson_topics.",
            "yesterday_summary": yesterday_summary,
            "review_items": review_items,
            "starter_message": "",
        }

    starter_message = build_starter_message(
        recommended_topic,
        yesterday_summary,
        review_items,
    )

    return {
        "recommended_topic": topic_to_dict(recommended_topic),
        "reason": reason,
        "yesterday_summary": yesterday_summary,
        "review_items": review_items,
        "starter_message": starter_message,
    }
