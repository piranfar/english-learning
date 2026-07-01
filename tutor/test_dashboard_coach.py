from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from tutor.dashboard_coach import build_coach_focus
from tutor.models import Mistake, StudyPlan, VocabularyItem
from tutor.services import get_user_profile


class DashboardCoachFocusTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="coachuser", password="testpass123")
        self.profile = get_user_profile(self.user)
        self.profile.weak_areas = []
        self.profile.save()
        self.today = date.today()
        self.empty_plan_summary = {
            "exists": False,
            "total_count": 0,
            "completed": False,
        }

    def _focus(self, **kwargs):
        defaults = {
            "today": self.today,
            "plan_summary": self.empty_plan_summary,
            "profile": self.profile,
            "vocab_due": 0,
            "mistakes_due": 0,
            "plan": None,
        }
        defaults.update(kwargs)
        return build_coach_focus(self.user, **defaults)

    def test_article_focus_returns_article_route_not_vocab(self):
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I saw an book on the table.",
            correct_text="I saw a book on the table.",
            reason="Article error",
            category="article",
        )
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="She bought an apple yesterday.",
            correct_text="She bought a apple yesterday.",
            reason="Another article error",
            category="article",
        )
        vocab = VocabularyItem.objects.create(
            user=self.user,
            word="terminate",
            definition="End something",
            next_review_date=self.today,
        )
        plan = StudyPlan.objects.create(
            user=self.user,
            date=self.today,
            items=[
                {"id": "v1", "type": "vocab", "ref_id": vocab.id, "completed": False},
                {"id": "t1", "type": "track", "track": "grammar", "minutes": 10, "completed": False},
            ],
        )
        plan_summary = {"exists": True, "total_count": 2, "completed": False}

        focus = self._focus(
            vocab_due=1,
            plan=plan,
            plan_summary=plan_summary,
        )

        self.assertEqual(focus["today_focus"]["title"], "Article errors")
        self.assertEqual(focus["today_focus"]["category"], "article")
        self.assertIn("article", focus["focus_action"]["route"])
        self.assertNotIn("/vocab", focus["focus_action"]["route"])
        self.assertNotIn("Terminate", focus["focus_action"]["title"])
        self.assertNotIn("vocabulary", focus["focus_action"]["title"].lower())
        self.assertEqual(focus["recommended_action"], focus["focus_action"]["title"])
        self.assertEqual(focus["action_route"], focus["focus_action"]["route"])

    def test_vocabulary_focus_returns_vocab_route(self):
        VocabularyItem.objects.create(
            user=self.user,
            word="analyze",
            definition="Examine in detail",
            next_review_date=self.today,
        )
        VocabularyItem.objects.create(
            user=self.user,
            word="terminate",
            definition="End something",
            next_review_date=self.today,
        )

        focus = self._focus(vocab_due=2)

        self.assertEqual(focus["today_focus"]["title"], "Vocabulary review")
        self.assertEqual(focus["today_focus"]["category"], "vocabulary_precision")
        self.assertEqual(focus["focus_action"]["route"], "/vocab")
        self.assertIn("2", focus["focus_action"]["title"])

    def test_no_vocab_due_does_not_recommend_vocab_review(self):
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I saw an book on the table.",
            correct_text="I saw a book on the table.",
            reason="Article error",
            category="article",
        )
        vocab = VocabularyItem.objects.create(
            user=self.user,
            word="terminate",
            definition="End something",
            next_review_date=self.today + timedelta(days=7),
        )
        plan = StudyPlan.objects.create(
            user=self.user,
            date=self.today,
            items=[
                {"id": "v1", "type": "vocab", "ref_id": vocab.id, "completed": False},
            ],
        )
        plan_summary = {"exists": True, "total_count": 1, "completed": False}

        focus = self._focus(vocab_due=0, plan=plan, plan_summary=plan_summary)

        self.assertEqual(focus["empty_states"]["vocab_due_message"], "No vocabulary due right now.")
        self.assertNotIn("/vocab", focus["focus_action"]["route"])
        self.assertNotIn("vocabulary", focus["focus_action"]["title"].lower())
        self.assertIsNone(focus["next_plan_task"])

    def test_single_vocab_due_message(self):
        focus = self._focus(vocab_due=1)
        self.assertEqual(focus["empty_states"]["vocab_due_message"], "1 vocabulary item is due.")

    def test_first_incomplete_plan_task_does_not_override_article_focus(self):
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I saw an book on the table.",
            correct_text="I saw a book on the table.",
            reason="Article error",
            category="article",
        )
        vocab = VocabularyItem.objects.create(
            user=self.user,
            word="terminate",
            definition="End something",
            next_review_date=self.today,
        )
        plan = StudyPlan.objects.create(
            user=self.user,
            date=self.today,
            items=[
                {"id": "v1", "type": "vocab", "ref_id": vocab.id, "completed": False},
            ],
        )
        plan_summary = {"exists": True, "total_count": 1, "completed": False}

        focus = self._focus(vocab_due=1, plan=plan, plan_summary=plan_summary)

        self.assertEqual(focus["today_focus"]["category"], "article")
        self.assertIn("article", focus["focus_action"]["route"])
        self.assertNotEqual(focus["focus_action"]["title"], focus["next_plan_task"]["title"])

    def test_matching_plan_task_can_align_with_focus_action(self):
        mistake = Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I saw an book on the table.",
            correct_text="I saw a book on the table.",
            reason="Article error",
            category="article",
            next_review_date=self.today,
        )
        plan = StudyPlan.objects.create(
            user=self.user,
            date=self.today,
            items=[
                {"id": "m1", "type": "mistake", "ref_id": mistake.id, "completed": False},
            ],
        )
        plan_summary = {"exists": True, "total_count": 1, "completed": False}

        focus = self._focus(plan=plan, plan_summary=plan_summary)

        self.assertEqual(focus["today_focus"]["category"], "article")
        self.assertIn("article", focus["focus_action"]["route"])
        self.assertIsNone(focus["next_plan_task"])

    def test_no_plan_fallback_message(self):
        VocabularyItem.objects.create(
            user=self.user,
            word="later",
            definition="Not due yet",
            next_review_date=self.today + timedelta(days=7),
        )
        focus = self._focus()
        self.assertEqual(focus["focus_action"]["title"], "Generate today's study plan")
        self.assertEqual(focus["focus_action"]["route"], "/plan")

    def test_preposition_focus_route(self):
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I am good in English.",
            correct_text="I am good at English.",
            reason="Preposition error",
            category="preposition",
        )

        focus = self._focus()

        self.assertEqual(focus["today_focus"]["category"], "preposition")
        self.assertEqual(focus["focus_action"]["route"], "/mistakes?category=preposition")
