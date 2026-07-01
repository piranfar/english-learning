export const EDIT_STRENGTHS = [
  { id: 'light', label: 'Light edit', hint: 'Fix only clear grammar and word choice problems' },
  { id: 'standard', label: 'Standard edit', hint: 'Fix grammar, clarity, and naturalness' },
  { id: 'strong', label: 'Strong rewrite', hint: 'Improve flow, structure, and clarity' },
  { id: 'teacher', label: 'Teacher mode', hint: 'Correct, explain, and give examples' },
]

export const EDIT_STYLES = [
  { id: 'simple_american_english', label: 'Simple American English', hint: 'Clear, everyday American English for learners' },
  { id: 'academic_english', label: 'Academic English', hint: 'Formal tone, precision, and paragraph structure' },
  { id: 'toefl_writing', label: 'TOEFL Writing', hint: 'Organized, direct writing for TOEFL practice' },
  { id: 'email_professional', label: 'Email / Professional', hint: 'Polite, concise workplace or academic email' },
  { id: 'natural_conversation', label: 'Natural Conversation', hint: 'Friendly, spoken-style everyday English' },
]

export const EDIT_LANGUAGE_LEVELS = [
  { id: 'beginner', label: 'Beginner', hint: 'Short sentences, common words, simple grammar (A1–B1)' },
  { id: 'normal', label: 'Normal', hint: 'Natural sentences with moderate complexity (B1–B2)' },
  { id: 'professional', label: 'Professional', hint: 'Polished, precise vocabulary and smoother structure' },
]

const STYLE_ALIASES = {
  simple: 'simple_american_english',
  academic: 'academic_english',
  toefl: 'toefl_writing',
  email: 'email_professional',
  conversation: 'natural_conversation',
}

export function normalizeEditStyle(style) {
  return STYLE_ALIASES[style] || style || 'simple_american_english'
}

export function normalizeEditLanguageLevel(level) {
  const key = (level || 'normal').toLowerCase()
  if (['beginner', 'normal', 'professional'].includes(key)) return key
  return 'normal'
}

export function getEditOption(list, id) {
  return list.find((item) => item.id === id) || list[0]
}

export function describeEditSettings({ strength, style, languageLevel }) {
  const strengthItem = getEditOption(EDIT_STRENGTHS, strength)
  const styleItem = getEditOption(EDIT_STYLES, style)
  const levelItem = getEditOption(EDIT_LANGUAGE_LEVELS, languageLevel)
  return {
    strength: strengthItem,
    style: styleItem,
    languageLevel: levelItem,
    summary: `${strengthItem.label} · ${styleItem.label} · ${levelItem.label}`,
  }
}

export const PARAPHRASE_LEVELS = [
  { id: 'simple', label: 'Simple' },
  { id: 'natural', label: 'Natural' },
  { id: 'academic', label: 'Academic' },
  { id: 'toefl', label: 'TOEFL' },
  { id: 'professional', label: 'Professional' },
]

export const WRITING_TOOL_TRACKS = [
  'writing_edit_coach',
  'writing_edit_generate',
  'writing_paraphrase_coach',
  'writing_paraphrase_generate',
  'writing_paraphrase_check',
  'sentence_builder_coach',
  'paragraph_builder_coach',
  'writing_lesson_coach',
  'writing_prompt_outline_coach',
]

export function buildEditMessage({ text, strength, style }) {
  return `[Writing edit request]

Original text:
${text.trim()}

Edit strength: ${strength}
Target style: ${style}

Edit supportively. Preserve the learner's ideas. Return the required Markdown sections.`
}

export function buildParaphraseMessage({ text, level }) {
  return `[Paraphrase request]

Original text:
${text.trim()}

Target level: ${level}

Teach the learner — explain vocabulary and structure changes. Return the required Markdown sections.`
}

export function buildSentenceBuilderMessage({ sentence }) {
  return `[Sentence builder request]

Basic sentence:
${sentence.trim()}

Build corrected, expanded, and stronger versions. Teach the reusable pattern. Return the required Markdown sections.`
}

export function buildParagraphBuilderMessage({ topic, reason, example, explanation, conclusion }) {
  return `[Paragraph builder request]

Topic sentence / main idea:
${topic.trim()}

Reason:
${reason.trim()}

Example:
${example.trim()}

Explanation:
${explanation.trim()}

Conclusion:
${conclusion.trim()}

Use the learner's ideas. Return the required Markdown sections.`
}

export function buildLessonPracticeMessage({ lesson, attempt, level = 'B1' }) {
  return `[Writing lesson mini practice]

Lesson: ${lesson.title}
Skill goal: ${lesson.skillGoal}
Level: ${level}
Practice task: ${lesson.miniPractice.prompt}
${lesson.miniPractice.starter ? `Starter: ${lesson.miniPractice.starter}` : ''}

Student attempt:
${attempt.trim()}

Evaluate supportively. Keep feedback short. Return Corrected version, Why, and Pattern sections.`
}

export function buildPromptOutlineMessage(task) {
  return `[Writing prompt outline request]

Mode: ${task.mode}
Level: ${task.level}
Prompt: ${task.prompt}
Target word count: ${task.wordMin}–${task.wordMax}
Writing goal: ${task.goal}

Generate a guided step-by-step outline, sentence starters, sample opening, and draft paragraph.
Use realistic learner-level English. Return the required Markdown sections.`
}
