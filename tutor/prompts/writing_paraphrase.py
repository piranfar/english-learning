"""Paraphrasing practice — generate and check prompts."""

WRITING_PARAPHRASE_GENERATE_SYSTEM = """You are an English writing coach for adult English learners. Generate short, clear paraphrasing practice texts. The text should match the selected target style, exercise difficulty, text type, and language level.

Return valid JSON only. Do not write anything before or after the JSON. No markdown fences."""

WRITING_PARAPHRASE_CHECK_SYSTEM = """You are an English writing coach for adult English learners. Evaluate paraphrases fairly based on meaning, grammar, naturalness, vocabulary, and whether the paraphrase matches the selected language level.

Return valid JSON only. Do not write anything before or after the JSON. No markdown fences."""

TARGET_LEVEL_LABELS = {
    "simple_american_english": "Simple American English",
    "academic": "Academic",
    "toefl": "TOEFL",
    "professional_email": "Professional Email",
    "natural_conversation": "Natural Conversation",
}

TARGET_LEVEL_ALIASES = {
    "simple": "simple_american_english",
    "natural": "natural_conversation",
    "professional_email": "professional_email",
}

DIFFICULTY_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}

DIFFICULTY_INSTRUCTIONS = {
    "easy": "Use familiar topics and straightforward ideas. Keep the task approachable.",
    "medium": "Use moderately challenging ideas that require careful paraphrasing.",
    "hard": "Use slightly more abstract or detailed ideas while staying learner-appropriate.",
}

TEXT_TYPE_LABELS = {
    "one_sentence": "One sentence",
    "short_paragraph": "Short paragraph",
    "toefl_sentence": "TOEFL-style sentence",
    "academic_sentence": "Academic sentence",
    "email_sentence": "Professional email sentence",
    "conversation_sentence": "Daily conversation sentence",
}

LANGUAGE_LEVEL_LABELS = {
    "beginner": "Beginner",
    "normal": "Normal",
    "professional": "Professional",
}

LANGUAGE_LEVEL_INSTRUCTIONS = {
    "beginner": """Beginner (A1–B1 learners):
- Use short, clear sentences.
- Use common everyday vocabulary.
- Avoid long clauses, complex grammar, and idioms.
- Prefer one main idea per sentence.
- Keep sentence length mostly under 15 words.
- Make the text easy for English learners to understand.""",
    "normal": """Normal (B1–B2 learners):
- Use natural everyday American English.
- Use moderate sentence length.
- Use simple transitions when helpful.
- Allow basic compound and complex sentences.
- Avoid overly advanced vocabulary.
- Keep the writing clear and practical.""",
    "professional": """Professional (advanced learners):
- Use more precise vocabulary.
- Use smoother sentence structure.
- Use professional or academic phrasing when appropriate.
- Allow more complex sentences, but keep clarity.
- Avoid unnecessary wordiness.
- Make the writing polished and natural.
- Do not make it artificially complicated.""",
}


def normalize_target_level(value: str | None) -> str:
    key = (value or "simple_american_english").strip().lower().replace(" ", "_")
    key = TARGET_LEVEL_ALIASES.get(key, key)
    if key not in TARGET_LEVEL_LABELS:
        for slug, label in TARGET_LEVEL_LABELS.items():
            if label.lower() == (value or "").strip().lower():
                return slug
        return "simple_american_english"
    return key


def normalize_difficulty(value: str | None) -> str:
    key = (value or "easy").strip().lower()
    if key not in DIFFICULTY_LABELS:
        for slug, label in DIFFICULTY_LABELS.items():
            if label.lower() == (value or "").strip().lower():
                return slug
        return "easy"
    return key


def normalize_text_type(value: str | None) -> str:
    key = (value or "one_sentence").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "one_sentence": "one_sentence",
        "short_paragraph": "short_paragraph",
        "toefl_style_sentence": "toefl_sentence",
        "toefl_sentence": "toefl_sentence",
        "academic_sentence": "academic_sentence",
        "professional_email_sentence": "email_sentence",
        "email_sentence": "email_sentence",
        "daily_conversation_sentence": "conversation_sentence",
        "conversation_sentence": "conversation_sentence",
    }
    key = aliases.get(key, key)
    if key not in TEXT_TYPE_LABELS:
        for slug, label in TEXT_TYPE_LABELS.items():
            if label.lower() == (value or "").strip().lower():
                return slug
        return "one_sentence"
    return key


def normalize_language_level(value: str | None) -> str:
    key = (value or "normal").strip().lower()
    if key not in LANGUAGE_LEVEL_LABELS:
        for slug, label in LANGUAGE_LEVEL_LABELS.items():
            if label.lower() == (value or "").strip().lower():
                return slug
        return "normal"
    return key


def target_level_display(value: str) -> str:
    return TARGET_LEVEL_LABELS.get(normalize_target_level(value), value)


def language_level_display(value: str) -> str:
    return LANGUAGE_LEVEL_LABELS.get(normalize_language_level(value), value)


def build_paraphrase_generate_message(
    target_level: str,
    difficulty: str,
    text_type: str,
    language_level: str,
) -> str:
    style = target_level_display(target_level)
    diff_label = DIFFICULTY_LABELS.get(normalize_difficulty(difficulty), difficulty)
    diff_instruction = DIFFICULTY_INSTRUCTIONS.get(normalize_difficulty(difficulty), "")
    ttype = TEXT_TYPE_LABELS.get(normalize_text_type(text_type), text_type)
    lang_instruction = LANGUAGE_LEVEL_INSTRUCTIONS.get(
        normalize_language_level(language_level), ""
    )

    return f"""Generate one paraphrasing practice text.

Target style:
{style}

Exercise difficulty:
{diff_label}
{diff_instruction}

Text type:
{ttype}

Language level:
{lang_instruction}

Return JSON only:
{{
  "original_text": "...",
  "teaching_tip": "..."
}}

Rules:
- Do not include the paraphrase answer.
- Do not include markdown outside JSON.
- Match the selected language level carefully.
- Beginner must be simple and short.
- Normal must be natural and clear.
- Professional must be polished but not unnecessarily complicated.
- For one sentence, write only one sentence.
- For short paragraph, write 2–4 sentences.
- Use American English."""


def build_paraphrase_check_message(
    target_level: str,
    language_level: str,
    original_text: str,
    learner_paraphrase: str,
) -> str:
    style = target_level_display(target_level)
    lang_instruction = LANGUAGE_LEVEL_INSTRUCTIONS.get(
        normalize_language_level(language_level), ""
    )

    return f"""Evaluate the learner's paraphrase.

Target style:
{style}

Expected language level:
{lang_instruction}

Original text:
{original_text.strip()}

Learner paraphrase:
{learner_paraphrase.strip()}

Return JSON only with this exact structure:
{{
  "overall_score": 0,
  "meaning_accuracy_score": 0,
  "grammar_score": 0,
  "naturalness_score": 0,
  "vocabulary_score": 0,
  "level_match_score": 0,
  "result_label": "...",
  "language_level_feedback": "...",
  "feedback": ["..."],
  "better_version": "...",
  "comparison": {{
    "original": "...",
    "learner_paraphrase": "...",
    "better_paraphrase": "..."
  }},
  "teaching_notes": ["..."]
}}

Scoring rules:
- Meaning accuracy: Does the paraphrase keep the same meaning?
- Grammar: Is the English correct?
- Naturalness: Does it sound natural in American English?
- Vocabulary: Is the word choice appropriate?
- Level match: Does the paraphrase match Beginner, Normal, or Professional level?
- Overall score should consider all categories.

Important:
- If the selected level is Beginner, do not punish the learner for using simple language.
- If the selected level is Professional, reward precise and polished wording.
- If the paraphrase is too advanced for Beginner level, mention that it may not match the selected level.
- If the paraphrase is too casual for Professional level, mention that.
- Penalize if the learner changes the meaning.
- Penalize if the paraphrase copies the original too closely.
- Reward clear structure and accurate meaning.
- If the learner's answer is better than the model answer, say so honestly.
- Include language_level_feedback as one short sentence about level match.
- Keep feedback friendly and useful (3–6 bullet points in feedback).
- Do not include markdown outside JSON."""


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


WRITING_PARAPHRASE_TEMPLATES = [
    *_templates("writing_paraphrase_generate", WRITING_PARAPHRASE_GENERATE_SYSTEM),
    *_templates("writing_paraphrase_check", WRITING_PARAPHRASE_CHECK_SYSTEM),
]
