"""Score lesson quizzes and update lesson progress."""

from __future__ import annotations

from django.utils import timezone

from tutor.lesson_quiz_bank import questions_for_topic, public_question
from tutor.models import LessonProgress, LessonTopic, Mistake
from tutor.utils.mistake_classification import classify_mistake


def lesson_quiz_payload(topic: LessonTopic) -> dict:
    questions = questions_for_topic(topic)
    if len(questions) < 4:
        raise ValueError("This lesson does not have enough quiz questions yet.")

    return {
        "topic_id": topic.id,
        "topic_title": topic.title,
        "question_count": len(questions),
        "questions": [public_question(item) for item in questions[:4]],
    }


def score_lesson_quiz(user, topic_id: int, answers: dict) -> dict:
    topic = LessonTopic.objects.filter(id=topic_id, is_active=True).first()
    if not topic:
        raise ValueError("Lesson topic not found.")

    questions = questions_for_topic(topic)[:4]
    if not questions:
        raise ValueError("This lesson does not have quiz questions.")

    results = []
    mistakes_saved = 0
    correct_count = 0

    for question in questions:
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
            if selected_index in range(len(question["options"]))
            else "No answer"
        )
        correct_text = question["options"][correct_index]
        explanation = question.get("explanation") or f"The correct answer is: {correct_text}"

        results.append(
            {
                "id": question_id,
                "question": question["question"],
                "selected_index": selected_index,
                "correct_index": correct_index,
                "selected_text": selected_text,
                "correct_text": correct_text,
                "is_correct": is_correct,
                "explanation": explanation,
            }
        )

        if is_correct:
            continue

        wrong_text = f"{question['question']} — Selected: {selected_text}"
        Mistake.objects.create(
            user=user,
            track="grammar_coach",
            wrong_text=wrong_text,
            correct_text=correct_text,
            reason=explanation,
            category=classify_mistake(
                wrong_text,
                correct_text,
                explanation,
                "grammar_coach",
            ),
        )
        mistakes_saved += 1

    total = len(questions)
    percent = round(100 * correct_count / total) if total else 0

    progress, _ = LessonProgress.objects.get_or_create(
        user=user,
        topic=topic,
        defaults={"status": LessonProgress.STATUS_STARTED},
    )
    progress.score = percent
    progress.last_practiced = timezone.now()
    progress.status = (
        LessonProgress.STATUS_COMPLETED
        if percent >= 70
        else LessonProgress.STATUS_NEEDS_REVIEW
    )
    progress.save()

    from tutor.plan_completion import auto_complete_plan_items

    plan_items_completed = auto_complete_plan_items(user, track="grammar")

    return {
        "topic_id": topic.id,
        "score": {
            "correct": correct_count,
            "total": total,
            "percent": percent,
        },
        "results": results,
        "mistakes_saved": mistakes_saved,
        "progress": {
            "topic_id": progress.topic_id,
            "status": progress.status,
            "score": progress.score,
            "notes": progress.notes,
            "last_practiced": (
                progress.last_practiced.isoformat() if progress.last_practiced else None
            ),
        },
        "plan_items_completed": plan_items_completed,
    }
