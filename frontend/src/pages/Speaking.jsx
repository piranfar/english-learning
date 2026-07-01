import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  getPrompts,
  sendChatMessage,
  submitSpeakingAudio,
} from '../api/client'
import {
  SPEAKING_LEVELS,
  EVALUATION_MODES,
  PRACTICE_TYPES,
  generateTask,
  buildSpeakingEvaluationMessage,
  getTrackForPracticeType,
} from '../data/speakingTasks'
import { saveSpeakingAttempt } from '../services/speakingStorage'
import ExamTextArea from '../components/ExamTextArea'
import AudioRecorder from '../components/AudioRecorder'
import SpeakingCompactProgress from '../components/SpeakingCompactProgress'
import SpeakingLatestFeedback from '../components/SpeakingLatestFeedback'
import SpeakingSummaryStrip from '../components/SpeakingSummaryStrip'
import SpeakingTimer from '../components/SpeakingTimer'
import { DEFAULT_AI_PROVIDER, pickDefaultProvider } from '../utils/defaultProvider'

const TYPED_ONLY_NOTICE =
  'Typed practice can evaluate grammar, vocabulary, and organization. Pronunciation cannot be scored without audio.'

function modeLabel(modeId) {
  return EVALUATION_MODES.find((item) => item.id === modeId)?.label || modeId
}

export default function Speaking() {
  const [level, setLevel] = useState('normal')
  const [evaluationMode, setEvaluationMode] = useState('normal')
  const [practiceType, setPracticeType] = useState('daily_conversation')
  const [task, setTask] = useState(null)
  const [articleText, setArticleText] = useState('')
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [voiceLoading, setVoiceLoading] = useState(false)
  const [error, setError] = useState('')
  const [typedInput, setTypedInput] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [progressKey, setProgressKey] = useState(0)
  const [timerActive, setTimerActive] = useState(false)
  const [followUpMode, setFollowUpMode] = useState(false)
  const [lastAnswer, setLastAnswer] = useState('')
  const [drillMode, setDrillMode] = useState(false)

  const track = useMemo(() => getTrackForPracticeType(practiceType), [practiceType])

  useEffect(() => {
    async function loadPrompts() {
      try {
        const data = await getPrompts()
        const speakingPrompts = data.prompts.filter((p) => p.task_type === track)
        setProvider(
          pickDefaultProvider(
            speakingPrompts,
            (prompt) => prompt.task_type === track,
          ),
        )
      } catch {
        // keep default
      }
    }
    loadPrompts()
  }, [track])

  const handleGenerateTask = useCallback(() => {
    setError('')
    setFeedback(null)
    setFollowUpMode(false)
    setDrillMode(false)
    setSessionId(null)
    const next = generateTask(practiceType, level, { articleText })
    setTask(next)
    setTimerActive(true)
  }, [practiceType, level, articleText])

  useEffect(() => {
    handleGenerateTask()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- initial task only

  function persistAttempt(result, transcript, inputMode) {
    const sf = result.speaking_feedback || {}
    saveSpeakingAttempt({
      task_id: task?.id,
      task_type: task?.type,
      task_title: task?.title,
      level: task?.level,
      evaluation_mode: evaluationMode,
      transcript,
      input_mode: inputMode,
      corrected_answer: sf.corrected_version || '',
      overall_score: sf.overall_score,
      breakdown: sf.breakdown,
      scores: sf.scores,
      key_mistakes: sf.main_issues || sf.strengths || [],
      recommended_next_task: sf.recommended_next_task || sf.retry_recommendation || '',
    })
    setProgressKey((k) => k + 1)
  }

  async function evaluateAnswer(answer, inputMode, options = {}) {
    if (!task) return
    if (inputMode === 'typed' && !String(answer).trim()) return
    if (inputMode === 'voice' && !answer) return

    setLoading(inputMode === 'typed')
    setVoiceLoading(inputMode === 'voice')
    setError('')

    const activeTask = options.taskOverride || task
    const activeMode = options.evaluationMode || evaluationMode

    try {
      let data
      if (inputMode === 'voice') {
        data = await submitSpeakingAudio({
          audioBlob: answer,
          scenario: activeTask.type,
          sessionId,
          provider,
          level: activeTask.level,
          evaluationMode: activeMode,
          taskType: activeTask.type,
          taskTitle: activeTask.title,
          taskPrompt: activeTask.prompt,
          articleText: activeTask.article_text || '',
          evaluationFocus: (activeTask.evaluation_focus || []).join(','),
          prepTime: activeTask.prep_seconds,
          speakTime: activeTask.speak_seconds,
        })
      } else {
        const message = buildSpeakingEvaluationMessage({
          task: activeTask,
          answer,
          inputMode: 'typed',
          followUp: followUpMode,
          previousAnswer: lastAnswer,
          evaluationMode: activeMode,
        })
        data = await sendChatMessage({
          message,
          track,
          provider,
          session_id: sessionId,
          scenario: activeTask.type,
        })
      }

      setSessionId(data.session_id)
      const transcript = data.transcript || answer
      setLastAnswer(transcript)
      setFeedback({
        transcript,
        reply: data.reply,
        speakingFeedback: data.speaking_feedback,
        inputMode,
      })
      persistAttempt(data, transcript, inputMode)

      if (practiceType === 'follow_up_conversation' && data.speaking_feedback?.follow_up_question) {
        setFollowUpMode(true)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
      setVoiceLoading(false)
    }
  }

  async function handleVoiceSubmit(audioBlob) {
    await evaluateAnswer(audioBlob, 'voice')
  }

  async function handleTypedSubmit(event) {
    event.preventDefault()
    const text = typedInput.trim()
    if (!text || loading || voiceLoading) return
    setTypedInput('')
    await evaluateAnswer(text, 'typed')
  }

  function handleRetryTask() {
    setFeedback(null)
    setTimerActive(true)
    setDrillMode(false)
  }

  function handleNextDrill() {
    const drill = feedback?.speakingFeedback?.next_drill
    if (!drill?.instruction) return
    setDrillMode(true)
    setFeedback(null)
    setTask((prev) => ({
      ...prev,
      title: drill.title || 'Targeted drill',
      prompt: drill.instruction,
      speak_seconds: 45,
      prep_seconds: 10,
    }))
    setTimerActive(true)
  }

  const latestScores = feedback?.speakingFeedback?.scores || null

  return (
    <div className="page speaking-page speaking-compact">
      <header className="speaking-header-compact">
        <h1>Speaking Coach</h1>
      </header>

      <SpeakingSummaryStrip
        refreshKey={progressKey}
        evaluationMode={modeLabel(evaluationMode)}
      />

      <div className="speaking-workspace-layout">
        <div className="speaking-workspace-main">
          <section className="card speaking-controls-row">
            <label className="form-field">
              Speaking level
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                disabled={loading || voiceLoading}
              >
                {SPEAKING_LEVELS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Practice type
              <select
                value={practiceType}
                onChange={(e) => setPracticeType(e.target.value)}
                disabled={loading || voiceLoading}
              >
                {PRACTICE_TYPES.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Evaluation mode
              <select
                value={evaluationMode}
                onChange={(e) => setEvaluationMode(e.target.value)}
                disabled={loading || voiceLoading}
              >
                {EVALUATION_MODES.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleGenerateTask}
              disabled={loading || voiceLoading}
            >
              Generate task
            </button>
          </section>

          {practiceType === 'talk_about_article' && (
            <section className="card speaking-article-compact">
              <label className="form-field">
                Paste article
                <textarea
                  value={articleText}
                  onChange={(e) => setArticleText(e.target.value)}
                  rows={3}
                  placeholder="Paste the article you want to discuss..."
                />
              </label>
            </section>
          )}

          {task && (
            <section className="card speaking-task-workspace">
              <div className="speaking-task-head">
                <h2>{task.title}</h2>
                <div className="tag-list">
                  <span className="tag">{modeLabel(evaluationMode)}</span>
                  <span className="tag">Prep {task.prep_seconds}s</span>
                  <span className="tag">Speak {task.speak_seconds}s</span>
                </div>
              </div>

              <p className="speaking-task-prompt">{task.prompt}</p>

              {task.support_phrases?.length > 0 && (
                <div className="speaking-support-inline">
                  <span className="label">Support phrases</span>
                  <span>{task.support_phrases.join(' · ')}</span>
                </div>
              )}

              {task.goals?.length > 0 && (
                <p className="speaking-goals-inline muted">
                  <span className="label">Learning goal</span> {task.goals[0]}
                </p>
              )}

              <SpeakingTimer
                prepSeconds={task.prep_seconds}
                speakSeconds={task.speak_seconds}
                active={timerActive}
                onReset={() => setTimerActive(false)}
              />

              <div className="speaking-recorder-inline">
                <AudioRecorder
                  onSubmit={handleVoiceSubmit}
                  loading={voiceLoading}
                  submitLabel="Submit"
                  disabled={loading}
                />
              </div>
            </section>
          )}

          <details className="card speaking-typed-backup">
            <summary>Typed backup if microphone fails</summary>
            <p className="muted">{TYPED_ONLY_NOTICE}</p>
            <form onSubmit={handleTypedSubmit}>
              <ExamTextArea
                value={typedInput}
                onChange={(e) => setTypedInput(e.target.value)}
                rows={3}
                placeholder="Type your speaking answer here..."
                disabled={loading || voiceLoading || !task}
                examMode
              />
              <button type="submit" disabled={loading || voiceLoading || !typedInput.trim() || !task}>
                {loading ? 'Evaluating...' : 'Submit typed answer'}
              </button>
            </form>
          </details>

          {error && <p className="error">{error}</p>}

          {feedback && (
            <SpeakingLatestFeedback
              feedback={feedback}
              onRetryTask={handleRetryTask}
              onNextDrill={handleNextDrill}
            />
          )}

          {drillMode && !feedback && (
            <p className="muted speaking-drill-hint">
              Complete the drill above, then submit your recording.
            </p>
          )}
        </div>

        <SpeakingCompactProgress
          refreshKey={progressKey}
          latestScores={latestScores}
          variant="sidebar"
        />
      </div>
    </div>
  )
}
