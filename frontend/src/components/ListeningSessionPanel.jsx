import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ExamTextArea from './ExamTextArea'
import ListeningPlayer from './ListeningPlayer'
import { useDeveloperMode } from '../hooks/useDeveloperMode'
import { apiRequest, createShadowingFromSentences } from '../api/client'
import { sendSentencesToShadowing } from '../services/listeningShadowing'
import { saveListeningAttempt } from '../services/listeningStorage'

const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function ListeningSessionPanel({
  session,
  loading,
  setLoading,
  setError,
  onReset,
  onProgressSaved,
}) {
  const devMode = useDeveloperMode()
  const navigate = useNavigate()
  const [notes, setNotes] = useState('')
  const [shadowingLoading, setShadowingLoading] = useState(false)
  const [quizStarted, setQuizStarted] = useState(false)
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
      const data = await apiRequest('/listening/submit-practice/', {
        method: 'POST',
        json: {
          session_id: session.session_id,
          answers,
        },
      })
      setResult(data)
      setSubmitted(true)
      saveListeningAttempt({
        session_id: session.session_id,
        score_percent: data.score?.percent,
        listening_type: session.listening_type,
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

  async function handleSendToShadowing() {
    if (!session?.shadowing_sentences?.length || shadowingLoading) return
    setShadowingLoading(true)
    setError('')
    try {
      await sendSentencesToShadowing(
        session.shadowing_sentences,
        navigate,
        createShadowingFromSentences,
      )
    } catch (err) {
      setError(err.message || 'Could not open Shadowing practice')
    } finally {
      setShadowingLoading(false)
    }
  }

  if (!session) return null

  return (
    <div className="listening-session-panel">
      {session.learner_message && !devMode && (
        <p className="muted reading-disclaimer">{session.learner_message}</p>
      )}
      {devMode && session.provider_metadata && (
        <p className="muted reading-disclaimer">
          Provider: {session.provider_metadata.provider}
          {' · '}
          Model: {session.provider_metadata.model}
          {session.provider_metadata.used_fallback ? ' · built-in fallback' : ''}
        </p>
      )}
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
          {session.estimated_duration_seconds ? (
            <> · ~{Math.round(session.estimated_duration_seconds / 60) || 1} min</>
          ) : null}
        </p>

        <ListeningPlayer text={session.transcript} defaultSpeed={session.speed} />

        {!submitted ? (
          <p className="muted listening-transcript-locked">
            The transcript is hidden until you submit your answers — listen (and replay as needed)
            and use the notes box below.
          </p>
        ) : (
          <div className="listening-transcript-revealed">
            <h3>Transcript</h3>
            <div className="reading-passage-text">{session.transcript}</div>
          </div>
        )}
      </section>

      {session.target_vocabulary?.length > 0 && submitted && (
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

      {!quizStarted ? (
        <section className="card listening-notes-card">
          <h3>Notes</h3>
          <p className="muted">
            Take notes while you listen, just like a real TOEFL listening section. Notes are not
            graded and stay on this page.
          </p>
          <ExamTextArea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Jot down key points while you listen…"
            rows={6}
            examMode={false}
          />
          <button type="button" className="btn" onClick={() => setQuizStarted(true)}>
            Start quiz
          </button>
        </section>
      ) : (
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

              {session.shadowing_sentences?.length > 0 && (
                <div className="listening-shadowing-callout">
                  <p className="muted">
                    {session.shadowing_sentences.length} difficult sentence
                    {session.shadowing_sentences.length === 1 ? '' : 's'} from this transcript could
                    help your pronunciation practice.
                  </p>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleSendToShadowing}
                    disabled={shadowingLoading}
                  >
                    {shadowingLoading ? 'Opening Shadowing…' : 'Practice in Shadowing'}
                  </button>
                </div>
              )}

              <button type="button" className="btn btn-secondary" onClick={onReset}>
                Start another session
              </button>
            </section>
          )}
        </form>
      )}
    </div>
  )
}
