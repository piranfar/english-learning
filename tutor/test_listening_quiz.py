import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()

SAMPLE_LISTENING_QUIZ = {
    "questions": [
        {
            "id": "q1",
            "question": "What is the main idea of the lecture?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 1,
            "focus": "main_idea",
            "explanation": "The speaker focuses on climate policy.",
        },
        {
            "id": "q2",
            "question": "Which detail is mentioned?",
            "options": ["A2", "B2", "C2", "D2"],
            "correct_index": 0,
            "focus": "detail",
            "explanation": "The transcript mentions solar panels.",
        },
        {
            "id": "q3",
            "question": "What can be inferred?",
            "options": ["A3", "B3", "C3", "D3"],
            "correct_index": 2,
            "focus": "inference",
            "explanation": "The speaker implies future investment.",
        },
        {
            "id": "q4",
            "question": "Why does the speaker mention the phrase?",
            "options": ["A4", "B4", "C4", "D4"],
            "correct_index": 3,
            "focus": "vocabulary_phrase",
            "explanation": "The phrase means gradual improvement.",
        },
    ],
    "shadowing_sentences": [
        "Many cities now invest in renewable power.",
    ],
}


def listening_quiz_ai_response() -> str:
    return (
        f"---LISTENING_QUIZ---\n{json.dumps(SAMPLE_LISTENING_QUIZ)}\n---END_LISTENING_QUIZ---"
    )


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class ListeningQuizAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="listeningquizuser",
            password="testpass123",
        )
        self.client.login(username="listeningquizuser", password="testpass123")
        self.transcript = (
            "Today we discuss renewable energy. Many cities now invest in renewable power."
        )

    @patch("tutor.services.generate_from_template")
    def test_generate_listening_quiz_hides_transcript(self, mock_generate):
        mock_generate.return_value = listening_quiz_ai_response()

        response = self.client.post(
            "/api/listening/quiz/generate/",
            {
                "transcript": self.transcript,
                "level": "TOEFL",
                "question_focus": "mixed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("transcript", payload)
        quiz = payload["quiz"]
        self.assertIn("quiz_id", quiz)
        self.assertGreaterEqual(len(quiz["questions"]), 4)
        self.assertNotIn("correct_index", quiz["questions"][0])

    @patch("tutor.services.generate_from_template")
    def test_submit_reveals_transcript_and_saves_mistakes(self, mock_generate):
        from tutor.models import Mistake

        mock_generate.return_value = listening_quiz_ai_response()
        generate_response = self.client.post(
            "/api/listening/quiz/generate/",
            {"transcript": self.transcript, "question_focus": "main_idea"},
            format="json",
        )
        quiz = generate_response.json()["quiz"]

        submit_response = self.client.post(
            "/api/listening/quiz/submit/",
            {
                "quiz_id": quiz["quiz_id"],
                "answers": {"q1": 1, "q2": 2, "q3": 2, "q4": 3},
            },
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200)
        data = submit_response.json()
        self.assertIn("transcript", data)
        self.assertIn("renewable power", data["transcript"])
        self.assertEqual(data["score"]["correct"], 3)
        self.assertEqual(data["mistakes_saved"], 1)
        self.assertEqual(len(data["shadowing_sentences"]), 1)

        mistake = Mistake.objects.get(user=self.user, track="listening_coach")
        self.assertEqual(mistake.category, "listening_comprehension")

    def test_generate_without_transcript_or_audio_fails(self):
        response = self.client.post(
            "/api/listening/quiz/generate/",
            {"transcript": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_parse_listening_quiz_rejects_invalid_payload(self):
        from tutor.services import parse_listening_quiz

        with self.assertRaises(ValueError):
            parse_listening_quiz("invalid")

        with self.assertRaises(ValueError):
            parse_listening_quiz(
                '---LISTENING_QUIZ---\n{"questions": []}\n---END_LISTENING_QUIZ---'
            )

    @patch("tutor.voice.transcribe_audio")
    @patch("tutor.services.generate_from_template")
    def test_generate_from_audio_uses_stt(self, mock_generate, mock_transcribe):
        mock_transcribe.return_value = self.transcript
        mock_generate.return_value = listening_quiz_ai_response()

        from django.core.files.uploadedfile import SimpleUploadedFile

        response = self.client.post(
            "/api/listening/quiz/generate/",
            {
                "audio": SimpleUploadedFile(
                    "clip.webm",
                    b"fake audio bytes",
                    content_type="audio/webm",
                ),
                "level": "B1",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        mock_transcribe.assert_called_once()
        self.assertIn("quiz_id", response.json()["quiz"])
