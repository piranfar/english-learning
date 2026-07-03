import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLessonQuiz, submitLessonQuiz } from '../api/client'

const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function LessonQuizPanel({ topicId, topicTitle, onCompleted }) {
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (!topicId) {
      setQuiz(null)
      setAnswers({})
      setResult(null)
      setError('')
      return
    }

    let cancelled = false

    async function loadQuiz() {
      setLoading(true)
      setError('')
      setResult(null)
      setAnswers({})
      try {
        const data = await getLessonQuiz(topicId)
        if (!cancelled) {
          setQuiz(data.quiz)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load lesson quiz')
          setQuiz(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadQuiz()
    return () => {
      cancelled = true
    }
  }, [topicId])

  const allAnswered = quiz?.questions?.every((question) => answers[question.id] !== undefined)

  function handleAnswerChange(questionId, optionIndex) {
    if (result) return
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!topicId || !allAnswered || submitting) return

    setSubmitting(true)
    setError('')
    try {
      const data = await submitLessonQuiz(topicId, answers)
      setResult(data)
      onCompleted?.(data)
    } catch (err) {
      setError(err.message || 'Failed to submit lesson quiz')
    } finally {
      setSubmitting(false)
    }
  }

  if (!topicId) {
    return (
      <section className="card lesson-quiz-card">
        <h2 className="lesson-section-title">Lesson quiz</h2>
        <p className="muted">Start a lesson to unlock the end-of-lesson quiz.</p>
      </section>
    )
  }

  return (
    <section className="card lesson-quiz-card">
      <div className="lesson-quiz-header">
        <div>
          <h2 className="lesson-section-title">Lesson quiz</h2>
          <p className="muted lesson-quiz-lead">
            Answer all four questions to complete {topicTitle || 'this lesson'}. Your score
            determines lesson completion.
          </p>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Loading quiz…</p>}

      {!loading && quiz && !result && (
        <form onSubmit={handleSubmit} className="lesson-quiz-form">
          {quiz.questions.map((question, index) => (
            <fieldset key={question.id} className="lesson-quiz-question">
              <legend>
                {index + 1}. {question.question}
              </legend>
              <div className="lesson-quiz-options">
                {question.options.map((option, optionIndex) => (
                  <label key={option} className="lesson-quiz-option">
                    <input
                      type="radio"
                      name={question.id}
                      checked={answers[question.id] === optionIndex}
                      onChange={() => handleAnswerChange(question.id, optionIndex)}
                    />
                    <span>
                      {OPTION_LABELS[optionIndex]}. {option}
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
          <button type="submit" className="btn btn-sm" disabled={!allAnswered || submitting}>
            {submitting ? 'Submitting…' : 'Submit quiz and complete lesson'}
          </button>
        </form>
      )}

      {result && (
        <div className="lesson-quiz-results">
          <h3>
            Score: {result.score.correct}/{result.score.total} ({result.score.percent}%)
          </h3>
          {result.progress?.status === 'completed' ? (
            <p className="success-msg">Lesson completed — great work!</p>
          ) : (
            <p className="muted">Score below 70% — review the lesson and try again.</p>
          )}
          {result.mistakes_saved > 0 && (
            <p className="muted">
              {result.mistakes_saved} wrong answer{result.mistakes_saved === 1 ? '' : 's'} saved to{' '}
              <Link to="/mistakes">Mistake Clinic</Link>.
            </p>
          )}
          <ul className="lesson-quiz-result-list">
            {result.results.map((row) => (
              <li key={row.id} className={row.is_correct ? 'is-correct' : 'is-wrong'}>
                <strong>{row.question}</strong>
                <p className="muted">{row.explanation}</p>
              </li>
            ))}
          </ul>
          {result.progress?.status !== 'completed' && (
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => {
                setResult(null)
                setAnswers({})
              }}
            >
              Try again
            </button>
          )}
        </div>
      )}
    </section>
  )
}
