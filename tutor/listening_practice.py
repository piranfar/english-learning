"""Original listening practice generation, scoring, and plan integration."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date

from django.utils import timezone

from tutor.ai.provider_resolution import (
    build_provider_attempt_order,
    is_ai_provider_configured,
    is_provider_error,
)
from tutor.learning_journey import STAGE1_SLUG, STAGE2_SLUG
from tutor.models import ListeningQuestionAttempt, ListeningSession
from tutor.reading_practice import gather_reading_context
from tutor.services import generate_from_template, get_prompt_template, save_mistakes

LEARNER_FALLBACK_MESSAGE = "Using local AI or sample practice."
FALLBACK_PROVIDER_METADATA = {
    "provider": "fallback",
    "model": "built-in",
    "used_fallback": True,
}

LISTENING_PRACTICE_PATTERN = re.compile(
    r"---LISTENING_PRACTICE---\s*(\{.*?\})\s*---END_LISTENING_PRACTICE---",
    re.DOTALL,
)

LISTENING_LEVELS = ("A2", "B1", "B2", "C1 Academic")
LISTENING_STAGES = (STAGE1_SLUG, STAGE2_SLUG)
LISTENING_TYPES = (
    "academic_mini_lecture",
    "campus_conversation",
    "daily_academic_life",
    "toefl_style_lecture",
    "toefl_style_conversation",
)
LISTENING_TOPICS = (
    "Science",
    "Health",
    "University Life",
    "Technology",
    "Society",
    "Academic Skills",
    "Random",
)
LESSON_FOCUS_CHOICES = (
    "current_lesson",
    "articles",
    "prepositions",
    "passive_voice",
    "present_perfect",
    "academic_linking_words",
    "academic_vocabulary",
    "none",
)
LENGTH_CHOICES = ("short", "medium", "toefl_style")
SPEED_CHOICES = ("slow", "normal", "toefl_like")

LISTENING_TYPE_LABELS = {
    "academic_mini_lecture": "Academic mini-lecture",
    "campus_conversation": "Campus conversation",
    "daily_academic_life": "Daily academic life",
    "toefl_style_lecture": "TOEFL-style lecture",
    "toefl_style_conversation": "TOEFL-style conversation",
}

LESSON_FOCUS_LABELS = {
    "current_lesson": "Current lesson",
    "articles": "Articles",
    "prepositions": "Prepositions",
    "passive_voice": "Passive voice",
    "present_perfect": "Present perfect",
    "academic_linking_words": "Academic linking words",
    "academic_vocabulary": "Academic vocabulary",
    "none": "No specific focus",
}

LESSON_FOCUS_TO_MISTAKE_CATEGORY = {
    "articles": "article",
    "prepositions": "preposition",
    "passive_voice": "tense",
    "present_perfect": "tense",
    "academic_linking_words": "sentence_structure",
    "academic_vocabulary": "vocabulary_precision",
}

SPEED_RATE_HINTS = {
    "slow": "Write shorter, simpler sentences with clear pauses (commas) so it can be read slowly and clearly.",
    "normal": "Use natural conversational/lecture pacing and sentence length.",
    "toefl_like": "Use natural, somewhat fast academic pacing similar to a real TOEFL lecture or conversation.",
}

# Stage 1: B2 / TOEFL 80+ — 150-350 words, 4-6 questions.
# Stage 2: Academic / TOEFL 100+ — 450-800 words, 6-10 questions.
STAGE_TRANSCRIPT_SETTINGS = {
    STAGE1_SLUG: {
        "word_min": 150,
        "word_max": 350,
        "question_min": 4,
        "question_max": 6,
        "cefr": "B1/B2",
        "description": (
            "Stage 1: B2 Academic English / TOEFL 80+ readiness. Clear structure, moderate speed, "
            "focus on main idea, detail, vocabulary in context, and basic inference."
        ),
    },
    STAGE2_SLUG: {
        "word_min": 450,
        "word_max": 800,
        "question_min": 6,
        "question_max": 10,
        "cefr": "B2/C1",
        "description": (
            "Stage 2: Full Academic English / TOEFL 100+ readiness. Denser academic language, more "
            "natural lecture/conversation flow, include inference, speaker purpose, attitude, and "
            "organization questions."
        ),
    },
}

LENGTH_OVERRIDES = {
    "short": {"word_min": 150, "word_max": 250, "question_min": 4, "question_max": 4},
    "medium": None,
    "toefl_style": None,
}


def resolve_listening_settings(stage: str, length: str) -> dict:
    base = dict(STAGE_TRANSCRIPT_SETTINGS.get(stage, STAGE_TRANSCRIPT_SETTINGS[STAGE1_SLUG]))
    override = LENGTH_OVERRIDES.get(length)
    if override:
        base.update(override)
    if stage == STAGE2_SLUG and length == "toefl_style":
        base["word_min"] = 600
        base["word_max"] = 800
        base["question_min"] = 8
        base["question_max"] = 10
    return base


def gather_listening_context(user) -> dict:
    """Stage/lesson/mistake/vocabulary context — shared with Reading Coach."""
    return gather_reading_context(user)


def resolve_lesson_focus(lesson_focus: str, context: dict) -> str:
    if lesson_focus != "current_lesson":
        return lesson_focus

    slug = context.get("current_lesson_slug") or ""
    slug_map = {
        "articles-a-an-the": "articles",
        "prepositions-of-time-and-place": "prepositions",
        "passive-voice": "passive_voice",
        "present-perfect": "present_perfect",
        "present-perfect-continuous": "present_perfect",
        "past-simple": "past_tense",
        "past-perfect": "past_tense",
        "past-simple-vs-present-perfect": "present_perfect",
        "academic-linking-words": "academic_linking_words",
    }
    for key, value in slug_map.items():
        if key in slug:
            return value
    if "vocabulary" in slug:
        return "academic_vocabulary"
    return "none"


def build_listening_generate_user_message(
    *,
    level: str,
    stage: str,
    listening_type: str,
    topic: str,
    lesson_focus: str,
    length: str,
    speed: str,
    context: dict,
) -> str:
    from tutor.prompts.listening_coach import (
        LISTENING_LESSON_FOCUS_INSTRUCTIONS,
        LISTENING_TOPIC_INSTRUCTIONS,
        LISTENING_TYPE_INSTRUCTIONS,
    )

    resolved_focus = resolve_lesson_focus(lesson_focus, context)
    settings = resolve_listening_settings(stage, length)
    topic_key = topic if topic in LISTENING_TOPIC_INSTRUCTIONS else "Random"
    type_instruction = LISTENING_TYPE_INSTRUCTIONS.get(
        listening_type, LISTENING_TYPE_INSTRUCTIONS["academic_mini_lecture"]
    )
    focus_instruction = LISTENING_LESSON_FOCUS_INSTRUCTIONS.get(
        resolved_focus, LISTENING_LESSON_FOCUS_INSTRUCTIONS["none"]
    )
    speed_instruction = SPEED_RATE_HINTS.get(speed, SPEED_RATE_HINTS["normal"])

    recent_categories = context.get("recent_mistake_categories") or {}
    top_categories = sorted(recent_categories, key=recent_categories.get, reverse=True)[:3]
    due_vocab = context.get("due_vocabulary") or []

    lines = [
        f"Student level: {level}",
        f"Learning stage: {stage} ({context.get('goal_name', '')})",
        f"Listening type: {listening_type}",
        type_instruction,
        f"Topic: {topic_key}",
        LISTENING_TOPIC_INSTRUCTIONS[topic_key],
        f"Lesson focus: {resolved_focus}",
        focus_instruction,
        f"Speed: {speed}",
        speed_instruction,
        f"Transcript length: {settings['word_min']}-{settings['word_max']} words",
        f"Number of questions: {settings['question_min']}-{settings['question_max']}",
        f"Target CEFR difficulty: {settings['cefr']}",
        settings["description"],
    ]

    if context.get("current_lesson_title"):
        lines.append(f"Current lesson: {context['current_lesson_title']}")
    if top_categories:
        lines.append(f"Recent mistake categories to connect with: {', '.join(top_categories)}")
    if due_vocab:
        lines.append(
            "Due vocabulary to weave in naturally when possible: " + ", ".join(due_vocab[:6])
        )

    return "\n".join(lines)


def _normalize_question(entry: dict, index: int) -> dict | None:
    question_text = (entry.get("question") or "").strip()
    choices = [
        str(choice).strip()
        for choice in entry.get("choices", entry.get("options", []))
        if str(choice).strip()
    ]
    if not question_text or len(choices) != 4:
        return None

    correct_answer = (entry.get("correct_answer") or "").strip()
    correct_index = entry.get("correct_index")
    if correct_answer:
        try:
            correct_index = choices.index(correct_answer)
        except ValueError:
            correct_index = None
    else:
        try:
            correct_index = int(correct_index)
        except (TypeError, ValueError):
            correct_index = None
        if correct_index in range(4):
            correct_answer = choices[correct_index]
        else:
            return None

    question_type = (entry.get("type") or entry.get("focus") or "detail").strip()
    mistake_category = (entry.get("mistake_category") or "listening_comprehension").strip()

    return {
        "id": (entry.get("id") or f"q{index}").strip(),
        "type": question_type,
        "question": question_text,
        "choices": choices,
        "correct_answer": correct_answer,
        "correct_index": correct_index,
        "explanation": (entry.get("explanation") or "").strip(),
        "mistake_category": mistake_category,
    }


SHADOWING_BOILERPLATE_PATTERN = re.compile(
    r"\n\s*shadowing sentences\s*:?\s*\n", re.IGNORECASE
)


def _clean_transcript(transcript: str) -> str:
    """Drop any trailing "Shadowing sentences:" section the model sometimes
    appends inside the transcript string itself instead of using the
    dedicated shadowing_sentences field."""
    match = SHADOWING_BOILERPLATE_PATTERN.search(transcript)
    if match:
        transcript = transcript[: match.start()]
    return transcript.strip()


def parse_listening_practice(raw_reply: str) -> dict:
    match = LISTENING_PRACTICE_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse listening practice from AI response")

    try:
        # strict=False tolerates literal newlines inside JSON string values —
        # small local models frequently emit real line breaks in multi-paragraph
        # transcripts instead of escaping them as \n.
        data = json.loads(match.group(1), strict=False)
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse listening practice JSON") from exc

    transcript = _clean_transcript((data.get("transcript") or "").strip())
    if len(transcript.split()) < 60:
        raise ValueError("Generated transcript is too short")

    questions = []
    for index, entry in enumerate(data.get("questions", []), start=1):
        normalized = _normalize_question(entry, index)
        if normalized:
            questions.append(normalized)

    if len(questions) < 4:
        raise ValueError("Listening practice must include at least 4 valid questions")

    target_vocabulary = []
    for entry in data.get("target_vocabulary", []):
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        target_vocabulary.append(
            {
                "word": word,
                "definition": (entry.get("definition") or "").strip(),
                "example": (entry.get("example") or "").strip(),
            }
        )

    shadowing_sentences = [
        str(sentence).strip()
        for sentence in data.get("shadowing_sentences", [])
        if str(sentence).strip()
    ]

    try:
        estimated_duration_seconds = int(data.get("estimated_duration_seconds") or 0)
    except (TypeError, ValueError):
        estimated_duration_seconds = 0
    if estimated_duration_seconds <= 0:
        # Fall back to a ~140 words-per-minute spoken estimate.
        estimated_duration_seconds = max(30, round(len(transcript.split()) / 140 * 60))

    return {
        "title": (data.get("title") or "Listening practice").strip(),
        "level": (data.get("level") or "B1").strip(),
        "stage": (data.get("stage") or STAGE1_SLUG).strip(),
        "listening_type": (data.get("listening_type") or "academic_mini_lecture").strip(),
        "topic": (data.get("topic") or "Random").strip(),
        "lesson_focus": (data.get("lesson_focus") or "none").strip(),
        "transcript": transcript,
        "estimated_duration_seconds": estimated_duration_seconds,
        "target_vocabulary": target_vocabulary,
        "questions": questions,
        "shadowing_sentences": shadowing_sentences,
    }


FALLBACK_STAGE1_TRANSCRIPT = (
    "Professor: Today we're going to talk about how universities support open access research. "
    "A recent study found that open libraries help learners read more academic articles. "
    "However, many students still struggle with article use when they write in English. "
    "The researchers interviewed two hundred undergraduates and reviewed their writing samples. "
    "Although the students understood the main ideas, they often chose the wrong article before a noun. "
    "For example, some wrote 'the university' when they meant any university in general. "
    "Others omitted articles entirely in front of countable singular nouns. "
    "Therefore, instructors now recommend short daily reading and listening tasks with focused feedback. "
    "In contrast, students who practiced article patterns improved faster on timed tests. "
    "The study was published by a team at a public university in 2024. "
    "These findings suggest that targeted practice can support academic success for many learners. "
    "Next week we will compare article rules in spoken lectures versus written essays. "
)

FALLBACK_STAGE2_TRANSCRIPT = (
    "Professor: Good morning. In today's lecture we'll examine how cities are redesigning green "
    "infrastructure to support biodiversity while meeting the energy demands of growing populations. "
    "Urban ecologists have long argued that parks alone cannot sustain diverse species in dense "
    "metropolitan areas. Instead, recent fieldwork suggests that connected corridors — rooftop gardens, "
    "restored riverbanks, and shaded pedestrian paths — allow birds and pollinators to move safely "
    "between habitats. A longitudinal study conducted across twelve North American cities tracked "
    "native bee populations for nearly a decade. Researchers found that neighborhoods with continuous "
    "tree cover experienced measurably higher pollination rates in community gardens. "
    "However, the same study noted a troubling trade-off. When municipalities installed large solar "
    "arrays on former brownfields, ground-nesting birds often abandoned those sites within two seasons. "
    "The lead author emphasized that sustainability planning must therefore balance renewable energy "
    "targets with habitat preservation rather than treating them as separate policy goals. "
    "Students sometimes assume that any green project automatically benefits wildlife, but the evidence "
    "shows that design details — plant species selection, height of structures, and maintenance schedules — "
    "determine whether a project helps or harms local ecosystems. "
    "Another team analyzed stormwater systems that combine permeable pavement with native wetland plants. "
    "These hybrid systems reduced flooding during heavy rainfall while filtering pollutants that would "
    "otherwise reach rivers. City planners in the study reported lower long-term maintenance costs compared "
    "with conventional concrete channels, although upfront investment remained a political challenge. "
    "From an academic skills perspective, notice how the researchers qualify their claims. "
    "They rarely say a strategy always works; they report probabilities, sample sizes, and limitations. "
    "That cautious tone is typical of environmental science lectures you will hear on standardized tests. "
    "Before we open discussion, I want to highlight one more finding. Citizen-science volunteers who "
    "recorded weekly species counts improved the model's accuracy more than satellite imagery alone. "
    "The professor concluded that public engagement is not merely outreach but a methodological asset. "
    "Next class we will compare these urban findings with rural reforestation programs in South America. "
    "Please review the assigned article on green roofs and prepare one question about speaker attitude "
    "or organizational structure, since those question types appear frequently at advanced levels. "
    "Remember to distinguish main ideas from supporting examples while you listen, and note any contrast "
    "markers such as however, in contrast, and instead, because exam questions often target those shifts. "
    "Finally, bring an example from your own city that could be evaluated using the framework we discussed "
    "today. That will prepare you for the short writing follow-up in our next seminar session. "
    "As you review, pay attention to how the speaker signals transitions between examples and broader "
    "conclusions, because advanced listening items frequently ask you to identify why a detail was mentioned. "
)


def _fallback_questions_stage1(lesson_focus: str) -> list[dict]:
    mistake = LESSON_FOCUS_TO_MISTAKE_CATEGORY.get(lesson_focus, "listening_comprehension")
    article_category = "article" if lesson_focus == "articles" else mistake
    return [
        {
            "id": "q1",
            "type": "main_idea",
            "question": "What is the main idea of the lecture?",
            "choices": [
                "Open libraries reduce tuition costs",
                "Targeted article practice supports academic writing",
                "All universities must publish open research",
                "Undergraduates prefer listening to reading",
            ],
            "correct_answer": "Targeted article practice supports academic writing",
            "correct_index": 1,
            "explanation": "The lecture focuses on article errors and how practice helps learners.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q2",
            "type": "detail",
            "question": "How many undergraduates did the researchers interview?",
            "choices": ["One hundred", "Two hundred", "Three hundred", "Four hundred"],
            "correct_answer": "Two hundred",
            "correct_index": 1,
            "explanation": "The lecture states that two hundred undergraduates were interviewed.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q3",
            "type": "vocabulary_in_context",
            "question": "In the lecture, what problem did many students have with articles?",
            "choices": [
                "They used too many articles",
                "They chose the wrong article or omitted it",
                "They confused articles with prepositions",
                "They only made mistakes with plural nouns",
            ],
            "correct_answer": "They chose the wrong article or omitted it",
            "correct_index": 1,
            "explanation": "Students chose the wrong article or omitted articles before countable nouns.",
            "mistake_category": article_category,
        },
        {
            "id": "q4",
            "type": "inference",
            "question": "What can be inferred about students who practiced article patterns?",
            "choices": [
                "They stopped reading academic articles",
                "They improved faster on timed tests",
                "They preferred spoken lectures only",
                "They avoided writing assignments",
            ],
            "correct_answer": "They improved faster on timed tests",
            "correct_index": 1,
            "explanation": "The professor contrasts those students with others who did not practice patterns.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q5",
            "type": "detail",
            "question": "When was the study published?",
            "choices": ["2022", "2023", "2024", "2025"],
            "correct_answer": "2024",
            "correct_index": 2,
            "explanation": "The lecture says the study was published in 2024.",
            "mistake_category": "listening_comprehension",
        },
    ]


def _fallback_questions_stage2() -> list[dict]:
    return [
        {
            "id": "q1",
            "type": "main_idea",
            "question": "What is the primary focus of the lecture?",
            "choices": [
                "How cities balance green infrastructure with other urban needs",
                "Why solar power is cheaper than wind power",
                "The history of community gardening in Europe",
                "How to volunteer for citizen-science programs",
            ],
            "correct_answer": "How cities balance green infrastructure with other urban needs",
            "correct_index": 0,
            "explanation": "The lecture discusses biodiversity, energy, and urban planning trade-offs.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q2",
            "type": "detail",
            "question": "What did the bee study find about continuous tree cover?",
            "choices": [
                "It reduced community garden size",
                "It increased pollination rates",
                "It eliminated native species",
                "It lowered property values",
            ],
            "correct_answer": "It increased pollination rates",
            "correct_index": 1,
            "explanation": "Neighborhoods with continuous tree cover had higher pollination rates.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q3",
            "type": "inference",
            "question": "What can be inferred about large solar arrays on brownfields?",
            "choices": [
                "They always increase bird populations",
                "They may cause ground-nesting birds to leave",
                "They are banned in North American cities",
                "They require no maintenance",
            ],
            "correct_answer": "They may cause ground-nesting birds to leave",
            "correct_index": 1,
            "explanation": "Ground-nesting birds often abandoned those sites within two seasons.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q4",
            "type": "speaker_purpose",
            "question": "Why does the professor mention contrast markers such as 'however'?",
            "choices": [
                "To warn students not to use them in writing",
                "Because exam questions often target those shifts",
                "Because they are grammatically incorrect",
                "To introduce the next course assignment only",
            ],
            "correct_answer": "Because exam questions often target those shifts",
            "correct_index": 1,
            "explanation": "The professor advises noting contrast markers for advanced listening questions.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q5",
            "type": "detail",
            "question": "How long did the bee population study track cities?",
            "choices": ["Two seasons", "Five years", "Nearly a decade", "Twenty years"],
            "correct_answer": "Nearly a decade",
            "correct_index": 2,
            "explanation": "Researchers tracked native bee populations for nearly a decade.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q6",
            "type": "organization",
            "question": "What does the professor ask students to prepare for next class?",
            "choices": [
                "A map of local parks",
                "One question about speaker attitude or structure",
                "A list of solar energy companies",
                "A summary of satellite imagery techniques",
            ],
            "correct_answer": "One question about speaker attitude or structure",
            "correct_index": 1,
            "explanation": "Students should prepare a question about attitude or organizational structure.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q7",
            "type": "attitude",
            "question": "What is the professor's attitude toward citizen-science volunteers?",
            "choices": [
                "They are unreliable compared with satellites",
                "They are a methodological asset",
                "They should replace professional scientists",
                "They are useful only for outreach",
            ],
            "correct_answer": "They are a methodological asset",
            "correct_index": 1,
            "explanation": "The professor says public engagement improved model accuracy.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q8",
            "type": "detail",
            "question": "What benefit did hybrid stormwater systems provide?",
            "choices": [
                "They eliminated the need for native plants",
                "They reduced flooding and filtered pollutants",
                "They increased solar panel efficiency",
                "They shortened lecture attendance",
            ],
            "correct_answer": "They reduced flooding and filtered pollutants",
            "correct_index": 1,
            "explanation": "Hybrid systems reduced flooding and filtered pollutants reaching rivers.",
            "mistake_category": "listening_comprehension",
        },
    ]


def build_fallback_listening_practice(
    *,
    level: str,
    stage: str,
    listening_type: str,
    topic: str,
    lesson_focus: str,
) -> dict:
    """Deterministic built-in practice when all AI providers fail."""
    type_label = LISTENING_TYPE_LABELS.get(listening_type, "Academic mini-lecture")
    topic_label = topic if topic != "Random" else "Academic Skills"
    if stage == STAGE2_SLUG:
        transcript = FALLBACK_STAGE2_TRANSCRIPT
        questions = _fallback_questions_stage2()
        title = f"{type_label}: Urban Green Infrastructure ({topic_label})"
    else:
        transcript = FALLBACK_STAGE1_TRANSCRIPT
        questions = _fallback_questions_stage1(lesson_focus)
        title = f"{type_label}: Open Access and Article Practice ({topic_label})"

    word_count = len(transcript.split())
    estimated_duration_seconds = max(60, round(word_count / 140 * 60))

    return {
        "title": title,
        "level": level,
        "stage": stage,
        "listening_type": listening_type,
        "topic": topic,
        "lesson_focus": lesson_focus,
        "transcript": transcript,
        "estimated_duration_seconds": estimated_duration_seconds,
        "target_vocabulary": [
            {
                "word": "undergraduates",
                "definition": "university students who do not yet have a degree",
                "example": "The researchers interviewed two hundred undergraduates.",
            },
            {
                "word": "biodiversity",
                "definition": "the variety of plant and animal life in a place",
                "example": "Green corridors can support urban biodiversity.",
            },
        ] if stage == STAGE2_SLUG else [
            {
                "word": "undergraduates",
                "definition": "university students who do not yet have a degree",
                "example": "The researchers interviewed two hundred undergraduates.",
            },
        ],
        "questions": questions,
        "shadowing_sentences": [
            "Although the students understood the main ideas, they often chose the wrong article before a noun.",
            "These findings suggest that targeted practice can support academic success for many learners.",
        ] if stage != STAGE2_SLUG else [
            "Urban ecologists have long argued that parks alone cannot sustain diverse species in dense metropolitan areas.",
            "The professor concluded that public engagement is not merely outreach but a methodological asset.",
        ],
    }


def _generate_listening_with_providers(
    user_message: str,
    requested_provider: str | None,
) -> tuple[dict | None, dict]:
    """Try providers in priority order; return (parsed, metadata) or (None, empty metadata)."""
    for provider in build_provider_attempt_order(requested_provider):
        if not is_ai_provider_configured(provider):
            continue
        try:
            raw_reply = generate_from_template(
                "listening_practice_generate",
                user_message,
                provider=provider,
            )
            parsed = parse_listening_practice(raw_reply)
            template = get_prompt_template("listening_practice_generate", provider=provider)
            return parsed, {
                "provider": provider,
                "model": template.model_name,
                "used_fallback": False,
            }
        except ValueError as exc:
            if is_provider_error(exc):
                continue
            continue
        except RuntimeError:
            continue
    return None, {}


def _session_payload(
    session: ListeningSession,
    *,
    include_answers: bool = False,
    provider_metadata: dict | None = None,
    learner_message: str | None = None,
) -> dict:
    questions = []
    for question in session.questions_json:
        row = {
            "id": question["id"],
            "type": question.get("type", "detail"),
            "question": question["question"],
            "choices": question.get("choices", []),
        }
        if include_answers:
            row["correct_answer"] = question.get("correct_answer")
            row["explanation"] = question.get("explanation", "")
            row["mistake_category"] = question.get("mistake_category", "listening_comprehension")
        questions.append(row)

    payload = {
        "session_id": session.id,
        "title": session.title,
        "level": session.level,
        "stage": session.stage,
        "listening_type": session.listening_type,
        "topic": session.topic,
        "lesson_focus": session.lesson_focus,
        "transcript": session.transcript,
        "estimated_duration_seconds": session.estimated_duration_seconds,
        "target_vocabulary": session.target_vocabulary,
        "questions": questions,
        "shadowing_sentences": session.shadowing_sentences,
    }
    if provider_metadata:
        payload["provider_metadata"] = provider_metadata
    if learner_message:
        payload["learner_message"] = learner_message
    return payload


def generate_listening_practice(
    user,
    *,
    level: str = "B1",
    stage: str = STAGE1_SLUG,
    listening_type: str = "academic_mini_lecture",
    topic: str = "Random",
    lesson_focus: str = "current_lesson",
    length: str = "medium",
    speed: str = "normal",
    provider: str | None = None,
) -> dict:
    context = gather_listening_context(user)
    if stage not in LISTENING_STAGES:
        stage = context["stage"]

    resolved_focus = resolve_lesson_focus(lesson_focus, context)
    user_message = build_listening_generate_user_message(
        level=level,
        stage=stage,
        listening_type=listening_type,
        topic=topic,
        lesson_focus=lesson_focus,
        length=length,
        speed=speed,
        context=context,
    )

    parsed, provider_metadata = _generate_listening_with_providers(user_message, provider)
    used_fallback = parsed is None
    if used_fallback:
        parsed = build_fallback_listening_practice(
            level=level,
            stage=stage,
            listening_type=listening_type,
            topic=topic,
            lesson_focus=resolved_focus,
        )
        provider_metadata = dict(FALLBACK_PROVIDER_METADATA)

    learner_message = None
    if used_fallback or provider_metadata.get("provider") == "ollama":
        learner_message = LEARNER_FALLBACK_MESSAGE

    session = ListeningSession.objects.create(
        user=user,
        title=parsed["title"],
        level=level,
        stage=stage,
        listening_type=listening_type,
        topic=topic,
        lesson_focus=resolved_focus,
        transcript=parsed["transcript"],
        questions_json=parsed["questions"],
        target_vocabulary=parsed["target_vocabulary"],
        shadowing_sentences=parsed["shadowing_sentences"],
        estimated_duration_seconds=parsed["estimated_duration_seconds"],
    )

    payload = _session_payload(
        session,
        include_answers=False,
        provider_metadata=provider_metadata,
        learner_message=learner_message,
    )
    payload["speed"] = speed
    payload["disclaimer"] = "Original TOEFL-style listening practice — not official ETS/TOEFL content."
    return payload


def _mistake_category_for_question(question: dict, session: ListeningSession) -> str:
    category = (question.get("mistake_category") or "").strip()
    if category and category != "listening_comprehension":
        return category

    lesson_category = LESSON_FOCUS_TO_MISTAKE_CATEGORY.get(session.lesson_focus)
    if lesson_category and session.lesson_focus != "none":
        return lesson_category
    return "listening_comprehension"


def score_listening_session(user, session_id: int, answers: dict) -> dict:
    try:
        session = ListeningSession.objects.get(id=session_id, user=user)
    except ListeningSession.DoesNotExist as exc:
        raise ValueError("Listening session not found.") from exc

    if session.completed_at:
        raise ValueError("This listening session was already submitted.")

    results = []
    mistakes = []
    correct_count = 0
    weak_types: Counter[str] = Counter()

    for question in session.questions_json:
        question_id = question["id"]
        raw_answer = answers.get(question_id)
        choices = question.get("choices", [])
        correct_answer = question.get("correct_answer") or (
            choices[question.get("correct_index", 0)] if choices else ""
        )

        selected_answer = ""
        if isinstance(raw_answer, int) and raw_answer in range(len(choices)):
            selected_answer = choices[raw_answer]
        elif isinstance(raw_answer, str):
            selected_answer = raw_answer.strip()
            if selected_answer not in choices:
                try:
                    index = int(raw_answer)
                    if index in range(len(choices)):
                        selected_answer = choices[index]
                except (TypeError, ValueError):
                    selected_answer = raw_answer

        is_correct = selected_answer == correct_answer
        if is_correct:
            correct_count += 1
        else:
            question_type = question.get("type") or "detail"
            weak_types[question_type] += 1
            category = _mistake_category_for_question(question, session)
            explanation = question.get("explanation") or f"The correct answer is: {correct_answer}"
            mistakes.append(
                {
                    "wrong_text": f"{question['question']} — Selected: {selected_answer or 'No answer'}",
                    "correct_text": correct_answer,
                    "reason": explanation,
                    "persian_explanation": "",
                    "review_sentence": session.transcript[:500],
                    "category": category,
                }
            )

        ListeningQuestionAttempt.objects.create(
            session=session,
            question_id=question_id,
            selected_answer=selected_answer or "No answer",
            correct_answer=correct_answer,
            is_correct=is_correct,
            question_type=question.get("type") or "",
            mistake_category=_mistake_category_for_question(question, session),
        )

        results.append(
            {
                "id": question_id,
                "question": question["question"],
                "selected_answer": selected_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "type": question.get("type", ""),
                "mistake_category": _mistake_category_for_question(question, session),
            }
        )

    if mistakes:
        save_mistakes(user, "listening_coach", mistakes)

    total = len(session.questions_json)
    percent = round((correct_count / total) * 100) if total else 0
    session.score = percent
    session.completed_at = timezone.now()
    session.save(update_fields=["score", "completed_at"])

    weak_question_types = [
        {"type": question_type, "count": count} for question_type, count in weak_types.most_common()
    ]

    return {
        "score": {"correct": correct_count, "total": total, "percent": percent},
        "results": results,
        "mistakes_saved": len(mistakes),
        "weak_question_types": weak_question_types,
        "transcript": session.transcript,
        "shadowing_sentences": session.shadowing_sentences,
    }


def _listening_plan_item(
    *,
    title: str,
    reason: str,
    listening_type: str = "academic_mini_lecture",
    topic: str = "Random",
    lesson_focus: str = "current_lesson",
    length: str = "medium",
) -> dict:
    params = {
        "listening_type": listening_type,
        "topic": topic,
        "lesson_focus": lesson_focus,
        "length": length,
    }
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return {
        "id": f"listening-{listening_type}-{lesson_focus}",
        "type": "listening",
        "title": title,
        "skill": "Listening",
        "reason": reason,
        "route": f"/listening?mode=generate&{query}",
        "minutes": 15,
        "completed": False,
        "status": "not_started",
        "metadata": {
            "listening_type": listening_type,
            "topic": topic,
            "lesson_focus": lesson_focus,
            "length": length,
        },
    }


def build_listening_plan_items_for_user(user, today: date | None = None) -> list[dict]:
    """Targeted listening tasks based on stage and current lesson focus."""
    context = gather_listening_context(user)
    stage = context.get("stage", STAGE1_SLUG)
    stage_label = "TOEFL 80+" if stage != STAGE2_SLUG else "TOEFL 100+"

    items = [
        _listening_plan_item(
            title="Listening practice: Academic mini-lecture",
            reason=f"You are working toward {stage_label} listening readiness.",
            listening_type="academic_mini_lecture",
        )
    ]

    resolved_focus = resolve_lesson_focus("current_lesson", context)
    if resolved_focus != "none":
        focus_label = LESSON_FOCUS_LABELS.get(resolved_focus, resolved_focus)
        items.append(
            _listening_plan_item(
                title=f"Listening practice: {focus_label} in academic lectures",
                reason=f"Your current lesson is {focus_label.lower()}.",
                listening_type="academic_mini_lecture",
                lesson_focus=resolved_focus,
            )
        )

    return items[:2]


def listening_score_for_user(user, stage_slug: str) -> int:
    """Average recent listening session scores for readiness integration."""
    sessions = ListeningSession.objects.filter(
        user=user,
        completed_at__isnull=False,
        stage=stage_slug,
    ).order_by("-completed_at")[:5]
    if not sessions:
        return 0
    return round(sum(session.score or 0 for session in sessions) / len(sessions))
