"""Writing edit coach — dynamic strength/style/level instructions and JSON output."""

WRITING_EDIT_SYSTEM_PROMPT = """You are an English writing coach for adult English learners. Your job is to correct writing, improve clarity, and teach the learner. Preserve the learner's meaning. Do not invent new facts. Keep explanations simple and practical.

You receive three separate controls in every request:
1. Edit strength — how much to change the text
2. Target style — the purpose or context of the writing
3. Language level — sentence complexity, vocabulary difficulty, and grammar difficulty

The edited_text MUST reflect all three controls together. Language level controls sentence length and complexity even when target style is academic or professional.

Return valid JSON only. No explanation before or after the JSON. No markdown fences."""

EDIT_STRENGTH_LABELS = {
    "light": "Light edit",
    "standard": "Standard edit",
    "strong": "Strong rewrite",
    "teacher": "Teacher mode",
}

TARGET_STYLE_LABELS = {
    "simple_american_english": "Simple American English",
    "academic_english": "Academic English",
    "toefl_writing": "TOEFL Writing",
    "email_professional": "Email / Professional",
    "natural_conversation": "Natural Conversation",
}

LANGUAGE_LEVEL_LABELS = {
    "beginner": "Beginner",
    "normal": "Normal",
    "professional": "Professional",
}

EDIT_STRENGTH_INSTRUCTIONS = {
    "light": """Light edit — Fix only clear grammar, spelling, punctuation, and basic word choice problems.
- Keep the learner's original wording as much as possible.
- Do not rewrite the whole paragraph.
- Do not make it too advanced.
- Preserve the learner's voice.
- Only fix errors that make the sentence incorrect or unnatural.
- Still match the selected language level for any small changes you make.""",
    "standard": """Standard edit — Fix grammar, clarity, naturalness, and sentence flow.
- Improve grammar, word choice, sentence structure, and clarity.
- Keep the meaning unchanged.
- Make the writing natural and easy to read.
- Do not make the writing too formal unless the target style asks for it.
- Shape sentence complexity to match the selected language level.""",
    "strong": """Strong rewrite — Rewrite the text more actively and improve structure.
- Rewrite the paragraph for stronger flow and clarity.
- Improve sentence order if needed.
- Combine or split sentences when helpful.
- Keep the same meaning and match the selected language level.
- Do not add new facts.
- Apply the target style clearly (e.g. TOEFL organization, email tone, academic formality).""",
    "teacher": """Teacher mode — Teach the learner step by step.
- First provide the corrected version in edited_text.
- In changes, explain the main grammar and writing problems (3–6 bullets).
- In teaching_notes, give simple writing tips and 2 example sentences using the same structure.
- Keep explanations simple for English learners.
- The corrected version must still match the selected language level and target style.""",
}

TARGET_STYLE_INSTRUCTIONS = {
    "simple_american_english": """Simple American English
- Use clear, natural American English.
- Prefer common words.
- Avoid complicated grammar.
- Suitable for English learners.""",
    "academic_english": """Academic English
- Use formal academic tone.
- Improve precision, cohesion, and paragraph structure.
- Avoid casual phrases.
- Do not make unsupported claims.
- Keep the language suitable for college-level writing.
- If language level is Beginner, stay formal but use short, clear sentences.""",
    "toefl_writing": """TOEFL Writing
- Use clear TOEFL-style writing.
- Improve topic sentences, transitions, examples, and conclusion if relevant.
- Keep the writing direct and organized.
- Avoid very advanced vocabulary unless language level is Professional.
- Make the text suitable for TOEFL independent/integrated writing practice.""",
    "email_professional": """Email / Professional
- Make the writing polite, professional, and concise.
- Improve tone and clarity.
- Avoid overly casual wording.
- Keep the message appropriate for workplace or academic email.
- If language level is Beginner, keep sentences short while staying polite.""",
    "natural_conversation": """Natural Conversation
- Make the writing sound natural in everyday American English.
- Use simple, spoken-style wording.
- Avoid academic or formal language.
- Keep it friendly and clear.""",
}

LANGUAGE_LEVEL_INSTRUCTIONS = {
    "beginner": """Beginner (A1–B1 learners) — sentence difficulty:
- Use short, clear sentences.
- Use common everyday vocabulary.
- Avoid long clauses, idioms, and complex grammar.
- Prefer one main idea per sentence.
- Keep sentence length mostly under 15 words.
- Make the writing easy for English learners to understand.
- Do not make the text childish.
- Preserve the learner's meaning.""",
    "normal": """Normal (B1–B2 learners) — sentence difficulty:
- Use natural everyday American English.
- Use moderate sentence length.
- Use simple transitions when helpful.
- Allow basic compound and complex sentences.
- Avoid overly advanced vocabulary.
- Keep the writing clear, practical, and natural.""",
    "professional": """Professional (advanced learners) — sentence difficulty:
- Use more precise vocabulary.
- Use smoother sentence structure.
- Use professional or academic phrasing when appropriate.
- Allow more complex sentences, but keep clarity.
- Avoid unnecessary wordiness.
- Make the writing polished and natural.
- Do not make it artificially complicated.
- Preserve the learner's meaning.
- Do not add unsupported new facts.""",
}

LANGUAGE_LEVEL_EXAMPLES = {
    "beginner": """Example for Beginner level:
Original: I believe online education has many advantage because people can learning from home.
Beginner edited: I believe online education has many advantages because people can learn from home.""",
    "normal": """Example for Normal level:
Original: I believe online education has many advantage because people can learning from home.
Normal edited: I believe online education has many advantages because people can learn from home and study more flexibly.""",
    "professional": """Example for Professional level:
Original: I believe online education has many advantage because people can learning from home.
Professional edited: I believe online education offers several advantages because it allows learners to study from home with greater flexibility.""",
}

# Legacy aliases from earlier frontend IDs
EDIT_STRENGTH_ALIASES = {
    "strong_rewrite": "strong",
}

TARGET_STYLE_ALIASES = {
    "simple": "simple_american_english",
    "academic": "academic_english",
    "toefl": "toefl_writing",
    "email": "email_professional",
    "conversation": "natural_conversation",
}


def normalize_edit_strength(value: str | None) -> str:
    key = (value or "standard").strip().lower()
    key = EDIT_STRENGTH_ALIASES.get(key, key)
    if key not in EDIT_STRENGTH_INSTRUCTIONS:
        return "standard"
    return key


def normalize_target_style(value: str | None) -> str:
    key = (value or "simple_american_english").strip().lower()
    key = TARGET_STYLE_ALIASES.get(key, key)
    if key not in TARGET_STYLE_INSTRUCTIONS:
        return "simple_american_english"
    return key


def normalize_language_level(value: str | None) -> str:
    key = (value or "normal").strip().lower()
    if key in LANGUAGE_LEVEL_INSTRUCTIONS:
        return key
    return "normal"


def edit_strength_display(value: str) -> str:
    return EDIT_STRENGTH_LABELS.get(normalize_edit_strength(value), value)


def target_style_display(value: str) -> str:
    return TARGET_STYLE_LABELS.get(normalize_target_style(value), value)


def language_level_display(value: str) -> str:
    return LANGUAGE_LEVEL_LABELS.get(normalize_language_level(value), value)


def build_writing_edit_user_message(
    text: str,
    edit_strength: str,
    target_style: str,
    language_level: str = "normal",
) -> str:
    strength_key = normalize_edit_strength(edit_strength)
    style_key = normalize_target_style(target_style)
    lang_key = normalize_language_level(language_level)
    strength_instruction = EDIT_STRENGTH_INSTRUCTIONS[strength_key]
    style_instruction = TARGET_STYLE_INSTRUCTIONS[style_key]
    language_instruction = LANGUAGE_LEVEL_INSTRUCTIONS[lang_key]
    level_example = LANGUAGE_LEVEL_EXAMPLES[lang_key]

    return f"""Task: Edit the learner's writing.

Selected settings:
- Edit strength: {edit_strength_display(strength_key)}
- Target style: {target_style_display(style_key)}
- Language level: {language_level_display(lang_key)}

How the controls work together:
- Edit strength decides how much you change the text (minimal fixes vs full rewrite vs teaching).
- Target style decides the purpose and tone (academic, TOEFL, email, conversation, etc.).
- Language level decides sentence complexity, vocabulary difficulty, and grammar difficulty.
- edited_text must follow ALL three. Do not ignore language level when applying target style.

Edit strength:
{strength_instruction}

Target style:
{style_instruction}

Language level:
{language_instruction}

Reference example for this language level:
{level_example}

Learner text:
{text.strip()}

Return JSON only with this exact structure:
{{
  "edited_text": "...",
  "changes": [
    "..."
  ],
  "teaching_notes": [
    "..."
  ],
  "sentence_comparisons": [
    {{
      "original": "...",
      "improved": "...",
      "reason": "..."
    }}
  ],
  "level_feedback": "...",
  "better_alternative": "..."
}}

Rules:
- Do not include markdown outside the JSON.
- Do not add new information.
- Keep the learner's original meaning.
- Match the selected language level carefully in edited_text.
- Beginner: simple, short sentences; common words; mostly under 15 words per sentence.
- Normal: natural, clear, moderate complexity.
- Professional: polished, precise; more complex sentences allowed but stay clear.
- Light edit: minimal changes only, but still respect language level.
- Strong rewrite: reorganize for target style, but sentence complexity must match language level.
- Teacher mode: corrected version plus teaching in changes and teaching_notes.
- Provide 3–6 items in changes when possible.
- Provide 2–4 teaching_notes.
- Provide 1–3 sentence_comparisons when useful.
- level_feedback: one sentence stating whether edited_text matches the {language_level_display(lang_key)} level and why.
- better_alternative: optional stronger version at the same language level (empty string if not needed).
- If there are no major errors, say that clearly in the changes section."""


WRITING_EDIT_GENERATE_SYSTEM = """You are an English writing coach for adult English learners. Generate short practice paragraphs that look like real learner writing with intentional mistakes.

Return valid JSON only. Do not write anything before or after the JSON. No markdown fences."""


def build_writing_edit_generate_message(
    target_style: str,
    language_level: str = "normal",
) -> str:
    style_key = normalize_target_style(target_style)
    lang_key = normalize_language_level(language_level)
    style_instruction = TARGET_STYLE_INSTRUCTIONS[style_key]
    language_instruction = LANGUAGE_LEVEL_INSTRUCTIONS[lang_key]

    return f"""Generate one practice paragraph for an editing exercise.

Target style:
{target_style_display(style_key)}
{style_instruction}

Language level:
{language_level_display(lang_key)}
{language_instruction}

Return JSON only:
{{
  "draft_text": "...",
  "teaching_tip": "..."
}}

Rules:
- draft_text must be 2–4 sentences of learner writing with intentional grammar, spelling, word choice, or clarity mistakes.
- The topic must fit the target style (e.g. TOEFL opinion, academic paragraph, professional email, everyday conversation).
- Sentence complexity and vocabulary in draft_text must match the language level.
- Beginner drafts: short sentences, basic vocabulary, common learner errors (articles, verb forms, word order).
- Normal drafts: moderate length, natural topics, mixed grammar and flow issues.
- Professional drafts: more advanced attempted vocabulary with polish issues, not gibberish.
- teaching_tip: one short sentence telling the learner what to look for when editing.
- Do not include the corrected version.
- Do not include markdown outside JSON.
- Use American English.
- The text must be real English words and ideas, never random letters or nonsense."""
