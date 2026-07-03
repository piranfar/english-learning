from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class LessonQuizAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="lessonquizuser",
            password="testpass123",
        )
        self.client.login(username="lessonquizuser", password="testpass123")
        call_command("seed_lesson_topics")

        from tutor.models import LessonTopic

        self.topic = LessonTopic.objects.filter(slug="articles-a-an-the").first()
        if not self.topic:
            self.topic = LessonTopic.objects.order_by("order").first()

        from tutor.lesson_quiz_bank import populate_all_topic_quizzes

        populate_all_topic_quizzes(force=True)

    def test_get_lesson_quiz_hides_answers(self):
        response = self.client.get(f"/api/lesson/quiz/?topic_id={self.topic.id}")
        self.assertEqual(response.status_code, 200)
        quiz = response.json()["quiz"]
        self.assertEqual(quiz["topic_id"], self.topic.id)
        self.assertEqual(len(quiz["questions"]), 4)
        self.assertNotIn("correct_index", quiz["questions"][0])

    def test_submit_scores_and_completes_lesson(self):
        from tutor.lesson_quiz_bank import questions_for_topic

        questions = questions_for_topic(self.topic)
        answers = {question["id"]: question["correct_index"] for question in questions}

        response = self.client.post(
            "/api/lesson/quiz/submit/",
            {"topic_id": self.topic.id, "answers": answers},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["score"]["percent"], 100)
        self.assertEqual(payload["progress"]["status"], "completed")

        progress = self.topic.lessonprogress_set.get(user=self.user)
        self.assertEqual(progress.status, "completed")
        self.assertEqual(progress.score, 100)

    def test_low_score_marks_needs_review(self):
        from tutor.lesson_quiz_bank import questions_for_topic

        questions = questions_for_topic(self.topic)
        wrong_index = 0 if questions[0]["correct_index"] != 0 else 1
        answers = {questions[0]["id"]: wrong_index}

        response = self.client.post(
            "/api/lesson/quiz/submit/",
            {"topic_id": self.topic.id, "answers": answers},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertLess(payload["score"]["percent"], 70)
        self.assertEqual(payload["progress"]["status"], "needs_review")
        self.assertGreaterEqual(payload["mistakes_saved"], 1)
