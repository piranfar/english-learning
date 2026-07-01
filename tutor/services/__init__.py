import json
import re

from django.contrib.auth import get_user_model

from tutor.ai.factory import get_provider
from tutor.models import (
    Message,
    Mistake,
    PracticeSession,
    PromptTemplate,
    UserProfile,
)

User = get_user_model()

CORRECTION_PATTERN = re.compile(
    r"---CORRECTION---\s*(\{.*?\})\s*---END_CORRECTION---",
    re.DOTALL,
)

VOCAB_JSON_PATTERN = re.compile(r"\{[^{}]*\}", re.DOTALL)

READING_ANALYSIS_PATTERN = re.compile(
    r"---READING_ANALYSIS---\s*(\{.*?\})\s*---END_READING_ANALYSIS---",
    re.DOTALL,
)

READING_QUIZ_PATTERN = re.compile(
    r"---READING_QUIZ---\s*(\{.*?\})\s*---END_READING_QUIZ---",
    re.DOTALL,
)

LISTENING_QUIZ_PATTERN = re.compile(
    r"---LISTENING_QUIZ---\s*(\{.*?\})\s*---END_LISTENING_QUIZ---",
    re.DOTALL,
)

LISTENING_ANALYSIS_PATTERN = re.compile(
    r"---LISTENING_ANALYSIS---\s*(\{.*?\})\s*---END_LISTENING_ANALYSIS---",
    re.DOTALL,
)

TOEFL_WRITING_FEEDBACK_PATTERN = re.compile(
    r"---TOEFL_WRITING_FEEDBACK---\s*(\{.*?\})\s*---END_TOEFL_WRITING_FEEDBACK---",
    re.DOTALL,
)

TOEFL_SPEAKING_FEEDBACK_PATTERN = re.compile(
    r"---TOEFL_SPEAKING_FEEDBACK---\s*(\{.*?\})\s*---END_TOEFL_SPEAKING_FEEDBACK---",
    re.DOTALL,
)

SPEAKING_FEEDBACK_PATTERN = re.compile(
    r"---SPEAKING_FEEDBACK---\s*(\{.*?\})\s*---END_SPEAKING_FEEDBACK---",
    re.DOTALL,
)

WRITING_FEEDBACK_PATTERN = re.compile(
    r"---WRITING_FEEDBACK---\s*(\{.*?\})\s*---END_WRITING_FEEDBACK---",
    re.DOTALL,
)

WRITING_REVISION_COMPARE_PATTERN = re.compile(
    r"---WRITING_REVISION_COMPARE---\s*(\{.*?\})\s*---END_WRITING_REVISION_COMPARE---",
    re.DOTALL,
)

RUBRIC_KEY_ALIASES = {
    "task_fulfillment": "task_response",
    "grammar": "grammar_accuracy",
    "vocabulary": "vocabulary_range",
}


def _normalize_writing_rubric(rubric: dict | None) -> dict:
    if not isinstance(rubric, dict):
        return {}
    normalized: dict = {}
    for key, value in rubric.items():
        new_key = RUBRIC_KEY_ALIASES.get(key, key)
        if new_key not in normalized:
            normalized[new_key] = value
    return normalized


def _coerce_main_mistakes(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    rows = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        wrong = (entry.get("wrong") or entry.get("original") or "").strip()
        correct = (entry.get("correct") or entry.get("corrected") or "").strip()
        reason = (entry.get("reason") or entry.get("why") or "").strip()
        if wrong:
            rows.append({"wrong": wrong, "correct": correct, "reason": reason})
    return rows


def get_default_user():
    user, _ = User.objects.get_or_create(
        username="learner",
        defaults={"email": "learner@localhost"},
    )
    return user


def get_user_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "level": "B1",
            "goal": "Academic English and TOEFL preparation",
            "weak_areas": ["grammar", "academic vocabulary"],
            "native_language": "Persian",
        },
    )
    return profile


def normalize_correction(data: dict) -> dict | None:
    wrong = (data.get("wrong") or data.get("original") or "").strip()
    correct = (data.get("correct") or data.get("corrected") or "").strip()
    if not wrong:
        return None

    from tutor.utils.text_validation import is_meaningful_mistake

    if not is_meaningful_mistake(wrong, correct):
        return None

    return {
        "wrong_text": wrong,
        "correct_text": correct,
        "reason": (data.get("reason") or "").strip(),
        "persian_explanation": (
            data.get("persian") or data.get("persian_note") or ""
        ).strip(),
        "review_sentence": (
            data.get("review_sentence") or data.get("academic") or ""
        ).strip(),
    }


def correction_to_api(correction: dict) -> dict:
    return {
        "original": correction["wrong_text"],
        "corrected": correction["correct_text"],
        "reason": correction["reason"],
        "academic": correction["review_sentence"],
        "persian": correction["persian_explanation"],
    }


def parse_corrections(raw_reply: str) -> tuple[str, list[dict]]:
    corrections = []
    for match in CORRECTION_PATTERN.finditer(raw_reply):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        normalized = normalize_correction(data)
        if normalized:
            corrections.append(normalized)

    clean_reply = CORRECTION_PATTERN.sub("", raw_reply).strip()
    return clean_reply, corrections


def parse_correction(raw_reply: str) -> tuple[str, dict | None]:
    clean_reply, corrections = parse_corrections(raw_reply)
    if not corrections:
        return clean_reply, None
    return clean_reply, corrections[0]


def save_mistakes(user, track: str, corrections: list[dict]) -> None:
    from tutor.utils.mistake_classification import classify_mistake
    from tutor.utils.text_validation import is_meaningful_mistake

    for correction in corrections:
        if not is_meaningful_mistake(
            correction.get("wrong_text", ""),
            correction.get("correct_text", ""),
        ):
            continue
        payload = dict(correction)
        if not payload.get("category"):
            payload["category"] = classify_mistake(
                payload.get("wrong_text", ""),
                payload.get("correct_text", ""),
                payload.get("reason", ""),
                track,
            )
        Mistake.objects.create(user=user, track=track, **payload)


def get_prompt_template(task_type: str, provider: str | None = None) -> PromptTemplate:
    queryset = PromptTemplate.objects.filter(task_type=task_type, is_active=True)
    if provider:
        queryset = queryset.filter(provider=provider)
    template = queryset.first()
    if template is None:
        if provider:
            raise ValueError(
                f"No active prompt for task '{task_type}' with provider '{provider}'"
            )
        raise ValueError(f"No active prompt for task '{task_type}'")
    return template


def call_provider(
    template: PromptTemplate,
    messages: list[dict],
) -> str:
    ai_provider = get_provider(template.provider)
    return ai_provider.generate(
        system_prompt=template.system_prompt,
        messages=messages,
        temperature=template.temperature,
        max_tokens=template.max_tokens,
        model_name=template.model_name,
    )


def generate_from_template(
    task_type: str,
    user_message: str,
    provider: str | None = None,
) -> str:
    template = get_prompt_template(task_type, provider)
    return call_provider(
        template,
        [{"role": "user", "content": user_message}],
    )


def parse_vocab_json(raw_reply: str) -> dict:
    try:
        return json.loads(raw_reply.strip())
    except json.JSONDecodeError:
        pass

    match = VOCAB_JSON_PATTERN.search(raw_reply)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse vocabulary data from AI response")


def parse_vocab_enrichment_json(raw_reply: str) -> dict:
    try:
        data = json.loads(raw_reply.strip())
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = VOCAB_JSON_PATTERN.search(raw_reply)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse vocabulary enrichment JSON from AI response")


def build_vocab_enrichment_prompt(seed) -> str:
    return (
        f'Enrich the vocabulary entry for "{seed.word}" '
        f'(category: {seed.category or "general"}, '
        f'CEFR: {seed.cefr_level or "B1"}, '
        f'part of speech: {seed.part_of_speech or "unknown"}).\n\n'
        "Return ONLY valid JSON with keys:\n"
        "definition, persian_meaning, example, collocations (array of strings), "
        "shadowing_sentence, common_mistake, correction.\n"
        "Tailor content for a Persian-speaking B1 learner preparing for academic English and TOEFL."
    )


def parse_reading_analysis(raw_reply: str) -> dict:
    match = READING_ANALYSIS_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse reading analysis from AI response")

    intro = READING_ANALYSIS_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse reading analysis JSON") from exc

    vocabulary = []
    for entry in data.get("vocabulary", []):
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        vocabulary.append(
            {
                "word": word,
                "definition": (entry.get("definition") or "").strip(),
                "persian": (entry.get("persian") or entry.get("persian_meaning") or "").strip(),
            }
        )

    grammar_points = []
    for entry in data.get("grammar_points", []):
        point = (entry.get("point") or "").strip()
        if not point:
            continue
        grammar_points.append(
            {
                "point": point,
                "example": (entry.get("example") or "").strip(),
                "persian": (entry.get("persian") or "").strip(),
            }
        )

    return {
        "intro": intro,
        "vocabulary": vocabulary,
        "main_idea": (data.get("main_idea") or "").strip(),
        "summary": (data.get("summary") or "").strip(),
        "comprehension_questions": [
            q.strip() for q in data.get("comprehension_questions", []) if str(q).strip()
        ],
        "grammar_points": grammar_points,
        "speaking_questions": [
            q.strip() for q in data.get("speaking_questions", []) if str(q).strip()
        ],
    }


def analyze_reading(passage: str, provider: str | None = None) -> dict:
    raw_reply = generate_from_template("reading_coach", passage, provider=provider)
    return parse_reading_analysis(raw_reply)


def build_reading_quiz_user_message(
    passage: str,
    level: str = "B1",
    question_focus: str = "mixed",
) -> str:
    from tutor.prompts.reading_coach import (
        FOCUS_INSTRUCTIONS,
        LEVEL_INSTRUCTIONS,
    )

    level_text = LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["B1"])
    focus_text = FOCUS_INSTRUCTIONS.get(question_focus, FOCUS_INSTRUCTIONS["mixed"])
    return (
        f"Reading level: {level}\n"
        f"{level_text}\n\n"
        f"Question focus: {question_focus}\n"
        f"{focus_text}\n\n"
        f"Passage:\n{passage.strip()}"
    )


def parse_reading_quiz(raw_reply: str) -> dict:
    match = READING_QUIZ_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse reading quiz from AI response")

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse reading quiz JSON") from exc

    questions = []
    for index, entry in enumerate(data.get("questions", []), start=1):
        question_text = (entry.get("question") or "").strip()
        options = [str(option).strip() for option in entry.get("options", []) if str(option).strip()]
        if not question_text or len(options) != 4:
            continue

        try:
            correct_index = int(entry.get("correct_index"))
        except (TypeError, ValueError):
            continue
        if correct_index not in range(4):
            continue

        questions.append(
            {
                "id": (entry.get("id") or f"q{index}").strip(),
                "question": question_text,
                "options": options,
                "correct_index": correct_index,
                "focus": (entry.get("focus") or "mixed").strip(),
                "explanation": (entry.get("explanation") or "").strip(),
            }
        )

    if len(questions) < 4:
        raise ValueError("Reading quiz must include at least 4 valid multiple-choice questions")

    return {"questions": questions}


def generate_reading_quiz(
    user,
    passage: str,
    level: str = "B1",
    question_focus: str = "mixed",
    provider: str | None = None,
) -> dict:
    import uuid

    from django.core.cache import cache

    user_message = build_reading_quiz_user_message(passage, level, question_focus)
    raw_reply = generate_from_template("reading_quiz", user_message, provider=provider)
    parsed = parse_reading_quiz(raw_reply)
    quiz_id = str(uuid.uuid4())
    cache.set(
        f"reading_quiz:{user.id}:{quiz_id}",
        {
            "passage": passage.strip(),
            "level": level,
            "question_focus": question_focus,
            "questions": parsed["questions"],
        },
        timeout=3600,
    )
    return {
        "quiz_id": quiz_id,
        "level": level,
        "question_focus": question_focus,
        "questions": [
            {
                "id": question["id"],
                "question": question["question"],
                "options": question["options"],
                "focus": question["focus"],
            }
            for question in parsed["questions"]
        ],
    }


def score_reading_quiz(user, quiz_id: str, answers: dict) -> dict:
    from django.core.cache import cache

    from tutor.utils.mistake_classification import MISTAKE_CATEGORY_READING

    cache_key = f"reading_quiz:{user.id}:{quiz_id}"
    quiz_data = cache.get(cache_key)
    if not quiz_data:
        raise ValueError("Quiz expired or not found. Please generate a new quiz.")

    results = []
    mistakes = []
    correct_count = 0

    for question in quiz_data["questions"]:
        question_id = question["id"]
        selected_index = answers.get(question_id)
        try:
            selected_index = int(selected_index)
        except (TypeError, ValueError):
            selected_index = None

        correct_index = question["correct_index"]
        is_correct = selected_index == correct_index
        if is_correct:
            correct_count += 1

        selected_text = (
            question["options"][selected_index]
            if selected_index in range(4)
            else "No answer"
        )
        correct_text = question["options"][correct_index]
        explanation = question.get("explanation") or (
            f"The correct answer is: {correct_text}"
        )

        result = {
            "id": question_id,
            "question": question["question"],
            "selected_index": selected_index,
            "correct_index": correct_index,
            "selected_text": selected_text,
            "correct_text": correct_text,
            "is_correct": is_correct,
            "explanation": explanation,
        }
        results.append(result)

        if not is_correct:
            mistakes.append(
                {
                    "wrong_text": f"{question['question']} — Selected: {selected_text}",
                    "correct_text": correct_text,
                    "reason": explanation,
                    "persian_explanation": "",
                    "review_sentence": quiz_data["passage"][:500],
                    "category": MISTAKE_CATEGORY_READING,
                }
            )

    if mistakes:
        save_mistakes(user, "reading_coach", mistakes)

    total = len(quiz_data["questions"])
    cache.delete(cache_key)

    return {
        "score": {
            "correct": correct_count,
            "total": total,
            "percent": round((correct_count / total) * 100) if total else 0,
        },
        "results": results,
        "mistakes_saved": len(mistakes),
    }


def parse_listening_analysis(raw_reply: str) -> dict:
    match = LISTENING_ANALYSIS_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse listening analysis from AI response")

    intro = LISTENING_ANALYSIS_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse listening analysis JSON") from exc

    vocabulary = []
    for entry in data.get("vocabulary", []):
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        vocabulary.append(
            {
                "word": word,
                "definition": (entry.get("definition") or "").strip(),
                "persian": (
                    entry.get("persian") or entry.get("persian_meaning") or ""
                ).strip(),
            }
        )

    questions = []
    for entry in data.get("comprehension_questions", []):
        if isinstance(entry, str):
            q = entry.strip()
            if q:
                questions.append({"question": q, "answer_hint": ""})
        elif isinstance(entry, dict):
            q = (entry.get("question") or "").strip()
            if q:
                questions.append(
                    {
                        "question": q,
                        "answer_hint": (entry.get("answer_hint") or "").strip(),
                    }
                )

    key_phrases = []
    for entry in data.get("key_phrases", []):
        phrase = (entry.get("phrase") or "").strip()
        if phrase:
            key_phrases.append(
                {
                    "phrase": phrase,
                    "meaning": (entry.get("meaning") or "").strip(),
                    "persian": (entry.get("persian") or "").strip(),
                }
            )

    return {
        "intro": intro,
        "comprehension_questions": questions,
        "vocabulary": vocabulary,
        "shadowing_sentences": [
            s.strip()
            for s in data.get("shadowing_sentences", [])
            if str(s).strip()
        ],
        "key_phrases": key_phrases,
    }


def analyze_listening(transcript: str, provider: str | None = None) -> dict:
    raw_reply = generate_from_template("listening_coach", transcript, provider=provider)
    return parse_listening_analysis(raw_reply)


def build_listening_quiz_user_message(
    transcript: str,
    level: str = "B1",
    question_focus: str = "mixed",
) -> str:
    from tutor.prompts.listening_coach import (
        LISTENING_FOCUS_INSTRUCTIONS,
        LISTENING_LEVEL_INSTRUCTIONS,
    )

    level_text = LISTENING_LEVEL_INSTRUCTIONS.get(level, LISTENING_LEVEL_INSTRUCTIONS["B1"])
    focus_text = LISTENING_FOCUS_INSTRUCTIONS.get(
        question_focus,
        LISTENING_FOCUS_INSTRUCTIONS["mixed"],
    )
    return (
        f"Listening level: {level}\n"
        f"{level_text}\n\n"
        f"Question focus: {question_focus}\n"
        f"{focus_text}\n\n"
        f"Transcript:\n{transcript.strip()}"
    )


def parse_listening_quiz(raw_reply: str) -> dict:
    match = LISTENING_QUIZ_PATTERN.search(raw_reply)
    if not match:
        raise ValueError("Could not parse listening quiz from AI response")

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse listening quiz JSON") from exc

    questions = []
    for index, entry in enumerate(data.get("questions", []), start=1):
        question_text = (entry.get("question") or "").strip()
        options = [str(option).strip() for option in entry.get("options", []) if str(option).strip()]
        if not question_text or len(options) != 4:
            continue

        try:
            correct_index = int(entry.get("correct_index"))
        except (TypeError, ValueError):
            continue
        if correct_index not in range(4):
            continue

        questions.append(
            {
                "id": (entry.get("id") or f"q{index}").strip(),
                "question": question_text,
                "options": options,
                "correct_index": correct_index,
                "focus": (entry.get("focus") or "mixed").strip(),
                "explanation": (entry.get("explanation") or "").strip(),
            }
        )

    if len(questions) < 4:
        raise ValueError("Listening quiz must include at least 4 valid multiple-choice questions")

    shadowing_sentences = [
        sentence.strip()
        for sentence in data.get("shadowing_sentences", [])
        if str(sentence).strip()
    ]

    return {
        "questions": questions,
        "shadowing_sentences": shadowing_sentences[:3],
    }


def generate_listening_quiz(
    user,
    *,
    transcript: str = "",
    audio_bytes: bytes | None = None,
    audio_name: str = "audio.webm",
    transcription_provider: str | None = None,
    provider: str | None = None,
    level: str = "B1",
    question_focus: str = "mixed",
) -> dict:
    import uuid

    from django.core.cache import cache

    from tutor.voice import transcribe_audio

    resolved_transcript = (transcript or "").strip()
    source = "transcript"

    if audio_bytes:
        resolved_transcript = transcribe_audio(
            audio_bytes,
            audio_name,
            provider=transcription_provider,
        ).strip()
        source = "audio"

    if not resolved_transcript:
        raise ValueError("No transcript available. Upload audio or paste a transcript.")

    user_message = build_listening_quiz_user_message(
        resolved_transcript,
        level,
        question_focus,
    )
    raw_reply = generate_from_template("listening_quiz", user_message, provider=provider)
    parsed = parse_listening_quiz(raw_reply)
    quiz_id = str(uuid.uuid4())
    cache.set(
        f"listening_quiz:{user.id}:{quiz_id}",
        {
            "transcript": resolved_transcript,
            "level": level,
            "question_focus": question_focus,
            "source": source,
            "questions": parsed["questions"],
            "shadowing_sentences": parsed["shadowing_sentences"],
        },
        timeout=3600,
    )
    return {
        "quiz_id": quiz_id,
        "level": level,
        "question_focus": question_focus,
        "source": source,
        "questions": [
            {
                "id": question["id"],
                "question": question["question"],
                "options": question["options"],
                "focus": question["focus"],
            }
            for question in parsed["questions"]
        ],
    }


def score_listening_quiz(user, quiz_id: str, answers: dict) -> dict:
    from django.core.cache import cache

    from tutor.utils.mistake_classification import MISTAKE_CATEGORY_LISTENING

    cache_key = f"listening_quiz:{user.id}:{quiz_id}"
    quiz_data = cache.get(cache_key)
    if not quiz_data:
        raise ValueError("Quiz expired or not found. Please generate a new quiz.")

    results = []
    mistakes = []
    correct_count = 0

    for question in quiz_data["questions"]:
        question_id = question["id"]
        selected_index = answers.get(question_id)
        try:
            selected_index = int(selected_index)
        except (TypeError, ValueError):
            selected_index = None

        correct_index = question["correct_index"]
        is_correct = selected_index == correct_index
        if is_correct:
            correct_count += 1

        selected_text = (
            question["options"][selected_index]
            if selected_index in range(4)
            else "No answer"
        )
        correct_text = question["options"][correct_index]
        explanation = question.get("explanation") or (
            f"The correct answer is: {correct_text}"
        )

        result = {
            "id": question_id,
            "question": question["question"],
            "selected_index": selected_index,
            "correct_index": correct_index,
            "selected_text": selected_text,
            "correct_text": correct_text,
            "is_correct": is_correct,
            "explanation": explanation,
        }
        results.append(result)

        if not is_correct:
            mistakes.append(
                {
                    "wrong_text": f"{question['question']} — Selected: {selected_text}",
                    "correct_text": correct_text,
                    "reason": explanation,
                    "persian_explanation": "",
                    "review_sentence": quiz_data["transcript"][:500],
                    "category": MISTAKE_CATEGORY_LISTENING,
                }
            )

    if mistakes:
        save_mistakes(user, "listening_coach", mistakes)

    total = len(quiz_data["questions"])
    response = {
        "score": {
            "correct": correct_count,
            "total": total,
            "percent": round((correct_count / total) * 100) if total else 0,
        },
        "results": results,
        "mistakes_saved": len(mistakes),
        "transcript": quiz_data["transcript"],
        "shadowing_sentences": quiz_data.get("shadowing_sentences", []),
    }
    cache.delete(cache_key)
    return response


def parse_toefl_writing_feedback(raw_reply: str) -> tuple[str, dict | None]:
    match = TOEFL_WRITING_FEEDBACK_PATTERN.search(raw_reply)
    if not match:
        return raw_reply.strip(), None

    reply = TOEFL_WRITING_FEEDBACK_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return reply, None

    return reply, {
        "estimated_toefl_score": data.get("estimated_toefl_score"),
        "scores": _normalize_writing_rubric(data.get("scores") or {}),
        "rubric_details": _normalize_writing_rubric(data.get("rubric_details") or {}),
        "feedback": (data.get("feedback") or "").strip(),
        "persian_summary": (data.get("persian_summary") or "").strip(),
        "strengths": [s for s in data.get("strengths", []) if str(s).strip()],
        "improvements": [s for s in data.get("improvements", []) if str(s).strip()],
        "main_mistakes": _coerce_main_mistakes(data.get("main_mistakes")),
        "sentence_corrections": data.get("sentence_corrections") or [],
        "corrected_version": (data.get("corrected_version") or "").strip(),
        "natural_version": (data.get("natural_version") or "").strip(),
        "high_score_sample": (data.get("high_score_sample") or "").strip(),
        "next_task": (data.get("next_task") or data.get("recommended_revision_task") or "").strip(),
        "recommended_revision_task": (
            data.get("recommended_revision_task") or data.get("next_task") or ""
        ).strip(),
    }


def _collect_feedback_mistakes(feedback: dict | None) -> list[dict]:
    if not feedback:
        return []

    payloads = []
    seen = set()

    def add_mistake(entry):
        normalized = normalize_correction(entry)
        if not normalized:
            return
        key = normalized["wrong_text"]
        if key in seen:
            return
        seen.add(key)
        payloads.append(normalized)

    for mistake in feedback.get("main_mistakes") or []:
        if isinstance(mistake, dict):
            add_mistake(mistake)

    for row in feedback.get("sentence_corrections") or []:
        if isinstance(row, dict):
            add_mistake(
                {
                    "original": row.get("original"),
                    "corrected": row.get("corrected"),
                    "reason": row.get("why") or row.get("reason"),
                }
            )

    return payloads


def persist_writing_feedback_mistakes(user, track: str, feedback: dict | None) -> None:
    payloads = _collect_feedback_mistakes(feedback)
    if payloads:
        save_mistakes(user, track, payloads)


def parse_writing_feedback(raw_reply: str) -> tuple[str, dict | None]:
    from tutor.writing_evaluation import parse_writing_evaluator_response

    reply, feedback = parse_writing_evaluator_response(raw_reply)
    if feedback:
        return reply, feedback

    match = WRITING_FEEDBACK_PATTERN.search(raw_reply)
    if not match:
        return raw_reply.strip(), None

    reply = WRITING_FEEDBACK_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return reply, None

    recommended = (
        data.get("recommended_revision_task") or data.get("next_task") or ""
    ).strip()

    return reply, {
        "overall_score": data.get("overall_score"),
        "word_count_note": (data.get("word_count_note") or "").strip(),
        "positive_comment": (data.get("positive_comment") or "").strip(),
        "main_problem": (data.get("main_problem") or "").strip(),
        "rubric": _normalize_writing_rubric(data.get("rubric") or {}),
        "main_mistakes": _coerce_main_mistakes(data.get("main_mistakes")),
        "corrected_version": (data.get("corrected_version") or "").strip(),
        "natural_version": (data.get("natural_version") or "").strip(),
        "high_score_sample": (data.get("high_score_sample") or "").strip(),
        "useful_phrases": [s for s in data.get("useful_phrases", []) if str(s).strip()],
        "next_task": recommended,
        "recommended_revision_task": recommended,
        "sentence_corrections": data.get("sentence_corrections") or [],
    }


def parse_toefl_speaking_feedback(raw_reply: str) -> tuple[str, dict | None]:
    match = TOEFL_SPEAKING_FEEDBACK_PATTERN.search(raw_reply)
    if not match:
        return raw_reply.strip(), None

    reply = TOEFL_SPEAKING_FEEDBACK_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return reply, None

    return reply, {
        "scores": data.get("scores", {}),
        "feedback": (data.get("feedback") or "").strip(),
        "persian_summary": (data.get("persian_summary") or "").strip(),
        "sample_improvement": (data.get("sample_improvement") or "").strip(),
    }


def parse_speaking_feedback(raw_reply: str) -> tuple[str, dict | None]:
    from tutor.speaking_evaluation import parse_evaluator_response

    reply, feedback = parse_evaluator_response(raw_reply)
    if feedback:
        return reply, feedback

    match = SPEAKING_FEEDBACK_PATTERN.search(raw_reply)
    if not match:
        return raw_reply.strip(), None

    reply = SPEAKING_FEEDBACK_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return reply, None

    rubric = _normalize_speaking_rubric(data.get("rubric") or {})
    breakdown = _speaking_rubric_to_breakdown(rubric, data.get("breakdown") or {})
    model_answer = (data.get("model_answer") or data.get("natural_version") or "").strip()
    repeat_task = (
        data.get("repeat_task_recommendation") or data.get("recommended_next_task") or ""
    ).strip()

    return reply, {
        "overall_score": data.get("overall_score"),
        "cefr_estimate": (data.get("cefr_estimate") or "").strip(),
        "input_mode": (data.get("input_mode") or "").strip(),
        "pronunciation_limited": bool(data.get("pronunciation_limited", True)),
        "pronunciation_notes": (data.get("pronunciation_notes") or "").strip(),
        "rubric": rubric,
        "breakdown": breakdown,
        "corrected_version": (data.get("corrected_version") or "").strip(),
        "model_answer": model_answer,
        "natural_version": (data.get("natural_version") or model_answer).strip(),
        "repeat_answer": (data.get("repeat_answer") or "").strip(),
        "follow_up_question": (data.get("follow_up_question") or "").strip(),
        "recommended_next_task": repeat_task,
        "repeat_task_recommendation": repeat_task,
        "positive_comment": (data.get("positive_comment") or "").strip(),
        "main_issues": [s for s in data.get("main_issues", []) if str(s).strip()],
        "main_mistakes": _coerce_speaking_main_mistakes(data.get("main_mistakes")),
        "vocabulary_upgrades": data.get("vocabulary_upgrades") or [],
    }


SPEAKING_RUBRIC_ALIASES = {
    "pronunciation_clarity": "fluency",
    "intonation_rhythm": "fluency",
    "task_completion": "organization",
}


def _normalize_speaking_rubric(rubric: dict | None) -> dict:
    if not isinstance(rubric, dict):
        return {}
    normalized: dict = {}
    for key, value in rubric.items():
        new_key = SPEAKING_RUBRIC_ALIASES.get(key, key)
        if new_key not in normalized:
            normalized[new_key] = value
    return normalized


def _speaking_rubric_to_breakdown(rubric: dict, legacy_breakdown: dict) -> dict:
    breakdown = {}
    for key in ("fluency", "grammar", "vocabulary", "organization"):
        item = rubric.get(key)
        if isinstance(item, dict) and item.get("score") is not None:
            breakdown[key] = item["score"]
        elif key in legacy_breakdown:
            breakdown[key] = legacy_breakdown[key]
        elif key == "fluency" and legacy_breakdown.get("pronunciation_clarity") is not None:
            breakdown[key] = legacy_breakdown["pronunciation_clarity"]
        elif key == "organization" and legacy_breakdown.get("task_completion") is not None:
            breakdown[key] = legacy_breakdown["task_completion"]
    return breakdown


def _coerce_speaking_main_mistakes(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    rows = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        wrong = (entry.get("wrong") or entry.get("original") or "").strip()
        correct = (entry.get("correct") or entry.get("corrected") or "").strip()
        reason = (entry.get("reason") or entry.get("why") or "").strip()
        area = (entry.get("area") or entry.get("category") or "").strip().lower()
        if wrong:
            rows.append(
                {
                    "area": area,
                    "wrong": wrong,
                    "correct": correct,
                    "reason": reason,
                }
            )
    return rows


SPEAKING_MISTAKE_AREAS = frozenset({"grammar", "vocabulary", "organization"})


def _collect_speaking_mistake_payloads(feedback: dict | None) -> list[dict]:
    if not feedback:
        return []

    payloads = []
    seen = set()

    def add_payload(wrong, correct, reason, area=""):
        normalized = normalize_correction(
            {"wrong": wrong, "correct": correct, "reason": reason}
        )
        if not normalized:
            return
        key = normalized["wrong_text"]
        if key in seen:
            return
        seen.add(key)
        if area == "grammar":
            normalized["category"] = "sentence_structure"
        elif area == "vocabulary":
            normalized["category"] = "vocabulary_precision"
        elif area == "organization":
            normalized["category"] = "speaking_organization"
        payloads.append(normalized)

    for mistake in feedback.get("main_mistakes") or []:
        area = (mistake.get("area") or "").lower()
        if area not in SPEAKING_MISTAKE_AREAS:
            continue
        add_payload(
            mistake.get("wrong"),
            mistake.get("correct"),
            mistake.get("reason"),
            area=area,
        )

    for upgrade in feedback.get("vocabulary_upgrades") or []:
        if not isinstance(upgrade, dict):
            continue
        instead_of = (upgrade.get("instead_of") or "").strip()
        options = upgrade.get("try") or []
        correct = options[0].strip() if options else ""
        if instead_of:
            add_payload(
                instead_of,
                correct,
                "Vocabulary upgrade suggestion",
                area="vocabulary",
            )

    return payloads


def persist_speaking_feedback_mistakes(user, track: str, feedback: dict | None) -> None:
    payloads = _collect_speaking_mistake_payloads(feedback)
    if payloads:
        save_mistakes(user, track, payloads)


def format_speaking_message(scenario: str | None, message: str) -> str:
    if scenario:
        return f"Scenario: {scenario}\n\n{message}"
    return message


def format_speaking_evaluation_message(
    *,
    level: str,
    task_type: str,
    task_title: str,
    task_prompt: str,
    student_answer: str,
    input_mode: str = "voice",
    article_text: str = "",
    evaluation_focus: list | None = None,
    follow_up: bool = False,
    previous_answer: str = "",
    evaluation_mode: str = "normal",
    speaking_time: int | None = None,
    prep_time: int | None = None,
) -> str:
    from tutor.speaking_evaluation import build_evaluator_user_message

    return build_evaluator_user_message(
        evaluation_mode=evaluation_mode,
        task_prompt=task_prompt or task_title or task_type,
        transcript=student_answer,
        input_mode=input_mode,
        speaking_level=level,
        speaking_time=speaking_time,
        prep_time=prep_time,
        practice_type=task_type,
        task_title=task_title,
        article_text=article_text,
        evaluation_focus=evaluation_focus,
    )


def build_writing_revision_message(
    *,
    prompt: str = "",
    original_answer: str,
    revised_answer: str,
) -> str:
    lines = [
        "[Writing Revision Compare]",
        f"Original prompt: {prompt.strip() or 'Not provided'}",
        "",
        "Original answer:",
        original_answer.strip(),
        "",
        "Revised answer:",
        revised_answer.strip(),
    ]
    return "\n".join(lines)


def parse_writing_revision_compare(raw_reply: str) -> tuple[str, dict | None]:
    match = WRITING_REVISION_COMPARE_PATTERN.search(raw_reply)
    if not match:
        return raw_reply.strip(), None

    reply = WRITING_REVISION_COMPARE_PATTERN.sub("", raw_reply).strip()
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return reply, None

    return reply, {
        "improvement_summary": (data.get("improvement_summary") or "").strip(),
        "improvements": [s for s in data.get("improvements", []) if str(s).strip()],
        "remaining_issues": [s for s in data.get("remaining_issues", []) if str(s).strip()],
        "score_change_note": (data.get("score_change_note") or "").strip(),
    }


def run_writing_revision_compare(
    *,
    original_answer: str,
    revised_answer: str,
    prompt: str = "",
    provider: str | None = None,
) -> dict:
    user_message = build_writing_revision_message(
        prompt=prompt,
        original_answer=original_answer,
        revised_answer=revised_answer,
    )
    raw_reply = generate_from_template(
        "writing_revision_compare",
        user_message,
        provider=provider,
    )
    reply, comparison = parse_writing_revision_compare(raw_reply)
    return {
        "reply": reply,
        "comparison": comparison,
    }


def run_task(
    task_type: str,
    user_message: str,
    user,
    session: PracticeSession,
    provider: str | None = None,
    scenario: str | None = None,
) -> dict:
    if task_type in ("writing_coach", "toefl_writing"):
        import re

        from tutor.writing_evaluation import run_writing_evaluation

        mode_match = re.search(r"User mode:\s*(\w+)", user_message)
        evaluation_mode = mode_match.group(1) if mode_match else "normal"
        return run_writing_evaluation(
            user=user,
            session=session,
            eval_message=user_message,
            provider=provider,
            task_type=task_type,
            evaluation_mode=evaluation_mode,
        )

    if task_type == "speaking_coach":
        import re

        from tutor.speaking_evaluation import run_speaking_evaluation

        mode_match = re.search(r"User mode:\s*(\w+)", user_message)
        evaluation_mode = mode_match.group(1) if mode_match else "normal"
        input_mode = "typed" if "Input mode: typed" in user_message else "voice"
        return run_speaking_evaluation(
            user=user,
            session=session,
            eval_message=user_message,
            provider=provider,
            scenario=scenario,
            evaluation_mode=evaluation_mode,
            input_mode=input_mode,
        )

    template = get_prompt_template(task_type, provider)
    history = [
        {"role": message.role, "content": message.content}
        for message in session.messages.order_by("created_at")
        if message.role in ("user", "assistant")
    ]
    content = format_speaking_message(scenario, user_message)
    messages = [*history, {"role": "user", "content": content}]

    raw_reply = call_provider(template, messages)
    reply, corrections = parse_corrections(raw_reply)

    toefl_writing_feedback = None
    toefl_speaking_feedback = None
    speaking_feedback = None
    writing_feedback = None

    if task_type == "toefl_writing":
        reply, toefl_writing_feedback = parse_toefl_writing_feedback(raw_reply)
    elif task_type == "toefl_speaking":
        reply, toefl_speaking_feedback = parse_toefl_speaking_feedback(raw_reply)
    elif task_type == "writing_coach":
        parsed_reply, writing_feedback = parse_writing_feedback(raw_reply)
        if writing_feedback:
            reply = parsed_reply

    Message.objects.create(session=session, role="user", content=user_message)
    Message.objects.create(session=session, role="assistant", content=reply)

    if corrections:
        save_mistakes(user, session.track, corrections)
    if writing_feedback:
        persist_writing_feedback_mistakes(user, session.track, writing_feedback)
    if toefl_writing_feedback:
        persist_writing_feedback_mistakes(user, session.track, toefl_writing_feedback)
    if speaking_feedback:
        persist_speaking_feedback_mistakes(user, session.track, speaking_feedback)

    result = {
        "reply": reply,
        "corrections": [correction_to_api(c) for c in corrections],
    }
    if toefl_writing_feedback:
        result["toefl_feedback"] = toefl_writing_feedback
    if toefl_speaking_feedback:
        result["toefl_feedback"] = toefl_speaking_feedback
    if speaking_feedback:
        result["speaking_feedback"] = speaking_feedback
    if writing_feedback:
        result["writing_feedback"] = writing_feedback

    return result


WRITING_EDIT_JSON_PATTERN = re.compile(r"\{[\s\S]*\}", re.DOTALL)


def _coerce_string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_sentence_comparisons(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    rows = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        original = (entry.get("original") or "").strip()
        improved = (entry.get("improved") or entry.get("corrected") or "").strip()
        reason = (entry.get("reason") or entry.get("why") or "").strip()
        if original or improved:
            rows.append({"original": original, "improved": improved, "reason": reason})
    return rows


def parse_writing_edit_response(raw_reply: str) -> dict:
    text = (raw_reply or "").strip()
    cleaned = text
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    data = None
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = WRITING_EDIT_JSON_PATTERN.search(cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, dict):
        fallback_text = cleaned or text
        return {
            "edited_text": fallback_text,
            "changes": [],
            "teaching_notes": [],
            "sentence_comparisons": [],
            "level_feedback": "",
            "better_alternative": "",
            "structured": False,
            "notice": (
                "The AI response was not fully structured, but here is the edited version."
            ),
        }

    edited_text = (data.get("edited_text") or data.get("corrected_text") or "").strip()
    if not edited_text:
        edited_text = cleaned or text

    return {
        "edited_text": edited_text,
        "changes": _coerce_string_list(data.get("changes")),
        "teaching_notes": _coerce_string_list(data.get("teaching_notes")),
        "sentence_comparisons": _coerce_sentence_comparisons(
            data.get("sentence_comparisons")
        ),
        "level_feedback": (data.get("level_feedback") or "").strip(),
        "better_alternative": (data.get("better_alternative") or "").strip(),
        "structured": True,
        "notice": None,
    }


def run_writing_edit(
    *,
    text: str,
    edit_strength: str,
    target_style: str,
    language_level: str = "normal",
    user,
    provider: str | None = None,
) -> dict:
    from tutor.prompts.writing_edit import (
        build_writing_edit_user_message,
        normalize_edit_strength,
        normalize_language_level,
        normalize_target_style,
    )

    strength = normalize_edit_strength(edit_strength)
    style = normalize_target_style(target_style)
    lang = normalize_language_level(language_level)
    user_message = build_writing_edit_user_message(text, strength, style, lang)
    raw_reply = generate_from_template("writing_edit_coach", user_message, provider=provider)
    result = parse_writing_edit_response(raw_reply)

    corrections = []
    for row in result["sentence_comparisons"]:
        if row["original"] and row["improved"]:
            corrections.append(
                {
                    "wrong_text": row["original"],
                    "correct_text": row["improved"],
                    "reason": row["reason"],
                    "persian_explanation": "",
                    "review_sentence": "",
                }
            )

    if corrections:
        save_mistakes(user, "writing_edit_coach", corrections)

    return {
        **result,
        "edit_strength": strength,
        "target_style": style,
        "language_level": lang,
    }


def parse_writing_edit_generate_response(raw_reply: str) -> dict:
    data = _parse_json_object(raw_reply)
    if not data:
        fallback = (raw_reply or "").strip()
        return {
            "draft_text": fallback,
            "teaching_tip": "",
            "structured": False,
            "notice": (
                "The AI response was not fully structured, but here is the generated text."
            ),
        }

    draft = (data.get("draft_text") or data.get("text") or "").strip()
    return {
        "draft_text": draft,
        "teaching_tip": (data.get("teaching_tip") or "").strip(),
        "structured": bool(draft),
        "notice": None if draft else (
            "The AI response was not fully structured, but here is the generated text."
        ),
    }


def run_writing_edit_generate(
    *,
    target_style: str,
    language_level: str = "normal",
    provider: str | None = None,
) -> dict:
    from tutor.prompts.writing_edit import (
        build_writing_edit_generate_message,
        normalize_language_level,
        normalize_target_style,
    )

    style = normalize_target_style(target_style)
    lang = normalize_language_level(language_level)
    user_message = build_writing_edit_generate_message(style, lang)
    raw_reply = generate_from_template(
        "writing_edit_generate", user_message, provider=provider
    )
    result = parse_writing_edit_generate_response(raw_reply)
    return {
        **result,
        "target_style": style,
        "language_level": lang,
    }


def _parse_json_object(raw_reply: str) -> dict | None:
    text = (raw_reply or "").strip()
    cleaned = text
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = WRITING_EDIT_JSON_PATTERN.search(cleaned)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return None


def _coerce_score(value, default=0) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, score))


def paraphrase_result_label(overall_score: int) -> str:
    if overall_score >= 90:
        return "Excellent paraphrase"
    if overall_score >= 75:
        return "Good paraphrase"
    if overall_score >= 60:
        return "Needs improvement"
    return "Try again"


def parse_paraphrase_generate_response(raw_reply: str) -> dict:
    data = _parse_json_object(raw_reply)
    if not data:
        fallback = (raw_reply or "").strip()
        return {
            "original_text": fallback,
            "teaching_tip": "",
            "structured": False,
            "notice": (
                "The AI response was not fully structured, but here is the generated text."
            ),
        }

    original = (data.get("original_text") or data.get("text") or "").strip()
    return {
        "original_text": original,
        "teaching_tip": (data.get("teaching_tip") or "").strip(),
        "structured": bool(original),
        "notice": None if original else (
            "The AI response was not fully structured, but here is the generated text."
        ),
    }


def parse_paraphrase_check_response(
    raw_reply: str,
    *,
    original_text: str,
    learner_paraphrase: str,
) -> dict:
    data = _parse_json_object(raw_reply)
    if not data:
        return {
            "overall_score": 0,
            "meaning_accuracy_score": 0,
            "grammar_score": 0,
            "naturalness_score": 0,
            "vocabulary_score": 0,
            "level_match_score": 0,
            "result_label": "Try again",
            "language_level_feedback": "",
            "feedback": [],
            "better_version": learner_paraphrase,
            "comparison": {
                "original": original_text,
                "learner_paraphrase": learner_paraphrase,
                "better_paraphrase": learner_paraphrase,
            },
            "teaching_notes": [],
            "structured": False,
            "notice": (
                "The AI response was not fully structured, but here is the available feedback."
            ),
        }

    comparison = data.get("comparison") if isinstance(data.get("comparison"), dict) else {}
    overall = _coerce_score(data.get("overall_score"))

    return {
        "overall_score": overall,
        "meaning_accuracy_score": _coerce_score(data.get("meaning_accuracy_score")),
        "grammar_score": _coerce_score(data.get("grammar_score")),
        "naturalness_score": _coerce_score(data.get("naturalness_score")),
        "vocabulary_score": _coerce_score(data.get("vocabulary_score")),
        "level_match_score": _coerce_score(data.get("level_match_score")),
        "result_label": (data.get("result_label") or paraphrase_result_label(overall)).strip(),
        "language_level_feedback": (
            data.get("language_level_feedback") or ""
        ).strip(),
        "feedback": _coerce_string_list(data.get("feedback")),
        "better_version": (data.get("better_version") or "").strip(),
        "comparison": {
            "original": (comparison.get("original") or original_text).strip(),
            "learner_paraphrase": (
                comparison.get("learner_paraphrase") or learner_paraphrase
            ).strip(),
            "better_paraphrase": (
                comparison.get("better_paraphrase")
                or data.get("better_version")
                or ""
            ).strip(),
        },
        "teaching_notes": _coerce_string_list(data.get("teaching_notes")),
        "structured": True,
        "notice": None,
    }


def run_paraphrase_generate(
    *,
    target_level: str,
    difficulty: str,
    text_type: str,
    language_level: str = "normal",
    provider: str | None = None,
) -> dict:
    from tutor.prompts.writing_paraphrase import (
        build_paraphrase_generate_message,
        normalize_difficulty,
        normalize_language_level,
        normalize_target_level,
        normalize_text_type,
    )

    level = normalize_target_level(target_level)
    diff = normalize_difficulty(difficulty)
    ttype = normalize_text_type(text_type)
    lang = normalize_language_level(language_level)
    user_message = build_paraphrase_generate_message(level, diff, ttype, lang)
    raw_reply = generate_from_template(
        "writing_paraphrase_generate", user_message, provider=provider
    )
    result = parse_paraphrase_generate_response(raw_reply)
    return {
        **result,
        "target_level": level,
        "difficulty": diff,
        "text_type": ttype,
        "language_level": lang,
    }


def run_paraphrase_check(
    *,
    target_level: str,
    original_text: str,
    learner_paraphrase: str,
    language_level: str = "normal",
    user,
    provider: str | None = None,
) -> dict:
    from tutor.prompts.writing_paraphrase import (
        build_paraphrase_check_message,
        normalize_language_level,
        normalize_target_level,
    )

    level = normalize_target_level(target_level)
    lang = normalize_language_level(language_level)
    user_message = build_paraphrase_check_message(
        level, lang, original_text, learner_paraphrase
    )
    raw_reply = generate_from_template(
        "writing_paraphrase_check", user_message, provider=provider
    )
    result = parse_paraphrase_check_response(
        raw_reply,
        original_text=original_text,
        learner_paraphrase=learner_paraphrase,
    )

    if result.get("better_version") and result.get("comparison", {}).get("better_paraphrase"):
        better = result["comparison"]["better_paraphrase"]
        if result["better_version"] != better and not result["better_version"]:
            result["better_version"] = better

    # Save important paraphrase mistakes when meaning/grammar issues appear
    corrections = []
    for note in result.get("feedback", []):
        if any(
            keyword in note.lower()
            for keyword in ("grammar", "meaning", "incorrect", "wrong", "changed")
        ):
            if original_text and learner_paraphrase:
                corrections.append(
                    {
                        "wrong_text": learner_paraphrase[:500],
                        "correct_text": (
                            result.get("better_version")
                            or result["comparison"].get("better_paraphrase", "")
                        )[:500],
                        "reason": note[:500],
                        "persian_explanation": "",
                        "review_sentence": "",
                    }
                )
                break

    if corrections:
        save_mistakes(user, "writing_paraphrase_coach", corrections)

    return {**result, "target_level": level, "language_level": lang}
