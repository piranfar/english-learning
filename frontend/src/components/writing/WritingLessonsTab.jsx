import { useCallback, useEffect, useMemo, useState } from 'react'
import { sendChatMessage } from '../../api/client'
import { WRITING_LESSONS, getLessonById } from '../../data/writingLessons'
import { buildLessonPracticeMessage } from '../../data/writingTools'
import {
  getNextIncompleteLessonId,
  loadLessonsProgress,
  markLessonComplete,
  saveLessonAttempt,
  setCurrentLesson,
} from '../../services/writingLessonsProgress'
import { parseMarkdownSections } from '../../utils/writingToolsParser'
import AssistantMessage from '../AssistantMessage'
import ExamTextArea from '../ExamTextArea'
import WritingToolProvider from './WritingToolProvider'

const FEEDBACK_SECTIONS = ['Corrected version', 'Why', 'Pattern']

export default function WritingLessonsTab({ provider, onProviderChange, prompts }) {
  const [progress, setProgress] = useState(() => loadLessonsProgress())
  const [selectedId, setSelectedId] = useState(
    () => loadLessonsProgress().currentLessonId || WRITING_LESSONS[0].id,
  )
  const [practiceInput, setPracticeInput] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [examplesOpen, setExamplesOpen] = useState(true)

  const lesson = useMemo(() => getLessonById(selectedId), [selectedId])
  const completedCount = progress.completedLessonIds.length
  const totalCount = WRITING_LESSONS.length

  useEffect(() => {
    const savedProgress = loadLessonsProgress()
    const saved = savedProgress.lastFeedback[selectedId]
    if (saved) {
      setFeedback(saved)
      setPracticeInput(saved.input || '')
    } else {
      setFeedback(null)
      setPracticeInput(lesson?.miniPractice?.starter || '')
    }
  }, [selectedId, lesson])

  const selectLesson = useCallback(
    (lessonId) => {
      setSelectedId(lessonId)
      setError('')
      const next = setCurrentLesson(lessonId)
      setProgress(next)
    },
    [],
  )

  function handleContinue() {
    const nextId = getNextIncompleteLessonId(WRITING_LESSONS, progress)
    if (nextId) selectLesson(nextId)
  }

  async function handleSubmitPractice(event) {
    event.preventDefault()
    if (!lesson || !practiceInput.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const data = await sendChatMessage({
        message: buildLessonPracticeMessage({ lesson, attempt: practiceInput, level: 'B1' }),
        track: 'writing_lesson_coach',
        provider,
      })

      const sections = parseMarkdownSections(data.reply, FEEDBACK_SECTIONS)
      const result = {
        input: practiceInput,
        feedback: data.reply,
        corrected: sections['Corrected version'],
        why: sections.Why,
        pattern: sections.Pattern,
      }

      setFeedback(result)
      const next = saveLessonAttempt(lesson.id, result)
      setProgress(next)
    } catch (err) {
      setError(err.message || 'Practice feedback failed')
    } finally {
      setLoading(false)
    }
  }

  function handleMarkComplete() {
    if (!lesson) return
    const next = markLessonComplete(lesson.id)
    setProgress(next)
  }

  if (!lesson) return null

  const isComplete = progress.completedLessonIds.includes(lesson.id)

  return (
    <div className="writing-lessons-tab">
      <WritingToolProvider
        provider={provider}
        prompts={prompts}
        track="writing_lesson_coach"
        onChange={onProviderChange}
      />

      <div className="writing-lessons-progress card card-compact">
        <p>
          Completed lessons: <strong>{completedCount} / {totalCount}</strong>
        </p>
        {completedCount < totalCount && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleContinue}>
            Continue where you left off
          </button>
        )}
      </div>

      <div className="writing-lessons-layout">
        <aside className="writing-lessons-sidebar card">
          <h2 className="writing-lessons-sidebar-title">Lessons</h2>
          <ul className="writing-lessons-list">
            {WRITING_LESSONS.map((item) => {
              const done = progress.completedLessonIds.includes(item.id)
              const active = item.id === selectedId
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`writing-lesson-link${active ? ' writing-lesson-link--active' : ''}`}
                    onClick={() => selectLesson(item.id)}
                  >
                    <span className="writing-lesson-num">{item.number}</span>
                    <span className="writing-lesson-link-text">{item.title}</span>
                    {done && <span className="writing-lesson-done" aria-label="Completed">✓</span>}
                  </button>
                </li>
              )
            })}
          </ul>
        </aside>

        <main className="writing-lessons-main">
          <section className="card writing-lesson-card">
            <p className="writing-lesson-meta muted">Lesson {lesson.number} of {totalCount}</p>
            <h2>{lesson.title}</h2>
            <p className="writing-lesson-goal">
              <span className="label">Skill goal</span> {lesson.skillGoal}
            </p>

            <div className="writing-lesson-section">
              <h3>Explanation</h3>
              <AssistantMessage content={lesson.explanation} />
            </div>

            <div className="writing-lesson-section">
              <h3>Formula / pattern</h3>
              <p className="writing-lesson-pattern">{lesson.pattern}</p>
            </div>

            {lesson.sentenceStarters?.length > 0 && (
              <div className="writing-lesson-section">
                <h3>Sentence starters</h3>
                <ul>
                  {lesson.sentenceStarters.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {lesson.connectors?.length > 0 && (
              <div className="writing-lesson-section">
                <h3>Connectors</h3>
                {lesson.connectors.map((c) => (
                  <article key={c.word} className="writing-connector-card">
                    <p><strong>{c.word}</strong> — {c.meaning}</p>
                    <p className="muted">Example: {c.example}</p>
                    <p className="muted">Common mistake: {c.mistake}</p>
                  </article>
                ))}
              </div>
            )}

            <div className="writing-lesson-section">
              <button
                type="button"
                className="writing-plan-toggle"
                onClick={() => setExamplesOpen((open) => !open)}
                aria-expanded={examplesOpen}
              >
                Examples {examplesOpen ? '▾' : '▸'}
              </button>
              {examplesOpen && (
                <div className="writing-lesson-examples">
                  {lesson.examples.map((ex) => (
                    <div key={`${ex.label}-${ex.text}`} className="writing-example-row">
                      <span className="label">{ex.label}</span>
                      <p>{ex.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <form onSubmit={handleSubmitPractice} className="writing-lesson-practice">
              <h3>Mini practice</h3>
              <p className="muted">{lesson.miniPractice.prompt}</p>
              <label className="form-field">
                Your answer
                <ExamTextArea
                  value={practiceInput}
                  onChange={(e) => setPracticeInput(e.target.value)}
                  rows={4}
                  disabled={loading}
                  examMode
                />
              </label>
              <button type="submit" className="btn" disabled={loading || !practiceInput.trim()}>
                {loading ? 'Checking...' : 'Submit practice'}
              </button>
            </form>

            {error && <p className="error">{error}</p>}

            {feedback?.corrected && (
              <section className="writing-lesson-feedback card">
                <h3>AI feedback</h3>
                {feedback.corrected && (
                  <div className="writing-tool-block">
                    <span className="label">Corrected</span>
                    <p>{feedback.corrected}</p>
                  </div>
                )}
                {feedback.why && (
                  <div className="writing-tool-block">
                    <span className="label">Why</span>
                    <AssistantMessage content={feedback.why} />
                  </div>
                )}
                {feedback.pattern && (
                  <div className="writing-tool-block">
                    <span className="label">Pattern</span>
                    <p>{feedback.pattern}</p>
                  </div>
                )}
              </section>
            )}

            <div className="writing-lesson-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleMarkComplete}
                disabled={isComplete}
              >
                {isComplete ? 'Lesson completed ✓' : 'Mark lesson complete'}
              </button>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}
