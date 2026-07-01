import { useCallback, useEffect, useRef, useState } from 'react'
import ExamTextArea from '../ExamTextArea'
import { checkParaphrase, generateParaphrasePractice } from '../../api/client'
import {
  PARAPHRASE_DIFFICULTIES,
  PARAPHRASE_LANGUAGE_LEVELS,
  PARAPHRASE_TARGET_LEVELS,
  PARAPHRASE_TEXT_TYPES,
  normalizeLanguageLevel,
  normalizeParaphraseLevel,
  paraphraseResultLabel,
} from '../../data/paraphrasePractice'
import { loadToolState, saveToolState, TOOL_STORAGE_KEYS } from '../../services/writingToolsStorage'
import WritingToolProvider from './WritingToolProvider'

function extractFieldError(err) {
  const message = err?.message || ''
  if (message.includes('original text first')) return 'Please generate or enter original text first.'
  if (message.includes('paraphrase first')) return 'Please write your paraphrase first.'
  return message || 'Something went wrong'
}

export default function WritingParaphraseTab({ provider, onProviderChange, prompts }) {
  const [targetLevel, setTargetLevel] = useState('simple_american_english')
  const [difficulty, setDifficulty] = useState('easy')
  const [textType, setTextType] = useState('one_sentence')
  const [languageLevel, setLanguageLevel] = useState('normal')
  const [useOwnText, setUseOwnText] = useState(false)
  const [originalText, setOriginalText] = useState('')
  const [teachingTip, setTeachingTip] = useState('')
  const [learnerParaphrase, setLearnerParaphrase] = useState('')
  const [checkResult, setCheckResult] = useState(null)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [checkLoading, setCheckLoading] = useState(false)
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')
  const saveTimer = useRef(null)

  useEffect(() => {
    const saved = loadToolState(TOOL_STORAGE_KEYS.paraphrasing)
    if (!saved) return
    setTargetLevel(normalizeParaphraseLevel(saved.targetLevel || saved.level || 'simple_american_english'))
    setDifficulty(saved.difficulty || 'easy')
    setTextType(saved.textType || 'one_sentence')
    setLanguageLevel(normalizeLanguageLevel(saved.languageLevel || 'normal'))
    setUseOwnText(Boolean(saved.useOwnText))
    setOriginalText(saved.originalText || saved.inputText || '')
    setTeachingTip(saved.teachingTip || '')
    setLearnerParaphrase(saved.learnerParaphrase || saved.practiceTry || '')
    setCheckResult(saved.checkResult || null)
  }, [])

  const persist = useCallback(
    (overrides = {}) => {
      saveToolState(TOOL_STORAGE_KEYS.paraphrasing, {
        targetLevel,
        difficulty,
        textType,
        languageLevel,
        useOwnText,
        originalText,
        teachingTip,
        learnerParaphrase,
        checkResult,
        ...overrides,
      })
    },
    [targetLevel, difficulty, textType, languageLevel, useOwnText, originalText, teachingTip, learnerParaphrase, checkResult],
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
    setCheckResult(null)

    try {
      const data = await generateParaphrasePractice({
        targetLevel,
        difficulty,
        textType,
        languageLevel,
        aiProvider: provider,
      })
      setUseOwnText(false)
      setOriginalText(data.original_text || '')
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
    setCheckResult(null)
    if (!originalText) setOriginalText('')
  }

  async function handleCheck(event) {
    event.preventDefault()
    if (checkLoading) return

    if (!originalText.trim()) {
      setValidationError('Please generate or enter original text first.')
      return
    }
    if (!learnerParaphrase.trim()) {
      setValidationError('Please write your paraphrase first.')
      return
    }

    setValidationError('')
    setCheckLoading(true)
    setError('')

    try {
      const data = await checkParaphrase({
        targetLevel,
        languageLevel,
        originalText,
        learnerParaphrase,
        aiProvider: provider,
      })
      setCheckResult(data)
      if (data.notice) setError(data.notice)
    } catch (err) {
      setError(extractFieldError(err))
    } finally {
      setCheckLoading(false)
    }
  }

  const scores = checkResult
    ? [
        { label: 'Overall', value: checkResult.overall_score },
        { label: 'Meaning', value: checkResult.meaning_accuracy_score },
        { label: 'Grammar', value: checkResult.grammar_score },
        { label: 'Naturalness', value: checkResult.naturalness_score },
        { label: 'Vocabulary', value: checkResult.vocabulary_score },
        { label: 'Level Match', value: checkResult.level_match_score },
      ]
    : []

  const resultLabel =
    checkResult?.result_label ||
    (checkResult ? paraphraseResultLabel(checkResult.overall_score) : '')

  return (
    <div className="writing-tool-tab">
      <WritingToolProvider
        provider={provider}
        prompts={prompts}
        tracks={['writing_paraphrase_generate', 'writing_paraphrase_check', 'writing_paraphrase_coach']}
        onChange={onProviderChange}
      />

      <section className="card writing-tool-input">
        <h2 className="writing-section-title">Practice setup</h2>

        <div className="writing-tool-options writing-tool-options--quad">
          <label className="form-field">
            Target level
            <select
              value={targetLevel}
              onChange={(e) => setTargetLevel(e.target.value)}
              disabled={generateLoading || checkLoading}
            >
              {PARAPHRASE_TARGET_LEVELS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Difficulty
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              disabled={generateLoading || checkLoading}
            >
              {PARAPHRASE_DIFFICULTIES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Text type
            <select
              value={textType}
              onChange={(e) => setTextType(e.target.value)}
              disabled={generateLoading || checkLoading}
            >
              {PARAPHRASE_TEXT_TYPES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Language level
            <select
              value={languageLevel}
              onChange={(e) => setLanguageLevel(e.target.value)}
              disabled={generateLoading || checkLoading}
            >
              {PARAPHRASE_LANGUAGE_LEVELS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="writing-prompt-actions">
          <button
            type="button"
            className="btn"
            onClick={handleGenerate}
            disabled={generateLoading || checkLoading}
          >
            {generateLoading ? 'Generating...' : 'Generate practice text'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleUseOwnText}
            disabled={generateLoading || checkLoading}
          >
            Use my own text
          </button>
        </div>
      </section>

      {(originalText || useOwnText) && (
        <section className="card writing-original-card">
          <h2 className="writing-section-title">Original Text</h2>
          {useOwnText ? (
            <label className="form-field">
              <textarea
                value={originalText}
                onChange={(e) => {
                  setOriginalText(e.target.value)
                  setCheckResult(null)
                  if (validationError) setValidationError('')
                }}
                rows={5}
                placeholder="Paste or write a sentence or short paragraph to paraphrase..."
                disabled={generateLoading || checkLoading}
              />
            </label>
          ) : (
            <p className="writing-original-highlight">{originalText}</p>
          )}
          {teachingTip && <p className="muted writing-teaching-tip">Tip: {teachingTip}</p>}
        </section>
      )}

      {originalText.trim() && (
        <form onSubmit={handleCheck}>
          <section className="card writing-tool-input">
            <h2 className="writing-section-title">Your paraphrase</h2>
            <label className="form-field">
              <ExamTextArea
                value={learnerParaphrase}
                onChange={(e) => {
                  setLearnerParaphrase(e.target.value)
                  if (validationError) setValidationError('')
                }}
                rows={5}
                placeholder="Rewrite the original text using your own words..."
                disabled={checkLoading}
                examMode
              />
            </label>

            {validationError && <p className="error">{validationError}</p>}
            {checkLoading && <p className="muted">Checking your paraphrase...</p>}

            <button type="submit" className="btn" disabled={checkLoading || generateLoading}>
              {checkLoading ? 'Checking...' : 'Check my paraphrase'}
            </button>
          </section>
        </form>
      )}

      {error && <p className="error">{error}</p>}

      {checkResult && (
        <section className="card writing-paraphrase-result">
          <h2>Paraphrase Feedback</h2>
          <p className="writing-result-label">{resultLabel}</p>

          <div className="writing-score-grid writing-score-grid--six">
            {scores.map((score) => (
              <div key={score.label} className="writing-score-card">
                <span className="label">{score.label}</span>
                <strong>{score.value ?? 0}/100</strong>
              </div>
            ))}
          </div>

          {checkResult.language_level_feedback && (
            <p className="writing-level-feedback">
              <span className="label">Language level feedback</span>{' '}
              {checkResult.language_level_feedback}
            </p>
          )}

          {checkResult.feedback?.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">Feedback</span>
              <ul className="writing-edit-list">
                {checkResult.feedback.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {checkResult.better_version && (
            <div className="writing-tool-block">
              <span className="label">Better version</span>
              <p className="writing-original-highlight">{checkResult.better_version}</p>
            </div>
          )}

          {checkResult.comparison && (
            <div className="writing-tool-block">
              <span className="label">Comparison</span>
              <div className="writing-comparison-stack">
                <p><span className="label">Original</span> {checkResult.comparison.original}</p>
                <p><span className="label">Learner paraphrase</span> {checkResult.comparison.learner_paraphrase}</p>
                <p><span className="label">Better paraphrase</span> {checkResult.comparison.better_paraphrase}</p>
              </div>
            </div>
          )}

          {checkResult.teaching_notes?.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">Teaching notes</span>
              <ul className="writing-edit-list">
                {checkResult.teaching_notes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
