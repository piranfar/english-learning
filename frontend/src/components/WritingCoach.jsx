import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getPrompts, sendChatMessage } from '../api/client'
import {
  WRITING_LEVELS,
  WRITING_MODES,
  WRITING_EVALUATION_MODES,
  generateWritingPrompt,
  buildWritingEvaluationMessage,
  buildSampleAnswerMessage,
  countWords,
  wordCountStatus,
  getTrackForMode,
} from '../data/writingModes'
import { buildPromptOutlineMessage } from '../data/writingTools'
import { DEFAULT_AI_PROVIDER, pickDefaultProvider } from '../utils/defaultProvider'
import {
  loadWritingDraft,
  saveWritingDraft,
  clearWritingDraft,
  saveWritingAttempt,
} from '../services/writingStorage'
import WritingTimer from './WritingTimer'
import WritingSummaryStrip from './WritingSummaryStrip'
import WritingCompactProgress from './WritingCompactProgress'
import WritingLatestFeedback from './WritingLatestFeedback'
import AssistantMessage from './AssistantMessage'
import ExamTextArea from './ExamTextArea'

function formatTimerLabel(seconds) {
  if (seconds == null) return '—'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function countWordsInSample(text) {
  const match = text.match(/## Sample answer\s*\n([\s\S]*?)(?=\n## |$)/i)
  return match ? countWords(match[1]) : countWords(text)
}

export default function WritingCoach() {
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)
  const [mode, setMode] = useState('toefl_writing')
  const [level, setLevel] = useState('normal')
  const [evaluationMode, setEvaluationMode] = useState('normal')
  const [task, setTask] = useState(null)
  const [draft, setDraft] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [sampleLoading, setSampleLoading] = useState(false)
  const [outlineLoading, setOutlineLoading] = useState(false)
  const [error, setError] = useState('')
  const [draftRestored, setDraftRestored] = useState(false)
  const [planOpen, setPlanOpen] = useState(true)
  const [sampleAnswer, setSampleAnswer] = useState(null)
  const [promptOutline, setPromptOutline] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [progressKey, setProgressKey] = useState(0)
  const [timerState, setTimerState] = useState({ remaining: null, running: false, finished: false })
  const [rewriteDraft, setRewriteDraft] = useState('')
  const autosaveTimer = useRef(null)

  const track = useMemo(() => getTrackForMode(mode), [mode])
  const wordCount = useMemo(() => countWords(draft), [draft])
  const wcStatus = useMemo(
    () => (task ? wordCountStatus(wordCount, task.wordMin, task.wordMax) : { status: 'empty', message: '' }),
    [wordCount, task],
  )
  const modeLabel = WRITING_MODES.find((m) => m.id === mode)?.label || mode
  const timerSeconds = task ? task.timeMinutes * 60 : 600

  useEffect(() => {
    async function loadPrompts() {
      try {
        const data = await getPrompts()
        const writingPrompts = data.prompts.filter(
          (p) =>
            p.task_type === 'writing_coach' ||
            p.task_type === 'toefl_writing' ||
            p.task_type === 'writing_prompt_outline_coach',
        )
        setProvider(
          pickDefaultProvider(
            writingPrompts,
            (p) =>
              p.task_type === 'writing_coach' ||
              p.task_type === 'toefl_writing' ||
              p.task_type === 'writing_prompt_outline_coach',
          ),
        )
      } catch {
        // keep default
      }
    }
    loadPrompts()
  }, [])

  useEffect(() => {
    const saved = loadWritingDraft()
    if (saved?.draft?.trim() || saved?.task) {
      if (saved.mode) setMode(saved.mode)
      if (saved.level) setLevel(saved.level)
      if (saved.evaluationMode) setEvaluationMode(saved.evaluationMode)
      if (saved.task) setTask(saved.task)
      if (saved.draft) setDraft(saved.draft)
      if (saved.sessionId) setSessionId(saved.sessionId)
      if (saved.timerState) setTimerState(saved.timerState)
      setDraftRestored(true)
    }
  }, [])

  useEffect(() => {
    setPlanOpen(evaluationMode === 'beginner')
  }, [evaluationMode])

  const persistDraft = useCallback(
    (overrides = {}) => {
      saveWritingDraft({
        mode,
        level,
        evaluationMode,
        task,
        draft,
        sessionId,
        timerState,
        ...overrides,
      })
    },
    [mode, level, evaluationMode, task, draft, sessionId, timerState],
  )

  useEffect(() => {
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
    autosaveTimer.current = setTimeout(() => {
      if (task || draft.trim()) persistDraft()
    }, 500)
    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
    }
  }, [mode, level, evaluationMode, task, draft, sessionId, timerState, persistDraft])

  function handleGeneratePrompt() {
    setError('')
    setFeedback(null)
    setSampleAnswer(null)
    setPromptOutline(null)
    setSessionId(null)
    setRewriteDraft('')
    const next = generateWritingPrompt(mode, level)
    setTask(next)
    setDraft('')
    setTimerState({ remaining: next.timeMinutes * 60, running: false, finished: false })
    setDraftRestored(false)
    clearWritingDraft()
  }

  async function handleShowOutline() {
    if (!task || outlineLoading) return
    setOutlineLoading(true)
    setError('')
    try {
      const data = await sendChatMessage({
        message: buildPromptOutlineMessage(task),
        track: 'writing_prompt_outline_coach',
        provider,
      })
      setPromptOutline(data.reply)
      setPlanOpen(true)
    } catch (err) {
      setError(err.message || 'Failed to generate outline')
    } finally {
      setOutlineLoading(false)
    }
  }

  async function handleShowSample() {
    if (!task || sampleLoading) return
    setSampleLoading(true)
    setError('')
    try {
      const data = await sendChatMessage({
        message: buildSampleAnswerMessage(task),
        track,
        provider,
      })
      setSampleAnswer({ content: data.reply, wordCount: countWordsInSample(data.reply) })
    } catch (err) {
      setError(err.message || 'Failed to generate sample answer')
    } finally {
      setSampleLoading(false)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!task || !draft.trim() || loading) return

    setLoading(true)
    setError('')
    setFeedback(null)

    try {
      const data = await sendChatMessage({
        message: buildWritingEvaluationMessage({
          task,
          draft,
          wordCount,
          evaluationMode,
        }),
        track,
        provider,
        session_id: sessionId,
      })

      setSessionId(data.session_id)
      const wf = data.writing_feedback || data.toefl_feedback || null

      setFeedback({
        originalAnswer: draft,
        writingFeedback: wf,
      })
      setRewriteDraft('')

      saveWritingAttempt({
        mode,
        level,
        evaluation_mode: evaluationMode,
        prompt: task.prompt,
        word_count: wordCount,
        target: `${task.wordMin}–${task.wordMax}`,
        score: wf?.overall_score || null,
        scores: wf?.scores || null,
      })
      setProgressKey((k) => k + 1)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  function handleRewriteDrill() {
    const instruction = feedback?.writingFeedback?.next_rewrite_drill?.instruction
    if (!instruction) return
    setRewriteDraft(instruction)
    setDraft('')
  }

  function handleClearDraft() {
    setDraft('')
    setFeedback(null)
    setRewriteDraft('')
    setDraftRestored(false)
    persistDraft({ draft: '' })
  }

  function handleNewSession() {
    setSessionId(null)
    setFeedback(null)
    setRewriteDraft('')
    setSampleAnswer(null)
    setPromptOutline(null)
    setDraft('')
    setTask(null)
    setDraftRestored(false)
    setTimerState({ remaining: null, running: false, finished: false })
    clearWritingDraft()
  }

  const latestScores = feedback?.writingFeedback?.scores || null
  const evalLabel = WRITING_EVALUATION_MODES.find((m) => m.id === evaluationMode)?.label || evaluationMode

  return (
    <div className="writing-page writing-compact">
      <WritingSummaryStrip
        refreshKey={progressKey}
        evaluationMode={evalLabel}
        level={level}
        targetWords={task ? `${task.wordMin}–${task.wordMax}` : '—'}
        timerLabel={formatTimerLabel(timerState.remaining)}
      />

      <section className="card writing-controls-row">
        <label className="form-field">
          Mode
          <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={loading}>
            {WRITING_MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          Level
          <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={loading}>
            {WRITING_LEVELS.map((l) => (
              <option key={l.id} value={l.id}>{l.label}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          Evaluation mode
          <select value={evaluationMode} onChange={(e) => setEvaluationMode(e.target.value)} disabled={loading}>
            {WRITING_EVALUATION_MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-primary" onClick={handleGeneratePrompt} disabled={loading}>
          Generate prompt
        </button>
      </section>

      {draftRestored && (
        <p className="writing-inline-note muted">Draft restored from your previous session.</p>
      )}

      {!task && (
        <p className="muted">Select mode and level, then generate a prompt to begin.</p>
      )}

      {task && (
        <div className="writing-workspace-layout">
          <div className="writing-workspace-main">
            <section className="card writing-task-workspace">
              <div className="writing-task-head">
                <span className="tag">{modeLabel}</span>
                <span className="tag">{task.timeMinutes} min</span>
                <span className="tag">{task.wordMin}–{task.wordMax} words</span>
              </div>
              <p className="writing-prompt-text">{task.prompt}</p>
              <p className="muted"><span className="label">Goal</span> {task.goal}</p>

              <WritingTimer
                totalSeconds={timerSeconds}
                initialRemaining={timerState.remaining ?? timerSeconds}
                initialRunning={timerState.running}
                onStateChange={setTimerState}
              />

              <div className="writing-task-actions">
                <button type="button" className="btn btn-secondary btn-sm" onClick={handleShowOutline} disabled={outlineLoading}>
                  {outlineLoading ? 'Building…' : 'Teach me how to write this'}
                </button>
                <button type="button" className="btn btn-secondary btn-sm" onClick={handleShowSample} disabled={sampleLoading}>
                  {sampleLoading ? 'Generating…' : 'Show sample answer'}
                </button>
              </div>
            </section>

            <details className="card writing-plan-panel" open={planOpen}>
              <summary onClick={(e) => { e.preventDefault(); setPlanOpen((o) => !o) }}>
                Plan your answer {planOpen ? '▾' : '▸'}
              </summary>
              {planOpen && (
                <div className="writing-plan-body">
                  {promptOutline ? (
                    <AssistantMessage content={promptOutline} />
                  ) : (
                    <>
                      <ol>{task.planning.map((step) => <li key={step}>{step}</li>)}</ol>
                      <ul className="writing-starters">
                        {task.sentenceStarters.map((starter) => (
                          <li key={starter}>
                            <button
                              type="button"
                              className="writing-starter-btn"
                              onClick={() => setDraft((text) => (text ? `${text} ${starter}` : starter))}
                            >
                              {starter}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}
            </details>

            {sampleAnswer && (
              <details className="card writing-sample-compact">
                <summary>Sample answer ({sampleAnswer.wordCount} words)</summary>
                <AssistantMessage content={sampleAnswer.content} />
              </details>
            )}

            <section className="card writing-editor-workspace">
              <form onSubmit={handleSubmit}>
                <ExamTextArea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder={rewriteDraft || 'Write your answer here...'}
                  rows={14}
                  disabled={loading}
                  className="writing-textarea"
                  examMode
                />
                <div className={`writing-word-count writing-word-count--${wcStatus.status}`}>
                  Words: {wordCount} / {task.wordMin}–{task.wordMax}
                  {wcStatus.message && <span className="writing-word-count-msg"> — {wcStatus.message}</span>}
                </div>
                {wcStatus.status === 'short' && evaluationMode === 'beginner' && (
                  <p className="writing-inline-alert muted">Add one more reason or example to reach the target length.</p>
                )}
                <div className="writing-actions">
                  <button type="submit" className="btn btn-primary" disabled={loading || !draft.trim()}>
                    {loading ? 'Scoring…' : 'Submit for scoring'}
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={handleClearDraft} disabled={loading}>
                    Clear draft
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={handleNewSession} disabled={loading}>
                    New session
                  </button>
                </div>
              </form>
            </section>

            {error && <p className="error">{error}</p>}

            {feedback && (
              <WritingLatestFeedback feedback={feedback} onRewriteDrill={handleRewriteDrill} />
            )}
          </div>

          <WritingCompactProgress latestScores={latestScores} refreshKey={progressKey} />
        </div>
      )}
    </div>
  )
}
