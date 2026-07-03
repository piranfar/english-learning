import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  getLessonRecommendation,
  getLessonTopics,
  startRecommendedLesson,
} from '../api/client'
import Chat from '../components/Chat'
import LessonQuizPanel from '../components/LessonQuizPanel'
import ProgressBar from '../components/ProgressBar'
import { useLearningSession } from '../hooks/useLearningSession'
import { courseIdFromTopic } from '../utils/courseProgress'
import { DEFAULT_AI_PROVIDER } from '../utils/defaultProvider'
import {
  findCurrentModule,
  moduleProgress,
  neighborLessons,
  nextUnlockedLesson,
  topicsForModule,
} from '../utils/roadmapModules'
import { findCurrentLesson } from '../utils/roadmapStatus'
import { formatLastActivity, sessionIdForTopic, clearCurrentSession } from '../services/learningSessionStorage'

function learningObjectives(topic) {
  if (!topic) return []
  const items = [
    `Use ${topic.title.toLowerCase()} accurately in short sentences`,
    'Understand Persian-friendly explanations and examples',
    'Apply the pattern in quick practice and correction tasks',
  ]
  if (topic.description) {
    items.push(topic.description)
  }
  return items.slice(0, 5)
}

export default function Lesson() {
  const [searchParams] = useSearchParams()
  const topicSlug = searchParams.get('topic')
  const [recommendation, setRecommendation] = useState(null)
  const [topics, setTopics] = useState([])
  const [stages, setStages] = useState([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [nextLessonAfterComplete, setNextLessonAfterComplete] = useState(null)
  const [showCompletionGuide, setShowCompletionGuide] = useState(false)

  const [currentTopicId, setCurrentTopicId] = useState(null)
  const [currentTopicTitle, setCurrentTopicTitle] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [chatResetKey, setChatResetKey] = useState(0)
  const [selectedTopicId, setSelectedTopicId] = useState('')
  const [selectedTrack, setSelectedTrack] = useState('grammar')
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)

  const restoredRef = useRef(false)
  const saveTimerRef = useRef(null)

  const {
    hydrated,
    savedSession,
    recentSessions,
    showWelcomeBack,
    welcomeMessage,
    persistSession,
    continueSession,
    markCompleted,
    handleClearAll,
    setShowWelcomeBack,
  } = useLearningSession('lesson')

  const applySessionToUi = useCallback((session) => {
    if (!session) return
    setSessionId(session.backendSessionId ?? null)
    setMessages(session.messages || [])
    setProvider(session.provider || 'ollama')
    setCurrentTopicId(session.topicId ?? null)
    setCurrentTopicTitle(session.courseTitle || session.title || '')
    if (session.topicId) {
      setSelectedTopicId(String(session.topicId))
    }
    setChatResetKey((key) => key + 1)
  }, [])

  useEffect(() => {
    if (!hydrated || restoredRef.current) return
    if (savedSession?.messages?.length > 0) {
      applySessionToUi(savedSession)
    }
    restoredRef.current = true
  }, [hydrated, savedSession, applySessionToUi])

  useEffect(() => {
    if (!hydrated || !restoredRef.current) return
    if (messages.length === 0 && !currentTopicId && !sessionId) return

    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => {
      const topic = topics.find((t) => t.id === currentTopicId)
      persistSession({
        id: currentTopicId ? sessionIdForTopic(currentTopicId) : savedSession?.id,
        pageKey: 'lesson',
        backendSessionId: sessionId,
        track: 'grammar_coach',
        provider,
        topicId: currentTopicId,
        title: currentTopicTitle || topic?.title || '',
        courseId: courseIdFromTopic(
          topic || { id: currentTopicId, title: currentTopicTitle },
        ),
        courseTitle: currentTopicTitle || topic?.title || '',
        messages,
      })
    }, 400)

    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    }
  }, [
    hydrated,
    sessionId,
    provider,
    currentTopicId,
    currentTopicTitle,
    messages,
    topics,
    persistSession,
    savedSession?.id,
  ])

  const loadLessonData = useCallback(async () => {
    setError('')
    try {
      const [rec, topicData] = await Promise.all([
        getLessonRecommendation(),
        getLessonTopics(),
      ])
      setRecommendation(rec)
      setTopics(topicData.topics || [])
      setStages(topicData.stages || [])
      setSelectedTopicId((current) => {
        if (current) return current
        return rec?.recommended_topic?.id ? String(rec.recommended_topic.id) : ''
      })
    } catch (err) {
      setError(err.message || 'Failed to load lesson data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLessonData()
  }, [loadLessonData])

  useEffect(() => {
    if (!topicSlug || !topics.length) return
    const match = topics.find((topic) => topic.slug === topicSlug)
    if (match) {
      setSelectedTopicId(String(match.id))
      if (match.category) setSelectedTrack(match.category)
    }
  }, [topicSlug, topics])

  const stage1 = useMemo(
    () => stages.find((s) => s.slug === 'b2_toefl_80') || stages[0],
    [stages],
  )

  const stage1Topics = useMemo(
    () => (stage1?.topics || topics.filter((t) => !t.locked)).slice(0, 40),
    [stage1, topics],
  )

  const currentLessonTopic = useMemo(
    () => findCurrentLesson(stage1Topics) || recommendation?.recommended_topic,
    [stage1Topics, recommendation],
  )

  const currentModule = useMemo(
    () => findCurrentModule(stage1?.modules, stage1Topics),
    [stage1, stage1Topics],
  )

  const moduleTopics = useMemo(
    () => (currentModule ? topicsForModule(stage1Topics, currentModule) : []),
    [currentModule, stage1Topics],
  )

  const moduleStats = useMemo(() => moduleProgress(moduleTopics), [moduleTopics])

  const neighbors = useMemo(
    () => neighborLessons(stage1Topics, currentLessonTopic),
    [stage1Topics, currentLessonTopic],
  )

  const trackOptions = useMemo(() => {
    const values = [...new Set(topics.map((t) => t.category).filter(Boolean))]
    return values.length ? values : ['grammar']
  }, [topics])

  const filteredTopics = useMemo(
    () => topics.filter((t) => !selectedTrack || t.category === selectedTrack),
    [topics, selectedTrack],
  )

  const hasSavedSession =
    showWelcomeBack ||
    (savedSession?.messages?.length > 0) ||
    recentSessions.length > 0

  async function handleStartTopic(topicId, providerName = provider) {
    if (!topicId || starting) return

    setStarting(true)
    setError('')
    setSuccess('')
    setNextLessonAfterComplete(null)
    setShowCompletionGuide(false)
    setShowWelcomeBack(false)
    try {
      const topicIdNum = Number(topicId)
      const data = await startRecommendedLesson(topicIdNum, providerName)
      const topic = data.topic || topics.find((t) => t.id === topicIdNum) || recommendation?.recommended_topic
      const title = topic?.title || ''
      setCurrentTopicId(topic?.id || topicIdNum)
      setCurrentTopicTitle(title)
      setSessionId(data.session_id)
      setProvider(providerName)
      const initialMessages = [
        {
          role: 'assistant',
          content: data.reply,
          corrections: data.corrections || [],
        },
      ]
      setMessages(initialMessages)
      setChatResetKey((key) => key + 1)
      setSuccess(`Started: ${title || 'lesson'}`)
      persistSession({
        id: sessionIdForTopic(topic?.id || topicIdNum),
        backendSessionId: data.session_id,
        track: 'grammar_coach',
        provider: providerName,
        topicId: topic?.id || topicIdNum,
        title,
        courseId: courseIdFromTopic(topic || { id: topicId, title }),
        courseTitle: title,
        messages: initialMessages,
      })
      await loadLessonData()
    } catch (err) {
      setError(err.message || 'Failed to start lesson')
    } finally {
      setStarting(false)
    }
  }

  async function handleStartRecommended() {
    const topicId = recommendation?.recommended_topic?.id
    if (!topicId) return
    await handleStartTopic(topicId, provider)
  }

  async function handleQuizCompleted(data) {
    const percent = data?.score?.percent ?? 0
    const completedTopicId = currentTopicId
    const completedTopic =
      topics.find((t) => t.id === completedTopicId) ||
      (completedTopicId
        ? { id: completedTopicId, title: currentTopicTitle, order: 0, locked: false }
        : null)

    if (data?.progress?.status === 'completed') {
      setSuccess(`Lesson completed with quiz score ${percent}%.`)
      if (completedTopicId) {
        persistSession({
          id: sessionIdForTopic(completedTopicId),
          topicId: completedTopicId,
          title: currentTopicTitle,
          courseId: courseIdFromTopic(completedTopic || { id: completedTopicId, title: currentTopicTitle }),
          progress: {
            ...(savedSession?.progress || {}),
            status: 'completed',
          },
        })
      } else {
        markCompleted()
      }
      clearCurrentSession()
      const next = completedTopic
        ? nextUnlockedLesson(stage1Topics, completedTopic)
        : null
      setNextLessonAfterComplete(next)
      setShowCompletionGuide(true)
      setCurrentTopicId(null)
      setCurrentTopicTitle('')
      setSessionId(null)
      setMessages([])
      setChatResetKey((key) => key + 1)
      await loadLessonData()
    } else {
      setSuccess('')
      setError(`Quiz score ${percent}% — review the lesson and try again (70% needed).`)
    }
  }

  async function handleStartNextLesson() {
    const next = nextLessonAfterComplete
    if (!next?.id) return
    setNextLessonAfterComplete(null)
    setShowCompletionGuide(false)
    await handleStartTopic(String(next.id), provider)
  }

  function handleContinuePrevious() {
    applySessionToUi(continueSession())
    setSuccess('Restored your previous session.')
  }

  function handleClearAllSessions() {
    handleClearAll()
    setSessionId(null)
    setMessages([])
    setCurrentTopicId(null)
    setCurrentTopicTitle('')
    setChatResetKey((key) => key + 1)
    setSuccess('All saved sessions cleared.')
  }

  if (loading) {
    return (
      <div className="page lesson-page lesson-compact">
        <p className="muted">Loading lesson…</p>
      </div>
    )
  }

  const recommended = recommendation?.recommended_topic
  const objectives = learningObjectives(recommended)
  const lastStudied = savedSession?.lastUpdatedAt
    ? formatLastActivity(savedSession.lastUpdatedAt)
    : recentSessions[0]?.lastUpdatedAt
      ? formatLastActivity(recentSessions[0].lastUpdatedAt)
      : 'Not yet'

  return (
    <div className="page lesson-page lesson-compact">
      <header className="lesson-header-compact">
        <h1>Lesson</h1>
      </header>

      {error && <p className="error">{error}</p>}
      {success && <p className="success-msg">{success}</p>}

      {showCompletionGuide && (
        <section className="card lesson-next-card">
          <p className="dashboard-focus-kicker">Lesson complete</p>
          <h2 className="lesson-section-title">Continue your path</h2>
          {nextLessonAfterComplete ? (
            <>
              <p className="muted">
                Great work finishing this topic. Your next lesson is ready.
              </p>
              <p className="lesson-next-title">
                <strong>{nextLessonAfterComplete.title}</strong>
              </p>
              <div className="lesson-next-actions">
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={handleStartNextLesson}
                  disabled={starting}
                >
                  {starting ? 'Starting…' : 'Start next lesson'}
                </button>
                <Link
                  to={`/lesson?topic=${nextLessonAfterComplete.slug}`}
                  className="btn btn-sm btn-secondary"
                >
                  View topic
                </Link>
                <Link to="/roadmap" className="btn btn-sm btn-secondary">
                  Open roadmap
                </Link>
              </div>
            </>
          ) : (
            <>
              <p className="muted">
                You finished this topic. No further unlocked lessons in this stage — check the roadmap or Today for your next focus.
              </p>
              <div className="lesson-next-actions">
                <Link to="/today" className="btn btn-sm">
                  Go to Today
                </Link>
                <Link to="/roadmap" className="btn btn-sm btn-secondary">
                  Open roadmap
                </Link>
              </div>
            </>
          )}
        </section>
      )}

      {hasSavedSession && !showCompletionGuide && (
        <section className="lesson-session-row card card-compact">
          <div className="lesson-session-meta">
            <span><strong>Track:</strong> Grammar coach</span>
            <span><strong>Current:</strong> {currentTopicTitle || recommended?.title || '—'}</span>
            <span><strong>Last studied:</strong> {lastStudied}</span>
          </div>
          <div className="lesson-session-actions">
            {showWelcomeBack && welcomeMessage && (
              <button type="button" className="btn btn-sm" onClick={handleContinuePrevious}>
                Continue session
              </button>
            )}
            <button type="button" className="btn btn-sm btn-secondary" onClick={handleClearAllSessions}>
              Clear saved sessions
            </button>
          </div>
        </section>
      )}

      <section className="card lesson-recommendation lesson-recommendation-main">
        <p className="dashboard-focus-kicker">Today&apos;s recommended lesson</p>
        {recommended ? (
          <>
            <h2 className="lesson-topic-title">{recommended.title}</h2>
            <p className="lesson-why-today">
              <span className="label">Why today</span> {recommendation.reason}
            </p>
            {recommendation.review_items?.length > 0 ? (
              <div className="lesson-review-items lesson-review-compact">
                <span className="label">Yesterday review mistakes</span>
                <ul>
                  {recommendation.review_items.slice(0, 3).map((item, index) => (
                    <li key={index}>
                      {item.wrong_text} → {item.correct_text}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="muted lesson-review-compact">
                {recommendation.yesterday_summary || 'No grammar mistakes to review from yesterday.'}
              </p>
            )}
            <div className="lesson-objectives">
              <span className="label">Learning objectives</span>
              <ul>
                {objectives.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <button
              type="button"
              className="btn btn-sm"
              onClick={handleStartRecommended}
              disabled={starting}
            >
              {starting ? 'Starting…' : 'Start recommended lesson'}
            </button>
          </>
        ) : (
          <p className="muted">{recommendation?.reason || 'No lesson recommendation available.'}</p>
        )}
      </section>

      {currentModule && (
        <section className="card lesson-module-progress">
          <h2 className="lesson-section-title">Current module progress</h2>
          <p className="muted">{currentModule.title}</p>
          <ProgressBar
            label="Module progress"
            valueLabel={`${moduleStats.done}/${moduleStats.total}`}
            percent={moduleStats.percent}
            size="sm"
          />
          <dl className="lesson-neighbor-lessons">
            <div>
              <dt>Previous</dt>
              <dd>
                {neighbors.previous ? (
                  <Link to={`/lesson?topic=${neighbors.previous.slug}`}>{neighbors.previous.title}</Link>
                ) : (
                  <span className="muted">—</span>
                )}
              </dd>
            </div>
            <div>
              <dt>Current</dt>
              <dd>{neighbors.current?.title || recommended?.title || '—'}</dd>
            </div>
            <div>
              <dt>Next</dt>
              <dd>
                {neighbors.next ? (
                  <Link to={`/lesson?topic=${neighbors.next.slug}`}>{neighbors.next.title}</Link>
                ) : (
                  <span className="muted">—</span>
                )}
              </dd>
            </div>
          </dl>
          <Link to="/roadmap" className="btn btn-sm btn-secondary">
            View full roadmap
          </Link>
        </section>
      )}

      <section className="card lesson-choose-topic lesson-choose-compact">
        <h2 className="lesson-section-title">Choose topic</h2>
        <div className="lesson-choose-row">
          <label className="form-field">
            Topic
            <select
              value={selectedTopicId}
              onChange={(event) => setSelectedTopicId(event.target.value)}
            >
              <option value="">Select a topic…</option>
              {filteredTopics.map((topic) => (
                <option key={topic.id} value={topic.id} disabled={topic.locked}>
                  {topic.locked ? `${topic.title} (locked)` : topic.title}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Track
            <select
              value={selectedTrack}
              onChange={(event) => {
                setSelectedTrack(event.target.value)
                setSelectedTopicId('')
              }}
            >
              {trackOptions.map((track) => (
                <option key={track} value={track}>{track}</option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => handleStartTopic(selectedTopicId, provider)}
            disabled={!selectedTopicId || starting}
          >
            Start selected topic
          </button>
        </div>
      </section>

      <section className="card lesson-workspace">
        {currentTopicId && (
          <div className="lesson-active-inline">
            <p>
              Active: <strong>{currentTopicTitle}</strong>
            </p>
          </div>
        )}
        <Chat
          key={chatResetKey}
          sessionId={sessionId}
          onSessionIdChange={setSessionId}
          messages={messages}
          onMessagesChange={setMessages}
          lockTrack="grammar_coach"
          provider={provider}
          onProviderChange={setProvider}
        />
      </section>

      <LessonQuizPanel
        topicId={currentTopicId}
        topicTitle={currentTopicTitle}
        onCompleted={handleQuizCompleted}
      />
    </div>
  )
}
