from django.contrib.auth import get_user_model
from django.test import TestCase

from tutor.learning_journey import (
    STAGE1_SLUG,
    STAGE2_SLUG,
    build_journey_summary,
    evaluate_stage1_ready,
    get_or_create_journey,
    plan_minutes_for_user,
)
from tutor.models import LearningGoal, LessonProgress, LessonTopic
from tutor.plan import build_plan_items

User = get_user_model()


class LearningJourneyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="journey_learner", password="test")

    def test_default_goals_created(self):
        goal1 = LearningGoal.objects.get(slug=STAGE1_SLUG)
        goal2 = LearningGoal.objects.get(slug=STAGE2_SLUG)
        self.assertTrue(goal1.is_default)
        self.assertFalse(goal2.is_default)
        self.assertEqual(goal2.unlocks_after_id, goal1.id)
        self.assertEqual(goal1.target_toefl_score, 80)
        self.assertEqual(goal2.target_toefl_score, 100)

    def test_stage1_is_default_for_new_user(self):
        journey = get_or_create_journey(self.user)
        self.assertEqual(journey.current_goal.slug, STAGE1_SLUG)
        self.assertFalse(journey.stage2_unlocked)

    def test_stage2_locked_initially(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/lesson/topics/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        stage2 = next(stage for stage in payload["stages"] if stage["slug"] == STAGE2_SLUG)
        self.assertTrue(stage2["locked"])
        self.assertTrue(all(topic["locked"] for topic in stage2["topics"]))

    def test_curriculum_lessons_linked_to_stage(self):
        stage1_count = LessonTopic.objects.filter(stage_slug=STAGE1_SLUG, is_active=True).count()
        stage2_count = LessonTopic.objects.filter(stage_slug=STAGE2_SLUG, is_active=True).count()
        self.assertEqual(stage1_count, 40)
        self.assertEqual(stage2_count, 16)

    def test_stage2_unlocks_after_readiness(self):
        stage1_topics = LessonTopic.objects.filter(stage_slug=STAGE1_SLUG, is_active=True)
        for topic in stage1_topics:
            LessonProgress.objects.update_or_create(
                user=self.user,
                topic=topic,
                defaults={"status": LessonProgress.STATUS_COMPLETED, "score": 85},
            )

        self.assertTrue(evaluate_stage1_ready(self.user))
        journey = get_or_create_journey(self.user)
        journey.stage2_unlocked = True
        journey.save(update_fields=["stage2_unlocked"])

        self.client.force_login(self.user)
        response = self.client.get("/api/lesson/topics/")
        stage2 = next(stage for stage in response.json()["stages"] if stage["slug"] == STAGE2_SLUG)
        self.assertFalse(stage2["locked"])

    def test_daily_plan_uses_current_stage(self):
        journey = get_or_create_journey(self.user)
        stage1_minutes = plan_minutes_for_user(self.user)
        self.assertEqual(stage1_minutes["grammar"], 18)

        goal2 = LearningGoal.objects.get(slug=STAGE2_SLUG)
        journey.current_goal = goal2
        journey.stage2_unlocked = True
        journey.save()
        stage2_minutes = plan_minutes_for_user(self.user)
        self.assertEqual(stage2_minutes["writing"], 20)

        items = build_plan_items(self.user)
        self.assertTrue(all(item.get("reason") for item in items))

    def test_dashboard_shows_goal_and_stage(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("journey", payload)
        self.assertEqual(payload["journey"]["current_goal"]["slug"], STAGE1_SLUG)
        self.assertEqual(payload["journey"]["current_stage"], 1)

    def test_readiness_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/readiness/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_goal"]["slug"], STAGE1_SLUG)
        self.assertFalse(payload["stage2_unlocked"])
        self.assertIn("criteria", payload)

    def test_locked_stage2_lesson_start_forbidden(self):
        stage2_topic = LessonTopic.objects.filter(stage_slug=STAGE2_SLUG).first()
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/lesson/start-recommended/",
            data={"topic_id": stage2_topic.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_journey_summary_includes_next_lesson(self):
        summary = build_journey_summary(self.user)
        self.assertEqual(summary["current_goal"]["slug"], STAGE1_SLUG)
        self.assertIsNotNone(summary["next_lesson"])
        self.assertIn("progress_percent", summary)
