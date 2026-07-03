import { useCallback, useEffect, useRef, useState } from 'react'
import ExamTextArea from '../ExamTextArea'
import { compareWritingRevision, generateWritingEditPractice, submitWritingEdit } from '../../api/client'
import { EDIT_STRENGTHS, EDIT_STYLES, EDIT_LANGUAGE_LEVELS, normalizeEditStyle, normalizeEditLanguageLevel, describeEditSettings } from '../../data/writingTools'
import { loadToolState, saveToolState, TOOL_STORAGE_KEYS } from '../../services/writingToolsStorage'
import TextDiffView from './TextDiffView'
import WritingToolProvider from './WritingToolProvider'

const EMPTY_RESULT = {
  edited_text: '',
  changes: [],
  teaching_notes: [],
  sentence_comparisons: [],
  level_feedback: '',
  better_alternative: '',
  structured: true,
  notice: null,
}

function extractFieldError(err) {
  const message = err?.message || ''
  if (message.includes('real English paragraph')) {
    return 'Please generate or paste a real English paragraph first.'
  }
  if (message.includes('paste a paragraph')) {
    return 'Please generate or paste a paragraph first.'
  }
  return message || 'Something went wrong'
}

export default function WritingEditingTab({ provider, onProviderChange, prompts }) {
  const [inputText, setInputText] = useState('')
  const [strength, setStrength] = useState('standard')
  const [style, setStyle] = useState('simple_american_english')
  const [languageLevel, setLanguageLevel] = useState('normal')
  const [useOwnText, setUseOwnText] = useState(false)
  const [teachingTip, setTeachingTip] = useState('')
  const [editResult, setEditResult] = useState(null)
  const [learnerEdited, setLearnerEdited] = useState('')
  const [showCompare, setShowCompare] = useState(false)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareResult, setCompareResult] = useState(null)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')
  const saveTimer = useRef(null)

  useEffect(() => {
    const saved = loadToolState(TOOL_STORAGE_KEYS.editing)
    if (!saved) return
    setInputText(saved.inputText || '')
    setStrength(saved.strength || 'standard')
    setStyle(normalizeEditStyle(saved.style || 'simple_american_english'))
    setLanguageLevel(normalizeEditLanguageLevel(saved.languageLevel || 'normal'))
    setUseOwnText(Boolean(saved.useOwnText))
    setTeachingTip(saved.teachingTip || '')
    setEditResult(saved.editResult || null)
    setLearnerEdited(saved.learnerEdited || saved.editResult?.edited_text || '')
    setShowCompare(Boolean(saved.showCompare))
  }, [])

  const persist = useCallback(
    (overrides = {}) => {
      saveToolState(TOOL_STORAGE_KEYS.editing, {
        inputText,
        strength,
        style,
        languageLevel,
        useOwnText,
        teachingTip,
        editResult,
        learnerEdited,
        showCompare,
        ...overrides,
      })
    },
    [inputText, strength, style, languageLevel, useOwnText, teachingTip, editResult, learnerEdited, showCompare],
  )

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => persist(), 400)
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current)
    }
  }, [persist])

  async function handleGenerate() {
    setGenerateLoading(true)
    setError('')
    setValidationError('')
    setEditResult(null)
    setLearnerEdited('')
    setShowCompare(false)

    try {
      const data = await generateWritingEditPractice({
        targetStyle: style,
        languageLevel,
        aiProvider: provider,
      })
      setUseOwnText(false)
      setInputText(data.draft_text || '')
      setTeachingTip(data.teaching_tip || '')
      if (data.notice) setError(data.notice)
    } catch (err) {
      setError(extractFieldError(err))
    } finally {
      setGenerateLoading(false)
    }
  }

  function handleUseOwnText() {
    setUseOwnText(true)
    setTeachingTip('')
    setEditResult(null)
    setLearnerEdited('')
    setShowCompare(false)
    if (!inputText) setInputText('')
  }

  async function handleEdit(event) {
    event.preventDefault()
    if (loading) return

    if (!inputText.trim()) {
      setValidationError('Please generate or paste a paragraph first.')
      return
    }

    setValidationError('')
    setLoading(true)
    setError('')
    setShowCompare(false)
    setCompareResult(null)

    try {
      const data = await submitWritingEdit({
        text: inputText,
        editStrength: strength,
        targetStyle: style,
        languageLevel,
        aiProvider: provider,
      })

      const result = data.edit_result || EMPTY_RESULT
      setEditResult(result)
      setLearnerEdited(result.edited_text || '')
      if (result.notice) setError(result.notice)
    } catch (err) {
      setError(extractFieldError(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleCompareRevision() {
    if (!aiText.trim() || compareLoading) return

    setCompareLoading(true)
    setError('')
    setShowCompare(true)

    try {
      const data = await compareWritingRevision({
        originalAnswer: inputText,
        revisedAnswer: learnerEdited,
        prompt: useOwnText ? '' : 'Writing edit practice paragraph',
        provider,
      })
      setCompareResult(data.comparison || null)
    } catch (err) {
      setError(extractFieldError(err))
      setCompareResult(null)
    } finally {
      setCompareLoading(false)
    }
  }

  const aiText = editResult?.edited_text || ''
  const activeSettings = describeEditSettings({ strength, style, languageLevel })
  const appliedSettings = editResult
    ? describeEditSettings({
        strength: editResult.edit_strength || strength,
        style: editResult.target_style || style,
        languageLevel: editResult.language_level || languageLevel,
      })
    : null
  const busy = loading || generateLoading

  return (
    <div className="writing-tool-tab">
      <WritingToolProvider
        provider={provider}
        prompts={prompts}
        tracks={['writing_edit_generate', 'writing_edit_coach']}
        onChange={onProviderChange}
      />

      <section className="card writing-tool-input">
        <h2 className="writing-section-title">Practice setup</h2>

        <div className="writing-tool-options writing-tool-options--triple">
          <label className="form-field">
            Edit strength
            <select value={strength} onChange={(e) => setStrength(e.target.value)} disabled={busy}>
              {EDIT_STRENGTHS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <span className="muted writing-field-hint">{activeSettings.strength.hint}</span>
          </label>
          <label className="form-field">
            Target style
            <select value={style} onChange={(e) => setStyle(e.target.value)} disabled={busy}>
              {EDIT_STYLES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <span className="muted writing-field-hint">{activeSettings.style.hint}</span>
          </label>
          <label className="form-field">
            Language level
            <select value={languageLevel} onChange={(e) => setLanguageLevel(e.target.value)} disabled={busy}>
              {EDIT_LANGUAGE_LEVELS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <span className="muted writing-field-hint">{activeSettings.languageLevel.hint}</span>
          </label>
        </div>

        <p className="writing-settings-summary muted">
          Generate a practice paragraph first, then edit it with{' '}
          <strong>{activeSettings.summary}</strong>.
        </p>

        <div className="writing-prompt-actions">
          <button
            type="button"
            className="btn"
            onClick={handleGenerate}
            disabled={busy}
          >
            {generateLoading ? 'Generating...' : 'Generate practice paragraph'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleUseOwnText}
            disabled={busy}
          >
            Use my own text
          </button>
        </div>
      </section>

      {(inputText || useOwnText) && (
        <form onSubmit={handleEdit}>
          <section className="card writing-original-card">
            <h2 className="writing-section-title">
              {useOwnText ? 'Your text' : 'Practice paragraph'}
            </h2>

            <label className="form-field">
              <ExamTextArea
                value={inputText}
                onChange={(e) => {
                  setInputText(e.target.value)
                  setEditResult(null)
                  setLearnerEdited('')
                  setShowCompare(false)
                  if (validationError) setValidationError('')
                }}
                rows={8}
                placeholder={
                  useOwnText
                    ? 'Paste your paragraph here...'
                    : 'Edit the generated paragraph if you want, then click Edit my writing...'
                }
                disabled={busy}
                examMode
              />
            </label>
            {!useOwnText && (
              <p className="muted writing-tool-hint">You can change the generated text before editing.</p>
            )}

            {teachingTip && (
              <p className="muted writing-teaching-tip">Tip: {teachingTip}</p>
            )}

            {validationError && <p className="error">{validationError}</p>}
            {loading && <p className="muted writing-edit-loading">Editing your writing...</p>}

            <button type="submit" className="btn" disabled={busy || !inputText.trim()}>
              {loading ? 'Editing...' : 'Edit my writing'}
            </button>
          </section>
        </form>
      )}

      {error && <p className="error">{error}</p>}

      {editResult?.edited_text && (
        <section className="card writing-edit-result">
          <h2>Edited Result</h2>

          {appliedSettings && (
            <div className="writing-settings-badges">
              <span className="writing-settings-badge">{appliedSettings.strength.label}</span>
              <span className="writing-settings-badge">{appliedSettings.style.label}</span>
              <span className="writing-settings-badge">{appliedSettings.languageLevel.label}</span>
            </div>
          )}

          {editResult.notice && (
            <p className="writing-edit-notice muted">{editResult.notice}</p>
          )}

          <div className="writing-tool-block">
            <span className="label">Edited Version</span>
            <textarea
              className="writing-edit-output-box"
              value={learnerEdited}
              onChange={(e) => {
                setLearnerEdited(e.target.value)
                setShowCompare(false)
              }}
              rows={8}
            />
            {learnerEdited !== aiText && (
              <p className="muted writing-tool-hint">You edited the AI version — compare below.</p>
            )}
          </div>

          {editResult.changes?.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">What Changed</span>
              <ul className="writing-edit-list">
                {editResult.changes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {editResult.teaching_notes?.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">Teaching Notes</span>
              <ul className="writing-edit-list">
                {editResult.teaching_notes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {editResult.sentence_comparisons?.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">Sentence-by-Sentence Help</span>
              <div className="writing-correction-table">
                {editResult.sentence_comparisons.map((row, index) => (
                  <article key={index} className="writing-correction-row">
                    <p><span className="label">Original</span> {row.original}</p>
                    <p><span className="label">Improved</span> {row.improved}</p>
                    {row.reason && <p><span className="label">Why</span> {row.reason}</p>}
                  </article>
                ))}
              </div>
            </div>
          )}

          {editResult.level_feedback && (
            <div className="writing-tool-block">
              <span className="label">Language Level Feedback</span>
              <p className="writing-level-feedback">{editResult.level_feedback}</p>
            </div>
          )}

          {editResult.better_alternative && (
            <div className="writing-tool-block">
              <span className="label">Better Alternative</span>
              <p className="writing-original-highlight">{editResult.better_alternative}</p>
            </div>
          )}

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCompareRevision}
            disabled={!aiText.trim() || compareLoading}
          >
            {compareLoading ? 'Comparing…' : 'Compare with AI version'}
          </button>

          {showCompare && (
            <div className="writing-compare-section">
              <TextDiffView aiText={aiText} learnerText={learnerEdited} />

              {compareResult && (
                <div className="writing-revision-compare card">
                  {compareResult.improvement_summary && (
                    <p><strong>Summary:</strong> {compareResult.improvement_summary}</p>
                  )}
                  {compareResult.improvements?.length > 0 && (
                    <div className="writing-tool-block">
                      <span className="label">Improvements in your revision</span>
                      <ul className="writing-edit-list">
                        {compareResult.improvements.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {compareResult.remaining_issues?.length > 0 && (
                    <div className="writing-tool-block">
                      <span className="label">Still to work on</span>
                      <ul className="writing-edit-list">
                        {compareResult.remaining_issues.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {compareResult.score_change_note && (
                    <p className="muted">{compareResult.score_change_note}</p>
                  )}
                </div>
              )}

              <div className="writing-side-by-side">
                <div>
                  <span className="label">AI corrected (reference)</span>
                  <p>{aiText}</p>
                </div>
                <div>
                  <span className="label">Your version</span>
                  <p>{learnerEdited}</p>
                </div>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
