export const PARAPHRASE_TARGET_LEVELS = [
  { id: 'simple_american_english', label: 'Simple American English' },
  { id: 'academic', label: 'Academic' },
  { id: 'toefl', label: 'TOEFL' },
  { id: 'professional_email', label: 'Professional Email' },
  { id: 'natural_conversation', label: 'Natural Conversation' },
]

export const PARAPHRASE_DIFFICULTIES = [
  { id: 'easy', label: 'Easy' },
  { id: 'medium', label: 'Medium' },
  { id: 'hard', label: 'Hard' },
]

export const PARAPHRASE_TEXT_TYPES = [
  { id: 'one_sentence', label: 'One sentence' },
  { id: 'short_paragraph', label: 'Short paragraph' },
  { id: 'toefl_sentence', label: 'TOEFL-style sentence' },
  { id: 'academic_sentence', label: 'Academic sentence' },
  { id: 'email_sentence', label: 'Professional email sentence' },
  { id: 'conversation_sentence', label: 'Daily conversation sentence' },
]

export const PARAPHRASE_LANGUAGE_LEVELS = [
  { id: 'beginner', label: 'Beginner' },
  { id: 'normal', label: 'Normal' },
  { id: 'professional', label: 'Professional' },
]

const LEVEL_ALIASES = {
  simple: 'simple_american_english',
  natural: 'natural_conversation',
  professional: 'professional_email',
}

export function normalizeParaphraseLevel(level) {
  return LEVEL_ALIASES[level] || level || 'simple_american_english'
}

export function normalizeLanguageLevel(level) {
  const key = (level || 'normal').toLowerCase()
  if (['beginner', 'normal', 'professional'].includes(key)) return key
  return 'normal'
}

export function paraphraseResultLabel(score) {
  if (score >= 90) return 'Excellent paraphrase'
  if (score >= 75) return 'Good paraphrase'
  if (score >= 60) return 'Needs improvement'
  return 'Try again'
}

export const PARAPHRASE_PROVIDER_TRACKS = [
  'writing_paraphrase_generate',
  'writing_paraphrase_check',
  'writing_paraphrase_coach',
]
