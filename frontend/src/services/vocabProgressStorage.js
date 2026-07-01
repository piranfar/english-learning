/**
 * Local-first vocabulary progress tracking.
 * Keys: fluentbridge_vocab_progress, fluentbridge_vocab_mistakes, fluentbridge_vocab_quiz_state
 */

const KEYS = {
  progress: 'fluentbridge_vocab_progress',
  mistakes: 'fluentbridge_vocab_mistakes',
  quizState: 'fluentbridge_vocab_quiz_state',
}

export const MASTERY_LEARNED = 3
export const CLEAR_REVIEW_STREAK = 2

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (error) {
    console.warn('[vocabProgressStorage] Failed to save:', error)
    return false
  }
}

export function wordKey(word) {
  return String(word?.id ?? word?.word ?? '').toLowerCase()
}

export function createEmptyProgress(wordId) {
  return {
    word_id: wordId,
    correct_count: 0,
    wrong_count: 0,
    current_streak: 0,
    mastery_level: 0,
    needs_review: false,
    status: 'new',
    last_practiced_at: null,
    next_review_at: null,
  }
}

export function normalizeProgressEntry(entry, wordId) {
  const base = createEmptyProgress(wordId)
  if (!entry || typeof entry !== 'object') return base

  let mastery = entry.mastery_level
  if (mastery === undefined || mastery === null) {
    mastery = entry.status === 'learned' ? MASTERY_LEARNED : 0
  }

  return {
    ...base,
    ...entry,
    mastery_level: mastery,
    current_streak: entry.current_streak ?? 0,
  }
}

export function loadAllProgress() {
  const data = safeParse(localStorage.getItem(KEYS.progress))
  if (!data || typeof data !== 'object') return {}

  const normalized = {}
  for (const [key, entry] of Object.entries(data)) {
    normalized[key] = normalizeProgressEntry(entry, entry.word_id ?? key)
  }
  return normalized
}

export function saveAllProgress(progressMap) {
  return safeSet(KEYS.progress, progressMap)
}

export function getWordProgress(wordId) {
  const key = wordKey({ id: wordId })
  return loadAllProgress()[key] || createEmptyProgress(wordId)
}

export function shouldClearReview(entry) {
  return Boolean(entry?.needs_review && entry.current_streak >= CLEAR_REVIEW_STREAK)
}

export function markAnswer(word, isCorrect) {
  const key = wordKey(word)
  const all = loadAllProgress()
  const entry = normalizeProgressEntry(
    all[key] || createEmptyProgress(word.id ?? word.word),
    word.id ?? word.word,
  )
  const now = new Date().toISOString()

  if (isCorrect) {
    entry.correct_count += 1
    entry.current_streak += 1
    entry.mastery_level = Math.min(entry.mastery_level + 1, MASTERY_LEARNED + 2)
    entry.last_practiced_at = now

    if (entry.needs_review && shouldClearReview(entry)) {
      entry.needs_review = false
      entry.next_review_at = null
      removeFromMistakes(word)
    }

    if (!entry.needs_review && entry.mastery_level >= MASTERY_LEARNED) {
      entry.status = 'learned'
    } else {
      entry.status = 'learning'
    }
  } else {
    entry.wrong_count += 1
    entry.current_streak = 0
    entry.mastery_level = Math.max(0, entry.mastery_level - 1)
    entry.needs_review = true
    entry.status = 'learning'
    entry.last_practiced_at = now
    entry.next_review_at = now
    addToMistakes(word)
  }

  all[key] = entry
  saveAllProgress(all)
  return entry
}

/** @deprecated Use markAnswer(word, true) */
export function recordCorrect(word) {
  return markAnswer(word, true)
}

/** @deprecated Use markAnswer(word, false) */
export function recordWrong(word) {
  return markAnswer(word, false)
}

export function markLearned(word) {
  const key = wordKey(word)
  const all = loadAllProgress()
  const entry = normalizeProgressEntry(
    all[key] || createEmptyProgress(word.id ?? word.word),
    word.id ?? word.word,
  )
  entry.status = 'learned'
  entry.needs_review = false
  entry.mastery_level = MASTERY_LEARNED
  entry.current_streak = CLEAR_REVIEW_STREAK
  entry.correct_count = Math.max(entry.correct_count, MASTERY_LEARNED)
  entry.last_practiced_at = new Date().toISOString()
  entry.next_review_at = null
  all[key] = entry
  saveAllProgress(all)
  removeFromMistakes(word)
  return entry
}

export function loadMistakes() {
  const data = safeParse(localStorage.getItem(KEYS.mistakes))
  return Array.isArray(data) ? data : []
}

export function addToMistakes(word) {
  const key = wordKey(word)
  const mistakes = loadMistakes()
  if (mistakes.some((m) => wordKey(m) === key)) return
  mistakes.unshift({
    id: word.id,
    word: word.word,
    meaning_en: word.meaning_en || word.definition,
    added_at: new Date().toISOString(),
  })
  safeSet(KEYS.mistakes, mistakes.slice(0, 200))
}

export function removeFromMistakes(word) {
  const key = wordKey(word)
  const filtered = loadMistakes().filter((m) => wordKey(m) !== key)
  safeSet(KEYS.mistakes, filtered)
}

export function loadQuizState() {
  return safeParse(localStorage.getItem(KEYS.quizState))
}

export function saveQuizState(state) {
  if (!state) {
    localStorage.removeItem(KEYS.quizState)
    return true
  }
  return safeSet(KEYS.quizState, state)
}

export function computeProgressSummary(words, progressMap) {
  let learned = 0
  let learning = 0
  let review = 0
  let newCount = 0
  let totalCorrect = 0
  let totalWrong = 0

  for (const word of words) {
    const key = wordKey(word)
    const entry = normalizeProgressEntry(
      progressMap[key] || createEmptyProgress(word.id),
      word.id,
    )
    totalCorrect += entry.correct_count
    totalWrong += entry.wrong_count

    if (entry.status === 'learned' && !entry.needs_review) learned += 1
    else if (entry.needs_review) review += 1
    else if (entry.status === 'learning') learning += 1
    else newCount += 1
  }

  const attempts = totalCorrect + totalWrong
  const accuracy = attempts > 0 ? Math.round((totalCorrect / attempts) * 100) : null

  return { learned, learning, review, new: newCount, accuracy, totalCorrect, totalWrong }
}

export function filterWordsByStatus(words, statusFilter, progressMap) {
  if (!statusFilter || statusFilter === 'all') return words

  return words.filter((word) => {
    const key = wordKey(word)
    const entry = normalizeProgressEntry(
      progressMap[key] || createEmptyProgress(word.id),
      word.id,
    )
    if (statusFilter === 'review') return entry.needs_review
    if (statusFilter === 'new') return entry.status === 'new' && !entry.needs_review
    return entry.status === statusFilter
  })
}
