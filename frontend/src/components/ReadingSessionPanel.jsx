import { useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../api/client'

const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function ReadingSessionPanel({
  session,
  loading,
  setLoading,
  setError,
  onReset,
}) {
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)

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
    <div className="reading-session-panel">
      {session.disclaimer && (
        <p className="muted reading-disclaimer">{session.disclaimer}</p>
      )}

      <section className="card reading-passage-card">
        <h2>{session.title}</h2>
        <p className="muted">
          {session.level} · {session.topic}
          {session.lesson_focus && session.lesson_focus !== 'none' && (
            <> · Focus: {session.lesson_focus.replaceAll('_', ' ')}</>
          )}
          {session.estimated_time_minutes ? (
            <> · ~{session.estimated_time_minutes} min</>
          ) : null}
        </p>
        <div className="reading-passage-text">{session.passage}</div>
      </section>

      {session.target_vocabulary?.length > 0 && (
        <section className="card reading-section">
          <h3>Target vocabulary</h3>
          <ul className="reading-vocab-list">
            {session.target_vocabulary.map((entry) => (
              <li key={entry.word}>
                <strong>{entry.word}</strong> — {entry.definition}
                {entry.example && <p className="muted">{entry.example}</p>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <form onSubmit={handleSubmit} className="reading-quiz-questions">
        <h3>Questions</h3>
        <ol className="reading-quiz-list">
          {session.questions.map((question, index) => {
            const questionResult = result?.results?.find((row) => row.id === question.id)
            return (
              <li key={question.id} className="reading-quiz-question card">
                <p>
                  <strong>{index + 1}. {question.question}</strong>
                  {question.type && (
                    <span className="muted reading-question-type"> ({question.type.replaceAll('_', ' ')})</span>
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
          <section className="reading-quiz-score card">
            <h3>Score: {result.score.correct}/{result.score.total} ({result.score.percent}%)</h3>
            {result.weak_question_types?.length > 0 && (
              <p className="muted">
                Weak question types:{' '}
                {result.weak_question_types.map((row) => `${row.type} (${row.count})`).join(', ')}
              </p>
            )}
            {result.mistakes_saved > 0 ? (
              <p className="muted">
                {result.mistakes_saved} wrong answer{result.mistakes_saved === 1 ? '' : 's'} saved to{' '}
                <Link to="/mistakes">Mistake Clinic</Link>.
              </p>
            ) : (
              <p className="muted">Great work — no mistakes to review.</p>
            )}
            <button type="button" className="btn btn-secondary" onClick={onReset}>
              Start another session
            </button>
          </section>
        )}
      </form>
    </div>
  )
}
