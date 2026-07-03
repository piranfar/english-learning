"""Original reading passage generation, scoring, and plan integration."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date

from django.utils import timezone

from tutor.learning_journey import STAGE1_SLUG, STAGE2_SLUG, next_lesson_for_stage
from tutor.models import ReadingQuestionAttempt, ReadingSession, UserLearningJourney, VocabularyItem
from tutor.plan_tasks import count_recent_mistakes_by_category
from tutor.services import generate_from_template, save_mistakes

READING_PASSAGE_PATTERN = re.compile(
    r"---READING_PASSAGE---\s*(\{.*?\})\s*---END_READING_PASSAGE---",
    re.DOTALL,
)

READING_LEVELS = ("A2", "B1", "B2", "C1 Academic")
READING_STAGES = (STAGE1_SLUG, STAGE2_SLUG)
READING_TOPICS = (
    "Academic",
    "Science",
    "Health",
    "University Life",
    "Technology",
    "Society",
    "Random",
)
LESSON_FOCUS_CHOICES = (
    "current_lesson",
    "articles",
    "prepositions",
    "passive_voice",
    "present_perfect",
    "academic_linking_words",
    "academic_sentence_structure",
    "vocabulary_in_context",
    "none",
)
QUESTION_FOCUS_CHOICES = (
    "mixed",
    "main_idea",
    "detail",
    "inference",
    "vocabulary_in_context",
    "sentence_function",
    "rhetorical_purpose",
)
LENGTH_CHOICES = ("short", "medium", "long", "toefl_style")
READING_MODES = ("general", "toefl_2026", "classic_toefl")
SIMULATION_TYPES = (
    "complete_the_words",
    "daily_life_reading",
    "academic_passage",
)

READING_SKILL_LABELS = {
    "main_idea": "Main idea",
    "detail": "Detail",
    "inference": "Inference",
    "vocabulary": "Vocabulary",
    "vocabulary_in_context": "Vocabulary",
    "vocabulary_context": "Vocabulary",
    "grammar": "Grammar/context",
    "grammar_context": "Grammar/context",
    "complete_words": "Complete the words",
    "sentence_meaning": "Sentence meaning",
}

READING_SKILL_TO_WEAKNESS = {
    "main_idea": "reading_main_idea",
    "detail": "reading_detail",
    "inference": "reading_inference",
    "vocabulary_in_context": "reading_vocabulary_context",
    "vocabulary_context": "reading_vocabulary_context",
    "vocabulary": "reading_vocabulary_context",
    "complete_the_words": "reading_complete_words",
    "sentence_meaning": "reading_sentence_meaning",
    "sentence_function": "reading_sentence_meaning",
    "rhetorical_purpose": "reading_inference",
    "reference": "reading_detail",
    "negative_factual": "reading_detail",
    "prose_summary": "reading_main_idea",
    "insert_sentence": "reading_inference",
    "sentence_simplification": "reading_sentence_meaning",
}

LESSON_FOCUS_LABELS = {
    "current_lesson": "Current lesson",
    "articles": "Articles",
    "prepositions": "Prepositions",
    "passive_voice": "Passive voice",
    "present_perfect": "Present perfect",
    "academic_linking_words": "Academic linking words",
    "academic_sentence_structure": "Academic sentence structure",
    "vocabulary_in_context": "Vocabulary in context",
    "none": "No specific grammar focus",
}

LESSON_FOCUS_TO_MISTAKE_CATEGORY = {
    "articles": "article",
    "prepositions": "preposition",
    "passive_voice": "tense",
    "present_perfect": "tense",
    "academic_linking_words": "sentence_structure",
    "academic_sentence_structure": "sentence_structure",
    "vocabulary_in_context": "vocabulary_precision",
}

STAGE_PASSAGE_SETTINGS = {
    STAGE1_SLUG: {
        "word_min": 250,
        "word_max": 450,
        "question_min": 4,
        "question_max": 6,
        "cefr": "B1/B2",
        "description": (
            "Stage 1: B2 Academic English / TOEFL 80+ readiness. "
            "Clear structure, B1/B2 vocabulary, focus on main idea, detail, "
            "vocabulary in context, and basic inference."
        ),
    },
    STAGE2_SLUG: {
        "word_min": 500,
        "word_max": 750,
        "question_min": 6,
        "question_max": 10,
        "cefr": "B2/C1",
        "description": (
            "Stage 2: Full Academic English / TOEFL 100+ readiness. "
            "Denser academic language, abstract vocabulary, include inference, "
            "rhetorical purpose, sentence function, and vocabulary in context."
        ),
    },
}

LENGTH_OVERRIDES = {
    "short": {"word_min": 200, "word_max": 300, "question_min": 4, "question_max": 5},
    "medium": {"word_min": 350, "word_max": 450, "question_min": 5, "question_max": 7},
    "long": {"word_min": 450, "word_max": 650, "question_min": 7, "question_max": 10},
    "toefl_style": None,
}


def resolve_passage_settings(stage: str, length: str) -> dict:
    base = dict(STAGE_PASSAGE_SETTINGS.get(stage, STAGE_PASSAGE_SETTINGS[STAGE1_SLUG]))
    override = LENGTH_OVERRIDES.get(length)
    if override:
        base.update(override)
    if stage == STAGE2_SLUG and length == "medium":
        base["word_min"] = 450
        base["word_max"] = 550
        base["question_min"] = 6
        base["question_max"] = 8
    return base


def gather_reading_context(user) -> dict:
    journey = UserLearningJourney.objects.filter(user=user).select_related("current_goal").first()
    stage_slug = STAGE1_SLUG
    goal_name = "B2 Academic English / TOEFL 80+ Readiness"
    if journey and journey.current_goal:
        stage_slug = journey.current_goal.slug
        goal_name = journey.current_goal.name

    next_lesson = next_lesson_for_stage(user, stage_slug)
    category_counts = count_recent_mistakes_by_category(user, days=30)
    due_words = list(
        VocabularyItem.objects.filter(
            user=user,
            next_review_date__lte=date.today(),
        )
        .order_by("next_review_date", "created_at")
        .values_list("word", flat=True)[:8]
    )

    return {
        "stage": stage_slug,
        "goal_name": goal_name,
        "current_lesson_slug": next_lesson.slug if next_lesson else "",
        "current_lesson_title": next_lesson.title if next_lesson else "",
        "recent_mistake_categories": category_counts,
        "due_vocabulary": due_words,
    }


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
        "academic-sentence-structure": "academic_sentence_structure",
    }
    for key, value in slug_map.items():
        if key in slug:
            return value
    if "reading" in slug or "vocabulary" in slug:
        return "vocabulary_in_context"
    return "none"


def build_reading_generate_user_message(
    *,
    level: str,
    stage: str,
    topic: str,
    lesson_focus: str,
    question_focus: str,
    length: str,
    context: dict,
    simulation_type: str = "",
    reading_mode: str = "general",
) -> str:
    from tutor.prompts.reading_coach import (
        LESSON_FOCUS_INSTRUCTIONS,
        QUESTION_FOCUS_INSTRUCTIONS,
        TOPIC_INSTRUCTIONS,
    )

    resolved_focus = resolve_lesson_focus(lesson_focus, context)
    settings = resolve_passage_settings(stage, length)
    topic_key = topic if topic in TOPIC_INSTRUCTIONS else "Random"
    focus_instruction = LESSON_FOCUS_INSTRUCTIONS.get(
        resolved_focus, LESSON_FOCUS_INSTRUCTIONS["none"]
    )
    question_instruction = QUESTION_FOCUS_INSTRUCTIONS.get(
        question_focus, QUESTION_FOCUS_INSTRUCTIONS["mixed"]
    )

    recent_categories = context.get("recent_mistake_categories") or {}
    top_categories = sorted(recent_categories, key=recent_categories.get, reverse=True)[:3]
    due_vocab = context.get("due_vocabulary") or []

    lines = [
        f"Reading mode: {reading_mode}",
        f"Student level: {level}",
        f"Learning stage: {stage} ({context.get('goal_name', '')})",
        f"Topic: {topic_key}",
        TOPIC_INSTRUCTIONS[topic_key],
        f"Lesson focus: {resolved_focus}",
        focus_instruction,
        f"Question focus: {question_focus}",
        question_instruction,
        f"Passage length: {settings['word_min']}-{settings['word_max']} words",
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
            "Due vocabulary to weave in naturally when possible: "
            + ", ".join(due_vocab[:6])
        )
    if simulation_type:
        lines.append(f"TOEFL-style simulation task type: {simulation_type}")
        lines.append(
            "This is TOEFL-style practice only — do NOT copy or reproduce official ETS/TOEFL passages."
        )

    return "\n".join(lines)


def _normalize_choices(raw_choices: list) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    ids: list[str] = []
    for index, choice in enumerate(raw_choices):
        if isinstance(choice, dict):
            text = (choice.get("text") or "").strip()
            choice_id = (choice.get("id") or chr(65 + index)).strip()
        else:
            text = str(choice).strip()
            choice_id = chr(65 + index)
        if text:
            texts.append(text)
            ids.append(choice_id)
    return texts, ids


def _normalize_question(entry: dict, index: int) -> dict | None:
    question_text = (
        (entry.get("question") or entry.get("text_with_blank") or "").strip()
    )
    choice_texts, choice_ids = _normalize_choices(
        entry.get("choices", entry.get("options", []))
    )
    if not question_text or len(choice_texts) != 4:
        return None

    correct_answer = (entry.get("correct_answer") or "").strip()
    correct_index = entry.get("correct_index")
    if correct_answer in choice_ids:
        correct_index = choice_ids.index(correct_answer)
        correct_answer = choice_texts[correct_index]
    elif correct_answer:
        try:
            correct_index = choice_texts.index(correct_answer)
        except ValueError:
            correct_index = None
    else:
        try:
            correct_index = int(correct_index)
        except (TypeError, ValueError):
            correct_index = None
        if correct_index in range(4):
            correct_answer = choice_texts[correct_index]
        else:
            return None

    question_type = (entry.get("type") or entry.get("focus") or "mixed").strip()
    skill = (entry.get("skill") or question_type).strip()
    mistake_category = (
        entry.get("mistake_category")
        or READING_SKILL_TO_WEAKNESS.get(skill)
        or READING_SKILL_TO_WEAKNESS.get(question_type)
        or "reading_comprehension"
    )

    return {
        "id": (entry.get("id") or f"q{index}").strip(),
        "type": question_type,
        "skill": skill,
        "question": question_text,
        "choices": choice_texts,
        "options": choice_texts,
        "choice_ids": choice_ids,
        "correct_answer": correct_answer,
        "correct_index": correct_index,
        "explanation": (entry.get("explanation") or "").strip(),
        "mistake_category": mistake_category,
    }


def parse_reading_json_payload(data: dict, *, level: str = "B1", stage: str = STAGE1_SLUG) -> dict:
    passage = (data.get("passage") or "").strip()
    min_words = 40 if data.get("mode") == "toefl_2026" else 80
    if len(passage.split()) < min_words:
        raise ValueError("Generated passage is too short")

    questions = []
    for index, entry in enumerate(data.get("questions", []), start=1):
        normalized = _normalize_question(entry, index)
        if normalized:
            questions.append(normalized)

    if len(questions) < 4:
        raise ValueError("Reading practice must include at least 4 valid questions")

    target_vocabulary = []
    vocab_source = data.get("vocabulary") or data.get("target_vocabulary") or []
    for entry in vocab_source:
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        target_vocabulary.append(
            {
                "word": word,
                "definition": (entry.get("meaning") or entry.get("definition") or "").strip(),
                "example": (entry.get("example") or "").strip(),
            }
        )

    answer_key = data.get("answer_key") or {}
    if not answer_key:
        answer_key = {q["id"]: q["correct_answer"] for q in questions}

    return {
        "title": (data.get("title") or "Reading practice").strip(),
        "level": (data.get("level") or level).strip(),
        "stage": (data.get("stage") or stage).strip(),
        "lesson_focus": (data.get("lesson_focus") or "none").strip(),
        "topic": (data.get("topic") or "Academic").strip(),
        "reading_mode": (data.get("mode") or "general").strip(),
        "passage": passage,
        "estimated_time_minutes": int(
            data.get("estimated_reading_time_minutes")
            or data.get("estimated_time_minutes")
            or 15
        ),
        "target_vocabulary": target_vocabulary,
        "questions": questions,
        "answer_key": answer_key,
        "skills_tested": data.get("skills_tested") or [],
        "next_drill": data.get("next_drill") or {},
    }


def parse_reading_passage(raw_reply: str) -> dict:
    cleaned = (raw_reply or "").strip()
    if cleaned.startswith("{"):
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return parse_reading_json_payload(data)
        except json.JSONDecodeError:
            pass

    match = READING_PASSAGE_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse reading passage from AI response")

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse reading passage JSON") from exc

    return parse_reading_json_payload(data)


def _session_payload(session: ReadingSession, *, include_answers: bool = False) -> dict:
    questions = []
    for question in session.questions_json:
        row = {
            "id": question["id"],
            "type": question.get("type", "mixed"),
            "skill": question.get("skill", question.get("type", "mixed")),
            "question": question["question"],
            "choices": question.get("choices") or question.get("options", []),
        }
        if include_answers:
            row["correct_answer"] = question.get("correct_answer")
            row["explanation"] = question.get("explanation", "")
            row["mistake_category"] = question.get("mistake_category", "reading_comprehension")
        questions.append(row)

    vocab = session.target_vocabulary
    if isinstance(vocab, dict):
        vocab = vocab.get("words") or []

    reading_mode = session.simulation_type or "general"
    if reading_mode in SIMULATION_TYPES:
        reading_mode = "toefl_2026"

    return {
        "session_id": session.id,
        "title": session.title,
        "level": session.level,
        "stage": session.stage,
        "lesson_focus": session.lesson_focus,
        "topic": session.topic,
        "mode": session.mode,
        "reading_mode": reading_mode,
        "simulation_type": session.simulation_type,
        "passage": session.passage,
        "estimated_time_minutes": session.estimated_time_minutes,
        "target_vocabulary": vocab,
        "questions": questions,
    }


def generate_reading_practice(
    user,
    *,
    level: str = "B1",
    stage: str = STAGE1_SLUG,
    topic: str = "Academic",
    lesson_focus: str = "current_lesson",
    question_focus: str = "mixed",
    length: str = "medium",
    provider: str | None = None,
    mode: str = ReadingSession.MODE_GENERATED,
    simulation_type: str = "",
    reading_mode: str = "general",
) -> dict:
    from tutor.reading_ai_service import (
        ReadingNotConfiguredError,
        generate_reading_practice_ai,
        resolve_reading_provider,
    )

    context = gather_reading_context(user)
    if stage not in READING_STAGES:
        stage = context["stage"]

    resolved_focus = resolve_lesson_focus(lesson_focus, context)

    if reading_mode == "toefl_2026":
        mode = ReadingSession.MODE_SIMULATION
        length = length if length in ("short", "medium", "long") else "toefl_style"
        if not simulation_type:
            simulation_type = "academic_passage"
    elif reading_mode == "classic_toefl":
        mode = ReadingSession.MODE_SIMULATION
        length = "toefl_style"
        simulation_type = simulation_type or "classic_toefl"
    else:
        reading_mode = "general"
        mode = ReadingSession.MODE_GENERATED

    try:
        parsed = generate_reading_practice_ai(
            user,
            level=level,
            stage=stage,
            topic=topic,
            lesson_focus=lesson_focus,
            question_focus=question_focus,
            length=length,
            reading_mode=reading_mode,
            simulation_type=simulation_type,
            provider=provider,
        )
    except ReadingNotConfiguredError:
        raise
    except Exception:
        resolved = resolve_reading_provider(provider)
        if resolved == "ollama":
            user_message = build_reading_generate_user_message(
                level=level,
                stage=stage,
                topic=topic,
                lesson_focus=lesson_focus,
                question_focus=question_focus,
                length=length,
                context=context,
                simulation_type=simulation_type,
                reading_mode=reading_mode,
            )
            task_type = (
                "reading_simulation"
                if mode == ReadingSession.MODE_SIMULATION
                else "reading_generate"
            )
            raw_reply = generate_from_template(task_type, user_message, provider="ollama")
            parsed = parse_reading_passage(raw_reply)
        else:
            raise

    session = ReadingSession.objects.create(
        user=user,
        title=parsed["title"],
        level=level,
        stage=stage,
        lesson_focus=resolved_focus,
        topic=topic,
        mode=mode,
        simulation_type=simulation_type or reading_mode,
        passage=parsed["passage"],
        questions_json=parsed["questions"],
        target_vocabulary=parsed["target_vocabulary"],
        estimated_time_minutes=parsed["estimated_time_minutes"],
    )

    payload = _session_payload(session, include_answers=False)
    payload["reading_mode"] = reading_mode
    payload["skills_tested"] = parsed.get("skills_tested", [])
    payload["next_drill"] = parsed.get("next_drill", {})
    payload["disclaimer"] = (
        "Original TOEFL-style practice — not official ETS/TOEFL content."
        if mode == ReadingSession.MODE_SIMULATION
        else "Original reading practice generated for your level and goals."
    )
    return payload


def _mistake_category_for_question(question: dict, session: ReadingSession) -> str:
    category = (question.get("mistake_category") or "").strip()
    if category and category != "reading_comprehension":
        return category

    lesson_category = LESSON_FOCUS_TO_MISTAKE_CATEGORY.get(session.lesson_focus)
    if lesson_category and session.lesson_focus != "none":
        return lesson_category
    return "reading_comprehension"


def _skill_key_for_question(question: dict) -> str:
    skill = (question.get("skill") or question.get("type") or "mixed").strip()
    mapping = {
        "main_idea": "main_idea",
        "detail": "detail",
        "inference": "inference",
        "vocabulary_in_context": "vocabulary",
        "vocabulary_context": "vocabulary",
        "complete_the_words": "complete_words",
        "sentence_meaning": "sentence_meaning",
        "sentence_function": "grammar_context",
        "rhetorical_purpose": "inference",
        "reference": "detail",
        "negative_factual": "detail",
        "prose_summary": "main_idea",
        "insert_sentence": "inference",
        "sentence_simplification": "grammar_context",
    }
    return mapping.get(skill, "grammar_context")


def _build_skill_scores(results: list[dict]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    correct: Counter[str] = Counter()
    for row in results:
        skill = _skill_key_for_question(row)
        totals[skill] += 1
        if row.get("is_correct"):
            correct[skill] += 1
    return {
        skill: round((correct[skill] / totals[skill]) * 100) if totals[skill] else 0
        for skill in totals
    }


def _build_next_drill(weak_types: Counter[str], skill_scores: dict[str, int]) -> dict:
    if not weak_types:
        return {
            "title": "Keep your momentum",
            "instruction": "You answered every question correctly. Try a longer passage or TOEFL simulation next.",
            "target_skill": "mixed",
        }

    weakest_type, count = weak_types.most_common(1)[0]
    skill = _skill_key_for_question({"type": weakest_type})
    label = READING_SKILL_LABELS.get(skill, weakest_type.replace("_", " "))
    return {
        "title": f"Practice: {label}",
        "instruction": (
            f"You missed {count} {label.lower()} question{'s' if count != 1 else ''}. "
            f"Practice identifying {label.lower()} in short academic passages."
        ),
        "target_skill": skill,
    }


def _practice_toefl_estimate(session: ReadingSession, percent: int) -> dict | None:
    sim = session.simulation_type or "general"
    if sim in SIMULATION_TYPES:
        score = max(1, min(6, round(1 + (percent / 100) * 5)))
        return {
            "scale": "1-6",
            "score": score,
            "label": "Practice estimate, not official ETS score",
        }
    if sim in ("classic_toefl", "classic_academic"):
        score = round((percent / 100) * 30)
        return {
            "scale": "0-30",
            "score": score,
            "label": "Practice estimate, not official ETS score",
        }
    return None


def score_reading_session(user, session_id: int, answers: dict) -> dict:
    try:
        session = ReadingSession.objects.get(id=session_id, user=user)
    except ReadingSession.DoesNotExist as exc:
        raise ValueError("Reading session not found.") from exc

    if session.completed_at:
        raise ValueError("This reading session was already submitted.")

    results = []
    mistakes = []
    correct_count = 0
    weak_types: Counter[str] = Counter()

    for question in session.questions_json:
        question_id = question["id"]
        raw_answer = answers.get(question_id)
        choices = question.get("choices") or question.get("options", [])
        correct_answer = question.get("correct_answer") or choices[question.get("correct_index", 0)]

        selected_answer = ""
        if isinstance(raw_answer, int) and raw_answer in range(len(choices)):
            selected_answer = choices[raw_answer]
        elif isinstance(raw_answer, str):
            selected_answer = raw_answer.strip()
            if selected_answer in choices:
                pass
            else:
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
            question_type = question.get("type") or "mixed"
            weak_types[question_type] += 1
            category = _mistake_category_for_question(question, session)
            explanation = question.get("explanation") or f"The correct answer is: {correct_answer}"
            mistakes.append(
                {
                    "wrong_text": f"{question['question']} — Selected: {selected_answer or 'No answer'}",
                    "correct_text": correct_answer,
                    "reason": explanation,
                    "persian_explanation": "",
                    "review_sentence": session.passage[:500],
                    "category": category,
                }
            )

        ReadingQuestionAttempt.objects.create(
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
                "skill": question.get("skill") or question.get("type", ""),
                "mistake_category": _mistake_category_for_question(question, session),
            }
        )

    if mistakes:
        save_mistakes(user, "reading_coach", mistakes)

    total = len(session.questions_json)
    percent = round((correct_count / total) * 100) if total else 0
    session.score_percent = percent
    session.completed_at = timezone.now()
    session.save(update_fields=["score_percent", "completed_at"])

    skill_scores = _build_skill_scores(results)
    weak_question_types = [
        {"type": question_type, "count": count}
        for question_type, count in weak_types.most_common()
    ]
    next_drill = _build_next_drill(weak_types, skill_scores)
    practice_estimate = _practice_toefl_estimate(session, percent)

    mistake_pattern = ""
    if weak_question_types:
        top = weak_question_types[0]
        mistake_pattern = (
            f"Most misses were {top['type'].replace('_', ' ')} questions ({top['count']})."
        )

    from tutor.plan_completion import auto_complete_plan_items

    plan_items_completed = auto_complete_plan_items(
        user,
        track="reading",
        metadata={"lesson_focus": session.lesson_focus},
    )

    return {
        "score": {
            "correct": correct_count,
            "total": total,
            "percent": percent,
        },
        "skill_scores": skill_scores,
        "results": results,
        "mistakes_saved": len(mistakes),
        "weak_question_types": weak_question_types,
        "mistake_pattern": mistake_pattern,
        "next_drill": next_drill,
        "practice_toefl_estimate": practice_estimate,
        "plan_items_completed": plan_items_completed,
    }


def grade_reading_attempt(user, practice_id: int, user_answers: dict) -> dict:
    """Alias for scoring a reading practice attempt."""
    return score_reading_session(user, practice_id, user_answers)


def analyze_reading_weaknesses(user, attempt: dict) -> dict:
    """Summarize reading weaknesses from a graded attempt."""
    skill_scores = attempt.get("skill_scores") or {}
    weakest = None
    worst = 101
    for skill, value in skill_scores.items():
        if value < worst:
            worst = value
            weakest = skill
    return {
        "weakest_skill": weakest,
        "skill_scores": skill_scores,
        "mistake_pattern": attempt.get("mistake_pattern", ""),
        "next_drill": attempt.get("next_drill", {}),
    }


def build_reading_plan_items_for_user(user, today: date | None = None) -> list[dict]:
    """Targeted reading tasks based on mistakes, lesson, and recent performance."""
    today = today or date.today()
    items: list[dict] = []
    category_counts = count_recent_mistakes_by_category(user, days=30)
    context = gather_reading_context(user)

    article_count = category_counts.get("article", 0)
    if article_count >= 2:
        items.append(
            _reading_plan_item(
                title="Reading practice: Articles in academic passages",
                reason=f"You made {article_count} article mistakes recently.",
                lesson_focus="articles",
                question_focus="vocabulary_in_context",
            )
        )

    weak_inference = (
        ReadingQuestionAttempt.objects.filter(
            session__user=user,
            is_correct=False,
            question_type="inference",
        ).count()
    )
    if weak_inference >= 2:
        items.append(
            _reading_plan_item(
                title="TOEFL-style reading: inference questions",
                reason="Your recent reading score shows weak inference accuracy.",
                question_focus="inference",
                length="toefl_style",
            )
        )

    next_lesson = context.get("current_lesson_title")
    if next_lesson and "reading" in (context.get("current_lesson_slug") or ""):
        items.append(
            _reading_plan_item(
                title=f"Reading practice: {next_lesson}",
                reason="This connects to your current lesson in the learning path.",
                lesson_focus="current_lesson",
            )
        )

    return items[:2]


def _reading_plan_item(
    *,
    title: str,
    reason: str,
    lesson_focus: str = "current_lesson",
    question_focus: str = "mixed",
    length: str = "medium",
) -> dict:
    params = {
        "lesson_focus": lesson_focus,
        "question_focus": question_focus,
        "length": length,
    }
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return {
        "id": f"reading-{lesson_focus}-{question_focus}",
        "type": "reading",
        "title": title,
        "skill": "Reading",
        "reason": reason,
        "route": f"/reading?tab=generate&{query}",
        "minutes": 15,
        "completed": False,
        "status": "not_started",
        "metadata": {
            "lesson_focus": lesson_focus,
            "question_focus": question_focus,
            "length": length,
        },
    }


def reading_score_for_user(user, stage_slug: str) -> int:
    """Average recent reading session scores for readiness integration."""
    sessions = ReadingSession.objects.filter(
        user=user,
        completed_at__isnull=False,
        stage=stage_slug,
    ).order_by("-completed_at")[:5]
    if not sessions:
        return 0
    return round(sum(session.score_percent or 0 for session in sessions) / len(sessions))
