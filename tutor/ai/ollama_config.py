"""Ollama model names and task routing (shared by settings, prompts, and fix command)."""

MAIN_OLLAMA_TASKS = [
    "grammar_coach",
    "speaking_coach",
    "shadowing_coach",
    "reading_coach",
    "reading_quiz",
    "reading_generate",
    "reading_simulation",
    "listening_coach",
    "listening_quiz",
    "writing_coach",
    "writing_edit_coach",
    "writing_edit_generate",
    "writing_paraphrase_coach",
    "writing_paraphrase_generate",
    "writing_paraphrase_check",
    "sentence_builder_coach",
    "paragraph_builder_coach",
    "writing_lesson_coach",
    "writing_prompt_outline_coach",
    "toefl_speaking",
    "toefl_writing",
]

LIGHT_OLLAMA_TASKS = [
    "vocab_builder",
    "lesson_recommendation",
]

RECOMMENDED_OLLAMA_MODELS = [
    "qwen2.5:7b",
    "llama3.2:3b",
    "nomic-embed-text:latest",
]

LEGACY_MODEL_RENAMES = {
    "llama3.2": "llama3.2:3b",
    "qwen2.5": "qwen2.5:7b",
}
