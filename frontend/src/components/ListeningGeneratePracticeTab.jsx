import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ListeningSessionPanel from './ListeningSessionPanel'
import { apiRequest } from '../api/client'

const LEVELS = [
  { value: 'A2', label: 'A2' },
  { value: 'B1', label: 'B1' },
  { value: 'B2', label: 'B2' },
  { value: 'C1 Academic', label: 'C1 Academic' },
]

const STAGES = [
  { value: 'b2_toefl_80', label: 'B2 Academic English / TOEFL 80+ Readiness' },
  { value: 'academic_toefl_100', label: 'Full Academic English / TOEFL 100+ Readiness' },
]

const LISTENING_TYPES = [
  { value: 'academic_mini_lecture', label: 'Academic mini-lecture' },
  { value: 'campus_conversation', label: 'Campus conversation' },
  { value: 'daily_academic_life', label: 'Daily academic life' },
  { value: 'toefl_style_lecture', label: 'TOEFL-style lecture' },
  { value: 'toefl_style_conversation', label: 'TOEFL-style conversation' },
]

const TOPICS = [
  'Science',
  'Health',
  'University Life',
  'Technology',
  'Society',
  'Academic Skills',
  'Random',
]

const LESSON_FOCUSES = [
  { value: 'current_lesson', label: 'Current lesson (default)' },
  { value: 'articles', label: 'Articles' },
  { value: 'prepositions', label: 'Prepositions' },
  { value: 'passive_voice', label: 'Passive voice' },
  { value: 'present_perfect', label: 'Present perfect' },
  { value: 'academic_linking_words', label: 'Academic linking words' },
  { value: 'academic_vocabulary', label: 'Academic vocabulary' },
  { value: 'none', label: 'No specific focus' },
]

const LENGTHS = [
  { value: 'short', label: 'Short' },
  { value: 'medium', label: 'Medium' },
  { value: 'toefl_style', label: 'TOEFL-style' },
]

const SPEEDS = [
  { value: 'slow', label: 'Slow' },
  { value: 'normal', label: 'Normal' },
  { value: 'toefl_like', label: 'TOEFL-like' },
]

export default function ListeningGeneratePracticeTab({ provider, loading, setLoading, setError }) {
  const [searchParams] = useSearchParams()
  const [level, setLevel] = useState('B1')
  const [stage, setStage] = useState('b2_toefl_80')
  const [listeningType, setListeningType] = useState('academic_mini_lecture')
  const [topic, setTopic] = useState('Random')
  const [lessonFocus, setLessonFocus] = useState('current_lesson')
  const [length, setLength] = useState('medium')
  const [speed, setSpeed] = useState('normal')
  const [session, setSession] = useState(null)
  const [contextNote, setContextNote] = useState('')

  useEffect(() => {
    async function loadContext() {
      try {
        const data = await apiRequest('/listening/practice/context/')
        const context = data.context || {}
        if (context.stage) setStage(context.stage)
        if (context.current_lesson_title) {
          setContextNote(`Current lesson: ${context.current_lesson_title}`)
        }
      } catch {
        // keep defaults
      }
    }
    loadContext()
  }, [])

  useEffect(() => {
    const paramType = searchParams.get('listening_type')
    const paramTopic = searchParams.get('topic')
    const paramFocus = searchParams.get('lesson_focus')
    const paramLength = searchParams.get('length')
    if (paramType) setListeningType(paramType)
    if (paramTopic) setTopic(paramTopic)
    if (paramFocus) setLessonFocus(paramFocus)
    if (paramLength) setLength(paramLength)
  }, [searchParams])

  async function handleGenerate(event) {
    event.preventDefault()
    if (loading) return

    setLoading(true)
    setError('')
    setSession(null)

    try {
      const data = await apiRequest('/listening/generate-practice/', {
        method: 'POST',
        json: {
          level,
          stage,
          listening_type: listeningType,
          topic,
          lesson_focus: lessonFocus,
          length,
          speed,
          provider,
        },
      })
      setSession(data.session)
    } catch (err) {
      setError(err.message || 'Failed to generate listening practice')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="listening-generate-panel">
      {!session ? (
        <form onSubmit={handleGenerate} className="reading-quiz-controls card card-compact">
          <p className="muted">
            Choose what to listen to. We&apos;ll generate an original transcript, read it aloud with
            your browser, and quiz you on it once you&apos;re ready.
          </p>
          {contextNote && <p className="muted">{contextNote}</p>}

          <div className="form-row">
            <label className="form-field">
              Level
              <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={loading}>
                {LEVELS.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Stage
              <select value={stage} onChange={(e) => setStage(e.target.value)} disabled={loading}>
                {STAGES.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Listening type
              <select
                value={listeningType}
                onChange={(e) => setListeningType(e.target.value)}
                disabled={loading}
              >
                {LISTENING_TYPES.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-row">
            <label className="form-field">
              Topic
              <select value={topic} onChange={(e) => setTopic(e.target.value)} disabled={loading}>
                {TOPICS.map((entry) => (
                  <option key={entry} value={entry}>{entry}</option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Lesson focus
              <select
                value={lessonFocus}
                onChange={(e) => setLessonFocus(e.target.value)}
                disabled={loading}
              >
                {LESSON_FOCUSES.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-row">
            <label className="form-field">
              Length
              <select value={length} onChange={(e) => setLength(e.target.value)} disabled={loading}>
                {LENGTHS.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Speed
              <select value={speed} onChange={(e) => setSpeed(e.target.value)} disabled={loading}>
                {SPEEDS.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Generating listening practice…' : 'Generate listening practice'}
          </button>
        </form>
      ) : (
        <ListeningSessionPanel
          session={session}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
          onReset={() => setSession(null)}
        />
      )}
    </div>
  )
}
