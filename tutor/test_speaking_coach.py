from django.contrib.auth import get_user_model
from django.test import TestCase

from tutor.models import Mistake
from tutor.services import (
    parse_speaking_feedback,
    persist_speaking_feedback_mistakes,
)
from tutor.speaking_evaluation import normalize_evaluator_json, parse_evaluator_response

User = get_user_model()


class SpeakingFeedbackParserTests(TestCase):
    def test_parse_legacy_speaking_feedback_block(self):
        raw = """### Positive note
Nice effort.

---SPEAKING_FEEDBACK---
{
  "overall_score": 78,
  "input_mode": "voice",
  "pronunciation_limited": true,
  "pronunciation_notes": "Try clearer word stress on important nouns.",
  "rubric": {
    "fluency": {"score": 3, "max": 4, "reason": "Mostly smooth", "next_step": "Reduce pauses"},
    "grammar": {"score": 3, "max": 4, "reason": "Minor errors", "next_step": "Check verb tense"},
    "vocabulary": {"score": 3, "max": 4, "reason": "Adequate range", "next_step": "Use stronger verbs"},
    "organization": {"score": 2, "max": 4, "reason": "Main point late", "next_step": "Lead with thesis"}
  },
  "main_mistakes": [
    {"area": "grammar", "wrong": "He go to work", "correct": "He goes to work", "reason": "Subject-verb agreement"},
    {"area": "organization", "wrong": "I like it because first", "correct": "First, I like it because", "reason": "Clearer opening"}
  ],
  "corrected_version": "He goes to work every day.",
  "model_answer": "He goes to work every day because it gives him structure.",
  "repeat_task_recommendation": "Practice giving your main point in the first sentence."
}
---END_SPEAKING_FEEDBACK---"""

        reply, feedback = parse_speaking_feedback(raw)

        self.assertIn("Nice effort", reply)
        self.assertEqual(feedback["overall_score"], 78)
        self.assertEqual(feedback["input_mode"], "voice")
        self.assertIn("word stress", feedback["pronunciation_notes"])
        self.assertEqual(feedback["breakdown"]["organization"], 2)
        self.assertEqual(feedback["model_answer"], feedback["natural_version"])
        self.assertEqual(len(feedback["main_mistakes"]), 2)

    def test_parse_json_evaluator_contract(self):
        raw = """{
          "mode": "advanced",
          "estimated_toefl_speaking": 18,
          "rubric_score_0_4": 2.5,
          "overall_score": 62,
          "overall_feedback": "Your answer is understandable, but development needs improvement.",
          "scores": {
            "delivery": 58,
            "fluency": 55,
            "pronunciation_clarity": 62,
            "language_use": 60,
            "grammar": 57,
            "topic_development": 52
          },
          "strengths": ["You answered the question directly."],
          "priority_corrections": [
            {
              "type": "grammar",
              "original": "I like it because it make me happy.",
              "corrected": "I like it because it makes me happy.",
              "explanation": "Use third-person singular makes."
            }
          ],
          "delivery_notes": {
            "pace": "Slightly slow with several pauses.",
            "pronunciation": "Mostly understandable.",
            "intonation": "Use rising and falling intonation."
          },
          "corrected_answer": "My favorite food is kebab.",
          "next_drill": {
            "title": "Repeat with better sentence stress",
            "instruction": "Say this sentence three times with stress on key words.",
            "target": "sentence stress and fluency"
          },
          "retry_recommendation": "Retry the same task once using the corrected answer structure."
        }"""

        reply, feedback = parse_evaluator_response(raw, input_mode="voice")

        self.assertIn("understandable", reply)
        self.assertEqual(feedback["mode"], "advanced")
        self.assertEqual(feedback["estimated_toefl_speaking"], 18)
        self.assertEqual(feedback["scores"]["delivery"], 58)
        self.assertEqual(feedback["main_mistakes"][0]["wrong"], "I like it because it make me happy.")
        self.assertEqual(feedback["next_drill"]["title"], "Repeat with better sentence stress")
        self.assertIn("Pace:", feedback["pronunciation_notes"])

    def test_normalize_evaluator_json_maps_fields(self):
        normalized = normalize_evaluator_json(
            {
                "mode": "normal",
                "overall_score": 70,
                "scores": {"grammar": 72, "topic_development": 68},
                "strengths": ["Clear main idea"],
                "priority_corrections": [],
                "corrected_answer": "Better answer.",
                "next_drill": {"instruction": "Try again with fewer pauses."},
                "retry_recommendation": "Retry once.",
            },
            input_mode="typed",
        )
        self.assertEqual(normalized["corrected_version"], "Better answer.")
        self.assertTrue(normalized["pronunciation_limited"])
        self.assertEqual(normalized["repeat_answer"], "Try again with fewer pauses.")


class SpeakingFeedbackMistakeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="speaker", password="test")

    def test_persist_speaking_feedback_mistakes_saves_grammar_and_vocab(self):
        feedback = {
            "main_mistakes": [
                {
                    "area": "grammar",
                    "wrong": "He go to school every day",
                    "correct": "He goes to school every day",
                    "reason": "Subject-verb agreement",
                },
                {
                    "area": "pronunciation",
                    "wrong": "should not save",
                    "correct": "ignored",
                    "reason": "Wrong area",
                },
            ],
            "vocabulary_upgrades": [
                {"instead_of": "very good", "try": ["effective", "useful"]},
            ],
        }

        persist_speaking_feedback_mistakes(self.user, "speaking_coach", feedback)

        mistakes = Mistake.objects.filter(user=self.user, track="speaking_coach").order_by("id")
        self.assertEqual(mistakes.count(), 2)
        self.assertEqual(mistakes[0].category, "sentence_structure")
        self.assertEqual(mistakes[1].category, "vocabulary_precision")
