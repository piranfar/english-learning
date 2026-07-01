from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.models import PracticeSession, ShadowingItem
from tutor.shadowing import compare_shadowing

User = get_user_model()


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    OPENAI_API_KEY="",
)
class TranscriptionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="learner",
            password="testpass123",
        )
        self.client.login(username="learner", password="testpass123")

    def test_transcribe_requires_audio(self):
        response = self.client.post("/api/transcribe/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("audio", response.json()["detail"])

    def test_transcribe_unsupported_type(self):
        audio = SimpleUploadedFile("clip.txt", b"hello", content_type="text/plain")
        response = self.client.post(
            "/api/transcribe/",
            {"audio": audio},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported audio type", response.json()["detail"])

    @patch("tutor.views.transcribe", side_effect=RuntimeError("OPENAI_API_KEY is not configured"))
    def test_transcribe_missing_api_key(self, _mock):
        audio = SimpleUploadedFile("clip.webm", b"fake-audio", content_type="audio/webm")
        response = self.client.post(
            "/api/transcribe/",
            {"audio": audio},
            format="multipart",
        )
        self.assertEqual(response.status_code, 502)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    @patch("tutor.views.transcribe", return_value="hello there")
    def test_transcribe_success_returns_transcript(self, _mock):
        audio = SimpleUploadedFile("clip.webm", b"fake-audio", content_type="audio/webm")
        response = self.client.post(
            "/api/transcribe/",
            {"audio": audio},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript"], "hello there")


class ShadowingCompareTests(TestCase):
    def test_compare_exact_match(self):
        result = compare_shadowing(
            "Scientists are studying bacteria.",
            "Scientists are studying bacteria.",
        )
        self.assertEqual(result["similarity_score"], 100)
        self.assertEqual(result["missing_words"], [])
        self.assertEqual(result["extra_words"], [])

    def test_compare_detects_missing_words(self):
        result = compare_shadowing(
            "Scientists are studying bacteria.",
            "Scientists studying.",
        )
        self.assertIn("are", result["missing_words"])
        self.assertIn("bacteria", result["missing_words"])

    def test_compare_returns_structured_feedback(self):
        result = compare_shadowing(
            "Scientists are studying bacteria.",
            "Scientists studying bacteria.",
            input_mode="voice",
            duration_seconds=4.0,
        )
        self.assertEqual(result["word_accuracy"], result["similarity_score"])
        self.assertIn("retry_instruction", result)
        self.assertIn("next_drill", result)
        self.assertIsNotNone(result["pronunciation_clarity"])
        self.assertIsNone(compare_shadowing("Hello world.", "Hello.", input_mode="typed")["intonation"])


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class SpeakingAndShadowingAudioTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="learner",
            password="testpass123",
        )
        self.client.login(username="learner", password="testpass123")
        self.item = ShadowingItem.objects.create(
            target_text="Scientists are studying bacteria.",
            persian_meaning="دانشمندان در حال مطالعه باکتری‌ها هستند.",
            sort_order=1,
        )

    def test_speaking_attempt_audio_requires_file(self):
        response = self.client.post("/api/speaking/attempt-audio/")
        self.assertEqual(response.status_code, 400)

    @patch("tutor.speaking_evaluation.run_speaking_evaluation")
    @patch("tutor.views.transcribe", return_value="I think science is important.")
    def test_speaking_attempt_audio_success(self, _transcribe, mock_run_evaluation):
        mock_run_evaluation.return_value = {
            "reply": "Good answer!",
            "corrections": [],
            "speaking_feedback": {"overall_score": 80, "scores": {"fluency": 75}},
        }
        audio = SimpleUploadedFile("clip.webm", b"fake-audio", content_type="audio/webm")
        response = self.client.post(
            "/api/speaking/attempt-audio/",
            {
                "audio": audio,
                "scenario": "daily conversation",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["transcript"], "I think science is important.")
        self.assertEqual(body["reply"], "Good answer!")
        self.assertIn("session_id", body)
        self.assertTrue(
            PracticeSession.objects.filter(user=self.user, track="speaking_coach").exists()
        )

    @patch("tutor.views.transcribe", return_value="Scientists are studying bacteria.")
    def test_shadowing_attempt_audio_success(self, _transcribe):
        audio = SimpleUploadedFile("clip.webm", b"fake-audio", content_type="audio/webm")
        response = self.client.post(
            f"/api/shadowing/items/{self.item.id}/attempt-audio/",
            {"audio": audio},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["similarity_score"], 100)
        self.assertEqual(body["transcript"], "Scientists are studying bacteria.")

    def test_shadowing_typed_attempt(self):
        response = self.client.post(
            f"/api/shadowing/items/{self.item.id}/attempt/",
            {"transcript": "Scientists are studying bacteria."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["similarity_score"], 100)


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
)
class VocabSeedAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="vocabuser", password="testpass123")
        self.client.login(username="vocabuser", password="testpass123")

    def test_vocab_seeds_list(self):
        from tutor.models import VocabularySeed

        VocabularySeed.objects.create(
            word="analyze",
            cefr_level="B1",
            category="toefl_academic",
            part_of_speech="noun",
            definition="Examine in detail",
            approved=True,
            is_active=True,
        )
        response = self.client.get("/api/vocab/seeds/?cefr_level=B1")
        self.assertEqual(response.status_code, 200)
        seeds = response.json()["seeds"]
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0]["word"], "analyze")
        self.assertIn("category", seeds[0])

    def test_vocab_categories(self):
        from tutor.models import VocabularySeed

        VocabularySeed.objects.create(
            word="analyze",
            category="toefl_academic",
            definition="Examine",
            is_active=True,
        )
        response = self.client.get("/api/vocab/categories/")
        self.assertEqual(response.status_code, 200)
        keys = [item["key"] for item in response.json()]
        self.assertIn("toefl_academic", keys)

    def test_vocab_from_seed_and_no_duplicate(self):
        from tutor.models import VocabularySeed

        seed = VocabularySeed.objects.create(
            word="hypothesis",
            category="toefl_academic",
            part_of_speech="noun",
            definition="An idea tested by research",
            persian_meaning="فرضیه",
            example="The hypothesis was tested.",
            cefr_level="B2",
            approved=True,
            is_active=True,
        )
        first = self.client.post(f"/api/vocab/from-seed/{seed.id}/")
        self.assertEqual(first.status_code, 201)
        self.assertTrue(first.json()["created"])

        second = self.client.post(f"/api/vocab/from-seed/{seed.id}/")
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["already_exists"])
        self.assertEqual(
            self.user.vocabularyitem_set.filter(word__iexact="hypothesis").count(),
            1,
        )

    def test_vocab_seeds_default_approved_only(self):
        from tutor.models import VocabularySeed

        VocabularySeed.objects.create(
            word="pendingword",
            category="toefl_academic",
            part_of_speech="noun",
            definition="Pending",
            approved=False,
            is_active=True,
        )
        VocabularySeed.objects.create(
            word="approvedword",
            category="toefl_academic",
            part_of_speech="noun",
            definition="Approved",
            approved=True,
            is_active=True,
        )
        response = self.client.get("/api/vocab/seeds/?category=toefl_academic")
        words = [s["word"] for s in response.json()["seeds"]]
        self.assertIn("approvedword", words)
        self.assertNotIn("pendingword", words)

    def test_category_stats(self):
        response = self.client.get("/api/vocab/category-stats/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)
        self.assertIn("approved", response.json()[0])

    def test_add_random_from_category(self):
        from tutor.models import VocabularySeed

        for index in range(3):
            VocabularySeed.objects.create(
                word=f"word{index}",
                category="toefl_academic",
                part_of_speech="noun",
                definition=f"Definition {index}",
                approved=True,
                is_active=True,
            )
        response = self.client.post(
            "/api/vocab/add-random-from-category/",
            {"category": "toefl_academic", "count": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["created_count"], 2)


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="authlearner",
            password="testpass123",
            email="learner@test.com",
        )

    def test_root_redirects_to_frontend(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"].rstrip("/"), "http://localhost:5173")

    def test_api_health(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["frontend"], "http://localhost:5173")
        self.assertEqual(data["admin"], "/admin/")
        self.assertEqual(data["api"], "/api/")

    def test_me_unauthenticated(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])

    def test_csrf_endpoint(self):
        response = self.client.get("/api/csrf/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_login_logout_flow(self):
        self.client.get("/api/csrf/")
        token = self.client.cookies["csrftoken"].value
        login_response = self.client.post(
            "/api/auth/login/",
            {"username": "authlearner", "password": "testpass123"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["authenticated"])

        me_response = self.client.get("/api/auth/me/")
        self.assertTrue(me_response.json()["authenticated"])

        self.client.get("/api/csrf/")
        token = self.client.cookies["csrftoken"].value
        logout_response = self.client.post(
            "/api/auth/logout/",
            {},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue(logout_response.json()["success"])

    def test_dashboard_requires_auth(self):
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 403)

        self.client.login(username="authlearner", password="testpass123")
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile", data)
        self.assertIn("coach_focus", data)
        self.assertIn("main_weakness", data["coach_focus"])
        self.assertIn("why_it_matters", data["coach_focus"])
        self.assertIn("recommended_action", data["coach_focus"])
        self.assertIn("action_route", data["coach_focus"])
        self.assertIn("today_focus", data["coach_focus"])
        self.assertIn("focus_action", data["coach_focus"])
        self.assertIn("empty_states", data["coach_focus"])
        self.assertIn("vocab_due_message", data["coach_focus"]["empty_states"])


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class PlanAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="planuser",
            password="testpass123",
        )
        self.client.login(username="planuser", password="testpass123")

    def test_plan_get_without_plan_returns_empty_state(self):
        response = self.client.get("/api/plan/today/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["exists"])
        self.assertEqual(data["items"], [])
        self.assertIn("vocab_due", data)
        self.assertIn("mistakes_due", data)

    def test_generate_plan_uses_due_items(self):
        from datetime import date

        from tutor.models import Mistake, VocabularyItem

        VocabularyItem.objects.create(
            user=self.user,
            word="analyze",
            definition="Examine",
            next_review_date=date.today(),
        )
        Mistake.objects.create(
            user=self.user,
            track="grammar",
            wrong_text="He go to school",
            correct_text="He goes to school",
            reason="Subject-verb agreement",
            next_review_date=date.today(),
        )

        response = self.client.post("/api/plan/today/generate/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["exists"])
        self.assertGreater(data["total_count"], 0)
        types = {item["type"] for item in data["items"]}
        self.assertIn("vocab", types)
        self.assertIn("mistake", types)
        self.assertIn("track", types)

    def test_plan_tasks_include_tutor_fields(self):
        from datetime import date

        from tutor.models import Mistake, VocabularyItem

        VocabularyItem.objects.create(
            user=self.user,
            word="analyze",
            definition="Examine in detail",
            next_review_date=date.today(),
        )
        Mistake.objects.create(
            user=self.user,
            track="grammar_coach",
            wrong_text="I saw an book.",
            correct_text="I saw a book.",
            reason="Article error",
            category="article",
            next_review_date=date.today(),
        )

        response = self.client.post("/api/plan/today/generate/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("main_focus", data["summary"])
        self.assertIn("why_it_matters", data["summary"])
        self.assertIn("recommended_order", data["summary"])

        for item in data["items"]:
            self.assertIn("reason", item)
            self.assertTrue(item["reason"])
            self.assertIn("route", item)
            self.assertIn("status", item)
            self.assertIn("skill", item)
            self.assertNotIn("_coach", item.get("skill", ""))

        mistake_item = next(item for item in data["items"] if item["type"] == "mistake")
        self.assertTrue(
            mistake_item["route"].startswith("/lesson?topic=")
            or mistake_item["route"].startswith("/mistakes?focus=")
        )

    def test_generate_plan_twice_fails(self):
        self.client.post("/api/plan/today/generate/", {}, format="json")
        response = self.client.post("/api/plan/today/generate/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_update_plan_item(self):
        self.client.post("/api/plan/today/generate/", {}, format="json")
        plan = self.client.get("/api/plan/today/").json()
        item_id = plan["items"][0]["id"]
        response = self.client.post(
            "/api/plan/today/",
            {"item_id": item_id, "completed": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        updated = response.json()
        first = next(item for item in updated["items"] if item["id"] == item_id)
        self.assertTrue(first["completed"])
        self.assertEqual(updated["completed_count"], 1)


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class LessonAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="lessonuser",
            password="testpass123",
        )
        self.client.login(username="lessonuser", password="testpass123")
        from django.core.management import call_command

        call_command("seed_lesson_topics")

    def test_lesson_recommendation(self):
        response = self.client.get("/api/lesson/recommendation/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommended_topic", data)
        self.assertIn("reason", data)
        self.assertIn("starter_message", data)
        self.assertIsNotNone(data["recommended_topic"])

    def test_lesson_topics_list(self):
        response = self.client.get("/api/lesson/topics/")
        self.assertEqual(response.status_code, 200)
        topics = response.json()["topics"]
        self.assertGreaterEqual(len(topics), 14)
        self.assertEqual(topics[0]["status"], "not_started")

    @patch(
        "tutor.views.run_task",
        return_value={"reply": "Welcome to today's lesson.", "corrections": []},
    )
    def test_start_recommended_lesson(self, _mock_run_task):
        from tutor.models import LessonTopic

        topic = LessonTopic.objects.order_by("order").first()
        response = self.client.post(
            "/api/lesson/start-recommended/",
            {"topic_id": topic.id, "provider": "ollama"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertEqual(data["reply"], "Welcome to today's lesson.")

        progress = topic.lessonprogress_set.get(user=self.user)
        self.assertEqual(progress.status, "started")

    def test_complete_lesson(self):
        from tutor.models import LessonTopic

        topic = LessonTopic.objects.order_by("order").first()
        response = self.client.post(
            "/api/lesson/complete/",
            {"topic_id": topic.id, "score": 85, "notes": "Good session"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["progress"]["status"], "completed")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
    OLLAMA_HOST="http://127.0.0.1:11435",
)
class OllamaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ollamauser",
            password="testpass123",
        )
        self.client.login(username="ollamauser", password="testpass123")

    @patch(
        "tutor.views.fetch_ollama_tags",
        return_value=(
            True,
            ["qwen2.5:7b", "llama3.2:3b", "nomic-embed-text:latest"],
            None,
        ),
    )
    def test_ollama_status_ok(self, _mock):
        response = self.client.get("/api/ollama/status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["host"], "http://127.0.0.1:11435")
        self.assertIn("qwen2.5:7b", data["models"])
        self.assertEqual(data["missing_recommended_models"], [])

    @patch(
        "tutor.views.fetch_ollama_tags",
        return_value=(False, [], "Ollama unreachable at http://127.0.0.1:11435"),
    )
    def test_ollama_status_unreachable(self, _mock):
        response = self.client.get("/api/ollama/status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertIn("error", data)


@override_settings(
    OLLAMA_HOST="http://127.0.0.1:11435",
    DEFAULT_OLLAMA_MODEL="qwen2.5:7b",
    FAST_OLLAMA_MODEL="llama3.2:3b",
)
class FixOllamaModelNamesTests(TestCase):
    def test_fix_command_updates_legacy_names(self):
        from django.core.management import call_command
        from io import StringIO

        from tutor.models import PromptTemplate

        PromptTemplate.objects.filter(provider="ollama").update(model_name="llama3.2")

        call_command("fix_ollama_model_names", stdout=StringIO())

        grammar = PromptTemplate.objects.get(
            task_type="grammar_coach",
            provider="ollama",
            title="Grammar Coach (Ollama)",
        )
        vocab = PromptTemplate.objects.get(
            task_type="vocab_builder",
            provider="ollama",
            title="Vocab Builder (Ollama)",
        )
        self.assertEqual(grammar.model_name, "qwen2.5:7b")
        self.assertEqual(vocab.model_name, "llama3.2:3b")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class AdminPromptAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="learneruser",
            password="testpass123",
        )
        self.staff = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )

    def test_admin_prompts_forbidden_for_learner(self):
        self.client.login(username="learneruser", password="testpass123")
        response = self.client.get("/api/admin/prompts/")
        self.assertEqual(response.status_code, 403)

    def test_admin_prompts_accessible_for_staff(self):
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get("/api/admin/prompts/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("prompts", response.json())


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class VocabQuizMistakeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="vocabquizuser",
            password="testpass123",
        )
        self.client.login(username="vocabquizuser", password="testpass123")

    def test_record_vocab_quiz_mistake(self):
        response = self.client.post(
            "/api/mistakes/vocab/",
            {
                "word": "accurate",
                "wrong_answer": "very fast",
                "meaning_en": "correct and exact",
                "meaning_fa": "دقیق",
                "example": "The diagnosis was accurate.",
                "quiz_mode": "multiple_choice",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["track"], "vocab_quiz")
        self.assertEqual(data["correct_text"], "accurate")
        self.assertEqual(data["wrong_text"], "very fast")

        list_response = self.client.get("/api/mistakes/")
        self.assertEqual(list_response.status_code, 200)
        mistakes = list_response.json()["mistakes"]
        self.assertEqual(len(mistakes), 1)
        self.assertEqual(mistakes[0]["track"], "vocab_quiz")

    def test_vocab_quiz_mistake_dedupes_by_word(self):
        payload = {
            "word": "hypothesis",
            "wrong_answer": "guess A",
            "meaning_en": "an idea to test",
        }
        first = self.client.post("/api/mistakes/vocab/", payload, format="json")
        second = self.client.post(
            "/api/mistakes/vocab/",
            {**payload, "wrong_answer": "guess B"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["wrong_text"], "guess B")

        from tutor.models import Mistake

        self.assertEqual(
            Mistake.objects.filter(user=self.user, track="vocab_quiz").count(),
            1,
        )


class WritingEditParserTests(TestCase):
    def test_parse_structured_json(self):
        from tutor.services import parse_writing_edit_response

        raw = """{
          "edited_text": "I like spring because the weather is good.",
          "changes": ["Added article 'the' before weather."],
          "teaching_notes": ["Use 'the weather' for specific weather."],
          "sentence_comparisons": [
            {"original": "weather is good", "improved": "the weather is good", "reason": "Add article"}
          ],
          "level_feedback": "Your edited paragraph matches the Normal level.",
          "better_alternative": "Spring is my favorite season because the weather is pleasant."
        }"""
        result = parse_writing_edit_response(raw)
        self.assertTrue(result["structured"])
        self.assertIn("spring", result["edited_text"])
        self.assertEqual(len(result["changes"]), 1)
        self.assertEqual(len(result["sentence_comparisons"]), 1)
        self.assertIn("Normal level", result["level_feedback"])
        self.assertIn("Spring", result["better_alternative"])

    def test_parse_invalid_json_fallback(self):
        from tutor.services import parse_writing_edit_response

        result = parse_writing_edit_response("I like spring because the weather is good.")
        self.assertFalse(result["structured"])
        self.assertIn("not fully structured", result["notice"])
        self.assertIn("spring", result["edited_text"])

    def test_build_prompt_includes_all_controls(self):
        from tutor.prompts.writing_edit import build_writing_edit_user_message

        message = build_writing_edit_user_message(
            "I like spring because weather is good.",
            "strong",
            "toefl_writing",
            "beginner",
        )
        self.assertIn("Strong rewrite", message)
        self.assertIn("TOEFL Writing", message)
        self.assertIn("Beginner", message)
        self.assertIn("sentence complexity", message)
        self.assertIn("mostly under 15 words", message)
        self.assertIn("How the controls work together", message)


class WritingEditViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="edituser", password="testpass123")
        self.client.login(username="edituser", password="testpass123")

    def test_empty_text_validation(self):
        response = self.client.post("/api/writing/edit/", {"text": "   "}, format="json")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        message = body.get("detail") or body.get("text", [""])[0]
        self.assertIn("paste a paragraph", str(message))

    def test_gibberish_text_validation(self):
        response = self.client.post(
            "/api/writing/edit/",
            {"text": "iuhb0uybb uyb ouyb uyb ouyb"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        message = body.get("detail") or body.get("text", [""])[0]
        self.assertIn("real English paragraph", str(message))

    @patch(
        "tutor.views.run_writing_edit",
        return_value={
            "edited_text": "I like spring because the weather is good.",
            "changes": ["Fixed grammar."],
            "teaching_notes": ["Use the before weather."],
            "sentence_comparisons": [],
            "level_feedback": "Matches Beginner level.",
            "better_alternative": "",
            "structured": True,
            "notice": None,
            "edit_strength": "light",
            "target_style": "simple_american_english",
            "language_level": "beginner",
        },
    )
    def test_writing_edit_with_language_level(self, mock_run):
        response = self.client.post(
            "/api/writing/edit/",
            {
                "text": "I like spring because weather is good.",
                "edit_strength": "light",
                "target_style": "simple_american_english",
                "language_level": "beginner",
                "ai_provider": "ollama",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["language_level"], "beginner")
        data = response.json()["edit_result"]
        self.assertEqual(data["language_level"], "beginner")
        self.assertIn("Beginner", data["level_feedback"])

    @patch(
        "tutor.views.run_writing_edit",
        return_value={
            "edited_text": "I like spring because the weather is good.",
            "changes": ["Fixed grammar."],
            "teaching_notes": ["Use the before weather."],
            "sentence_comparisons": [],
            "structured": True,
            "notice": None,
            "edit_strength": "standard",
            "target_style": "simple_american_english",
            "language_level": "normal",
        },
    )
    def test_writing_edit_success(self, _mock_run):
        response = self.client.post(
            "/api/writing/edit/",
            {
                "text": "I like spring because weather is good.",
                "edit_strength": "standard",
                "target_style": "simple_american_english",
                "ai_provider": "ollama",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["edit_result"]
        self.assertIn("edited_text", data)
        self.assertEqual(data["changes"], ["Fixed grammar."])


class WritingEditGenerateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="editgen", password="testpass123")
        self.client.login(username="editgen", password="testpass123")

    def test_parse_generate_json(self):
        from tutor.services import parse_writing_edit_generate_response

        raw = """{
          "draft_text": "I like spring because weather is good and I can walking outside.",
          "teaching_tip": "Look for verb forms and missing articles."
        }"""
        result = parse_writing_edit_generate_response(raw)
        self.assertTrue(result["structured"])
        self.assertIn("spring", result["draft_text"])
        self.assertIn("articles", result["teaching_tip"])

    @patch(
        "tutor.views.run_writing_edit_generate",
        return_value={
            "draft_text": "I like spring because weather is good and I can walking outside.",
            "teaching_tip": "Check verb forms.",
            "structured": True,
            "notice": None,
            "target_style": "toefl_writing",
            "language_level": "normal",
        },
    )
    def test_generate_endpoint(self, mock_run):
        response = self.client.post(
            "/api/writing/edit/generate/",
            {
                "target_style": "toefl_writing",
                "language_level": "normal",
                "ai_provider": "ollama",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        mock_run.assert_called_once()
        data = response.json()
        self.assertIn("spring", data["draft_text"])


class ParaphraseParserTests(TestCase):
    def test_parse_generate_json(self):
        from tutor.services import parse_paraphrase_generate_response

        raw = '{"original_text": "Exercise improves health.", "teaching_tip": "Change structure."}'
        result = parse_paraphrase_generate_response(raw)
        self.assertTrue(result["structured"])
        self.assertIn("Exercise", result["original_text"])

    def test_parse_check_json(self):
        from tutor.services import parse_paraphrase_check_response

        raw = """{
          "overall_score": 85,
          "meaning_accuracy_score": 90,
          "grammar_score": 80,
          "naturalness_score": 85,
          "vocabulary_score": 80,
          "level_match_score": 85,
          "result_label": "Good paraphrase",
          "language_level_feedback": "Your paraphrase matches the Normal level well.",
          "feedback": ["Good meaning."],
          "better_version": "Better text.",
          "comparison": {
            "original": "A",
            "learner_paraphrase": "B",
            "better_paraphrase": "Better text."
          },
          "teaching_notes": ["Change structure."]
        }"""
        result = parse_paraphrase_check_response(
            raw, original_text="A", learner_paraphrase="B"
        )
        self.assertTrue(result["structured"])
        self.assertEqual(result["overall_score"], 85)
        self.assertEqual(result["level_match_score"], 85)
        self.assertEqual(result["result_label"], "Good paraphrase")


class ParaphraseViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="parauser", password="testpass123")
        self.client.login(username="parauser", password="testpass123")

    @patch(
        "tutor.views.run_paraphrase_generate",
        return_value={
            "original_text": "Many students prefer online classes.",
            "teaching_tip": "Use your own words.",
            "structured": True,
            "notice": None,
            "target_level": "simple_american_english",
            "difficulty": "easy",
            "text_type": "one_sentence",
        },
    )
    def test_generate_paraphrase(self, _mock_run):
        response = self.client.post(
            "/api/writing/paraphrasing/generate/",
            {
                "target_level": "simple_american_english",
                "difficulty": "easy",
                "text_type": "one_sentence",
                "ai_provider": "ollama",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("original_text", response.json())

    def test_check_missing_paraphrase(self):
        response = self.client.post(
            "/api/writing/paraphrasing/check/",
            {
                "original_text": "Exercise improves health.",
                "learner_paraphrase": "   ",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class LearnerTextValidationTests(TestCase):
    def test_accepts_legitimate_short_mistakes(self):
        from tutor.utils.text_validation import is_meaningful_learner_text

        for text in ("studing", "an book", "Best regaurd", "I agree", "He go to school"):
            with self.subTest(text=text):
                self.assertTrue(is_meaningful_learner_text(text))

    def test_rejects_garbage_keyboard_smash(self):
        from tutor.utils.text_validation import is_meaningful_learner_text

        garbage = "iuhb0uybb uyb ouyb uyb ouyb"
        self.assertFalse(is_meaningful_learner_text(garbage))
        self.assertFalse(is_meaningful_learner_text("   "))
        self.assertFalse(is_meaningful_learner_text("asdf qwer zxcv tyui"))


class SaveMistakesValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mistakefilteruser",
            password="testpass123",
        )

    def test_save_mistakes_skips_garbage(self):
        from tutor.models import Mistake
        from tutor.services import save_mistakes

        save_mistakes(
            self.user,
            "grammar",
            [
                {
                    "wrong_text": "iuhb0uybb uyb ouyb uyb ouyb",
                    "correct_text": "I enjoy spring weather.",
                    "reason": "Not meaningful input",
                },
                {
                    "wrong_text": "He go to school",
                    "correct_text": "He goes to school",
                    "reason": "Subject-verb agreement",
                },
            ],
        )

        mistakes = Mistake.objects.filter(user=self.user)
        self.assertEqual(mistakes.count(), 1)
        self.assertEqual(mistakes.first().wrong_text, "He go to school")

    def test_normalize_correction_rejects_garbage(self):
        from tutor.services import normalize_correction

        self.assertIsNone(
            normalize_correction(
                {
                    "wrong": "iuhb0uybb uyb ouyb uyb ouyb",
                    "correct": "I enjoy spring weather.",
                }
            )
        )
        self.assertIsNotNone(
            normalize_correction(
                {
                    "wrong": "studing",
                    "correct": "studying",
                }
            )
        )


class PlanMistakeFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="planfilteruser",
            password="testpass123",
        )
        self.client.login(username="planfilteruser", password="testpass123")

    def test_plan_excludes_garbage_mistakes(self):
        from datetime import date

        from tutor.models import Mistake, StudyPlan

        good = Mistake.objects.create(
            user=self.user,
            track="grammar",
            wrong_text="He go to school",
            correct_text="He goes to school",
            reason="Subject-verb agreement",
            next_review_date=date.today(),
        )
        bad = Mistake.objects.create(
            user=self.user,
            track="writing_edit_coach",
            wrong_text="iuhb0uybb uyb ouyb uyb ouyb",
            correct_text="I enjoy spring weather.",
            reason="Garbage input",
            next_review_date=date.today(),
        )

        StudyPlan.objects.create(
            user=self.user,
            date=date.today(),
            items=[
                {
                    "id": f"mistake-{good.id}",
                    "type": "mistake",
                    "track": good.track,
                    "title": f"Review mistake: {good.wrong_text}",
                    "minutes": 5,
                    "completed": False,
                    "ref_id": good.id,
                },
                {
                    "id": f"mistake-{bad.id}",
                    "type": "mistake",
                    "track": bad.track,
                    "title": f"Review mistake: {bad.wrong_text[:50]}",
                    "minutes": 5,
                    "completed": False,
                    "ref_id": bad.id,
                },
            ],
        )

        response = self.client.get("/api/plan/today/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        mistake_items = [item for item in data["items"] if item["type"] == "mistake"]
        self.assertEqual(len(mistake_items), 1)
        self.assertEqual(mistake_items[0]["ref_id"], good.id)
        self.assertEqual(data["mistakes_due"], 1)

    def test_generate_plan_skips_garbage_mistakes(self):
        from datetime import date

        from tutor.models import Mistake

        Mistake.objects.create(
            user=self.user,
            track="grammar",
            wrong_text="He go to school",
            correct_text="He goes to school",
            reason="Subject-verb agreement",
            next_review_date=date.today(),
        )
        Mistake.objects.create(
            user=self.user,
            track="writing_edit_coach",
            wrong_text="iuhb0uybb uyb ouyb uyb ouyb",
            correct_text="I enjoy spring weather.",
            reason="Garbage input",
            next_review_date=date.today(),
        )

        response = self.client.post("/api/plan/today/generate/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        mistake_items = [
            item for item in response.json()["items"] if item["type"] == "mistake"
        ]
        self.assertEqual(len(mistake_items), 1)
        self.assertIn("He go to school", mistake_items[0]["title"])


class MistakeClassificationTests(TestCase):
    def test_classification_examples(self):
        from tutor.utils.mistake_classification import classify_mistake

        cases = [
            (
                "I saw an book.",
                "I saw a book.",
                "Use a before consonant sounds.",
                "grammar_coach",
                "article",
            ),
            (
                "studing",
                "studying",
                "Spelling error.",
                "writing_coach",
                "spelling",
            ),
            (
                "My favorite hobby traveling.",
                "My favorite hobby is traveling.",
                "Missing linking verb.",
                "writing_coach",
                "sentence_structure",
            ),
            (
                "which make it hard",
                "which makes it hard",
                "Subject-verb agreement.",
                "grammar_coach",
                "subject_verb_agreement",
            ),
            (
                "Best regaurd",
                "Best regards",
                "Misspelling.",
                "writing_coach",
                "spelling",
            ),
        ]

        for wrong, correct, reason, track, expected in cases:
            with self.subTest(wrong=wrong):
                self.assertEqual(
                    classify_mistake(wrong, correct, reason, track),
                    expected,
                )

    def test_save_mistakes_assigns_category(self):
        from tutor.models import Mistake
        from tutor.services import save_mistakes

        user = User.objects.create_user(
            username="categoryuser",
            password="testpass123",
        )
        save_mistakes(
            user,
            "grammar_coach",
            [
                {
                    "wrong_text": "I saw an book.",
                    "correct_text": "I saw a book.",
                    "reason": "Article error before consonant sound.",
                    "persian_explanation": "",
                    "review_sentence": "",
                }
            ],
        )

        mistake = Mistake.objects.get(user=user)
        self.assertEqual(mistake.category, "article")

    def test_mistakes_api_includes_category(self):
        from tutor.models import Mistake

        user = User.objects.create_user(
            username="categoryapiuser",
            password="testpass123",
        )
        Mistake.objects.create(
            user=user,
            track="grammar_coach",
            wrong_text="He go to school",
            correct_text="He goes to school",
            reason="Subject-verb agreement",
            category="subject_verb_agreement",
        )

        client = APIClient()
        client.login(username="categoryapiuser", password="testpass123")
        response = client.get("/api/mistakes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mistakes"][0]["category"], "subject_verb_agreement")

