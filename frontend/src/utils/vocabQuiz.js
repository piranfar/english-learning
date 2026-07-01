/**
 * Vocabulary quiz generation helpers.
 */

export const QUIZ_MODES = [
  { id: 'multiple_choice', label: 'Multiple choice', implemented: true },
  { id: 'spelling', label: 'Spelling', implemented: true },
  { id: 'sentence_completion', label: 'Sentence completion', implemented: true },
  { id: 'word_meaning', label: 'Word meaning', implemented: true },
  { id: 'meaning_to_word', label: 'Meaning → word', implemented: true },
  { id: 'sentence_writing', label: 'Write your own sentence', implemented: true },
  { id: 'review_mistakes', label: 'Review vocab mistakes', implemented: true },
  { id: 'spelling_audio', label: 'Spelling from audio', implemented: false },
  { id: 'synonym_match', label: 'Synonym match', implemented: false },
  { id: 'antonym_match', label: 'Antonym match', implemented: false },
]

export function normalizeVocabWord(seed) {
  return {
    id: String(seed.id ?? seed.word),
    word: seed.word,
    meaning_en: seed.definition || seed.meaning_en || '',
    meaning_fa: seed.persian_meaning || seed.meaning_fa || '',
    example: seed.example || '',
    level: seed.cefr_level || seed.level || '',
    category: seed.category || '',
    part_of_speech: seed.part_of_speech || '',
    synonyms: seed.synonyms || [],
    antonyms: seed.antonyms || [],
    collocations: seed.collocations || [],
  }
}

export function shuffle(array) {
  const arr = [...array]
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

function uniqueBy(items, keyFn) {
  const seen = new Set()
  const result = []
  for (const item of items) {
    const key = keyFn(item)
    if (!key || seen.has(key)) continue
    seen.add(key)
    result.push(item)
  }
  return result
}

function pickDistractors(pool, target, count, valueFn) {
  const targetValue = valueFn(target)?.toLowerCase?.() || valueFn(target)
  const candidates = shuffle(pool.filter((w) => wordKey(w) !== wordKey(target)))
  const picked = []

  for (const candidate of candidates) {
    const value = valueFn(candidate)
    if (!value) continue
    const normalized = typeof value === 'string' ? value.toLowerCase() : value
    if (normalized === targetValue) continue
    if (picked.some((p) => valueFn(p)?.toLowerCase?.() === normalized)) continue
    picked.push(candidate)
    if (picked.length >= count) break
  }

  return picked
}

function wordKey(word) {
  return String(word?.id ?? word?.word ?? '').toLowerCase()
}

function shortMeaning(word) {
  const text = word.meaning_en || word.definition || ''
  if (text.length <= 80) return text
  return `${text.slice(0, 77)}...`
}

function buildChoices(correct, distractors, labelFn, fallbackLabels = []) {
  const correctLabel = labelFn(correct)
  const choices = uniqueBy(
    [
      { word: correct, label: correctLabel, isCorrect: true },
      ...distractors.map((d) => ({
        word: d,
        label: labelFn(d),
        isCorrect: false,
      })),
    ],
    (c) => c.label?.toLowerCase?.(),
  )

  let fallbackIndex = 0
  while (choices.length < 4 && fallbackIndex < fallbackLabels.length) {
    const label = fallbackLabels[fallbackIndex]
    fallbackIndex += 1
    if (!label || choices.some((c) => c.label?.toLowerCase?.() === label.toLowerCase())) {
      continue
    }
    choices.push({ word: null, label, isCorrect: false })
  }

  return shuffle(choices).slice(0, 4)
}

const MEANING_FALLBACKS = [
  'very fast',
  'easy to break',
  'related to food',
  'not important',
  'very old',
  'without color',
]

const WORD_FALLBACKS = ['fragile', 'ancient', 'empty', 'rapid', 'trivial', 'opaque']

function blankExampleSentence(word) {
  const example = word.example?.trim()
  if (!example) {
    return `Use the word in context: The result was very ______.`
  }

  const pattern = new RegExp(`\\b${escapeRegex(word.word)}\\b`, 'i')
  if (pattern.test(example)) {
    return example.replace(pattern, '______')
  }
  return `${example.replace(/\.$/, '')} → ______`
}

function escapeRegex(text) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function buildQuestion(mode, word, pool) {
  const normalized = normalizeVocabWord(word)

  switch (mode) {
    case 'multiple_choice':
    case 'word_meaning':
      return {
        mode,
        word: normalized,
        prompt: `What does "${normalized.word}" mean?`,
        choices: buildChoices(
          normalized,
          pickDistractors(pool, normalized, 3, (w) => shortMeaning(w)),
          (w) => shortMeaning(w),
          MEANING_FALLBACKS,
        ),
        explanation: normalized.meaning_en,
        persian: normalized.meaning_fa,
        example: normalized.example,
      }

    case 'meaning_to_word':
      return {
        mode,
        word: normalized,
        prompt: `Which word means "${shortMeaning(normalized)}"?`,
        choices: buildChoices(
          normalized,
          pickDistractors(pool, normalized, 3, (w) => w.word),
          (w) => w.word,
          WORD_FALLBACKS,
        ),
        explanation: normalized.meaning_en,
        persian: normalized.meaning_fa,
        example: normalized.example,
      }

    case 'sentence_completion':
      return {
        mode,
        word: normalized,
        prompt: 'Choose the correct word:',
        sentence: blankExampleSentence(normalized),
        choices: buildChoices(
          normalized,
          pickDistractors(pool, normalized, 3, (w) => w.word),
          (w) => w.word,
          WORD_FALLBACKS,
        ),
        explanation: normalized.meaning_en,
        persian: normalized.meaning_fa,
        example: normalized.example,
      }

    case 'spelling':
      return {
        mode,
        word: normalized,
        prompt: 'Type the word that matches the meaning:',
        meaning: shortMeaning(normalized),
        sentence: blankExampleSentence(normalized),
        correctAnswer: normalized.word,
        explanation: normalized.meaning_en,
        persian: normalized.meaning_fa,
        example: normalized.example,
      }

    case 'sentence_writing':
      return {
        mode,
        word: normalized,
        prompt: `Write one sentence using "${normalized.word}".`,
        meaning: shortMeaning(normalized),
        example: normalized.example,
      }

    case 'review_mistakes':
      return buildQuestion('multiple_choice', normalized, pool)

    default:
      return buildQuestion('multiple_choice', normalized, pool)
  }
}

export function checkSpellingAnswer(input, correct) {
  const normalized = input.trim().toLowerCase()
  const target = correct.trim().toLowerCase()
  return normalized === target
}

export function pickQuizWords(words, mode, progressMap, count = 10, focusWord = null) {
  if (focusWord) {
    const match = words.find((w) => wordKey(w) === wordKey(focusWord))
    if (match) return [match]
  }

  let pool = [...words]

  if (mode === 'review_mistakes') {
    pool = pool.filter((w) => {
      const key = wordKey(w)
      const entry = progressMap[key]
      return entry?.needs_review
    })
  }

  if (pool.length === 0) return []

  return shuffle(pool).slice(0, Math.min(count, pool.length))
}

export function buildWritingPrompt(word, sentence) {
  return `[Vocabulary practice]

Target word: "${word.word}"
Meaning: ${word.meaning_en || '—'}

Student sentence:
${sentence.trim()}

Please provide:
1. Corrected sentence (if needed)
2. Brief grammar feedback
3. Vocabulary usage feedback for "${word.word}"
4. One better example sentence using "${word.word}"`
}
