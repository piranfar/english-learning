import { useEffect, useMemo, useState } from 'react'
import { apiRequest } from '../api/client'
import { saveReadingAttempt } from '../services/readingStorage'
import ReadingResultsPanel from './ReadingResultsPanel'

const OPTION_LABELS = ['A', 'B', 'C', 'D']

function formatElapsed(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
}

export default function ReadingWorkspace({
  session,
  loading,
  setLoading,
  setError,
  onReset,
  onProgressSaved,
}) {
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    setAnswers({})
    setSubmitted(false)
    setResult(null)
    setElapsed(0)
  }, [session?.session_id])

  useEffect(() => {
    if (!session || submitted) return undefined
    const timer = window.setInterval(() => setElapsed((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [session, submitted])

  const answeredCount = useMemo(
    () => session?.questions?.filter((question) => answers[question.id] !== undefined).length || 0,
    [session, answers],
  )

  const allAnswered = session?.questions?.every((question) => answers[question.id] !== undefined)

  async function handleSubmit(event) {
    event.preventDefault()
    if (!session || loading) return

    setLoading(true)
    setError('')

    try {
      const data = await apiRequest('/reading/submit/', {
        method: 'POST',
        json: {
          session_id: session.session_id,
          answers,
        },
      })
      setResult(data)
      setSubmitted(true)
      saveReadingAttempt({
        session_id: session.session_id,
        score_percent: data.score?.percent,
        skill_scores: data.skill_scores,
        reading_mode: session.reading_mode,
      })
      onProgressSaved?.()
    } catch (err) {
      setError(err.message || 'Failed to submit answers')
    } finally {
      setLoading(false)
    }
  }

  function handleAnswerChange(questionId, optionIndex) {
    if (submitted) return
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  if (!session) return null

  return (
    <div className="reading-workspace">
      {session.disclaimer && (
        <p className="muted reading-disclaimer">{session.disclaimer}</p>
      )}

      <div className="reading-workspace-meta">
        <span>Timer: {formatElapsed(elapsed)}</span>
        <span>
          Progress: {answeredCount}/{session.questions.length} answered
        </span>
        <span>~{session.estimated_time_minutes} min read</span>
      </div>

      <div className="reading-workspace-grid">
        <section className="card reading-passage-card">
          <h2>{session.title}</h2>
          <p className="muted reading-passage-meta">
            {session.level} · {session.topic}
            {session.lesson_focus && session.lesson_focus !== 'none' && (
              <> · {session.lesson_focus.replaceAll('_', ' ')}</>
            )}
          </p>
          <div className="reading-passage-text">{session.passage}</div>

          {session.target_vocabulary?.length > 0 && (
            <div className="reading-vocab-highlights">
              <h3>Vocabulary highlights</h3>
              <ul className="reading-vocab-list">
                {session.target_vocabulary.map((entry) => (
                  <li key={entry.word}>
                    <strong>{entry.word}</strong> — {entry.definition}
                    {entry.example && <p className="muted">{entry.example}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <form onSubmit={handleSubmit} className="reading-questions-panel card">
          <h3>Questions</h3>
          <ol className="reading-quiz-list">
            {session.questions.map((question, index) => {
              const questionResult = result?.results?.find((row) => row.id === question.id)
              return (
                <li key={question.id} className="reading-quiz-question">
                  <p>
                    <strong>{index + 1}. {question.question}</strong>
                    {question.type && (
                      <span className="muted reading-question-type">
                        {' '}({question.type.replaceAll('_', ' ')})
                      </span>
                    )}
                  </p>
                  <div className="reading-quiz-options">
                    {question.choices.map((option, optionIndex) => {
                      const selected = answers[question.id] === optionIndex
                      const isCorrect = questionResult?.correct_answer === option
                      const isWrongSelection = submitted && selected && !questionResult?.is_correct
                      return (
                        <label
                          key={`${question.id}-${optionIndex}`}
                          className={`reading-quiz-option${
                            submitted && isCorrect ? ' reading-quiz-option-correct' : ''
                          }${isWrongSelection ? ' reading-quiz-option-wrong' : ''}`}
                        >
                          <input
                            type="radio"
                            name={question.id}
                            checked={selected}
                            onChange={() => handleAnswerChange(question.id, optionIndex)}
                            disabled={submitted}
                          />
                          <span>{OPTION_LABELS[optionIndex]}. {option}</span>
                        </label>
                      )
                    })}
                  </div>
                  {submitted && (
                    <p className="reading-quiz-explanation">
                      {questionResult?.is_correct ? (
                        <span className="reading-correct-label">Correct.</span>
                      ) : (
                        <>
                          <strong>Correct answer:</strong> {questionResult?.correct_answer}
                          {' — '}
                          {questionResult?.explanation}
                        </>
                      )}
                    </p>
                  )}
                </li>
              )
            })}
          </ol>

          {!submitted ? (
            <button type="submit" disabled={loading || !allAnswered}>
              {loading ? 'Submitting…' : 'Submit answers'}
            </button>
          ) : (
            <ReadingResultsPanel
              result={result}
              onRetry={() => {
                setAnswers({})
                setSubmitted(false)
                setResult(null)
                setElapsed(0)
              }}
              onGenerateNew={onReset}
            />
          )}
        </form>
      </div>
    </div>
  )
}
