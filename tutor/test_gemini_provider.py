import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.ai.exceptions import ProviderUnavailableError
from tutor.ai.factory import get_provider
from tutor.ai.gemini_client import call_gemini_chat
from tutor.ai.registry import AI_PROVIDER_REGISTRY, get_ai_provider_spec
from tutor.ai.provider_resolution import is_ai_provider_configured
from tutor.learning_journey import STAGE1_SLUG
from tutor.utils.provider_access import resolve_user_provider

User = get_user_model()

SAMPLE_LISTENING_RAW = (
    "---LISTENING_PRACTICE---\n"
    + json.dumps(
        {
            "title": "Gemini Test Lecture",
            "level": "B1",
            "stage": STAGE1_SLUG,
            "listening_type": "academic_mini_lecture",
            "topic": "Science",
            "lesson_focus": "none",
            "transcript": "Professor: " + ("Today we study ecosystems. " * 40),
            "estimated_duration_seconds": 120,
            "target_vocabulary": [],
            "questions": [
                {
                    "id": f"q{i}",
                    "type": "detail",
                    "question": f"Question {i}?",
                    "choices": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": "Because A.",
                }
                for i in range(1, 5)
            ],
            "shadowing_sentences": ["Today we study ecosystems."],
        }
    )
    + "\n---END_LISTENING_PRACTICE---"
)


@override_settings(GEMINI_API_KEY="")
class GeminiClientTests(TestCase):
    def test_call_gemini_chat_raises_when_key_missing(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            call_gemini_chat("Hello")
        self.assertEqual(ctx.exception.provider, "gemini")
        self.assertNotIn("GEMINI_API_KEY", str(ctx.exception))

    @override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-test-model")
    @patch("google.genai.Client")
    def test_call_gemini_chat_returns_normalized_response(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini"
        mock_response.model_dump.return_value = {"candidates": []}
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        result = call_gemini_chat(
            "Say hello",
            system_prompt="You are helpful.",
            json_mode=True,
        )

        self.assertEqual(result["provider"], "gemini")
        self.assertEqual(result["model"], "gemini-test-model")
        self.assertEqual(result["content"], "Hello from Gemini")
        self.assertIn("raw", result)

    def test_is_ai_provider_configured_false_without_key(self):
        self.assertFalse(is_ai_provider_configured("gemini"))

    @override_settings(GEMINI_API_KEY="test-key")
    def test_is_ai_provider_configured_true_with_key(self):
        self.assertTrue(is_ai_provider_configured("gemini"))


class GeminiRegistryTests(TestCase):
    def test_gemini_appears_in_provider_registry(self):
        spec = get_ai_provider_spec("gemini")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.id, "gemini")
        self.assertEqual(spec.display_name, "Google Gemini")
        self.assertEqual(spec.required_env, "GEMINI_API_KEY")
        self.assertEqual(spec.default_model_setting, "GEMINI_MODEL")
        self.assertTrue(spec.cloud)
        self.assertIn("listening", spec.supported_tasks)
        self.assertIn("reading", spec.supported_tasks)
        self.assertIn("gemini", AI_PROVIDER_REGISTRY)

    def test_get_provider_returns_gemini_instance(self):
        provider = get_provider("gemini")
        self.assertEqual(provider.__class__.__name__, "GeminiProvider")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    ALLOW_LEARNER_PROVIDER_OVERRIDE=False,
    GEMINI_API_KEY="",
)
class GeminiProviderAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.learner = User.objects.create_user(
            username="geminilearner",
            password="testpass123",
        )
        self.staff = User.objects.create_user(
            username="geministaff",
            password="testpass123",
            is_staff=True,
        )

    def test_resolve_user_provider_staff_may_select_gemini(self):
        request = type("Req", (), {"user": self.staff})()
        self.assertEqual(resolve_user_provider(request, "gemini"), "gemini")

    def test_resolve_user_provider_non_staff_cannot_select_gemini(self):
        request = type("Req", (), {"user": self.learner})()
        self.assertIsNone(resolve_user_provider(request, "gemini"))

    @override_settings(ALLOW_LEARNER_PROVIDER_OVERRIDE=True)
    def test_resolve_user_provider_learner_may_select_when_override_enabled(self):
        request = type("Req", (), {"user": self.learner})()
        self.assertEqual(resolve_user_provider(request, "gemini"), "gemini")

    @patch("tutor.listening_practice.generate_from_template")
    def test_missing_gemini_key_falls_back_safely(self, mock_generate):
        mock_generate.return_value = "unparseable"
        self.client.login(username="geminilearner", password="testpass123")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "provider": "gemini"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("GEMINI_API_KEY", response.content.decode())
        self.assertTrue(body["session"]["provider_metadata"]["used_fallback"])

    @override_settings(GEMINI_API_KEY="test-key")
    @patch("tutor.listening_practice.generate_from_template")
    def test_staff_gemini_selection_includes_provider_metadata(self, mock_generate):
        mock_generate.return_value = SAMPLE_LISTENING_RAW
        self.client.login(username="geministaff", password="testpass123")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {
                "level": "B1",
                "stage": STAGE1_SLUG,
                "provider": "gemini",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session = response.json()["session"]
        self.assertEqual(session["provider_metadata"]["provider"], "gemini")
        self.assertTrue(session["provider_metadata"]["model"])
        self.assertFalse(session["provider_metadata"]["used_fallback"])
        mock_generate.assert_called()
        self.assertEqual(mock_generate.call_args.kwargs.get("provider"), "gemini")
