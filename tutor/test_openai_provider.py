import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.ai.exceptions import ProviderUnavailableError
from tutor.ai.factory import get_provider
from tutor.ai.openai_client import call_openai_chat
from tutor.ai.registry import AI_PROVIDER_REGISTRY, get_ai_provider_spec
from tutor.ai.provider_resolution import is_ai_provider_configured
from tutor.learning_journey import STAGE1_SLUG
from tutor.utils.provider_access import resolve_user_provider

User = get_user_model()

SAMPLE_LISTENING_RAW = (
    "---LISTENING_PRACTICE---\n"
    + json.dumps(
        {
            "title": "OpenAI Test Lecture",
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


@override_settings(OPENAI_API_KEY="")
class OpenAIClientTests(TestCase):
    def test_call_openai_chat_raises_when_key_missing(self):
        with self.assertRaises(ProviderUnavailableError) as ctx:
            call_openai_chat("Hello")
        self.assertEqual(ctx.exception.provider, "openai")
        self.assertNotIn("OPENAI_API_KEY", str(ctx.exception))

    @override_settings(OPENAI_API_KEY="test-key", OPENAI_MODEL="gpt-test-model")
    @patch("openai.OpenAI")
    def test_call_openai_chat_returns_normalized_response(self, mock_client_cls):
        mock_message = MagicMock()
        mock_message.content = "Hello from OpenAI"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model_dump.return_value = {"id": "chatcmpl-test"}
        mock_client_cls.return_value.chat.completions.create.return_value = mock_response

        result = call_openai_chat(
            "Say hello",
            system_prompt="You are helpful.",
            json_mode=True,
            max_tokens=500,
        )

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-test-model")
        self.assertEqual(result["content"], "Hello from OpenAI")
        self.assertIn("raw", result)

        create_kwargs = mock_client_cls.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(create_kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(create_kwargs["messages"][0]["role"], "system")
        self.assertNotIn("max_tokens", create_kwargs)
        self.assertIn("max_completion_tokens", create_kwargs)

    def test_is_ai_provider_configured_false_without_key(self):
        self.assertFalse(is_ai_provider_configured("openai"))

    @override_settings(OPENAI_API_KEY="test-key")
    def test_is_ai_provider_configured_true_with_key(self):
        self.assertTrue(is_ai_provider_configured("openai"))


class OpenAIRegistryTests(TestCase):
    def test_openai_appears_in_provider_registry(self):
        spec = get_ai_provider_spec("openai")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.id, "openai")
        self.assertEqual(spec.display_name, "OpenAI GPT")
        self.assertEqual(spec.required_env, "OPENAI_API_KEY")
        self.assertEqual(spec.default_model_setting, "OPENAI_MODEL")
        self.assertTrue(spec.cloud)
        self.assertIn("listening", spec.supported_tasks)
        self.assertIn("writing", spec.supported_tasks)
        self.assertIn("openai", AI_PROVIDER_REGISTRY)

    def test_get_provider_returns_openai_instance(self):
        provider = get_provider("openai")
        self.assertEqual(provider.__class__.__name__, "OpenAIProvider")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    ALLOW_LEARNER_PROVIDER_OVERRIDE=False,
    OPENAI_API_KEY="",
)
class OpenAIProviderAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.learner = User.objects.create_user(
            username="openailearner",
            password="testpass123",
        )
        self.staff = User.objects.create_user(
            username="openaistaff",
            password="testpass123",
            is_staff=True,
        )

    def test_resolve_user_provider_staff_may_select_openai(self):
        request = type("Req", (), {"user": self.staff})()
        self.assertEqual(resolve_user_provider(request, "openai"), "openai")

    def test_resolve_user_provider_non_staff_cannot_select_openai(self):
        request = type("Req", (), {"user": self.learner})()
        self.assertIsNone(resolve_user_provider(request, "openai"))

    @override_settings(ALLOW_LEARNER_PROVIDER_OVERRIDE=True)
    def test_resolve_user_provider_learner_may_select_when_override_enabled(self):
        request = type("Req", (), {"user": self.learner})()
        self.assertEqual(resolve_user_provider(request, "openai"), "openai")

    @patch("tutor.listening_practice.generate_from_template")
    def test_missing_openai_key_falls_back_safely(self, mock_generate):
        mock_generate.return_value = "unparseable"
        self.client.login(username="openailearner", password="testpass123")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "provider": "openai"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("OPENAI_API_KEY", response.content.decode())
        self.assertTrue(body["session"]["provider_metadata"]["used_fallback"])

    @override_settings(OPENAI_API_KEY="test-key")
    @patch("tutor.listening_practice.generate_from_template")
    def test_staff_openai_selection_includes_provider_metadata(self, mock_generate):
        mock_generate.return_value = SAMPLE_LISTENING_RAW
        self.client.login(username="openaistaff", password="testpass123")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {
                "level": "B1",
                "stage": STAGE1_SLUG,
                "provider": "openai",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session = response.json()["session"]
        self.assertEqual(session["provider_metadata"]["provider"], "openai")
        self.assertTrue(session["provider_metadata"]["model"])
        self.assertFalse(session["provider_metadata"]["used_fallback"])
        mock_generate.assert_called()
        self.assertEqual(mock_generate.call_args.kwargs.get("provider"), "openai")
