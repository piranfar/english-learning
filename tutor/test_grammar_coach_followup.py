from django.contrib.auth import get_user_model
from django.test import TestCase

from tutor.models import PracticeSession
from tutor.services import format_grammar_coach_message, run_task

User = get_user_model()


class GrammarCoachFollowUpTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="grammarfollowup", password="testpass123")
        self.session = PracticeSession.objects.create(user=self.user, track="grammar_coach")

    def test_format_grammar_coach_message_first_turn(self):
        message = format_grammar_coach_message("Teach present simple.", is_follow_up=False)
        self.assertEqual(message, "Teach present simple.")

    def test_format_grammar_coach_message_follow_up(self):
        message = format_grammar_coach_message(
            "When do I use present continuous?",
            is_follow_up=True,
        )
        self.assertIn("MODE B", message)
        self.assertIn("When do I use present continuous?", message)

    def test_run_task_wraps_grammar_follow_up_for_provider(self):
        from unittest.mock import patch

        from tutor.models import Message

        Message.objects.create(
            session=self.session,
            role="assistant",
            content="### Title\nPresent simple\n\n### 1. Simple explanation\n...",
        )
        Message.objects.create(
            session=self.session,
            role="user",
            content="Start the lesson.",
        )

        captured = {}

        def fake_call_provider(template, messages):
            captured["messages"] = messages
            return "Short follow-up answer."

        with patch("tutor.services.call_provider", side_effect=fake_call_provider):
            with patch(
                "tutor.services.parse_corrections",
                return_value=("Short follow-up answer.", []),
            ):
                result = run_task(
                    "grammar_coach",
                    "Is this sentence correct: I am go to school?",
                    self.user,
                    self.session,
                    provider="ollama",
                )

        self.assertEqual(result["reply"], "Short follow-up answer.")
        last_user = captured["messages"][-1]
        self.assertEqual(last_user["role"], "user")
        self.assertIn("MODE B", last_user["content"])
        self.assertIn("I am go to school", last_user["content"])
