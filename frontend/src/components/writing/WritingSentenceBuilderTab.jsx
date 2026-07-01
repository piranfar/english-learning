import { useCallback, useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '../../api/client'
import { buildSentenceBuilderMessage } from '../../data/writingTools'
import { loadToolState, saveToolState, TOOL_STORAGE_KEYS } from '../../services/writingToolsStorage'
import { parseMarkdownSections } from '../../utils/writingToolsParser'
import AssistantMessage from '../AssistantMessage'
import ExamTextArea from '../ExamTextArea'
import WritingToolProvider from './WritingToolProvider'

const SECTIONS = [
  'Basic sentence',
  'Corrected sentence',
  'Expanded sentence',
  'Stronger sentence',
  'Explanation',
  'Pattern to reuse',
]

export default function WritingSentenceBuilderTab({ provider, onProviderChange, prompts }) {
  const [inputSentence, setInputSentence] = useState('')
  const [sections, setSections] = useState({})
  const [corrections, setCorrections] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const saveTimer = useRef(null)

  useEffect(() => {
    const saved = loadToolState(TOOL_STORAGE_KEYS.sentenceBuilder)
    if (!saved) return
    setInputSentence(saved.inputSentence || '')
    setSections(saved.sections || {})
    setCorrections(saved.corrections || [])
  }, [])

  const persist = useCallback(
    (overrides = {}) => {
      saveToolState(TOOL_STORAGE_KEYS.sentenceBuilder, {
        inputSentence,
        sections,
        corrections,
        ...overrides,
      })
    },
    [inputSentence, sections, corrections],
  )

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => persist(), 400)
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current)
    }
  }, [persist])

  async function handleBuild(event) {
    event.preventDefault()
    if (!inputSentence.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const data = await sendChatMessage({
        message: buildSentenceBuilderMessage({ sentence: inputSentence }),
        track: 'sentence_builder_coach',
        provider,
      })
      setSections(parseMarkdownSections(data.reply, SECTIONS))
      setCorrections(data.corrections || [])
    } catch (err) {
      setError(err.message || 'Sentence build failed')
    } finally {
      setLoading(false)
    }
  }

  const hasOutput = Object.values(sections).some((value) => value?.trim())

  return (
    <div className="writing-tool-tab">
      <WritingToolProvider
        provider={provider}
        prompts={prompts}
        track="sentence_builder_coach"
        onChange={onProviderChange}
      />

      <form onSubmit={handleBuild}>
        <section className="card writing-tool-input">
          <label className="form-field">
            Write a basic sentence
            <ExamTextArea
              value={inputSentence}
              onChange={(e) => setInputSentence(e.target.value)}
              rows={3}
              placeholder="Spring is good."
              disabled={loading}
              examMode
            />
          </label>

          <button type="submit" className="btn" disabled={loading || !inputSentence.trim()}>
            {loading ? 'Building...' : 'Build this sentence'}
          </button>
        </section>
      </form>

      {error && <p className="error">{error}</p>}

      {hasOutput && (
        <section className="card writing-tool-output">
          <h2>Sentence builder results</h2>

          {sections['Basic sentence'] && (
            <div className="writing-tool-block">
              <span className="label">Basic sentence</span>
              <p>{sections['Basic sentence']}</p>
            </div>
          )}

          {sections['Corrected sentence'] && (
            <div className="writing-tool-block">
              <span className="label">Corrected sentence</span>
              <p>{sections['Corrected sentence']}</p>
            </div>
          )}

          {sections['Expanded sentence'] && (
            <div className="writing-tool-block">
              <span className="label">Expanded sentence</span>
              <p>{sections['Expanded sentence']}</p>
            </div>
          )}

          {sections['Stronger sentence'] && (
            <div className="writing-tool-block">
              <span className="label">Stronger sentence</span>
              <p>{sections['Stronger sentence']}</p>
            </div>
          )}

          {sections.Explanation && (
            <div className="writing-tool-block">
              <span className="label">Explanation</span>
              <AssistantMessage content={sections.Explanation} />
            </div>
          )}

          {sections['Pattern to reuse'] && (
            <div className="writing-tool-block">
              <span className="label">Pattern to reuse</span>
              <AssistantMessage content={sections['Pattern to reuse']} />
            </div>
          )}

          {corrections.length > 0 && (
            <div className="writing-tool-block">
              <span className="label">Important corrections</span>
              <div className="writing-correction-table">
                {corrections.map((row, index) => (
                  <article key={index} className="writing-correction-row">
                    <p><span className="label">Original</span> {row.original}</p>
                    <p><span className="label">Corrected</span> {row.corrected}</p>
                    {row.reason && <p><span className="label">Why</span> {row.reason}</p>}
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
