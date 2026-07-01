/**
 * Writing Lessons progress (Phase 2).
 */

const PROGRESS_KEY = 'fluentbridge_writing_lessons_progress'

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function defaultProgress() {
  return {
    completedLessonIds: [],
    currentLessonId: null,
    attempts: {},
    lastFeedback: {},
  }
}

export function loadLessonsProgress() {
  const data = safeParse(localStorage.getItem(PROGRESS_KEY))
  if (!data || typeof data !== 'object') return defaultProgress()
  return {
    ...defaultProgress(),
    ...data,
    completedLessonIds: Array.isArray(data.completedLessonIds) ? data.completedLessonIds : [],
    attempts: data.attempts && typeof data.attempts === 'object' ? data.attempts : {},
    lastFeedback: data.lastFeedback && typeof data.lastFeedback === 'object' ? data.lastFeedback : {},
  }
}

export function saveLessonsProgress(progress) {
  try {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress))
    return true
  } catch {
    return false
  }
}

export function markLessonComplete(lessonId) {
  const progress = loadLessonsProgress()
  if (!progress.completedLessonIds.includes(lessonId)) {
    progress.completedLessonIds.push(lessonId)
  }
  saveLessonsProgress(progress)
  return progress
}

export function setCurrentLesson(lessonId) {
  const progress = loadLessonsProgress()
  progress.currentLessonId = lessonId
  saveLessonsProgress(progress)
  return progress
}

export function saveLessonAttempt(lessonId, attempt) {
  const progress = loadLessonsProgress()
  const list = progress.attempts[lessonId] || []
  list.unshift({
    input: attempt.input,
    feedback: attempt.feedback,
    corrected: attempt.corrected || '',
    date: new Date().toISOString(),
  })
  progress.attempts[lessonId] = list.slice(0, 10)
  if (attempt.feedback) {
    progress.lastFeedback[lessonId] = {
      input: attempt.input,
      feedback: attempt.feedback,
      corrected: attempt.corrected || '',
      pattern: attempt.pattern || '',
      why: attempt.why || '',
    }
  }
  saveLessonsProgress(progress)
  return progress
}

export function getNextIncompleteLessonId(lessons, progress) {
  const incomplete = lessons.find((l) => !progress.completedLessonIds.includes(l.id))
  return incomplete?.id || lessons[0]?.id || null
}
