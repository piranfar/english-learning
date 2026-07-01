LISTENING_COACH_SYSTEM_PROMPT = """You are a Listening Coach for a Persian-speaking English learner at B1 level preparing for academic English and TOEFL.

The student will paste a transcript from YouTube, a lecture, or a podcast (no audio — transcript only).

RULES:
- Use simple A2/B1 English in all explanations.
- Be practical and encouraging.

First write a brief friendly introduction (2-3 sentences) about the transcript.

Then append ONE machine-readable block in this exact format:

---LISTENING_ANALYSIS---
{
  "comprehension_questions": [
    {"question": "question in simple English", "answer_hint": "short hint for self-check"}
  ],
  "vocabulary": [
    {"word": "word from transcript", "definition": "simple English definition", "persian": "معنی فارسی"}
  ],
  "shadowing_sentences": ["sentence 1 to repeat aloud", "sentence 2", "sentence 3"],
  "key_phrases": [
    {"phrase": "useful phrase from transcript", "meaning": "simple meaning", "persian": "توضیح فارسی"}
  ]
}
---END_LISTENING_ANALYSIS---

REQUIREMENTS:
- comprehension_questions: exactly 5 questions
- vocabulary: 5-8 useful words
- shadowing_sentences: exactly 3 useful sentences for pronunciation practice
- key_phrases: 4-6 important phrases
- Valid JSON only between the markers."""

LISTENING_COACH_TEMPLATES = [
    {
        "title": "Listening Coach (Ollama)",
        "task_type": "listening_coach",
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "system_prompt": LISTENING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Listening Coach (OpenAI)",
        "task_type": "listening_coach",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": LISTENING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Listening Coach (Anthropic)",
        "task_type": "listening_coach",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": LISTENING_COACH_SYSTEM_PROMPT,
        "temperature": 0.5,
        "max_tokens": 2500,
        "is_active": True,
    },
]

LISTENING_QUIZ_LEVELS = ("B1", "B2", "TOEFL")

LISTENING_QUIZ_FOCUSES = (
    "mixed",
    "main_idea",
    "detail",
    "inference",
    "speaker_purpose",
    "vocabulary_phrase",
)

LISTENING_FOCUS_INSTRUCTIONS = {
    "mixed": "Mix question types: main idea, detail, inference, speaker purpose, and vocabulary/phrase meaning.",
    "main_idea": "All questions should test the main idea or central message of the listening passage.",
    "detail": "All questions should test specific factual details from the transcript.",
    "inference": "All questions should require reasonable inference beyond explicit wording.",
    "speaker_purpose": "All questions should focus on speaker purpose, attitude, or intent.",
    "vocabulary_phrase": "All questions should test vocabulary or phrase meaning in context.",
}

LISTENING_LEVEL_INSTRUCTIONS = {
    "B1": "Use B1-level question wording with clear options.",
    "B2": "Use B2-level academic listening question wording.",
    "TOEFL": "Use TOEFL lecture/conversation style questions with plausible distractors.",
}

LISTENING_QUIZ_SYSTEM_PROMPT = """You are a Listening Quiz generator for Persian-speaking English learners preparing for academic English and TOEFL.

The student provides a transcript from a lecture, podcast, or conversation. Generate exactly 4-6 multiple-choice listening comprehension questions based ONLY on the transcript.

RULES:
- Every question must have exactly 4 options.
- Exactly one option is correct (correct_index 0-3).
- Distractors must be plausible but clearly wrong based on the transcript.
- Use simple, clear English in explanations.

Return ONLY one machine-readable block in this exact format:

---LISTENING_QUIZ---
{
  "questions": [
    {
      "id": "q1",
      "question": "Question text?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "focus": "main_idea",
      "explanation": "Short explanation of why the correct answer is right."
    }
  ],
  "shadowing_sentences": [
    "One useful sentence from the transcript for pronunciation practice."
  ]
}
---END_LISTENING_QUIZ---

REQUIREMENTS:
- questions: 4 to 6 items
- focus must be one of: main_idea, detail, inference, speaker_purpose, vocabulary_phrase
- shadowing_sentences: 1-3 short useful sentences from the transcript
- valid JSON only inside the block, no trailing commas"""

LISTENING_QUIZ_TEMPLATES = [
    {
        "title": "Listening Quiz (Ollama)",
        "task_type": "listening_quiz",
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "system_prompt": LISTENING_QUIZ_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Listening Quiz (OpenAI)",
        "task_type": "listening_quiz",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": LISTENING_QUIZ_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 2500,
        "is_active": True,
    },
    {
        "title": "Listening Quiz (Anthropic)",
        "task_type": "listening_quiz",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": LISTENING_QUIZ_SYSTEM_PROMPT,
        "temperature": 0.4,
        "max_tokens": 2500,
        "is_active": True,
    },
]

LISTENING_TYPE_INSTRUCTIONS = {
    "academic_mini_lecture": (
        "Write a short academic mini-lecture, as if a professor is explaining a concept to a class. "
        "Use a single clear speaker and a logical structure (introduction, development, brief conclusion)."
    ),
    "campus_conversation": (
        "Write a natural conversation between two speakers on a university campus (e.g. student and "
        "advisor, two students, student and staff member) with a clear purpose or problem being discussed."
    ),
    "daily_academic_life": (
        "Write a natural spoken exchange about everyday academic life (study routines, group work, "
        "deadlines, campus services) — practical and conversational, not lecture-style."
    ),
    "toefl_style_lecture": (
        "Write a TOEFL-style academic lecture excerpt: one speaker, denser academic content, organized "
        "with clear signposting (first, however, for example, in other words)."
    ),
    "toefl_style_conversation": (
        "Write a TOEFL-style conversation (e.g. student and professor, or student and campus staff) "
        "with a clear context, a problem or question, and natural turn-taking between two speakers."
    ),
}

LISTENING_TOPIC_INSTRUCTIONS = {
    "Science": "Base the content on a scientific discovery, experiment, or natural phenomenon.",
    "Health": "Base the content on public health, medicine, or wellness in accessible academic language.",
    "University Life": "Base the content on campus life, student services, or academic routines.",
    "Technology": "Base the content on technology trends, digital tools, or innovation.",
    "Society": "Base the content on social change, culture, or community issues.",
    "Academic Skills": "Base the content on study skills, research methods, or academic writing/presentation skills.",
    "Random": "Choose any fresh academic topic suitable for the student's level.",
}

LISTENING_LESSON_FOCUS_INSTRUCTIONS = {
    "articles": (
        "Include natural article use (a/an/the) in the transcript. Include at least one question that "
        "makes the student notice article meaning or use."
    ),
    "prepositions": (
        "Include natural preposition use in academic contexts. Include at least one detail or "
        "vocabulary_in_context question related to preposition meaning."
    ),
    "passive_voice": (
        "Include passive constructions naturally in the transcript. Include one question related to "
        "passive voice meaning or use."
    ),
    "present_perfect": (
        "Include present perfect naturally where appropriate. Include one question about time "
        "reference or verb meaning."
    ),
    "academic_linking_words": (
        "Include linking words such as however, therefore, although, in contrast, moreover, in "
        "addition. Include an organization question about how ideas connect."
    ),
    "academic_vocabulary": (
        "Highlight 4-6 useful academic words naturally in the transcript. Include "
        "vocabulary_in_context questions."
    ),
    "none": "No specific grammar focus — balanced academic listening practice.",
    "current_lesson": "Connect naturally to the student's current lesson theme.",
}

LISTENING_PRACTICE_JSON_SCHEMA = """
{
  "title": "string",
  "level": "string",
  "stage": "string",
  "listening_type": "string",
  "topic": "string",
  "lesson_focus": "string",
  "transcript": "string",
  "estimated_duration_seconds": number,
  "target_vocabulary": [
    {"word": "string", "definition": "string", "example": "string"}
  ],
  "questions": [
    {
      "id": "string",
      "type": "main_idea|detail|inference|speaker_purpose|attitude|vocabulary_in_context|organization",
      "question": "string",
      "choices": ["string", "string", "string", "string"],
      "correct_answer": "string",
      "explanation": "string",
      "mistake_category": "listening_comprehension"
    }
  ],
  "shadowing_sentences": ["string"]
}
"""

LISTENING_PRACTICE_GENERATE_SYSTEM_PROMPT = f"""You are a Listening Coach for Persian-speaking English learners preparing for academic English and TOEFL.

Generate ORIGINAL spoken-style listening practice only. Do NOT copy, paraphrase closely, or reproduce
official TOEFL/ETS audio, transcripts, or any copyrighted test material. Every transcript must be
freshly written.

The student provides level, stage, listening type, topic, lesson focus, length, and speed settings.

RULES:
- Write an original transcript meant to be read aloud (natural spoken English, not a formal essay).
- Match the requested listening_type structure (lecture vs conversation) and speaker count.
- Write at the requested length and difficulty for the stage (follow the word counts in the user message).
- Create the number of questions requested in the user message.
- Every question must have exactly 4 choices and one correct_answer that exactly matches one choice.
- All questions must be answerable using ONLY the transcript — never require outside knowledge.
- Use mistake_category "listening_comprehension" unless the question clearly targets the lesson focus
  grammar point (e.g. "article", "preposition", "tense").
- Include target_vocabulary with 3-6 useful words actually used in the transcript.
- Include 2-4 shadowing_sentences: short, natural sentences copied verbatim from the transcript that are
  good for pronunciation practice.
- estimated_duration_seconds should be a realistic spoken-aloud estimate (roughly 130-150 words per minute).

Return ONLY one machine-readable block:

---LISTENING_PRACTICE---
{LISTENING_PRACTICE_JSON_SCHEMA}
---END_LISTENING_PRACTICE---

REQUIREMENTS:
- Valid JSON only inside the block, no trailing commas
- The transcript must be original and connect to the lesson focus when one is specified
- Questions must be answerable ONLY from the transcript, never from outside knowledge"""

LISTENING_PRACTICE_GENERATE_TEMPLATES = [
    {
        "title": "Listening Practice Generate (Ollama)",
        "task_type": "listening_practice_generate",
        "provider": "ollama",
        "model_name": "qwen2.5:7b",
        "system_prompt": LISTENING_PRACTICE_GENERATE_SYSTEM_PROMPT,
        "temperature": 0.55,
        "max_tokens": 4000,
        "is_active": True,
    },
    {
        "title": "Listening Practice Generate (OpenAI)",
        "task_type": "listening_practice_generate",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": LISTENING_PRACTICE_GENERATE_SYSTEM_PROMPT,
        "temperature": 0.55,
        "max_tokens": 4000,
        "is_active": True,
    },
    {
        "title": "Listening Practice Generate (Anthropic)",
        "task_type": "listening_practice_generate",
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-latest",
        "system_prompt": LISTENING_PRACTICE_GENERATE_SYSTEM_PROMPT,
        "temperature": 0.55,
        "max_tokens": 4000,
        "is_active": True,
    },
]
