export const GRAMMAR_CATEGORIES = new Set([
  'article',
  'preposition',
  'tense',
  'subject_verb_agreement',
  'word_order',
  'fragment',
  'run_on_sentence',
  'collocation',
  'direct_translation',
])

export const WRITING_CATEGORIES = new Set([
  'spelling',
  'sentence_structure',
  'academic_tone',
  'fragment',
  'run_on_sentence',
])

export const VOCAB_CATEGORIES = new Set(['vocabulary_precision'])

export const SPEAKING_CATEGORIES = new Set(['speaking_organization', 'pronunciation_fluency'])

export const READING_CATEGORIES = new Set(['reading_comprehension'])

export const LISTENING_CATEGORIES = new Set(['listening_comprehension'])

export const CATEGORY_LESSON_TOPICS = {
  article: 'articles-a-an-the',
  preposition: 'prepositions-of-time-and-place',
  tense: 'present-perfect',
  subject_verb_agreement: 'common-persian-speaker-grammar-mistakes',
  word_order: 'common-persian-speaker-grammar-mistakes',
  fragment: 'relative-clauses',
  run_on_sentence: 'relative-clauses',
  collocation: 'common-persian-speaker-grammar-mistakes',
  direct_translation: 'common-persian-speaker-grammar-mistakes',
}

export const TRACK_LABELS = {
  writing_edit_coach: 'Writing correction',
  grammar_coach: 'Grammar',
  writing_lesson_coach: 'Writing lesson',
  vocab_quiz: 'Vocabulary quiz',
  writing_coach: 'Writing practice',
  speaking_coach: 'Speaking practice',
  reading_coach: 'Reading practice',
  listening_coach: 'Listening practice',
  writing_paraphrase_coach: 'Paraphrasing practice',
  writing_paraphrase_generate: 'Paraphrasing practice',
  writing_paraphrase_check: 'Paraphrasing practice',
  sentence_builder_coach: 'Sentence builder',
  paragraph_builder_coach: 'Paragraph builder',
}

export const CATEGORY_LABELS = {
  article: 'Article errors',
  preposition: 'Preposition errors',
  tense: 'Verb tense',
  subject_verb_agreement: 'Subject-verb agreement',
  word_order: 'Word order',
  spelling: 'Spelling',
  sentence_structure: 'Sentence structure',
  fragment: 'Sentence fragments',
  run_on_sentence: 'Run-on sentences',
  collocation: 'Collocation',
  vocabulary_precision: 'Vocabulary precision',
  academic_tone: 'Academic tone',
  direct_translation: 'Direct translation',
  speaking_organization: 'Speaking organization',
  pronunciation_fluency: 'Pronunciation & fluency',
  reading_comprehension: 'Reading comprehension',
  listening_comprehension: 'Listening comprehension',
  other: 'Other',
}

export const CATEGORY_EXPLANATIONS = {
  article: 'Article mistakes show up in almost every TOEFL speaking and writing answer.',
  preposition: 'Prepositions change meaning quickly, especially in academic sentences.',
  tense: 'Consistent verb tense helps you sound clear and confident on timed tasks.',
  subject_verb_agreement: 'Agreement errors are easy to fix once you notice the pattern.',
  word_order: 'Natural word order makes your ideas easier to follow under pressure.',
  spelling: 'Spelling fixes improve clarity in essays and typed responses.',
  sentence_structure: 'Strong sentence structure makes your main idea easier to understand.',
  fragment: 'Complete sentences help you score higher on grammar and coherence.',
  run_on_sentence: 'Controlled sentence length keeps academic writing readable.',
  collocation: 'Natural word combinations make your English sound more fluent.',
  vocabulary_precision: 'Precise vocabulary helps you say exactly what you mean on test day.',
  academic_tone: 'Academic tone matters for essays, summaries, and integrated tasks.',
  direct_translation: 'English word order is different from Persian — small shifts help a lot.',
  speaking_organization: 'Clear organization helps you finish speaking tasks on time.',
  pronunciation_fluency: 'Fluency practice makes your speaking sound smoother and more natural.',
  reading_comprehension: 'Reading inference is important for TOEFL.',
  listening_comprehension: 'Listening for main ideas and details is essential for lecture questions.',
  other: 'Reviewing your recent mistakes helps you stop repeating the same errors.',
}

export function categoryExplanation(categoryId) {
  return CATEGORY_EXPLANATIONS[categoryId] || CATEGORY_EXPLANATIONS.other
}

export const CATEGORY_ORDER = [
  'article',
  'preposition',
  'tense',
  'subject_verb_agreement',
  'word_order',
  'spelling',
  'sentence_structure',
  'fragment',
  'run_on_sentence',
  'collocation',
  'vocabulary_precision',
  'academic_tone',
  'direct_translation',
  'speaking_organization',
  'pronunciation_fluency',
  'reading_comprehension',
  'listening_comprehension',
  'other',
]

function titleCaseFromSnake(value) {
  return (value || '')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function trackLabel(track) {
  if (!track) return 'Practice'
  if (TRACK_LABELS[track]) return TRACK_LABELS[track]
  return titleCaseFromSnake(track)
}

export function inferMistakeCategory(mistake) {
  if (mistake?.category && CATEGORY_LABELS[mistake.category]) {
    return mistake.category
  }

  return 'other'
}

export function categoryLabel(categoryId) {
  return CATEGORY_LABELS[categoryId] || CATEGORY_LABELS.other
}

export function groupMistakesByCategory(mistakes) {
  const groups = new Map()

  for (const mistake of mistakes) {
    const category = inferMistakeCategory(mistake)
    if (!groups.has(category)) {
      groups.set(category, [])
    }
    groups.get(category).push({ ...mistake, category })
  }

  const ordered = CATEGORY_ORDER.filter((category) => groups.has(category))
  const extras = [...groups.keys()].filter((category) => !ordered.includes(category))

  return [...ordered, ...extras].map((category) => ({
    category,
    label: categoryLabel(category),
    mistakes: groups.get(category),
  }))
}

export function practiceRouteForCategory(category) {
  if (VOCAB_CATEGORIES.has(category)) {
    return '/vocab?mode=review_mistakes'
  }
  if (WRITING_CATEGORIES.has(category)) {
    return '/writing?tab=editing'
  }
  if (SPEAKING_CATEGORIES.has(category)) {
    return '/speaking'
  }
  if (READING_CATEGORIES.has(category)) {
    return '/reading?tab=generate'
  }
  if (LISTENING_CATEGORIES.has(category)) {
    return '/listening?tab=generate'
  }

  const topic = CATEGORY_LESSON_TOPICS[category]
  if (topic) {
    return `/lesson?topic=${topic}`
  }

  if (GRAMMAR_CATEGORIES.has(category)) {
    return '/lesson'
  }

  return '/lesson'
}

export function canPracticeCategory(category) {
  return Boolean(practiceRouteForCategory(category))
}

export function formatMistakeDate(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return value
  }
}

export function mistakeCardFields(mistake) {
  const isVocab = mistake.track === 'vocab_quiz'

  if (isVocab) {
    return {
      wrong: mistake.wrong_text,
      correct: mistake.correct_text,
      why: mistake.reason,
      example: mistake.review_sentence,
      isVocab: true,
    }
  }

  return {
    wrong: mistake.wrong_text,
    correct: mistake.correct_text,
    why: mistake.reason,
    example: mistake.review_sentence,
    isVocab: false,
  }
}
