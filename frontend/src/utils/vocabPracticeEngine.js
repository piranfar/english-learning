/**
 * Adaptive vocab quiz session engine — queue, review insertion, mastery tracking.
 */

import {
  CLEAR_REVIEW_STREAK,
  markAnswer,
  shouldClearReview,
  wordKey,
} from '../services/vocabProgressStorage'
import { normalizeVocabWord, pickQuizWords, shuffle } from './vocabQuiz'

const DEFAULT_LENGTH = 10
const MIN_REVIEW_GAP = 2
const MAX_REVIEW_GAP = 4

export function queueItemWord(item) {
  return item?.word ?? item
}

export function makeQueueItem(word, isReview = false) {
  return { word: normalizeVocabWord(word), isReview }
}

export function createPracticeSession({
  mode,
  words,
  progressMap,
  length = DEFAULT_LENGTH,
  focusWord = null,
  reviewOnly = false,
}) {
  let picked = []

  if (focusWord) {
    picked = [normalizeVocabWord(focusWord)]
  } else if (reviewOnly || mode === 'review_mistakes') {
    picked = shuffle(
      words.filter((w) => {
        const key = wordKey(w)
        return progressMap[key]?.needs_review
      }),
    )
  } else {
    picked = pickQuizWords(words, mode, progressMap, length).map(normalizeVocabWord)
  }

  if (picked.length === 0) return null

  const queue = picked.map((word) => makeQueueItem(word, false))

  return {
    mode: reviewOnly || mode === 'review_mistakes' ? 'review_mistakes' : mode,
    reviewOnly: reviewOnly || mode === 'review_mistakes',
    queue,
    index: 0,
    originalLength: reviewOnly || mode === 'review_mistakes' ? picked.length : queue.length,
    sessionReview: {},
    score: {
      originalCorrect: 0,
      originalTotal: 0,
      reviewCorrect: 0,
      reviewTotal: 0,
    },
    finishedOriginal: false,
  }
}

export function getCurrentQueueItem(session) {
  if (!session || session.index >= session.queue.length) return null
  return session.queue[session.index]
}

export function countSessionReviewPending(session) {
  return Object.values(session.sessionReview).filter(
    (entry) => entry.correctStreak < CLEAR_REVIEW_STREAK,
  ).length
}

export function isWordScheduledAhead(session, word) {
  const key = wordKey(word)
  return session.queue
    .slice(session.index + 1)
    .some((item) => wordKey(queueItemWord(item)) === key)
}

export function insertReviewQuestionRandomly(session, word, fromIndex = session.index) {
  const key = wordKey(word)
  const queue = [...session.queue]

  if (queue.slice(fromIndex + 1).some((item) => wordKey(queueItemWord(item)) === key)) {
    return queue
  }

  const poolSize = queue.length - fromIndex - 1
  let gap = MIN_REVIEW_GAP + Math.floor(Math.random() * (MAX_REVIEW_GAP - MIN_REVIEW_GAP + 1))

  if (poolSize <= MIN_REVIEW_GAP) {
    gap = Math.max(1, poolSize)
  }

  let insertAt = fromIndex + 1 + gap
  insertAt = Math.min(insertAt, queue.length)

  const prevKey =
    insertAt > 0 ? wordKey(queueItemWord(queue[insertAt - 1])) : null
  const nextKey =
    insertAt < queue.length ? wordKey(queueItemWord(queue[insertAt])) : null

  if (prevKey === key) insertAt += 1
  if (insertAt < queue.length && nextKey === key) insertAt += 1
  insertAt = Math.min(insertAt, queue.length)

  queue.splice(insertAt, 0, makeQueueItem(word, true))
  return queue
}

export function processSessionAnswer(session, word, isCorrect) {
  const key = wordKey(word)
  const item = getCurrentQueueItem(session)
  const isReview = Boolean(item?.isReview)
  const wasTracked = Boolean(session.sessionReview[key])
  const trackReview = isReview || wasTracked

  const progress = markAnswer(word, isCorrect)

  const score = { ...session.score }
  if (isReview) {
    score.reviewTotal += 1
    if (isCorrect) score.reviewCorrect += 1
  } else {
    score.originalTotal += 1
    if (isCorrect) score.originalCorrect += 1
  }

  let sessionReview = { ...session.sessionReview }
  let queue = [...session.queue]
  let scheduledAgain = false

  if (!isCorrect) {
    sessionReview[key] = { correctStreak: 0 }
    queue = insertReviewQuestionRandomly({ ...session, queue }, word, session.index)
    scheduledAgain = true
  } else if (trackReview) {
    const prevStreak = sessionReview[key]?.correctStreak ?? 0
    const newStreak = prevStreak + 1
    const cleared = newStreak >= CLEAR_REVIEW_STREAK && !progress.needs_review

    if (cleared) {
      const { [key]: _removed, ...rest } = sessionReview
      sessionReview = rest
    } else {
      sessionReview[key] = { correctStreak: newStreak }
      if (!isWordScheduledAhead({ ...session, queue }, word)) {
        queue = insertReviewQuestionRandomly({ ...session, queue }, word, session.index)
        scheduledAgain = true
      }
    }
  }

  const finishedOriginal =
    session.finishedOriginal ||
    (!session.reviewOnly && session.index + 1 >= session.originalLength)

  return {
    session: {
      ...session,
      queue,
      sessionReview,
      score,
      finishedOriginal,
    },
    progress,
    scheduledAgain,
    clearedReview: !isCorrect ? false : trackReview && !sessionReview[key],
  }
}

export function appendPendingReviewWords(session, words) {
  let queue = [...session.queue]
  let changed = false

  for (const [key, entry] of Object.entries(session.sessionReview)) {
    if (entry.correctStreak >= CLEAR_REVIEW_STREAK) continue
    if (queue.slice(session.index).some((item) => wordKey(queueItemWord(item)) === key)) {
      continue
    }
    const word = words.find((w) => wordKey(w) === key)
    if (word) {
      queue.push(makeQueueItem(word, true))
      changed = true
    }
  }

  if (!changed) return session
  return { ...session, queue }
}

export function extendReviewOnlySession(session, words, progressMap) {
  const pool = shuffle(
    words.filter((w) => {
      const key = wordKey(w)
      return progressMap[key]?.needs_review || session.sessionReview[key]
    }),
  ).map((w) => makeQueueItem(w, true))

  if (pool.length === 0) return session

  return {
    ...session,
    queue: [...session.queue, ...pool],
  }
}

export function advanceSession(session) {
  return { ...session, index: session.index + 1 }
}

export function isSessionComplete(session) {
  if (!session) return true
  if (session.index < session.queue.length - 1) return false
  return countSessionReviewPending(session) === 0
}

export function canFinishAnyway(session) {
  if (!session) return false
  return session.finishedOriginal && countSessionReviewPending(session) > 0
}

export function getCompletionMessage(session) {
  const { originalCorrect, originalTotal, reviewCorrect, reviewTotal } = session.score
  const pending = countSessionReviewPending(session)

  if (pending > 0) {
    return null
  }

  if (reviewTotal > 0) {
    return (
      `Quiz complete after review. ` +
      `Score: ${originalCorrect}/${originalTotal} original · ` +
      `Review passed: ${reviewCorrect}/${reviewTotal}`
    )
  }

  return `Quiz complete! Score: ${originalCorrect}/${originalTotal}`
}

export function getReviewHint(session, word) {
  const key = wordKey(word)
  const entry = session.sessionReview[key]
  if (!entry && !session.reviewOnly) return null

  const streak = entry?.correctStreak ?? 0
  const remaining = Math.max(0, CLEAR_REVIEW_STREAK - streak)
  if (remaining === 0) return null

  return `Needs ${remaining} more correct answer${remaining === 1 ? '' : 's'} in a row to clear review`
}

export function serializeSession(session) {
  if (!session) return null
  return {
    ...session,
    queue: session.queue.map((item) => ({
      word: item.word,
      isReview: item.isReview,
    })),
  }
}

export function deserializeSession(raw) {
  if (!raw || !Array.isArray(raw.queue)) return null
  return {
    ...raw,
    queue: raw.queue.map((item) => makeQueueItem(item.word, item.isReview)),
    sessionReview: raw.sessionReview || {},
    score: raw.score || {
      originalCorrect: 0,
      originalTotal: 0,
      reviewCorrect: 0,
      reviewTotal: 0,
    },
  }
}

export { shouldClearReview, CLEAR_REVIEW_STREAK }
