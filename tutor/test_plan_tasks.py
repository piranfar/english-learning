from django.test import TestCase

from tutor.plan_tasks import (
    build_mistake_plan_item,
    build_track_plan_item,
    build_vocab_plan_item,
    count_recent_mistakes_by_category,
)
from tutor.utils.mistake_classification import classify_mistake


class PlanTaskContentTests(TestCase):
    def test_article_mistake_routes_to_lesson(self):
        from django.contrib.auth import get_user_model

        from tutor.models import Mistake

        user = get_user_model().objects.create_user(
            username="planrouteuser",
            password="testpass123",
        )
        mistake = Mistake.objects.create(
            user=user,
            track="grammar_coach",
            wrong_text="I saw an book.",
            correct_text="I saw a book.",
            reason="Article error",
            category=classify_mistake(
                "I saw an book.",
                "I saw a book.",
                "Article error",
                "grammar_coach",
            ),
        )
        item = build_mistake_plan_item(mistake, count_recent_mistakes_by_category(user))
        self.assertEqual(item["metadata"]["category"], "article")
        self.assertTrue(item["route"].startswith("/lesson?topic="))
        self.assertTrue(item["reason"])

    def test_vocab_item_has_review_route(self):
        from datetime import date

        from django.contrib.auth import get_user_model

        from tutor.models import VocabularyItem

        user = get_user_model().objects.create_user(
            username="planvocabuser",
            password="testpass123",
        )
        vocab = VocabularyItem.objects.create(
            user=user,
            word="analyze",
            definition="Examine",
            next_review_date=date.today(),
        )
        item = build_vocab_plan_item(vocab)
        self.assertEqual(item["route"], f"/vocab?word={vocab.id}")
        self.assertIn("due for review", item["reason"])

    def test_track_item_has_learner_reason(self):
        item = build_track_plan_item("speaking", 10)
        self.assertEqual(item["skill"], "Speaking")
        self.assertIn("fluency", item["reason"].lower())
