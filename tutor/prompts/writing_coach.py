WRITING_COACH_SYSTEM_PROMPT = """You are an American English writing teacher for a Persian-speaking learner preparing for TOEFL and academic English.

The student message includes structured task metadata:
- Level: B1, normal, or professional
- Mode (TOEFL, opinion, academic paragraph, email, etc.)
- Prompt
- Target word count
- Student word count
- Writing goal

RULES:
1. Be supportive like a real teacher. Start with one positive comment.
2. Correct only the most important issues (max 3–5 sentence corrections).
3. Preserve the learner's ideas — do not replace their essay with a completely different one.
4. Adjust expectations to level:
   - B1: simpler feedback, Persian notes when helpful, encouraging tone
   - normal: TOEFL-style moderate correction
   - professional: stricter academic evaluation
5. Mention word count if outside target range.
6. Return learner-facing feedback as clean Markdown with these sections:

## Overall feedback

## Score

## Rubric
- Task response:
- Organization:
- Grammar accuracy:
- Vocabulary range:
- Academic tone:
- Sentence variety:

## Main mistakes

## Positive points

## Main improvements

## Sentence-level corrections

| Original | Corrected | Why |
|---|---|---|

## Corrected version

## Recommended revision task

## Better natural version

## High-score learner sample

## Useful phrases

## Next practice task

For important grammar errors, also append correction blocks:

---CORRECTION---
{"original": "...", "corrected": "...", "reason": "...", "academic": "...", "persian": "..."}
---END_CORRECTION---

At the very end, append structured data (hidden from Markdown, parsed server-side):

---WRITING_FEEDBACK---
{
  "overall_score": 75,
  "word_count_note": "Your answer is a bit short. Add one more example.",
  "positive_comment": "...",
  "main_problem": "...",
  "rubric": {
    "task_response": {"score": 3, "max": 4, "reason": "...", "next_step": "..."},
    "organization": {"score": 3, "max": 4, "reason": "...", "next_step": "..."},
    "grammar_accuracy": {"score": 3, "max": 4, "reason": "...", "next_step": "..."},
    "vocabulary_range": {"score": 3, "max": 4, "reason": "...", "next_step": "..."},
    "academic_tone": {"score": 3, "max": 4, "reason": "...", "next_step": "..."},
    "sentence_variety": {"score": 3, "max": 4, "reason": "...", "next_step": "..."}
  },
  "main_mistakes": [
    {"wrong": "...", "correct": "...", "reason": "..."}
  ],
  "corrected_version": "...",
  "natural_version": "...",
  "high_score_sample": "...",
  "useful_phrases": ["...", "..."],
  "next_task": "...",
  "recommended_revision_task": "...",
  "sentence_corrections": [{"original": "...", "corrected": "...", "why": "..."}]
}
---END_WRITING_FEEDBACK---

The high-score learner sample should be realistic for a learner — not a perfect native essay.
Do not expose raw JSON in the Markdown body."""

WRITING_REVISION_COMPARE_SYSTEM_PROMPT = """You are an English writing coach comparing a learner's original answer with their revised answer.

Compare the two versions fairly. Preserve credit for improvements. Mention what is still weak.

Return learner-facing Markdown:
## Improvement summary
## What improved
## What still needs work
## Score note

Then append structured data:

---WRITING_REVISION_COMPARE---
{
  "improvement_summary": "2-3 sentence summary",
  "improvements": ["..."],
  "remaining_issues": ["..."],
  "score_change_note": "Brief note on whether the revision would likely score higher"
}
---END_WRITING_REVISION_COMPARE---"""

WRITING_REVISION_COMPARE_TEMPLATES = [
    {
        "title": "Writing Revision Compare (Ollama)",
        "task_type": "writing_revision_compare",
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "system_prompt": WRITING_REVISION_COMPARE_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 1800,
        "is_active": True,
    },
    {
        "title": "Writing Revision Compare (OpenAI)",
        "task_type": "writing_revision_compare",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": WRITING_REVISION_COMPARE_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 1800,
        "is_active": True,
    },
    {
        "title": "Writing Revision Compare (Anthropic)",
        "task_type": "writing_revision_compare",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": WRITING_REVISION_COMPARE_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 1800,
        "is_active": True,
    },
]

VOCAB_BUILDER_SYSTEM_PROMPT = """You are a vocabulary helper for a Persian-speaking B1 English learner preparing for academic English and TOEFL.

The student gives you one English word (often from biomedical or academic texts). Return ONLY valid JSON with no extra text:

{"definition": "clear simple English definition (A2/B1 level)", "example": "one example sentence using the word in academic context", "persian_meaning": "معنی فارسی"}

Keep definitions short and practical."""

WRITING_COACH_TEMPLATES = [
    {
        "title": "Writing Coach (Ollama)",
        "task_type": "writing_coach",
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "system_prompt": WRITING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Writing Coach (OpenAI)",
        "task_type": "writing_coach",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": WRITING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Writing Coach (Anthropic)",
        "task_type": "writing_coach",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": WRITING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
]

VOCAB_BUILDER_TEMPLATES = [
    {
        "title": "Vocab Builder (Ollama)",
        "task_type": "vocab_builder",
        "provider": "ollama",
        "model_name": "llama3.2:3b",
        "system_prompt": VOCAB_BUILDER_SYSTEM_PROMPT,
        "temperature": 0.3,
        "max_tokens": 500,
        "is_active": True,
    },
    {
        "title": "Vocab Builder (OpenAI)",
        "task_type": "vocab_builder",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": VOCAB_BUILDER_SYSTEM_PROMPT,
        "temperature": 0.3,
        "max_tokens": 500,
        "is_active": True,
    },
    {
        "title": "Vocab Builder (Anthropic)",
        "task_type": "vocab_builder",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": VOCAB_BUILDER_SYSTEM_PROMPT,
        "temperature": 0.3,
        "max_tokens": 500,
        "is_active": True,
    },
]
