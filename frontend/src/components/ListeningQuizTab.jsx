import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ExamTextArea from './ExamTextArea'
import { apiRequest, createShadowingFromSentences, postForm } from '../api/client'
import { sendSentencesToShadowing } from '../services/listeningShadowing'

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
  { value: 'speaker_purpose', label: 'Speaker purpose' },
  { value: 'vocabulary_phrase', label: 'Vocabulary / phrase meaning' },
]

const FOCUS_LABELS = Object.fromEntries(FOCUSES.map((entry) => [entry.value, entry.label]))
const OPTION_LABELS = ['A', 'B', 'C', 'D']

export default function ListeningQuizTab({
  provider,
  transcriptionProvider,
  loading,
  setLoading,
  setError,
}) {
  const [phase, setPhase] = useState('setup')
  const [draftTranscript, setDraftTranscript] = useState('')
  const [audioFile, setAudioFile] = useState(null)
  const [level, setLevel] = useState('B1')
  const [focus, setFocus] = useState('mixed')
  const [notes, setNotes] = useState('')
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [shadowingLoading, setShadowingLoading] = useState(false)
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const audioUrl = useMemo(() => {
    if (!audioFile) return null
    return URL.createObjectURL(audioFile)
  }, [audioFile])

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  async function handleGenerate(event) {
    event.preventDefault()
    const text = draftTranscript.trim()
    if ((!text && !audioFile) || loading) {
      setError('Upload audio or paste a transcript before generating a quiz.')
      return
    }

    setLoading(true)
    setError('')
    setQuiz(null)
    setAnswers({})
    setResult(null)
    setNotes('')

    try {
      let data
      if (audioFile) {
        const form = new FormData()
        form.append('audio', audioFile)
        form.append('provider', provider)
        form.append('transcription_provider', transcriptionProvider)
        form.append('level', level)
        form.append('question_focus', focus)
        data = await postForm('/listening/quiz/generate/', form)
      } else {
        data = await apiRequest('/listening/quiz/generate/', {
          method: 'POST',
          json: {
            transcript: text,
            provider,
            transcription_provider: transcriptionProvider,
            level,
            question_focus: focus,
          },
        })
      }

      setQuiz(data.quiz)
      setDraftTranscript('')
      setPhase('quiz')
    } catch (err) {
      const message = err.message || 'Failed to generate listening quiz'
      if (/stt failed/i.test(message)) {
        setError(`${message} Try pasting a transcript instead.`)
      } else if (/quiz generation failed/i.test(message)) {
        setError(`${message} Please try again or choose a shorter clip.`)
      } else {
        setError(message)
      }
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
      const data = await apiRequest('/listening/quiz/submit/', {
        method: 'POST',
        json: {
          quiz_id: quiz.quiz_id,
          answers,
        },
      })
      setResult(data)
      setPhase('results')
    } catch (err) {
      setError(err.message || 'Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  function handleAnswerChange(questionId, optionIndex) {
    if (phase === 'results') return
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  function resetQuiz() {
    setPhase('setup')
    setQuiz(null)
    setAnswers({})
    setResult(null)
    setNotes('')
    setError('')
  }

  async function handleSendToShadowing() {
    if (!result?.shadowing_sentences?.length || shadowingLoading) return
    setShadowingLoading(true)
    setError('')
    try {
      await sendSentencesToShadowing(
        result.shadowing_sentences,
        navigate,
        createShadowingFromSentences,
      )
    } catch (err) {
      setError(err.message || 'Could not open Shadowing practice')
    } finally {
      setShadowingLoading(false)
    }
  }

  const allAnswered = quiz?.questions?.every((question) => answers[question.id] !== undefined)

  if (phase === 'setup') {
    return (
      <div className="reading-quiz-panel">
        <form onSubmit={handleGenerate} className="reading-quiz-controls card card-compact">
          <p className="muted">
            Upload audio or paste a transcript. The transcript stays hidden during the quiz until
            you submit your answers.
          </p>

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
              Question focus
              <select value={focus} onChange={(e) => setFocus(e.target.value)} disabled={loading}>
                {FOCUSES.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="audio-upload">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={(event) => {
                const file = event.target.files?.[0]
                setAudioFile(file || null)
                if (file) setDraftTranscript('')
              }}
              disabled={loading}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              className="secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              {audioFile ? `Selected: ${audioFile.name}` : 'Upload audio file'}
            </button>
            {audioFile && (
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setAudioFile(null)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
                disabled={loading}
              >
                Clear audio
              </button>
            )}
          </div>

          <textarea
            value={draftTranscript}
            onChange={(event) => {
              setDraftTranscript(event.target.value)
              if (event.target.value) setAudioFile(null)
            }}
            placeholder="Or paste a transcript here (hidden during the quiz)..."
            rows={10}
            disabled={loading || !!audioFile}
          />

          {!draftTranscript.trim() && !audioFile && (
            <p className="muted">No transcript yet — upload audio or paste text to continue.</p>
          )}

          <button type="submit" disabled={loading || (!draftTranscript.trim() && !audioFile)}>
            {loading ? 'Preparing quiz…' : 'Generate quiz'}
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="reading-quiz-panel">
      <section className="card listening-quiz-instructions">
        <h2>Listening quiz</h2>
        <p className="muted">
          Listen carefully{quiz?.source === 'audio' ? ' to the audio' : ''}, take notes, then answer
          the questions. The transcript is hidden until you submit.
        </p>
        {audioUrl && (
          <audio controls src={audioUrl} className="listening-quiz-audio">
            Your browser does not support audio playback.
          </audio>
        )}
        <label className="form-field">
          Your notes
          <ExamTextArea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={6}
            placeholder="Take notes while you listen. Spellcheck and writing assistants are disabled in exam mode."
            disabled={phase === 'results'}
          />
        </label>
      </section>

      {quiz && (
        <form onSubmit={handleSubmit} className="reading-quiz-questions">
          <p className="muted">
            {quiz.level} · {FOCUS_LABELS[quiz.question_focus] || 'Mixed'}
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
                      const isWrongSelection = phase === 'results' && selected && !questionResult?.is_correct
                      return (
                        <label
                          key={`${question.id}-${optionIndex}`}
                          className={`reading-quiz-option${
                            phase === 'results' && isCorrect ? ' reading-quiz-option-correct' : ''
                          }${isWrongSelection ? ' reading-quiz-option-wrong' : ''}`}
                        >
                          <input
                            type="radio"
                            name={question.id}
                            checked={selected}
                            onChange={() => handleAnswerChange(question.id, optionIndex)}
                            disabled={phase === 'results'}
                          />
                          <span>{OPTION_LABELS[optionIndex]}. {option}</span>
                        </label>
                      )
                    })}
                  </div>
                  {phase === 'results' && !questionResult?.is_correct && (
                    <p className="reading-quiz-explanation">
                      <strong>Explanation:</strong> {questionResult?.explanation}
                    </p>
                  )}
                </li>
              )
            })}
          </ol>

          {phase !== 'results' ? (
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

              <section className="reading-section">
                <h3>Transcript</h3>
                <p className="listening-quiz-transcript">{result.transcript}</p>
              </section>

              {result.shadowing_sentences?.length > 0 && (
                <section className="reading-section">
                  <h3>Difficult sentences for shadowing</h3>
                  <ul>
                    {result.shadowing_sentences.map((sentence) => (
                      <li key={sentence}>{sentence}</li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleSendToShadowing}
                    disabled={shadowingLoading}
                  >
                    {shadowingLoading ? 'Opening Shadowing…' : 'Send difficult sentences to Shadowing'}
                  </button>
                </section>
              )}

              <button type="button" className="btn btn-secondary" onClick={resetQuiz}>
                Start another listening quiz
              </button>
            </section>
          )}
        </form>
      )}
    </div>
  )
}
