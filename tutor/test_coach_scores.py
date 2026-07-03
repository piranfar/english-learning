import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from tutor.coach_scores import (
    coach_score_for_user,
    estimated_toefl_total,
    speaking_score_for_user,
    vocabulary_score_for_user,
    writing_score_for_user,
)
from tutor.learning_journey import STAGE1_SLUG, _skill_score
from tutor.models import ListeningSession, Message, Mistake, PracticeSession, ReadingSession, VocabularyItem
from tutor.reading_practice import reading_score_for_user

User = get_user_model()


class CoachScoresTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="coachscoreuser", password="testpass123")

    def test_reading_score_from_completed_sessions(self):
        session = ReadingSession.objects.create(
            user=self.user,
            title="Test",
            level="B1",
            stage=STAGE1_SLUG,
            lesson_focus="articles",
            topic="Academic",
            passage="word " * 100,
            questions_json=[{"id": "q1"}],
            score_percent=80,
            completed_at=timezone.now(),
        )
        self.assertEqual(reading_score_for_user(self.user, STAGE1_SLUG), 80)
        self.assertEqual(coach_score_for_user(self.user, "reading", STAGE1_SLUG), 80)

    def test_listening_score_from_completed_sessions(self):
        ListeningSession.objects.create(
            user=self.user,
            title="Lecture",
            level="B1",
            stage=STAGE1_SLUG,
            transcript="hello " * 50,
            questions_json=[{"id": "q1"}],
            score=72,
            completed_at=timezone.now(),
        )
        self.assertEqual(coach_score_for_user(self.user, "listening", STAGE1_SLUG), 72)

    def test_speaking_score_from_assistant_message(self):
        session = PracticeSession.objects.create(user=self.user, track="speaking_coach")
        Message.objects.create(
            session=session,
            role="assistant",
            content=json.dumps({"overall_score": 76, "overall_feedback": "Good job."}),
        )
        self.assertEqual(speaking_score_for_user(self.user, STAGE1_SLUG), 76)

    def test_writing_score_from_assistant_message(self):
        session = PracticeSession.objects.create(user=self.user, track="writing_coach")
        Message.objects.create(
            session=session,
            role="assistant",
            content=json.dumps({"overall_score": 68, "overall_feedback": "Needs work."}),
        )
        self.assertEqual(writing_score_for_user(self.user, STAGE1_SLUG), 68)

    def test_vocabulary_score_uses_review_progress(self):
        VocabularyItem.objects.create(
            user=self.user,
            word="analyze",
            definition="examine",
            next_review_date=timezone.now().date(),
            repetitions=2,
        )
        VocabularyItem.objects.create(
            user=self.user,
            word="infer",
            definition="deduce",
            next_review_date=timezone.now().date(),
            repetitions=0,
        )
        score = vocabulary_score_for_user(self.user, STAGE1_SLUG)
        self.assertGreaterEqual(score, 60)

    def test_vocabulary_score_penalizes_recent_mistakes(self):
        VocabularyItem.objects.create(
            user=self.user,
            word="analyze",
            definition="examine",
            next_review_date=timezone.now().date(),
            repetitions=1,
        )
        Mistake.objects.create(
            user=self.user,
            wrong_text="analyse",
            correct_text="analyze",
            reason="spelling",
            track="vocab_quiz",
            category="vocabulary_precision",
        )
        score_with_mistake = vocabulary_score_for_user(self.user, STAGE1_SLUG)
        self.assertLess(score_with_mistake, 90)

    def test_skill_score_falls_back_to_estimate_without_sessions(self):
        score, detail = _skill_score(self.user, "reading", STAGE1_SLUG)
        self.assertGreaterEqual(score, 40)
        self.assertIn("estimate", detail)

    def test_estimated_toefl_from_coach_scores(self):
        ReadingSession.objects.create(
            user=self.user,
            title="Test",
            level="B1",
            stage=STAGE1_SLUG,
            lesson_focus="articles",
            topic="Academic",
            passage="word " * 100,
            questions_json=[{"id": "q1"}],
            score_percent=80,
            completed_at=timezone.now(),
        )
        ListeningSession.objects.create(
            user=self.user,
            title="Lecture",
            level="B1",
            stage=STAGE1_SLUG,
            transcript="hello " * 50,
            questions_json=[{"id": "q1"}],
            score=72,
            completed_at=timezone.now(),
        )

        total, detail = estimated_toefl_total(self.user, STAGE1_SLUG, mastery_ratio=0.5, grammar_score=70)

        self.assertGreaterEqual(total, 40)
        self.assertLessEqual(total, 120)
        self.assertIn("coach scores", detail)

    def test_estimated_toefl_falls_back_without_sessions(self):
        total, detail = estimated_toefl_total(self.user, STAGE1_SLUG, mastery_ratio=0.2, grammar_score=60)

        self.assertGreaterEqual(total, 40)
        self.assertLessEqual(total, 120)
        self.assertIn("lesson progress", detail)
