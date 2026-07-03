from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from tutor.models import StudyPlan
from tutor.plan import get_today_plan
from tutor.plan_completion import auto_complete_plan_items
from tutor.plan_tasks import build_track_plan_item

User = get_user_model()


class PlanCompletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="plancompleteuser", password="testpass123")
        self.today = date(2026, 6, 25)
        self.plan = StudyPlan.objects.create(
            user=self.user,
            date=self.today,
            items=[
                build_track_plan_item("reading", 15),
                build_track_plan_item("listening", 10),
                {
                    "id": "reading-articles",
                    "type": "reading",
                    "track": "reading",
                    "title": "Reading: articles",
                    "minutes": 15,
                    "completed": False,
                    "status": "not_started",
                    "metadata": {"lesson_focus": "articles"},
                },
            ],
        )

    def test_completes_matching_track_item(self):
        completed = auto_complete_plan_items(self.user, track="reading", today=self.today)

        self.assertEqual(completed, ["track-reading", "reading-articles"])
        plan, _ = get_today_plan(self.user, self.today)
        completed_ids = [item["id"] for item in plan.items if item.get("completed")]
        self.assertIn("track-reading", completed_ids)
        self.assertIn("reading-articles", completed_ids)

    def test_completes_only_listening_when_specified(self):
        completed = auto_complete_plan_items(self.user, track="listening", today=self.today)

        self.assertEqual(completed, ["track-listening"])
        plan, _ = get_today_plan(self.user, self.today)
        by_id = {item["id"]: item for item in plan.items}
        self.assertTrue(by_id["track-listening"]["completed"])
        self.assertFalse(by_id["track-reading"]["completed"])

    def test_skips_already_completed_items(self):
        items = list(self.plan.items)
        items[0]["completed"] = True
        self.plan.items = items
        self.plan.save(update_fields=["items"])

        completed = auto_complete_plan_items(self.user, track="reading", today=self.today)

        self.assertEqual(completed, ["reading-articles"])
