"""Two-stage learning journey: B2/TOEFL 80+ then Academic/TOEFL 100+."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from tutor.models import (
    LearningGoal,
    LessonProgress,
    LessonTopic,
    Mistake,
    UserLearningJourney,
)
from tutor.utils.text_validation import is_meaningful_mistake

STAGE1_SLUG = "b2_toefl_80"
STAGE2_SLUG = "academic_toefl_100"

GRAMMAR_MISTAKE_CATEGORIES = {
    "article",
    "preposition",
    "tense",
    "subject_verb_agreement",
    "word_order",
    "fragment",
    "run_on_sentence",
    "collocation",
    "direct_translation",
    "sentence_structure",
}

STAGE1_MODULES = [
    {
        "id": "1a",
        "title": "Stage 1A: B1 Grammar Foundation — Tense Control",
        "start_order": 1,
        "end_order": 12,
    },
    {
        "id": "1b",
        "title": "Stage 1B: Core Grammar Accuracy",
        "start_order": 13,
        "end_order": 24,
    },
    {
        "id": "1c",
        "title": "Stage 1C: B2 Academic Sentence Control",
        "start_order": 25,
        "end_order": 32,
    },
    {
        "id": "1d",
        "title": "Stage 1D: TOEFL 80 Readiness",
        "start_order": 33,
        "end_order": 40,
    },
]

STAGE2_SLUG_OVERRIDES = {
    "TOEFL integrated writing": "toefl-integrated-writing-stage2",
}

STAGE1_SLUG_OVERRIDES = {
    "Articles: a/an/the": "articles-a-an-the",
    "Prepositions of time and place": "prepositions-of-time-and-place",
    "Modal verbs": "modal-verbs-should-must-have-to",
    "Conditionals type 0/1/2": "conditionals-type-0-1-2",
    "Used to / be used to / get used to": "used-to-be-used-to-get-used-to",
    "Passive voice": "passive-voice",
    "Relative clauses": "relative-clauses",
    "Gerunds and infinitives": "gerunds-and-infinitives",
    "Academic linking words": "academic-linking-words",
    "Common learner mistakes": "common-persian-speaker-grammar-mistakes",
    "Present simple vs present continuous": "present-simple-vs-present-continuous",
    "Past simple vs present perfect": "past-simple-vs-present-perfect",
}

STAGE1_CURRICULUM = [
    ("Present simple", "Habits, facts, and routines — the foundation for all other tenses."),
    ("Present continuous", "Actions happening now and temporary situations."),
    ("Present perfect", "Past events connected to now; life experience and recent results."),
    ("Present perfect continuous", "Duration and ongoing results up to the present."),
    ("Past simple", "Finished actions at a specific past time."),
    ("Past continuous", "Background actions and interrupted past events."),
    ("Past perfect", "Earlier past before another past action (sequence in narratives)."),
    ("Past perfect continuous", "Duration before a point in the past."),
    ("Future simple with will", "Predictions, promises, and spontaneous decisions."),
    ("Future with going to / planned future", "Plans, intentions, and evidence-based predictions."),
    ("Future continuous", "Actions in progress at a future time."),
    ("Future perfect and future perfect continuous", "Completion and duration before a future point."),
    ("Articles: a/an/the", "Indefinite and definite articles for academic English."),
    ("Countable and uncountable nouns", "Quantity, much/many, and article patterns with nouns."),
    ("Prepositions of time and place", "In, on, at and related prepositions."),
    ("Subject–verb agreement", "Singular/plural subjects with correct verb forms."),
    ("Modal verbs", "Should, must, have to, can, and may for obligation and possibility."),
    ("Used to / be used to / get used to", "Past habits vs familiarity."),
    ("Passive voice", "Academic passive structures for summaries and reports."),
    ("Conditionals type 0/1/2", "Real and unreal conditionals for hypotheses and argument."),
    ("Conditionals type 3 and mixed conditionals", "Past unreal conditions and mixed time references."),
    ("Gerunds and infinitives", "Verb patterns after common verbs and prepositions."),
    ("Relative clauses", "Defining and non-defining clauses."),
    ("Comparatives and superlatives", "Comparing ideas in essays and speaking."),
    ("Academic linking words", "However, therefore, moreover, and other connectors."),
    ("Academic sentence structure", "Complex sentences and subordination for clarity."),
    ("Complex sentences", "Combining ideas with subordinate clauses accurately."),
    ("Common learner mistakes", "Article, preposition, tense, and word-order patterns."),
    ("Paragraph organization", "Topic sentences, support, and conclusion for B2 writing."),
    ("Paraphrasing and summarizing", "Restating ideas without copying — key for TOEFL tasks."),
    ("Opinion and argument structure", "Clear thesis, reasons, and examples in timed responses."),
    ("Cause/effect and contrast language", "Because, therefore, whereas, and despite for academic flow."),
    ("TOEFL reading question types", "Main idea, detail, inference, and vocabulary in context."),
    ("TOEFL listening question types", "Lecture and conversation question strategies."),
    ("TOEFL speaking structure", "Independent and integrated response organization."),
    ("TOEFL independent speaking", "Personal preference and choice tasks with clear structure."),
    ("TOEFL integrated speaking", "Campus and academic integrated speaking patterns."),
    ("TOEFL writing structure", "Integrated and academic discussion essay structure."),
    ("TOEFL integrated writing", "Reading-listening-writing synthesis under time pressure."),
    (
        "Integrated B2 / TOEFL 80 readiness practice",
        "Mixed skills practice toward B2 academic English and TOEFL 80+.",
    ),
]

STAGE2_CURRICULUM = [
    ("Advanced academic vocabulary and collocations", "High-level word choice and natural combinations."),
    ("Complex sentence control", "Advanced clauses without losing clarity."),
    ("Advanced cohesion and argument structure", "Thesis, counterargument, and synthesis."),
    ("Dense academic reading", "Long passages with academic register."),
    ("Reading inference and rhetorical purpose", "Author purpose, tone, and implied meaning."),
    ("Lecture listening and note-taking", "Campus lecture comprehension strategies."),
    ("Listening inference and speaker attitude", "Attitude, function, and organization cues."),
    ("TOEFL Speaking Q1 mastery", "Personal preference / choice tasks at high score."),
    ("TOEFL Speaking Q2/Q3/Q4 integrated responses", "Campus and academic integrated speaking."),
    ("TOEFL integrated writing", "Reading-listening-writing synthesis."),
    ("TOEFL academic discussion writing", "Contribute clearly to an academic discussion."),
    ("High-scoring essay development", "Depth, precision, and timed development."),
    ("Discipline-specific academic English", "Field-style vocabulary and structure."),
    ("Timed section practice", "Section timing and stamina."),
    ("Full mock test cycle", "Full-length timed practice and review."),
    ("TOEFL 100+ readiness review", "Final review toward advanced academic readiness."),
]

STAGE1_CATEGORIES = (
    ["grammar"] * 12
    + ["grammar"] * 12
    + ["writing"] * 6
    + ["grammar", "writing"]
    + ["reading", "listening", "speaking", "speaking", "speaking", "writing", "writing", "mixed"]
)

STAGE1_LEVELS = ["B1"] * 24 + ["B2"] * 16

STAGE2_CATEGORIES = [
    "vocabulary", "writing", "writing", "reading", "reading", "listening", "listening",
    "speaking", "speaking", "writing", "writing", "writing", "vocabulary", "mixed",
    "mixed", "mixed",
]

STAGE2_LEVELS = ["B2"] * 8 + ["C1"] * 8

STAGE1_PLAN_MINUTES = {
    "grammar": 18,
    "reading": 15,
    "writing": 15,
    "listening": 12,
    "speaking": 12,
    "shadowing": 8,
}

STAGE2_PLAN_MINUTES = {
    "grammar": 10,
    "reading": 18,
    "writing": 20,
    "listening": 18,
    "speaking": 18,
    "shadowing": 10,
}

STAGE1_TRACK_REASONS = {
    "grammar": "Stage 1 prioritizes B1/B2 grammar accuracy for TOEFL 80+ readiness.",
    "reading": "Reading basics and TOEFL question types build comprehension for Stage 1.",
    "writing": "Paragraph writing practice supports B2 academic structure.",
    "listening": "Listening basics prepare you for lecture-style TOEFL tasks.",
    "speaking": "Speaking structure practice helps you answer clearly under time pressure.",
    "shadowing": "Shadowing supports pronunciation rhythm while you build fluency.",
}

STAGE2_TRACK_REASONS = {
    "grammar": "Stage 2 keeps grammar sharp while you focus on advanced tasks.",
    "reading": "Long academic reading is essential for TOEFL 100+ preparation.",
    "writing": "Integrated and discussion writing need timed high-score refinement.",
    "listening": "Lecture listening and note-taking target advanced TOEFL skills.",
    "speaking": "Integrated speaking responses need fluent, structured answers.",
    "shadowing": "Shadowing keeps delivery natural during advanced speaking work.",
}


@dataclass
class ReadinessCriterion:
    key: str
    label: str
    score: int
    ready: bool
    detail: str


def _slugify_title(title: str, *, stage_slug: str = STAGE1_SLUG) -> str:
    from django.utils.text import slugify

    if stage_slug == STAGE2_SLUG:
        return STAGE2_SLUG_OVERRIDES.get(title, slugify(title))
    return STAGE1_SLUG_OVERRIDES.get(title, slugify(title))


def goal_to_dict(goal: LearningGoal) -> dict:
    return {
        "slug": goal.slug,
        "name": goal.name,
        "description": goal.description,
        "entry_level": goal.entry_level,
        "target_level": goal.target_level,
        "target_toefl_score": goal.target_toefl_score,
        "order": goal.order,
        "stage_number": goal.stage_number,
        "is_default": goal.is_default,
        "unlocks_after": goal.unlocks_after.slug if goal.unlocks_after_id else None,
    }


def get_or_create_journey(user) -> UserLearningJourney:
    try:
        return user.learning_journey
    except UserLearningJourney.DoesNotExist:
        pass

    default_goal = LearningGoal.objects.filter(is_default=True).first()
    if default_goal is None:
        default_goal = LearningGoal.objects.order_by("order").first()
    if default_goal is None:
        raise LearningGoal.DoesNotExist("No learning goals seeded.")

    # get_or_create (not create) avoids a race when concurrent requests for a
    # brand-new user's first page load all try to create the journey at once.
    journey, _ = UserLearningJourney.objects.get_or_create(
        user=user,
        defaults={"current_goal": default_goal, "stage2_unlocked": False},
    )
    return journey


def is_stage2_unlocked(user) -> bool:
    journey = get_or_create_journey(user)
    return journey.stage2_unlocked


def stage_topics(stage_slug: str):
    return LessonTopic.objects.filter(is_active=True, stage_slug=stage_slug).order_by("order", "id")


def lessons_mastered_count(user, stage_slug: str) -> int:
    return LessonProgress.objects.filter(
        user=user,
        topic__stage_slug=stage_slug,
        topic__is_active=True,
        status=LessonProgress.STATUS_COMPLETED,
    ).count()


def lessons_total_count(stage_slug: str) -> int:
    return stage_topics(stage_slug).count()


def goal_progress_percent(user, stage_slug: str) -> int:
    total = lessons_total_count(stage_slug)
    if total == 0:
        return 0
    mastered = lessons_mastered_count(user, stage_slug)
    return round(100 * mastered / total)


def next_lesson_for_stage(user, stage_slug: str) -> LessonTopic | None:
    topics = list(stage_topics(stage_slug))
    if not topics:
        return None
    progress_by_topic = {
        row.topic_id: row
        for row in LessonProgress.objects.filter(user=user, topic__in=topics)
    }
    for topic in topics:
        progress = progress_by_topic.get(topic.id)
        if progress and progress.status == LessonProgress.STATUS_NEEDS_REVIEW:
            return topic
    for topic in topics:
        progress = progress_by_topic.get(topic.id)
        if progress is None or progress.status in {
            LessonProgress.STATUS_NOT_STARTED,
            LessonProgress.STATUS_STARTED,
        }:
            return topic
    return topics[-1]


def recent_grammar_mistake_count(user, days: int = 7) -> int:
    since = timezone.now() - timedelta(days=days)
    count = 0
    for mistake in Mistake.objects.filter(user=user, created_at__gte=since).iterator():
        if not is_meaningful_mistake(mistake.wrong_text, mistake.correct_text):
            continue
        category = mistake.category or "other"
        if category in GRAMMAR_MISTAKE_CATEGORIES or mistake.track == "grammar_coach":
            count += 1
    return count


def _placeholder_skill_score(user, skill: str, stage_slug: str) -> int:
    """Skill score proxy; uses persisted reading session scores when available."""
    if skill == "reading":
        from tutor.reading_practice import reading_score_for_user

        stored = reading_score_for_user(user, stage_slug)
        if stored:
            return stored

    progress = goal_progress_percent(user, stage_slug)
    base = 45 + progress // 2
    offsets = {
        "vocabulary": 5,
        "reading": 3,
        "listening": 0,
        "speaking": -2,
        "writing": 2,
    }
    return min(95, max(40, base + offsets.get(skill, 0)))


def _stage1_readiness_criteria(user) -> list[ReadinessCriterion]:
    stage_slug = STAGE1_SLUG
    total = lessons_total_count(stage_slug)
    mastered = lessons_mastered_count(user, stage_slug)
    mastery_ratio = mastered / total if total else 0
    grammar_mistakes = recent_grammar_mistake_count(user)

    grammar_score = max(0, 100 - grammar_mistakes * 8)
    vocab_score = _placeholder_skill_score(user, "vocabulary", stage_slug)
    reading_score = _placeholder_skill_score(user, "reading", stage_slug)
    listening_score = _placeholder_skill_score(user, "listening", stage_slug)
    speaking_score = _placeholder_skill_score(user, "speaking", stage_slug)
    writing_score = _placeholder_skill_score(user, "writing", stage_slug)

    # TODO: Replace TOEFL estimate with aggregated AI scoring from writing/speaking feedback.
    estimated_toefl = min(
        95,
        round(
            55
            + mastery_ratio * 20
            + (grammar_score + reading_score + listening_score + speaking_score + writing_score) / 25
        ),
    )

    lessons_ready = mastery_ratio >= 0.75
    grammar_ready = grammar_mistakes <= 5 and grammar_score >= 60
    reading_ready = reading_score >= 70
    listening_ready = listening_score >= 70
    writing_ready = writing_score >= 70
    speaking_ready = speaking_score >= 70
    toefl_ready = estimated_toefl >= 80

    return [
        ReadinessCriterion(
            "grammar_control",
            "Grammar control",
            grammar_score,
            grammar_ready,
            f"{grammar_mistakes} grammar mistakes in the last 7 days.",
        ),
        ReadinessCriterion(
            "vocabulary_readiness",
            "Vocabulary readiness",
            vocab_score,
            vocab_score >= 70,
            "Academic vocabulary progress for Stage 1.",
        ),
        ReadinessCriterion(
            "reading_readiness",
            "Reading readiness",
            reading_score,
            reading_ready,
            "Reading quiz / comprehension readiness (placeholder estimate).",
        ),
        ReadinessCriterion(
            "listening_readiness",
            "Listening readiness",
            listening_score,
            listening_ready,
            "Listening quiz readiness (placeholder estimate).",
        ),
        ReadinessCriterion(
            "speaking_readiness",
            "Speaking readiness",
            speaking_score,
            speaking_ready,
            "Speaking score estimate (placeholder until audio scoring history exists).",
        ),
        ReadinessCriterion(
            "writing_readiness",
            "Writing readiness",
            writing_score,
            writing_ready,
            "Writing score estimate (placeholder until essay scoring history exists).",
        ),
        ReadinessCriterion(
            "lessons_mastered",
            "Stage 1 lessons mastered",
            round(mastery_ratio * 100),
            lessons_ready,
            f"{mastered}/{total} Stage 1 lessons completed.",
        ),
        ReadinessCriterion(
            "estimated_toefl_score",
            "Estimated TOEFL score",
            estimated_toefl,
            toefl_ready,
            "Practice estimate toward TOEFL 80+ (not an official ETS score).",
        ),
    ]


def _stage2_readiness_criteria(user) -> list[ReadinessCriterion]:
    stage_slug = STAGE2_SLUG
    total = lessons_total_count(stage_slug)
    mastered = lessons_mastered_count(user, stage_slug)
    mastery_ratio = mastered / total if total else 0
    progress = goal_progress_percent(user, stage_slug)

    # TODO: Replace with mock-test and advanced AI scoring when available.
    estimated_toefl = min(110, 85 + progress // 3)
    writing_score = _placeholder_skill_score(user, "writing", stage_slug) + 5
    speaking_score = _placeholder_skill_score(user, "speaking", stage_slug) + 5
    vocab_score = _placeholder_skill_score(user, "vocabulary", stage_slug) + 8
    mock_score = min(100, 60 + progress // 2)

    return [
        ReadinessCriterion(
            "toefl_100_readiness",
            "TOEFL 100+ readiness",
            estimated_toefl,
            estimated_toefl >= 100,
            "Advanced practice estimate toward TOEFL 100+.",
        ),
        ReadinessCriterion(
            "academic_writing_strength",
            "Academic writing strength",
            writing_score,
            writing_score >= 80,
            "Integrated and discussion writing refinement.",
        ),
        ReadinessCriterion(
            "speaking_fluency",
            "Speaking fluency",
            speaking_score,
            speaking_score >= 80,
            "Integrated speaking fluency and structure.",
        ),
        ReadinessCriterion(
            "advanced_vocabulary",
            "Advanced vocabulary",
            vocab_score,
            vocab_score >= 80,
            "Advanced academic vocabulary and collocations.",
        ),
        ReadinessCriterion(
            "mock_test_performance",
            "Mock test performance",
            mock_score,
            mock_score >= 85,
            "Full mock test cycle performance (placeholder).",
        ),
        ReadinessCriterion(
            "stage2_lessons_mastered",
            "Stage 2 lessons mastered",
            round(mastery_ratio * 100),
            mastery_ratio >= 0.8,
            f"{mastered}/{total} Stage 2 lessons completed.",
        ),
    ]


def evaluate_stage1_ready(user) -> bool:
    criteria = _stage1_readiness_criteria(user)
    required_keys = {
        "lessons_mastered",
        "grammar_control",
        "reading_readiness",
        "listening_readiness",
        "writing_readiness",
        "speaking_readiness",
        "estimated_toefl_score",
    }
    return all(
        criterion.ready
        for criterion in criteria
        if criterion.key in required_keys
    )


def maybe_unlock_stage2(user) -> UserLearningJourney:
    journey = get_or_create_journey(user)
    if journey.stage2_unlocked:
        return journey
    if evaluate_stage1_ready(user):
        journey.stage2_unlocked = True
        journey.stage1_completed_at = timezone.now()
        journey.save(update_fields=["stage2_unlocked", "stage1_completed_at", "updated_at"])
    return journey


def skills_needing_review(user, stage_slug: str) -> list[str]:
    criteria = (
        _stage1_readiness_criteria(user)
        if stage_slug == STAGE1_SLUG
        else _stage2_readiness_criteria(user)
    )
    review = []
    mapping = {
        "grammar_control": "Grammar",
        "vocabulary_readiness": "Vocabulary",
        "advanced_vocabulary": "Vocabulary",
        "reading_readiness": "Reading",
        "listening_readiness": "Listening",
        "speaking_readiness": "Speaking",
        "speaking_fluency": "Speaking",
        "writing_readiness": "Writing",
        "academic_writing_strength": "Writing",
    }
    for criterion in criteria:
        if not criterion.ready and criterion.key in mapping:
            label = mapping[criterion.key]
            if label not in review:
                review.append(label)
    return review[:4]


def build_readiness_report(user) -> dict:
    journey = maybe_unlock_stage2(user)
    goal = journey.current_goal
    stage_slug = goal.slug
    criteria = (
        _stage1_readiness_criteria(user)
        if stage_slug == STAGE1_SLUG
        else _stage2_readiness_criteria(user)
    )
    ready_for_stage2 = journey.stage2_unlocked or evaluate_stage1_ready(user)
    if stage_slug == STAGE1_SLUG:
        recommendation = "unlock_stage_2" if ready_for_stage2 else "continue_stage_1"
    else:
        recommendation = "continue_stage_2"

    return {
        "current_goal": goal_to_dict(goal),
        "stage2_unlocked": journey.stage2_unlocked,
        "stage2_locked": not journey.stage2_unlocked and stage_slug == STAGE1_SLUG,
        "progress_percent": goal_progress_percent(user, stage_slug),
        "lessons_mastered": lessons_mastered_count(user, stage_slug),
        "lessons_total": lessons_total_count(stage_slug),
        "next_lesson": _topic_summary(next_lesson_for_stage(user, stage_slug)),
        "skills_needing_review": skills_needing_review(user, stage_slug),
        "criteria": [
            {
                "key": item.key,
                "label": item.label,
                "score": item.score,
                "ready": item.ready,
                "detail": item.detail,
            }
            for item in criteria
        ],
        "estimated_toefl_score": next(
            (item.score for item in criteria if "toefl" in item.key),
            goal.target_toefl_score,
        ),
        "ready_for_stage2": ready_for_stage2,
        "recommendation": recommendation,
    }


def build_journey_summary(user) -> dict:
    journey = get_or_create_journey(user)
    goal = journey.current_goal
    stage2_goal = LearningGoal.objects.filter(slug=STAGE2_SLUG).first()
    next_lesson = next_lesson_for_stage(user, goal.slug)

    return {
        "current_stage": goal.stage_number,
        "current_goal": goal_to_dict(goal),
        "stage2_goal": goal_to_dict(stage2_goal) if stage2_goal else None,
        "stage2_unlocked": journey.stage2_unlocked,
        "stage2_locked_label": (
            "Locked until TOEFL 80+ readiness"
            if not journey.stage2_unlocked
            else "Unlocked"
        ),
        "progress_percent": goal_progress_percent(user, goal.slug),
        "target_toefl_score": goal.target_toefl_score,
        "next_lesson": _topic_summary(next_lesson),
        "lessons_mastered": lessons_mastered_count(user, goal.slug),
        "lessons_total": lessons_total_count(goal.slug),
        "skills_needing_review": skills_needing_review(user, goal.slug),
    }


def _topic_summary(topic: LessonTopic | None) -> dict | None:
    if topic is None:
        return None
    return {
        "id": topic.id,
        "title": topic.title,
        "slug": topic.slug,
        "stage_slug": topic.stage_slug,
        "level": topic.level,
        "category": topic.category,
    }


def plan_minutes_for_user(user) -> dict[str, int]:
    journey = get_or_create_journey(user)
    if journey.current_goal.slug == STAGE2_SLUG:
        return dict(STAGE2_PLAN_MINUTES)
    return dict(STAGE1_PLAN_MINUTES)


def plan_track_reason(user, track: str) -> str | None:
    journey = get_or_create_journey(user)
    reasons = (
        STAGE2_TRACK_REASONS
        if journey.current_goal.slug == STAGE2_SLUG
        else STAGE1_TRACK_REASONS
    )
    return reasons.get(track)


def topic_is_locked(user, topic: LessonTopic) -> bool:
    if topic.stage_slug != STAGE2_SLUG:
        return False
    journey = get_or_create_journey(user)
    return not journey.stage2_unlocked


def ensure_user_on_accessible_goal(user) -> UserLearningJourney:
    journey = get_or_create_journey(user)
    if journey.current_goal.slug == STAGE2_SLUG and not journey.stage2_unlocked:
        stage1 = LearningGoal.objects.filter(slug=STAGE1_SLUG).first()
        if stage1:
            journey.current_goal = stage1
            journey.save(update_fields=["current_goal", "updated_at"])
    return journey
