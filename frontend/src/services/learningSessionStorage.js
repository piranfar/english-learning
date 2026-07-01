/**
 * Local-first learning session persistence.
 * Designed for future sync to Django PracticeSession / LessonProgress.
 */

const KEYS = {
  current: 'english_app_current_session',
  sessions: 'english_app_sessions',
  progress: 'english_app_progress',
}

const MAX_HISTORY = 5
const STORAGE_VERSION = 1

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (error) {
    console.warn('[learningSessionStorage] Corrupted saved data ignored:', error)
    return null
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (error) {
    console.warn('[learningSessionStorage] Failed to save:', error)
    return false
  }
}

export function createEmptySession(overrides = {}) {
  const now = new Date().toISOString()
  return {
    version: STORAGE_VERSION,
    id: overrides.id || `local_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    pageKey: overrides.pageKey || 'lesson',
    backendSessionId: overrides.backendSessionId ?? null,
    track: overrides.track || 'grammar_coach',
    provider: overrides.provider || 'ollama',
    title: overrides.title || '',
    courseId: overrides.courseId || '',
    courseTitle: overrides.courseTitle || '',
    topicId: overrides.topicId ?? null,
    messages: overrides.messages || [],
    practiceQuestions: overrides.practiceQuestions || [],
    userAnswers: overrides.userAnswers || [],
    correctionResults: overrides.correctionResults || [],
    progress: overrides.progress || createEmptyProgress(overrides),
    lastUpdatedAt: now,
    welcomeBackMessage: '',
  }
}

export function createEmptyProgress(overrides = {}) {
  return {
    course_id: overrides.courseId || overrides.course_id || '',
    course_title: overrides.courseTitle || overrides.course_title || '',
    current_step: 1,
    completed_steps: [],
    total_steps: 6,
    completed_practice_questions: 0,
    total_practice_questions: 0,
    status: 'in_progress',
    last_message_at: new Date().toISOString(),
  }
}

export function loadCurrentSession() {
  const data = safeParse(localStorage.getItem(KEYS.current))
  if (!data || typeof data !== 'object') return null
  if (!Array.isArray(data.messages)) return null
  return normalizeSession(data)
}

export function saveCurrentSession(session) {
  if (!session) return false
  const normalized = normalizeSession({
    ...session,
    lastUpdatedAt: new Date().toISOString(),
  })
  safeSet(KEYS.current, normalized)
  saveSessionToHistory(normalized)
  if (normalized.progress?.course_id) {
    saveProgressEntry(normalized.progress.course_id, normalized.progress)
  }
  return true
}

export function clearCurrentSession() {
  try {
    localStorage.removeItem(KEYS.current)
    return true
  } catch (error) {
    console.warn('[learningSessionStorage] Failed to clear current session:', error)
    return false
  }
}

export function loadRecentSessions(limit = MAX_HISTORY) {
  const data = safeParse(localStorage.getItem(KEYS.sessions))
  if (!Array.isArray(data)) return []
  return data
    .map(normalizeSession)
    .filter(Boolean)
    .sort((a, b) => new Date(b.lastUpdatedAt) - new Date(a.lastUpdatedAt))
    .slice(0, limit)
}

export function saveSessionToHistory(session) {
  if (!session?.id) return false
  const normalized = normalizeSession(session)
  const existing = loadRecentSessions(MAX_HISTORY + 5)
  const filtered = existing.filter((item) => item.id !== normalized.id)
  const next = [normalized, ...filtered]
    .sort((a, b) => new Date(b.lastUpdatedAt) - new Date(a.lastUpdatedAt))
    .slice(0, MAX_HISTORY)
  return safeSet(KEYS.sessions, next)
}

export function loadSessionById(sessionId) {
  if (!sessionId) return null
  const current = loadCurrentSession()
  if (current?.id === sessionId) return current
  return loadRecentSessions(MAX_HISTORY + 5).find((item) => item.id === sessionId) || null
}

export function loadProgressMap() {
  const data = safeParse(localStorage.getItem(KEYS.progress))
  if (!data || typeof data !== 'object') return {}
  return data
}

export function saveProgressEntry(courseId, progress) {
  if (!courseId || !progress) return false
  const map = loadProgressMap()
  map[courseId] = { ...progress, course_id: courseId }
  return safeSet(KEYS.progress, map)
}

export function clearAllSessions() {
  try {
    localStorage.removeItem(KEYS.current)
    localStorage.removeItem(KEYS.sessions)
    localStorage.removeItem(KEYS.progress)
    return true
  } catch (error) {
    console.warn('[learningSessionStorage] Failed to clear all sessions:', error)
    return false
  }
}

function normalizeSession(raw) {
  if (!raw || typeof raw !== 'object') return null
  return {
    version: raw.version || STORAGE_VERSION,
    id: String(raw.id || `local_${Date.now()}`),
    pageKey: raw.pageKey || 'lesson',
    backendSessionId: raw.backendSessionId ?? null,
    track: raw.track || 'grammar_coach',
    provider: raw.provider || 'ollama',
    title: raw.title || raw.courseTitle || '',
    courseId: raw.courseId || raw.progress?.course_id || '',
    courseTitle: raw.courseTitle || raw.progress?.course_title || raw.title || '',
    topicId: raw.topicId ?? null,
    messages: Array.isArray(raw.messages) ? raw.messages : [],
    practiceQuestions: Array.isArray(raw.practiceQuestions) ? raw.practiceQuestions : [],
    userAnswers: Array.isArray(raw.userAnswers) ? raw.userAnswers : [],
    correctionResults: Array.isArray(raw.correctionResults) ? raw.correctionResults : [],
    progress: normalizeProgress(raw.progress, raw),
    lastUpdatedAt: raw.lastUpdatedAt || new Date().toISOString(),
    welcomeBackMessage: raw.welcomeBackMessage || '',
  }
}

function normalizeProgress(progress, session) {
  const base = progress && typeof progress === 'object' ? progress : {}
  return {
    course_id: base.course_id || session.courseId || '',
    course_title: base.course_title || session.courseTitle || session.title || '',
    current_step: Number(base.current_step) || 1,
    completed_steps: Array.isArray(base.completed_steps) ? base.completed_steps : [],
    total_steps: Number(base.total_steps) || 6,
    completed_practice_questions: Number(base.completed_practice_questions) || 0,
    total_practice_questions: Number(base.total_practice_questions) || 0,
    status: base.status === 'completed' ? 'completed' : 'in_progress',
    last_message_at: base.last_message_at || session.lastUpdatedAt || new Date().toISOString(),
  }
}

export function progressPercent(progress) {
  if (!progress) return 0
  const stepPart =
    progress.total_steps > 0
      ? (progress.completed_steps?.length || 0) / progress.total_steps
      : 0
  const practicePart =
    progress.total_practice_questions > 0
      ? (progress.completed_practice_questions || 0) / progress.total_practice_questions
      : 0
  const combined =
    progress.total_practice_questions > 0
      ? stepPart * 0.6 + practicePart * 0.4
      : stepPart
  return Math.min(100, Math.round(combined * 100))
}

export function formatLastActivity(iso) {
  if (!iso) return 'Unknown'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
