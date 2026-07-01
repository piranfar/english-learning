import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.learning_journey import STAGE1_SLUG, STAGE2_SLUG
from tutor.models import Mistake, ReadingQuestionAttempt, ReadingSession
from tutor.reading_practice import (
    build_reading_generate_user_message,
    gather_reading_context,
    parse_reading_passage,
    resolve_passage_settings,
    score_reading_session,
)
from tutor.services import get_user_profile

User = get_user_model()

SAMPLE_PASSAGE = (
    "Universities around the world are changing how students access research. "
    "A recent study found that open libraries help learners read more academic articles. "
    "However, many students still struggle with article use in English. "
    "The researchers interviewed two hundred undergraduates and reviewed their writing. "
    "Although the students understood main ideas, they often chose the wrong article before a noun. "
    "Therefore, instructors now recommend short daily reading tasks with focused feedback. "
    "In contrast, students who practiced article patterns improved faster on timed tests. "
    "The study was published by a team at a public university in 2024. "
    "These findings suggest that targeted reading practice can support academic success. "
)

SAMPLE_READING_PAYLOAD = {
    "title": "Articles in Academic Reading",
    "level": "B1",
    "stage": STAGE1_SLUG,
    "lesson_focus": "articles",
    "topic": "Academic",
    "passage": SAMPLE_PASSAGE,
    "estimated_time_minutes": 15,
    "target_vocabulary": [
        {
            "word": "undergraduates",
            "definition": "university students who do not yet have a degree",
            "example": "The researchers interviewed two hundred undergraduates.",
        }
    ],
    "questions": [
        {
            "id": "q1",
            "type": "main_idea",
            "question": "What is the main idea of the passage?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "The passage focuses on article practice.",
            "mistake_category": "reading_comprehension",
        },
        {
            "id": "q2",
            "type": "vocabulary_in_context",
            "question": "Which article fits before 'university'?",
            "choices": ["a", "an", "the", "no article"],
            "correct_answer": "a",
            "explanation": "University starts with a consonant sound.",
            "mistake_category": "article",
        },
        {
            "id": "q3",
            "type": "detail",
            "question": "How many undergraduates were interviewed?",
            "choices": ["100", "200", "300", "400"],
            "correct_answer": "200",
            "explanation": "The passage states two hundred undergraduates.",
            "mistake_category": "reading_comprehension",
        },
        {
            "id": "q4",
            "type": "inference",
            "question": "What can be inferred about article practice?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "C",
            "explanation": "Targeted practice helped students improve.",
            "mistake_category": "reading_comprehension",
        },
    ],
}


def reading_ai_response() -> str:
    return f"---READING_PASSAGE---\n{json.dumps(SAMPLE_READING_PAYLOAD)}\n---END_READING_PASSAGE---"


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class ReadingGenerateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="readinggenuser",
            password="testpass123",
        )
        self.profile = get_user_profile(self.user)
        self.profile.weak_areas = []
        self.profile.save()
        self.client.login(username="readinggenuser", password="testpass123")

    def test_parse_reading_passage_accepts_schema(self):
        parsed = parse_reading_passage(reading_ai_response())
        self.assertEqual(parsed["title"], "Articles in Academic Reading")
        self.assertEqual(parsed["lesson_focus"], "articles")
        self.assertGreaterEqual(len(parsed["questions"]), 4)
        self.assertEqual(parsed["questions"][1]["mistake_category"], "article")

    def test_stage_settings_differ_by_stage(self):
        stage1 = resolve_passage_settings(STAGE1_SLUG, "toefl_style")
        stage2 = resolve_passage_settings(STAGE2_SLUG, "toefl_style")
        self.assertLess(stage1["word_max"], stage2["word_min"])
        self.assertLess(stage1["question_min"], stage2["question_min"])

    def test_generate_user_message_includes_lesson_focus(self):
        context = gather_reading_context(self.user)
        message = build_reading_generate_user_message(
            level="B1",
            stage=STAGE1_SLUG,
            topic="Academic",
            lesson_focus="articles",
            question_focus="mixed",
            length="medium",
            context=context,
        )
        self.assertIn("articles", message.lower())
        self.assertIn("article", message.lower())

    @patch("tutor.reading_ai_service._generate_raw_json")
    def test_generate_reading_endpoint(self, mock_generate):
        mock_generate.return_value = json.dumps(SAMPLE_READING_PAYLOAD)
        response = self.client.post(
            "/api/reading/generate/",
            {
                "level": "B1",
                "stage": STAGE1_SLUG,
                "topic": "Academic",
                "lesson_focus": "articles",
                "question_focus": "mixed",
                "length": "medium",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session = response.json()["session"]
        self.assertIn("session_id", session)
        self.assertIn("passage", session)
        self.assertNotIn("correct_answer", session["questions"][0])
        self.assertTrue(
            ReadingSession.objects.filter(user=self.user, lesson_focus="articles").exists()
        )

    @patch("tutor.reading_ai_service._generate_raw_json")
    def test_submit_saves_mistakes_and_attempts(self, mock_generate):
        mock_generate.return_value = json.dumps(SAMPLE_READING_PAYLOAD)
        generate_response = self.client.post(
            "/api/reading/generate/",
            {
                "level": "B1",
                "stage": STAGE1_SLUG,
                "lesson_focus": "articles",
            },
            format="json",
        )
        session_id = generate_response.json()["session"]["session_id"]

        submit_response = self.client.post(
            "/api/reading/submit/",
            {
                "session_id": session_id,
                "answers": {"q1": 0, "q2": 1, "q3": 2, "q4": 2},
            },
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200)
        data = submit_response.json()
        self.assertEqual(data["score"]["total"], 4)
        self.assertGreaterEqual(data["mistakes_saved"], 1)
        self.assertTrue(data["weak_question_types"])

        self.assertEqual(
            ReadingQuestionAttempt.objects.filter(session_id=session_id).count(),
            4,
        )
        article_mistakes = Mistake.objects.filter(
            user=self.user,
            track="reading_coach",
            category="article",
        )
        self.assertGreaterEqual(article_mistakes.count(), 1)

    @patch("tutor.reading_ai_service._generate_raw_json")
    def test_article_focus_metadata(self, mock_generate):
        mock_generate.return_value = json.dumps(SAMPLE_READING_PAYLOAD)
        response = self.client.post(
            "/api/reading/generate/",
            {"lesson_focus": "articles", "stage": STAGE1_SLUG},
            format="json",
        )
        session = response.json()["session"]
        self.assertEqual(session["lesson_focus"], "articles")

    def test_score_reading_session_marks_complete(self):
        session = ReadingSession.objects.create(
            user=self.user,
            title="Test",
            level="B1",
            stage=STAGE1_SLUG,
            lesson_focus="articles",
            topic="Academic",
            passage=SAMPLE_PASSAGE,
            questions_json=SAMPLE_READING_PAYLOAD["questions"],
        )
        result = score_reading_session(
            self.user,
            session.id,
            {"q1": 1, "q2": 0, "q3": 1, "q4": 2},
        )
        session.refresh_from_db()
        self.assertIsNotNone(session.completed_at)
        self.assertEqual(result["score"]["correct"], 4)

    @patch("tutor.reading_ai_service._generate_raw_json")
    def test_simulation_mode(self, mock_generate):
        mock_generate.return_value = json.dumps(SAMPLE_READING_PAYLOAD)
        response = self.client.post(
            "/api/reading/generate/",
            {
                "stage": STAGE1_SLUG,
                "reading_mode": "toefl_2026",
                "simulation_type": "academic_passage",
                "length": "toefl_style",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("TOEFL-style", response.json()["session"]["disclaimer"])

    @patch("tutor.reading_ai_service.resolve_reading_provider", return_value=None)
    def test_generate_without_ai_key_returns_friendly_error(self, _mock):
        response = self.client.post(
            "/api/reading/generate/",
            {"level": "B1", "stage": STAGE1_SLUG},
            format="json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_plan_can_include_reading_tasks(self):
        from datetime import date

        from tutor.plan import build_plan_items

        for _ in range(3):
            Mistake.objects.create(
                user=self.user,
                track="grammar_coach",
                wrong_text="I saw an book.",
                correct_text="I saw a book.",
                reason="Article error",
                category="article",
            )

        items = build_plan_items(self.user, date.today())
        reading_items = [item for item in items if item.get("type") == "reading"]
        self.assertTrue(reading_items)
        self.assertIn("article", reading_items[0]["title"].lower())
