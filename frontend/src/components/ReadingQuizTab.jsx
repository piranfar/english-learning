import { useState } from 'react'
import { Link } from 'react-router-dom'
import WritingTimer from './WritingTimer'
import { apiRequest } from '../api/client'

const LEVELS = [
  { value: 'B1', label: 'B1' },
  { value: 'B2', label: 'B2' },
  { value: 'TOEFL', label: 'TOEFL' },
]

const FOCUSES = [
  { value: 'mixed', label: 'Mixed' },
  { value: 'main_idea', label: 'Main idea' },
  { value: 'detail', label: 'Detail' },
  { value: 'inference', label: 'Inference' },
  { value: 'vocabulary_in_context', label: 'Vocabulary in context' },
  { value: 'sentence_simplification', label: 'Sentence simplification' },
]

const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function ReadingQuizTab({ passage, setPassage, provider, loading, setLoading, setError }) {
  const [level, setLevel] = useState('B1')
  const [focus, setFocus] = useState('mixed')
  const [useTimer, setUseTimer] = useState(false)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)

  async function handleGenerate(event) {
    event.preventDefault()
    const text = passage.trim()
    if (!text || loading) return

    setLoading(true)
    setError('')
    setQuiz(null)
    setAnswers({})
    setSubmitted(false)
    setResult(null)

    try {
      const data = await apiRequest('/reading/quiz/generate/', {
        method: 'POST',
        json: {
          passage: text,
          level,
          question_focus: focus,
          provider,
        },
      })
      setQuiz(data.quiz)
    } catch (err) {
      setError(err.message || 'Failed to generate quiz')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!quiz || loading) return

    setLoading(true)
    setError('')

    try {
      const data = await apiRequest('/reading/quiz/submit/', {
        method: 'POST',
        json: {
          quiz_id: quiz.quiz_id,
          answers,
        },
      })
      setResult(data)
      setSubmitted(true)
    } catch (err) {
      setError(err.message || 'Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  function handleAnswerChange(questionId, optionIndex) {
    if (submitted) return
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  const allAnswered = quiz?.questions?.every((question) => answers[question.id] !== undefined)

  return (
    <div className="reading-quiz-panel">
      <form onSubmit={handleGenerate} className="reading-quiz-controls card card-compact">
        <div className="form-row">
          <label className="form-field">
            Level
            <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={loading || submitted}>
              {LEVELS.map((entry) => (
                <option key={entry.value} value={entry.value}>{entry.label}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Question focus
            <select value={focus} onChange={(e) => setFocus(e.target.value)} disabled={loading || submitted}>
              {FOCUSES.map((entry) => (
                <option key={entry.value} value={entry.value}>{entry.label}</option>
              ))}
            </select>
          </label>
          <label className="form-field reading-quiz-timer-toggle">
            <input
              type="checkbox"
              checked={useTimer}
              onChange={(e) => setUseTimer(e.target.checked)}
              disabled={loading || submitted}
            />
            Use optional timer
          </label>
        </div>

        {useTimer && (
          <WritingTimer totalSeconds={900} label="Quiz timer" />
        )}

        <textarea
          value={passage}
          onChange={(e) => setPassage(e.target.value)}
          placeholder="Paste a passage for quiz generation..."
          rows={12}
          disabled={loading}
        />

        {!quiz && (
          <button type="submit" disabled={loading || !passage.trim()}>
            {loading ? 'Generating quiz…' : 'Generate quiz'}
          </button>
        )}
      </form>

      {quiz && (
        <form onSubmit={handleSubmit} className="reading-quiz-questions">
          <h2>Reading quiz</h2>
          <p className="muted">
            {quiz.level} · {FOCUSES.find((entry) => entry.value === quiz.question_focus)?.label || 'Mixed'}
          </p>

          <ol className="reading-quiz-list">
            {quiz.questions.map((question, index) => {
              const questionResult = result?.results?.find((row) => row.id === question.id)
              return (
                <li key={question.id} className="reading-quiz-question card">
                  <p><strong>{index + 1}. {question.question}</strong></p>
                  <div className="reading-quiz-options">
                    {question.options.map((option, optionIndex) => {
                      const selected = answers[question.id] === optionIndex
                      const isCorrect = questionResult?.correct_index === optionIndex
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
                  {submitted && !questionResult?.is_correct && (
                    <p className="reading-quiz-explanation">
                      <strong>Explanation:</strong> {questionResult?.explanation}
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
              {result.mistakes_saved > 0 ? (
                <p className="muted">
                  {result.mistakes_saved} wrong answer{result.mistakes_saved === 1 ? '' : 's'} saved to{' '}
                  <Link to="/mistakes">Mistake Clinic</Link>.
                </p>
              ) : (
                <p className="muted">Great work — no mistakes to review.</p>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setQuiz(null)
                  setAnswers({})
                  setSubmitted(false)
                  setResult(null)
                }}
              >
                Generate another quiz
              </button>
            </section>
          )}
        </form>
      )}
    </div>
  )
}
