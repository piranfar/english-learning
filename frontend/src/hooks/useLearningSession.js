import { useCallback, useEffect, useRef, useState } from 'react'
import {
  clearAllSessions,
  clearCurrentSession,
  createEmptySession,
  loadCurrentSession,
  loadRecentSessions,
  loadSessionById,
  saveCurrentSession,
} from '../services/learningSessionStorage'
import {
  buildWelcomeBackMessage,
  courseIdFromTopic,
  mergeSessionUpdate,
} from '../utils/courseProgress'

export function useLearningSession(pageKey = 'lesson') {
  const [savedSession, setSavedSession] = useState(null)
  const [recentSessions, setRecentSessions] = useState([])
  const [showWelcomeBack, setShowWelcomeBack] = useState(false)
  const [welcomeMessage, setWelcomeMessage] = useState('')
  const [hydrated, setHydrated] = useState(false)
  const skipNextSave = useRef(false)

  const refreshRecent = useCallback(() => {
    setRecentSessions(loadRecentSessions())
  }, [])

  useEffect(() => {
    const stored = loadCurrentSession()
    refreshRecent()
    if (stored && stored.pageKey === pageKey && stored.messages?.length > 0) {
      if (stored.progress?.status !== 'completed') {
        setSavedSession(stored)
        setWelcomeMessage(buildWelcomeBackMessage(stored))
        setShowWelcomeBack(true)
      }
    }
    setHydrated(true)
  }, [pageKey, refreshRecent])

  const persistSession = useCallback(
    (partial) => {
      if (skipNextSave.current) {
        skipNextSave.current = false
        return null
      }
      setSavedSession((prev) => {
        const merged = mergeSessionUpdate(
          prev || createEmptySession({ pageKey, ...partial }),
          partial,
        )
        saveCurrentSession(merged)
        refreshRecent()
        return merged
      })
    },
    [pageKey, refreshRecent],
  )

  const applyRestoredSession = useCallback((session) => {
    if (!session) return null
    skipNextSave.current = true
    setSavedSession(session)
    setShowWelcomeBack(false)
    saveCurrentSession(session)
    refreshRecent()
    return session
  }, [refreshRecent])

  const continueSession = useCallback(() => {
    const session = savedSession || loadCurrentSession()
    return applyRestoredSession(session)
  }, [applyRestoredSession, savedSession])

  const loadSession = useCallback(
    (sessionId) => {
      const session = loadSessionById(sessionId)
      if (!session) return null
      setWelcomeMessage(buildWelcomeBackMessage(session))
      return applyRestoredSession(session)
    },
    [applyRestoredSession],
  )

  const startNewSession = useCallback(
    (overrides = {}) => {
      clearCurrentSession()
      const fresh = createEmptySession({ pageKey, ...overrides })
      setSavedSession(null)
      setShowWelcomeBack(false)
      setWelcomeMessage('')
      refreshRecent()
      return fresh
    },
    [pageKey, refreshRecent],
  )

  const startOverCourse = useCallback(
    (topicMeta = {}) => {
      const fresh = createEmptySession({
        pageKey,
        track: topicMeta.track || 'grammar_coach',
        provider: topicMeta.provider || 'ollama',
        title: topicMeta.title || '',
        courseId: topicMeta.courseId || courseIdFromTopic(topicMeta),
        courseTitle: topicMeta.courseTitle || topicMeta.title || '',
        topicId: topicMeta.topicId ?? null,
        messages: [],
        practiceQuestions: [],
        userAnswers: [],
        correctionResults: [],
        backendSessionId: null,
      })
      saveCurrentSession(fresh)
      setSavedSession(fresh)
      setShowWelcomeBack(false)
      setWelcomeMessage('')
      refreshRecent()
      return fresh
    },
    [pageKey, refreshRecent],
  )

  const markCompleted = useCallback(() => {
    persistSession({
      progress: {
        ...(savedSession?.progress || {}),
        status: 'completed',
      },
    })
  }, [persistSession, savedSession])

  const handleClearAll = useCallback(() => {
    clearAllSessions()
    setSavedSession(null)
    setShowWelcomeBack(false)
    setWelcomeMessage('')
    refreshRecent()
  }, [refreshRecent])

  return {
    hydrated,
    savedSession,
    recentSessions,
    showWelcomeBack,
    welcomeMessage,
    persistSession,
    continueSession,
    loadSession,
    startNewSession,
    startOverCourse,
    markCompleted,
    handleClearAll,
    setShowWelcomeBack,
  }
}
