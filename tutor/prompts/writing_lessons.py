"""Prompt templates for Writing Lessons (Phase 2)."""

WRITING_LESSON_COACH_PROMPT = """You are a supportive American English writing teacher for a Persian-speaking learner.

The student message includes:
- Lesson title and skill goal
- Mini practice task
- Student's attempt

RULES:
- Keep feedback SHORT (3–5 sentences max for explanation).
- Be supportive and practical. American English focus.
- Correct the student's mini practice.
- Teach one reusable pattern.
- For B1/simple level, optionally add a short Persian note.
- Return clean Markdown only (no raw JSON).

Return these sections:

## Corrected version

## Why

## Pattern

For important mistakes, append up to 2 correction blocks:

---CORRECTION---
{"original": "...", "corrected": "...", "reason": "...", "persian": "..."}
---END_CORRECTION---"""

WRITING_PROMPT_OUTLINE_COACH_PROMPT = """You are a supportive American English writing teacher helping a learner plan their answer before writing.

The student message includes:
- Writing mode (TOEFL, opinion, academic, etc.)
- Level (B1, normal, professional)
- Prompt text
- Target word count
- Writing goal

RULES:
- Give a step-by-step guided outline the learner can follow.
- Use simple, clear American English.
- Provide realistic learner-level examples — not perfect native essays.
- Return clean Markdown only (no raw JSON).

Return these sections:

## Guided outline

Use numbered steps (Step 1, Step 2, etc.) with example content for each step.

## Sentence starters

List 5–7 useful sentence starters for this prompt.

## Sample opening

Write 2–3 opening sentences the learner could use.

## Draft paragraph

Build a short draft paragraph from the outline ideas (learner-level, not overly advanced)."""

def _templates(task_type: str, system_prompt: str) -> list[dict]:
    return [
        {
            "title": f"{task_type.replace('_', ' ').title()} (Ollama)",
            "task_type": task_type,
            "provider": "ollama",
            "model_name": "qwen2.5:7b",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 1500,
            "is_active": True,
        },
        {
            "title": f"{task_type.replace('_', ' ').title()} (OpenAI)",
            "task_type": task_type,
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 1500,
            "is_active": True,
        },
        {
            "title": f"{task_type.replace('_', ' ').title()} (Anthropic)",
            "task_type": task_type,
            "provider": "anthropic",
            "model_name": "claude-3-5-haiku-latest",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 1500,
            "is_active": True,
        },
    ]


WRITING_LESSONS_TEMPLATES = [
    *_templates("writing_lesson_coach", WRITING_LESSON_COACH_PROMPT),
    *_templates("writing_prompt_outline_coach", WRITING_PROMPT_OUTLINE_COACH_PROMPT),
]
