import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ReadingWorkspace from './ReadingWorkspace'
import { apiRequest } from '../api/client'

const LEVELS = ['A2', 'B1', 'B2', 'C1 Academic']
const STAGES = [
  { value: 'b2_toefl_80', label: 'B2 / TOEFL 80+ readiness' },
  { value: 'academic_toefl_100', label: 'TOEFL 100+ readiness' },
]
const TOPICS = [
  'Academic',
  'Science',
  'Health',
  'University Life',
  'Technology',
  'Society',
  'Random',
]
const LESSON_FOCUSES = [
  { value: 'current_lesson', label: 'Current lesson' },
  { value: 'articles', label: 'Articles' },
  { value: 'prepositions', label: 'Prepositions' },
  { value: 'passive_voice', label: 'Passive voice' },
  { value: 'present_perfect', label: 'Present perfect' },
  { value: 'academic_linking_words', label: 'Linking words' },
  { value: 'academic_sentence_structure', label: 'Sentence structure' },
  { value: 'vocabulary_in_context', label: 'Vocabulary in context' },
  { value: 'none', label: 'No focus' },
]
const QUESTION_FOCUSES = [
  { value: 'mixed', label: 'Mixed' },
  { value: 'main_idea', label: 'Main idea' },
  { value: 'detail', label: 'Detail' },
  { value: 'inference', label: 'Inference' },
  { value: 'vocabulary_in_context', label: 'Vocabulary' },
  { value: 'sentence_function', label: 'Sentence meaning' },
  { value: 'rhetorical_purpose', label: 'Rhetorical purpose' },
]
const LENGTHS = [
  { value: 'short', label: 'Short' },
  { value: 'medium', label: 'Medium' },
  { value: 'long', label: 'Long' },
]
const READING_MODES = [
  { value: 'general', label: 'General' },
  { value: 'toefl_2026', label: 'TOEFL 2026' },
  { value: 'classic_toefl', label: 'Classic TOEFL academic' },
]
const TOEFL_2026_TASKS = [
  { value: 'complete_the_words', label: 'Complete the Words' },
  { value: 'daily_life_reading', label: 'Read in Daily Life' },
  { value: 'academic_passage', label: 'Read an Academic Passage' },
]

export default function ReadingGenerateTab({
  provider,
  loading,
  setLoading,
  setError,
  onSessionChange,
  onProgressSaved,
  defaultReadingMode = 'general',
  tabVariant = 'generate',
}) {
  const [searchParams] = useSearchParams()
  const [level, setLevel] = useState('B1')
  const [stage, setStage] = useState('b2_toefl_80')
  const [topic, setTopic] = useState('Academic')
  const [lessonFocus, setLessonFocus] = useState('current_lesson')
  const [questionFocus, setQuestionFocus] = useState('mixed')
  const [length, setLength] = useState('medium')
  const [readingMode, setReadingMode] = useState(defaultReadingMode)
  const [simulationType, setSimulationType] = useState('academic_passage')
  const [session, setSession] = useState(null)
  const [contextNote, setContextNote] = useState('')

  useEffect(() => {
    async function loadContext() {
      try {
        const data = await apiRequest('/reading/context/')
        const context = data.context || {}
        if (context.stage) setStage(context.stage)
        if (context.current_lesson_title) {
          setContextNote(context.current_lesson_title)
        }
      } catch {
        // keep defaults
      }
    }
    loadContext()
  }, [])

  useEffect(() => {
    const paramFocus = searchParams.get('lesson_focus')
    const paramQuestion = searchParams.get('question_focus')
    const paramLength = searchParams.get('length')
    if (paramFocus) setLessonFocus(paramFocus)
    if (paramQuestion) setQuestionFocus(paramQuestion)
    if (paramLength) setLength(paramLength)
  }, [searchParams])

  useEffect(() => {
    onSessionChange?.(session, { level, readingMode, contextNote })
  }, [session, level, readingMode, contextNote, onSessionChange])

  async function handleGenerate(event) {
    event.preventDefault()
    if (loading) return

    setLoading(true)
    setError('')
    setSession(null)

    try {
      const payload = {
        level,
        stage,
        topic,
        lesson_focus: lessonFocus,
        question_focus: questionFocus,
        length: readingMode === 'classic_toefl' ? 'toefl_style' : length,
        reading_mode: readingMode,
      }
      if (readingMode === 'toefl_2026') {
        payload.simulation_type = simulationType
      }
      if (provider) {
        payload.provider = provider
      }

      const data = await apiRequest('/reading/generate/', {
        method: 'POST',
        json: payload,
      })
      setSession(data.session)
    } catch (err) {
      setError(err.message || 'Failed to generate reading practice')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !session) {
    return (
      <div className="reading-loading card">
        <p>Generating original reading practice…</p>
      </div>
    )
  }

  if (session) {
    return (
      <ReadingWorkspace
        session={session}
        loading={loading}
        setLoading={setLoading}
        setError={setError}
        onReset={() => setSession(null)}
        onProgressSaved={onProgressSaved}
      />
    )
  }

  return (
    <div className="reading-generate-panel">
      <p className="muted reading-helper">
        {tabVariant === 'simulation'
          ? 'TOEFL 2026 simulation — original practice passages, not official ETS content.'
          : 'Set your filters, generate an original passage, then answer questions and review your score.'}
      </p>

      <form onSubmit={handleGenerate} className="reading-filter-row card card-compact">
        {contextNote && (
          <p className="muted reading-context-note">Current lesson: {contextNote}</p>
        )}

        <div className="reading-filter-grid">
          <label className="form-field">
            Level
            <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={loading}>
              {LEVELS.map((entry) => (
                <option key={entry} value={entry}>{entry}</option>
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
            Topic
            <select value={topic} onChange={(e) => setTopic(e.target.value)} disabled={loading}>
              {TOPICS.map((entry) => (
                <option key={entry} value={entry}>{entry}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            Lesson focus
            <select value={lessonFocus} onChange={(e) => setLessonFocus(e.target.value)} disabled={loading}>
              {LESSON_FOCUSES.map((entry) => (
                <option key={entry.value} value={entry.value}>{entry.label}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            Question focus
            <select value={questionFocus} onChange={(e) => setQuestionFocus(e.target.value)} disabled={loading}>
              {QUESTION_FOCUSES.map((entry) => (
                <option key={entry.value} value={entry.value}>{entry.label}</option>
              ))}
            </select>
          </label>

          {readingMode !== 'classic_toefl' && (
            <label className="form-field">
              Length
              <select value={length} onChange={(e) => setLength(e.target.value)} disabled={loading}>
                {LENGTHS.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          )}

          <label className="form-field">
            Mode
            <select
              value={readingMode}
              onChange={(e) => setReadingMode(e.target.value)}
              disabled={loading || tabVariant === 'simulation'}
            >
              {READING_MODES.map((entry) => (
                <option key={entry.value} value={entry.value}>{entry.label}</option>
              ))}
            </select>
          </label>

          {readingMode === 'toefl_2026' && (
            <label className="form-field">
              TOEFL 2026 task
              <select value={simulationType} onChange={(e) => setSimulationType(e.target.value)} disabled={loading}>
                {TOEFL_2026_TASKS.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          )}
        </div>

        <button type="submit" disabled={loading}>
          Generate reading practice
        </button>
      </form>
    </div>
  )
}
