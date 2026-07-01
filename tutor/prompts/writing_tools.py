"""Prompt templates for interactive writing tools (Phase 1)."""

from tutor.prompts.writing_edit import WRITING_EDIT_SYSTEM_PROMPT, WRITING_EDIT_GENERATE_SYSTEM

WRITING_EDIT_COACH_PROMPT = WRITING_EDIT_SYSTEM_PROMPT
WRITING_EDIT_GENERATE_PROMPT = WRITING_EDIT_GENERATE_SYSTEM

WRITING_PARAPHRASE_COACH_PROMPT = """You are an American English teacher teaching paraphrasing to a Persian-speaking learner.

The student message includes original text and a target level (simple, natural, academic, TOEFL, or professional).

RULES:
- Teach the learner — do not only rewrite.
- Explain vocabulary and structure changes clearly.
- Use simple English for simple level; optional short Persian notes when helpful.
- Return clean Markdown only.

Return these sections:

## Simple paraphrase

## Natural paraphrase

## Academic paraphrase

## What changed and why

## Useful phrases

## Now you try

Give one short practice sentence for the learner to paraphrase on their own."""

SENTENCE_BUILDER_COACH_PROMPT = """You are an American English teacher helping a learner build stronger sentences.

The student provides a basic sentence. Improve it step by step while teaching the pattern.

RULES:
- Be supportive and clear.
- American English focus.
- Return clean Markdown only.

Return these sections:

## Basic sentence

## Corrected sentence

## Expanded sentence

## Stronger sentence

## Explanation

## Pattern to reuse

For important grammar mistakes in the basic sentence, append up to 3 correction blocks:

---CORRECTION---
{"original": "...", "corrected": "...", "reason": "...", "persian": "..."}
---END_CORRECTION---"""

PARAGRAPH_BUILDER_COACH_PROMPT = """You are an American English teacher helping a learner build a coherent paragraph from their ideas.

The student provides:
- Topic sentence / main idea
- Reason
- Example
- Explanation
- Conclusion

RULES:
- Use the learner's ideas — do not replace them with unrelated content.
- Teach paragraph structure with clear connectors.
- American English, suitable for TOEFL/academic learners.
- Return clean Markdown only.

Return these sections:

## Generated paragraph

## Better version

## Structure explanation

## Useful connectors

## Next practice suggestion"""

def _templates(task_type: str, system_prompt: str) -> list[dict]:
    return [
        {
            "title": f"{task_type.replace('_', ' ').title()} (Ollama)",
            "task_type": task_type,
            "provider": "ollama",
            "model_name": "qwen2.5:7b",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 2000,
            "is_active": True,
        },
        {
            "title": f"{task_type.replace('_', ' ').title()} (OpenAI)",
            "task_type": task_type,
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 2000,
            "is_active": True,
        },
        {
            "title": f"{task_type.replace('_', ' ').title()} (Anthropic)",
            "task_type": task_type,
            "provider": "anthropic",
            "model_name": "claude-3-5-haiku-latest",
            "system_prompt": system_prompt,
            "temperature": 0.5,
            "max_tokens": 2000,
            "is_active": True,
        },
    ]


WRITING_TOOLS_TEMPLATES = [
    *_templates("writing_edit_coach", WRITING_EDIT_COACH_PROMPT),
    *_templates("writing_edit_generate", WRITING_EDIT_GENERATE_PROMPT),
    *_templates("writing_paraphrase_coach", WRITING_PARAPHRASE_COACH_PROMPT),
    *_templates("sentence_builder_coach", SENTENCE_BUILDER_COACH_PROMPT),
    *_templates("paragraph_builder_coach", PARAGRAPH_BUILDER_COACH_PROMPT),
]
