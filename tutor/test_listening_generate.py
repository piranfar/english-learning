import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tutor.learning_journey import STAGE1_SLUG, STAGE2_SLUG
from tutor.listening_practice import (
    build_fallback_listening_practice,
    build_listening_generate_user_message,
    gather_listening_context,
    parse_listening_practice,
    resolve_listening_settings,
    score_listening_session,
)
from tutor.models import ListeningQuestionAttempt, ListeningSession, Mistake
from tutor.services import get_user_profile

User = get_user_model()

SAMPLE_TRANSCRIPT = (
    "Professor: Today we're going to talk about how universities support open access research. "
    "A recent study found that open libraries help learners read more academic articles. "
    "However, many students still struggle with article use when they write in English. "
    "The researchers interviewed two hundred undergraduates and reviewed their writing samples. "
    "Although the students understood the main ideas, they often chose the wrong article before a noun. "
    "Therefore, instructors now recommend short daily reading and listening tasks with focused feedback. "
    "In contrast, students who practiced article patterns improved faster on timed tests. "
    "The study was published by a team at a public university in 2024. "
    "These findings suggest that targeted practice can support academic success for many learners. "
)

SAMPLE_LISTENING_PAYLOAD = {
    "title": "Open Access Research at Universities",
    "level": "B1",
    "stage": STAGE1_SLUG,
    "listening_type": "academic_mini_lecture",
    "topic": "University Life",
    "lesson_focus": "articles",
    "transcript": SAMPLE_TRANSCRIPT,
    "estimated_duration_seconds": 90,
    "target_vocabulary": [
        {
            "word": "undergraduates",
            "definition": "university students who do not yet have a degree",
            "example": "The researchers interviewed two hundred undergraduates.",
        }
    ],
    "questions": [
        {
            "id": "q1",
            "type": "main_idea",
            "question": "What is the main idea of the lecture?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "The lecture focuses on article practice and open access research.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q2",
            "type": "vocabulary_in_context",
            "question": "Which article fits before 'university'?",
            "choices": ["a", "an", "the", "no article"],
            "correct_answer": "a",
            "explanation": "University starts with a consonant sound.",
            "mistake_category": "article",
        },
        {
            "id": "q3",
            "type": "detail",
            "question": "How many undergraduates were interviewed?",
            "choices": ["100", "200", "300", "400"],
            "correct_answer": "200",
            "explanation": "The lecture states two hundred undergraduates.",
            "mistake_category": "listening_comprehension",
        },
        {
            "id": "q4",
            "type": "inference",
            "question": "What can be inferred about article practice?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "C",
            "explanation": "Targeted practice helped students improve.",
            "mistake_category": "listening_comprehension",
        },
    ],
    "shadowing_sentences": [
        "A recent study found that open libraries help learners read more academic articles.",
        "These findings suggest that targeted practice can support academic success for many learners.",
    ],
}


def listening_ai_response() -> str:
    return f"---LISTENING_PRACTICE---\n{json.dumps(SAMPLE_LISTENING_PAYLOAD)}\n---END_LISTENING_PRACTICE---"


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    CSRF_TRUSTED_ORIGINS=["http://testserver"],
)
class ListeningGenerateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="listeninggenuser",
            password="testpass123",
        )
        self.profile = get_user_profile(self.user)
        self.profile.weak_areas = []
        self.profile.save()
        self.client.login(username="listeninggenuser", password="testpass123")

    # --- parser ---

    def test_parse_listening_practice_accepts_schema(self):
        parsed = parse_listening_practice(listening_ai_response())
        self.assertEqual(parsed["title"], "Open Access Research at Universities")
        self.assertEqual(parsed["lesson_focus"], "articles")
        self.assertGreaterEqual(len(parsed["questions"]), 4)
        self.assertEqual(parsed["questions"][1]["mistake_category"], "article")
        self.assertEqual(len(parsed["shadowing_sentences"]), 2)
        self.assertEqual(parsed["estimated_duration_seconds"], 90)

    def test_parse_listening_practice_rejects_missing_block(self):
        with self.assertRaises(ValueError):
            parse_listening_practice("not a structured reply at all")

    def test_parse_listening_practice_rejects_invalid_json(self):
        broken = "---LISTENING_PRACTICE---\n{not valid json\n---END_LISTENING_PRACTICE---"
        with self.assertRaises(ValueError):
            parse_listening_practice(broken)

    def test_parse_listening_practice_rejects_too_few_questions(self):
        payload = dict(SAMPLE_LISTENING_PAYLOAD)
        payload["questions"] = SAMPLE_LISTENING_PAYLOAD["questions"][:2]
        raw = f"---LISTENING_PRACTICE---\n{json.dumps(payload)}\n---END_LISTENING_PRACTICE---"
        with self.assertRaises(ValueError):
            parse_listening_practice(raw)

    def test_parse_listening_practice_rejects_short_transcript(self):
        payload = dict(SAMPLE_LISTENING_PAYLOAD)
        payload["transcript"] = "Too short."
        raw = f"---LISTENING_PRACTICE---\n{json.dumps(payload)}\n---END_LISTENING_PRACTICE---"
        with self.assertRaises(ValueError):
            parse_listening_practice(raw)

    def test_parse_listening_practice_tolerates_literal_newlines_in_strings(self):
        # Small local models frequently emit real line breaks inside JSON string
        # values (e.g. multi-paragraph transcripts) instead of escaping them as
        # \n, which a strict json.loads() rejects. The parser must still accept it.
        raw = (
            "---LISTENING_PRACTICE---\n"
            "{\n"
            '  "title": "Paragraph Breaks",\n'
            '  "level": "B1",\n'
            f'  "stage": "{STAGE1_SLUG}",\n'
            '  "listening_type": "academic_mini_lecture",\n'
            '  "topic": "Science",\n'
            '  "lesson_focus": "none",\n'
            '  "transcript": "' + SAMPLE_TRANSCRIPT.replace(". ", ".\n\n") + '",\n'
            '  "estimated_duration_seconds": 90,\n'
            '  "target_vocabulary": [],\n'
            '  "questions": ' + json.dumps(SAMPLE_LISTENING_PAYLOAD["questions"]) + ",\n"
            '  "shadowing_sentences": []\n'
            "}\n"
            "---END_LISTENING_PRACTICE---"
        )
        parsed = parse_listening_practice(raw)
        self.assertIn("universities", parsed["transcript"].lower())

    def test_parse_listening_practice_strips_inline_shadowing_boilerplate(self):
        payload = dict(SAMPLE_LISTENING_PAYLOAD)
        payload["transcript"] = (
            SAMPLE_TRANSCRIPT + "\n\nShadowing sentences:\n- One.\n- Two.\n"
        )
        raw = f"---LISTENING_PRACTICE---\n{json.dumps(payload)}\n---END_LISTENING_PRACTICE---"
        parsed = parse_listening_practice(raw)
        self.assertNotIn("Shadowing sentences", parsed["transcript"])

    # --- stage settings ---

    def test_stage_settings_differ_by_stage(self):
        stage1 = resolve_listening_settings(STAGE1_SLUG, "toefl_style")
        stage2 = resolve_listening_settings(STAGE2_SLUG, "toefl_style")
        self.assertLess(stage1["word_max"], stage2["word_min"])
        self.assertLess(stage1["question_min"], stage2["question_min"])
        self.assertGreaterEqual(stage1["word_min"], 150)
        self.assertLessEqual(stage1["word_max"], 350)
        self.assertGreaterEqual(stage2["word_min"], 450)
        self.assertLessEqual(stage2["word_max"], 800)
        self.assertGreaterEqual(stage1["question_min"], 4)
        self.assertLessEqual(stage1["question_max"], 6)
        self.assertGreaterEqual(stage2["question_min"], 6)
        self.assertLessEqual(stage2["question_max"], 10)

    def test_generate_user_message_includes_level_stage_and_lesson_focus(self):
        context = gather_listening_context(self.user)
        message = build_listening_generate_user_message(
            level="B1",
            stage=STAGE1_SLUG,
            listening_type="academic_mini_lecture",
            topic="University Life",
            lesson_focus="articles",
            length="medium",
            speed="normal",
            context=context,
        )
        self.assertIn("Student level: B1", message)
        self.assertIn(STAGE1_SLUG, message)
        self.assertIn("articles", message.lower())
        self.assertIn("academic_mini_lecture", message)

    # --- endpoint ---

    @patch("tutor.listening_practice.generate_from_template")
    def test_generate_listening_practice_endpoint(self, mock_generate):
        mock_generate.return_value = listening_ai_response()
        response = self.client.post(
            "/api/listening/generate-practice/",
            {
                "level": "B1",
                "stage": STAGE1_SLUG,
                "listening_type": "academic_mini_lecture",
                "topic": "University Life",
                "lesson_focus": "articles",
                "length": "short",
                "speed": "normal",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session = response.json()["session"]
        self.assertIn("session_id", session)
        self.assertIn("transcript", session)
        self.assertNotIn("correct_answer", session["questions"][0])
        self.assertTrue(
            ListeningSession.objects.filter(user=self.user, lesson_focus="articles").exists()
        )

    @patch("tutor.listening_practice.generate_from_template")
    def test_invalid_ai_output_falls_back_to_builtin_sample(self, mock_generate):
        mock_generate.return_value = "the model said something unparseable"
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session = response.json()["session"]
        self.assertIn("transcript", session)
        self.assertGreaterEqual(len(session["questions"]), 4)
        self.assertGreaterEqual(len(session.get("shadowing_sentences", [])), 1)
        self.assertEqual(session["provider_metadata"]["provider"], "fallback")
        self.assertEqual(session["provider_metadata"]["model"], "built-in")
        self.assertTrue(session["provider_metadata"]["used_fallback"])
        self.assertEqual(session["learner_message"], "Using local AI or sample practice.")
        self.assertNotIn("API_KEY", response.content.decode())
        self.assertTrue(ListeningSession.objects.filter(user=self.user).exists())

    @override_settings(
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        GEMINI_API_KEY="",
        DEFAULT_AI_PROVIDER="anthropic",
    )
    @patch("tutor.listening_practice.generate_from_template")
    def test_missing_anthropic_key_falls_back_without_error(self, mock_generate):
        mock_generate.side_effect = RuntimeError("ANTHROPIC_API_KEY is not configured")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "provider": "anthropic"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("session", body)
        self.assertNotIn("ANTHROPIC_API_KEY", response.content.decode())
        self.assertTrue(body["session"]["provider_metadata"]["used_fallback"])

    @override_settings(
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        GEMINI_API_KEY="",
        DEFAULT_AI_PROVIDER="openai",
    )
    @patch("tutor.listening_practice.generate_from_template")
    def test_missing_openai_key_falls_back_without_error(self, mock_generate):
        mock_generate.side_effect = RuntimeError("OPENAI_API_KEY is not configured")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "provider": "openai"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("OPENAI_API_KEY", response.content.decode())
        self.assertTrue(body["session"]["provider_metadata"]["used_fallback"])

    @override_settings(
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
        GEMINI_API_KEY="",
        DEFAULT_AI_PROVIDER="gemini",
    )
    @patch("tutor.listening_practice.generate_from_template")
    def test_missing_gemini_key_falls_back_without_error(self, mock_generate):
        mock_generate.side_effect = RuntimeError("GEMINI_API_KEY is not configured")
        response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "provider": "gemini"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("GEMINI_API_KEY", response.content.decode())
        self.assertTrue(body["session"]["provider_metadata"]["used_fallback"])

    def test_fallback_sample_includes_required_fields(self):
        parsed = build_fallback_listening_practice(
            level="B1",
            stage=STAGE1_SLUG,
            listening_type="academic_mini_lecture",
            topic="University Life",
            lesson_focus="articles",
        )
        self.assertIn("title", parsed)
        self.assertIn("transcript", parsed)
        self.assertGreaterEqual(len(parsed["transcript"].split()), 150)
        self.assertGreaterEqual(len(parsed["questions"]), 4)
        self.assertLessEqual(len(parsed["questions"]), 6)
        self.assertGreaterEqual(len(parsed["shadowing_sentences"]), 1)

        stage2 = build_fallback_listening_practice(
            level="B2",
            stage=STAGE2_SLUG,
            listening_type="toefl_style_lecture",
            topic="Science",
            lesson_focus="none",
        )
        self.assertGreaterEqual(len(stage2["transcript"].split()), 450)
        self.assertGreaterEqual(len(stage2["questions"]), 6)
        self.assertLessEqual(len(stage2["questions"]), 10)

    @patch("tutor.listening_practice.generate_from_template")
    def test_submit_saves_mistakes_and_attempts(self, mock_generate):
        mock_generate.return_value = listening_ai_response()
        generate_response = self.client.post(
            "/api/listening/generate-practice/",
            {"level": "B1", "stage": STAGE1_SLUG, "lesson_focus": "articles"},
            format="json",
        )
        session_id = generate_response.json()["session"]["session_id"]

        submit_response = self.client.post(
            "/api/listening/submit-practice/",
            {
                "session_id": session_id,
                "answers": {"q1": 0, "q2": 1, "q3": 2, "q4": 2},
            },
            format="json",
        )
        self.assertEqual(submit_response.status_code, 200)
        data = submit_response.json()
        self.assertEqual(data["score"]["total"], 4)
        self.assertGreaterEqual(data["mistakes_saved"], 1)
        self.assertIn("transcript", data)

        self.assertEqual(
            ListeningQuestionAttempt.objects.filter(session_id=session_id).count(),
            4,
        )
        article_mistakes = Mistake.objects.filter(
            user=self.user,
            track="listening_coach",
            category="article",
        )
        self.assertGreaterEqual(article_mistakes.count(), 1)
        for mistake in article_mistakes:
            self.assertEqual(mistake.category, "article")

        listening_mistakes = Mistake.objects.filter(
            user=self.user,
            track="listening_coach",
        )
        self.assertTrue(
            all(
                m.category in {"article", "listening_comprehension"}
                for m in listening_mistakes
            )
        )

    def test_score_listening_session_marks_complete(self):
        session = ListeningSession.objects.create(
            user=self.user,
            title="Test",
            level="B1",
            stage=STAGE1_SLUG,
            listening_type="academic_mini_lecture",
            lesson_focus="articles",
            topic="University Life",
            transcript=SAMPLE_TRANSCRIPT,
            questions_json=SAMPLE_LISTENING_PAYLOAD["questions"],
        )
        result = score_listening_session(
            self.user,
            session.id,
            {"q1": 1, "q2": 0, "q3": 1, "q4": 2},
        )
        session.refresh_from_db()
        self.assertIsNotNone(session.completed_at)
        self.assertEqual(result["score"]["correct"], 4)
        self.assertEqual(session.score, 100)

    def test_resubmitting_completed_session_raises(self):
        session = ListeningSession.objects.create(
            user=self.user,
            title="Test",
            level="B1",
            stage=STAGE1_SLUG,
            transcript=SAMPLE_TRANSCRIPT,
            questions_json=SAMPLE_LISTENING_PAYLOAD["questions"],
        )
        score_listening_session(self.user, session.id, {"q1": 1, "q2": 0, "q3": 1, "q4": 2})
        with self.assertRaises(ValueError):
            score_listening_session(self.user, session.id, {"q1": 1, "q2": 0, "q3": 1, "q4": 2})

    # --- plan integration ---

    def test_plan_can_include_listening_tasks(self):
        from datetime import date

        from tutor.plan import build_plan_items

        items = build_plan_items(self.user, date.today())
        listening_items = [item for item in items if item.get("type") == "listening"]
        self.assertTrue(listening_items)
        self.assertIn("listening practice", listening_items[0]["title"].lower())
        self.assertIn("readiness", listening_items[0]["reason"].lower())

    def test_plan_listening_task_reflects_current_lesson_focus(self):
        from datetime import date

        from tutor.learning_journey import get_or_create_journey
        from tutor.models import LessonProgress, LessonTopic
        from tutor.plan import build_plan_items

        journey = get_or_create_journey(self.user)
        stage_slug = journey.current_goal.slug
        passive_voice_topic = LessonTopic.objects.get(stage_slug=stage_slug, slug="passive-voice")

        # Mark every other already-seeded Stage 1 topic as completed so the
        # seeded "Passive voice" topic becomes the resolved current lesson.
        for existing_topic in LessonTopic.objects.filter(
            stage_slug=stage_slug, is_active=True
        ).exclude(id=passive_voice_topic.id):
            LessonProgress.objects.update_or_create(
                user=self.user,
                topic=existing_topic,
                defaults={"status": LessonProgress.STATUS_COMPLETED},
            )

        items = build_plan_items(self.user, date.today())
        listening_items = [item for item in items if item.get("type") == "listening"]
        titles = " ".join(item["title"].lower() for item in listening_items)
        self.assertIn("passive voice", titles)
