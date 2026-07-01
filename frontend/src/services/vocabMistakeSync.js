import { recordVocabQuizMistake } from '../api/client'

/**
 * Sync a vocab quiz wrong answer to the backend Mistakes list (track: vocab_quiz).
 * Fire-and-forget; localStorage progress remains the source for quiz UI.
 */
export function syncVocabQuizMistake(word, { userAnswer = '', quizMode = '' } = {}) {
  recordVocabQuizMistake({
    word: word.word,
    wrongAnswer: userAnswer,
    meaningEn: word.meaning_en || word.definition || '',
    meaningFa: word.meaning_fa || word.persian_meaning || '',
    example: word.example || '',
    quizMode,
  }).catch((error) => {
    console.warn('[vocabMistakeSync] Failed to sync mistake:', error.message)
  })
}
