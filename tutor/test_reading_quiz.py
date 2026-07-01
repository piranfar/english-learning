import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()

SAMPLE_QUIZ_PAYLOAD = {
    "questions": [
        {
            "id": "q1",
            "question": "What is the main idea?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 1,
            "focus": "main_idea",
            "explanation": "The passage centers on renewable energy.",
        },
        {
            "id": "q2",
            "question": "Which detail is stated?",
            "options": ["A2", "B2", "C2", "D2"],
            "correct_index": 0,
            "focus": "detail",
            "explanation": "The text explicitly mentions solar panels.",
        },
        {
            "id": "q3",
            "question": "What can be inferred?",
            "options": ["A3", "B3", "C3", "D3"],
            "correct_index": 2,
            "focus": "inference",
            "explanation": "The author implies future growth.",
        },
        {
            "id": "q4",
            "question": "What does the word mean?",
            "options": ["A4", "B4", "C4", "D4"],
            "correct_index": 3,
            "focus": "vocabulary_in_context",
            "explanation": "Context shows the word means improvement.",
        },
    ]
}


def quiz_ai_response() -> str:
    return f"---READING_QUIZ---\n{json.dumps(SAMPLE_QUIZ_PAYLOAD)}\n---END_READING_QUIZ---"


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class ReadingQuizAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="readingquizuser",
            password="testpass123",
        )
        self.client.login(username="readingquizuser", password="testpass123")
        self.passage = (
            "Solar energy is becoming more affordable. Many cities now invest in renewable power."
        )

    @patch("tutor.services.generate_from_template")
    def test_generate_reading_quiz(self, mock_generate):
        mock_generate.return_value = quiz_ai_response()

        response = self.client.post(
            "/api/reading/quiz/generate/",
            {
                "passage": self.passage,
                "level": "B2",
                "question_focus": "mixed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz"]
        self.assertIn("quiz_id", quiz)
        self.assertGreaterEqual(len(quiz["questions"]), 4)
        self.assertNotIn("correct_index", quiz["questions"][0])

    @patch("tutor.services.generate_from_template")
    def test_submit_reading_quiz_scores_and_saves_mistakes(self, mock_generate):
        from tutor.models import Mistake

        mock_generate.return_value = quiz_ai_response()
        generate_response = self.client.post(
            "/api/reading/quiz/generate/",
            {"passage": self.passage, "level": "B1", "question_focus": "main_idea"},
            format="json",
        )
        quiz = generate_response.json()["quiz"]

        submit_response = self.client.post(
            "/api/reading/quiz/submit/",
            {
                "quiz_id": quiz["quiz_id"],
                "answers": {
                    "q1": 1,
                    "q2": 2,
                    "q3": 2,
                    "q4": 3,
                },
            },
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200)
        data = submit_response.json()
        self.assertEqual(data["score"]["total"], 4)
        self.assertEqual(data["score"]["correct"], 3)
        self.assertEqual(data["mistakes_saved"], 1)

        mistakes = Mistake.objects.filter(user=self.user, track="reading_coach")
        self.assertEqual(mistakes.count(), 1)
        self.assertEqual(mistakes.first().category, "reading_comprehension")

    def test_parse_reading_quiz_rejects_invalid_payload(self):
        from tutor.services import parse_reading_quiz

        with self.assertRaises(ValueError):
            parse_reading_quiz("not valid json block")

        with self.assertRaises(ValueError):
            parse_reading_quiz(
                '---READING_QUIZ---\n{"questions": [{"question": "Only one?", "options": ["a"], "correct_index": 0}]}\n---END_READING_QUIZ---'
            )

    @patch("tutor.services.generate_from_template")
    def test_submit_expired_quiz_returns_error(self, mock_generate):
        mock_generate.return_value = quiz_ai_response()
        self.client.post(
            "/api/reading/quiz/generate/",
            {"passage": self.passage},
            format="json",
        )

        response = self.client.post(
            "/api/reading/quiz/submit/",
            {"quiz_id": "missing-quiz-id", "answers": {"q1": 0}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
