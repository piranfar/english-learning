import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  completeLesson,
  getLessonRecommendation,
  getLessonTopics,
  startRecommendedLesson,
} from '../api/client'
import Chat from '../components/Chat'
import ProgressBar from '../components/ProgressBar'
import { useLearningSession } from '../hooks/useLearningSession'
import { courseIdFromTopic } from '../utils/courseProgress'
import { DEFAULT_AI_PROVIDER } from '../utils/defaultProvider'
import {
  findCurrentModule,
  moduleProgress,
  neighborLessons,
  topicsForModule,
} from '../utils/roadmapModules'
import { findCurrentLesson } from '../utils/roadmapStatus'
import { formatLastActivity } from '../services/learningSessionStorage'

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
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [currentTopicId, setCurrentTopicId] = useState(null)
  const [currentTopicTitle, setCurrentTopicTitle] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [chatResetKey, setChatResetKey] = useState(0)
  const [selectedTopicId, setSelectedTopicId] = useState('')
  const [selectedTrack, setSelectedTrack] = useState('grammar')
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)

  const restoredRef = useRef(false)

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

    const topic = topics.find((t) => t.id === currentTopicId)
    persistSession({
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
  }, [
    hydrated,
    sessionId,
    provider,
    currentTopicId,
    currentTopicTitle,
    messages,
    topics,
    persistSession,
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
    setShowWelcomeBack(false)
    try {
      const data = await startRecommendedLesson(Number(topicId), providerName)
      const topic = data.topic || recommendation?.recommended_topic
      const title = topic?.title || ''
      setCurrentTopicId(topic?.id || Number(topicId))
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
        id: savedSession?.id,
        backendSessionId: data.session_id,
        track: 'grammar_coach',
        provider: providerName,
        topicId: topic?.id || Number(topicId),
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

  async function handleCompleteLesson(score = 80) {
    if (!currentTopicId || completing) return

    setCompleting(true)
    setError('')
    setSuccess('')
    try {
      await completeLesson(currentTopicId, score, '')
      setSuccess(`Lesson marked complete (score ${score}).`)
      markCompleted()
      setCurrentTopicId(null)
      setCurrentTopicTitle('')
      await loadLessonData()
    } catch (err) {
      setError(err.message || 'Failed to complete lesson')
    } finally {
      setCompleting(false)
    }
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
  const lastStudied = savedSession?.updatedAt
    ? formatLastActivity(savedSession.updatedAt)
    : recentSessions[0]?.updatedAt
      ? formatLastActivity(recentSessions[0].updatedAt)
      : 'Not yet'

  return (
    <div className="page lesson-page lesson-compact">
      <header className="lesson-header-compact">
        <h1>Lesson</h1>
      </header>

      {error && <p className="error">{error}</p>}
      {success && <p className="success-msg">{success}</p>}

      {hasSavedSession && (
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
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => handleCompleteLesson(80)}
              disabled={completing}
            >
              {completing ? 'Saving…' : 'Complete lesson'}
            </button>
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
    </div>
  )
}
