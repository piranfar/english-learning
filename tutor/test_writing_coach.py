from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from tutor.models import Mistake
from tutor.services import (
    parse_toefl_writing_feedback,
    parse_writing_feedback,
    parse_writing_revision_compare,
    persist_writing_feedback_mistakes,
    run_writing_revision_compare,
)

User = get_user_model()


class WritingFeedbackParserTests(TestCase):
    def test_parse_writing_feedback_includes_rubric_and_main_mistakes(self):
        raw = """## Overall feedback
Good effort.

---WRITING_FEEDBACK---
{
  "overall_score": 72,
  "rubric": {
    "task_response": {"score": 3, "max": 4, "reason": "Addresses prompt", "next_step": "Add example"},
    "grammar_accuracy": {"score": 2, "max": 4, "reason": "Agreement errors", "next_step": "Check verbs"}
  },
  "main_mistakes": [
    {"wrong": "He go to school", "correct": "He goes to school", "reason": "Subject-verb agreement"}
  ],
  "recommended_revision_task": "Fix verb agreement and add one supporting example.",
  "sentence_corrections": [{"original": "He go", "corrected": "He goes", "why": "SVA"}]
}
---END_WRITING_FEEDBACK---"""

        reply, feedback = parse_writing_feedback(raw)

        self.assertIn("Good effort", reply)
        self.assertEqual(feedback["overall_score"], 72)
        self.assertIn("task_response", feedback["rubric"])
        self.assertEqual(len(feedback["main_mistakes"]), 1)
        self.assertEqual(
            feedback["recommended_revision_task"],
            "Fix verb agreement and add one supporting example.",
        )

    def test_parse_toefl_writing_feedback_includes_estimated_score(self):
        raw = """## Score
Solid attempt.

---TOEFL_WRITING_FEEDBACK---
{
  "estimated_toefl_score": 3.5,
  "scores": {
    "task_response": 3,
    "grammar_accuracy": 2
  },
  "rubric_details": {
    "task_response": {"score": 3, "max": 4, "reason": "On topic", "next_step": "Expand"},
    "grammar_accuracy": {"score": 2, "max": 4, "reason": "Errors", "next_step": "Review tenses"}
  },
  "main_mistakes": [
    {"wrong": "Many student think", "correct": "Many students think", "reason": "Plural noun"}
  ],
  "recommended_revision_task": "Fix plural forms and add a clearer conclusion."
}
---END_TOEFL_WRITING_FEEDBACK---"""

        reply, feedback = parse_toefl_writing_feedback(raw)

        self.assertIn("Solid attempt", reply)
        self.assertEqual(feedback["estimated_toefl_score"], 3.5)
        self.assertEqual(feedback["scores"]["task_response"], 3)
        self.assertEqual(len(feedback["main_mistakes"]), 1)

    def test_parse_writing_json_evaluator_contract(self):
        from tutor.writing_evaluation import parse_writing_evaluator_response

        raw = """{
          "mode": "normal",
          "overall_score": 74,
          "overall_feedback": "Good structure with some grammar issues.",
          "scores": {
            "task_response": 78,
            "organization": 75,
            "grammar": 68,
            "vocabulary": 72,
            "cohesion": 70,
            "sentence_control": 71
          },
          "strengths": ["Clear main idea"],
          "priority_corrections": [
            {
              "type": "grammar",
              "original": "Many student think",
              "corrected": "Many students think",
              "explanation": "Use plural students."
            }
          ],
          "corrected_version": "Many students think education is important.",
          "next_rewrite_drill": {
            "title": "Add a specific reason",
            "instruction": "Rewrite the second sentence using present perfect.",
            "target": "grammar and development"
          }
        }"""

        reply, feedback = parse_writing_evaluator_response(raw)
        self.assertIn("structure", reply)
        self.assertEqual(feedback["overall_score"], 74)
        self.assertEqual(feedback["scores"]["grammar"], 68)
        self.assertEqual(feedback["next_rewrite_drill"]["title"], "Add a specific reason")

    def test_parse_writing_revision_compare(self):
        raw = """## Improvement summary
You fixed several grammar issues.

---WRITING_REVISION_COMPARE---
{
  "improvement_summary": "Clearer organization and fewer grammar errors.",
  "improvements": ["Better topic sentence", "Fixed verb tense"],
  "remaining_issues": ["Word choice still basic"],
  "score_change_note": "Likely higher than the original."
}
---END_WRITING_REVISION_COMPARE---"""

        reply, comparison = parse_writing_revision_compare(raw)

        self.assertIn("grammar issues", reply)
        self.assertEqual(comparison["improvements"], ["Better topic sentence", "Fixed verb tense"])


class WritingFeedbackMistakeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="writer", password="test")

    def test_persist_writing_feedback_mistakes_saves_categorized_mistakes(self):
        feedback = {
            "main_mistakes": [
                {
                    "wrong": "He go to school every day",
                    "correct": "He goes to school every day",
                    "reason": "Subject-verb agreement",
                }
            ],
            "sentence_corrections": [
                {
                    "original": "He go to school every day",
                    "corrected": "He goes to school every day",
                    "why": "Subject-verb agreement",
                }
            ],
        }

        persist_writing_feedback_mistakes(self.user, "writing_coach", feedback)

        mistakes = Mistake.objects.filter(user=self.user, track="writing_coach")
        self.assertEqual(mistakes.count(), 1)
        self.assertEqual(mistakes.first().wrong_text, "He go to school every day")
        self.assertTrue(mistakes.first().category)


class WritingRevisionCompareViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviser", password="test")
        self.client.force_login(self.user)

    @patch("tutor.views.run_writing_revision_compare")
    def test_revision_compare_endpoint(self, mock_compare):
        mock_compare.return_value = {
            "reply": "## Improvement summary\nBetter flow.",
            "comparison": {
                "improvement_summary": "Better flow.",
                "improvements": ["Clearer thesis"],
                "remaining_issues": ["Some word repetition"],
                "score_change_note": "Would likely score higher.",
            },
        }

        response = self.client.post(
            "/api/writing/revision/compare/",
            data={
                "original_answer": "I think online learning is good because flexible.",
                "revised_answer": "I believe online learning is beneficial because it is flexible.",
                "prompt": "Do you prefer online or in-person classes?",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("comparison", payload)
        self.assertEqual(payload["comparison"]["improvements"], ["Clearer thesis"])
        mock_compare.assert_called_once()

    @patch("tutor.services.generate_from_template")
    def test_run_writing_revision_compare_service(self, mock_generate):
        mock_generate.return_value = """## Improvement summary
Nice revision.

---WRITING_REVISION_COMPARE---
{
  "improvement_summary": "Grammar improved.",
  "improvements": ["Fixed articles"],
  "remaining_issues": ["Needs stronger conclusion"],
  "score_change_note": "Higher than original."
}
---END_WRITING_REVISION_COMPARE---"""

        result = run_writing_revision_compare(
            original_answer="Student need more time.",
            revised_answer="Students need more time.",
        )

        self.assertIn("Nice revision", result["reply"])
        self.assertEqual(result["comparison"]["improvements"], ["Fixed articles"])
