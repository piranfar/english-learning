import { useCallback, useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '../../api/client'
import { buildParagraphBuilderMessage } from '../../data/writingTools'
import { loadToolState, saveToolState, TOOL_STORAGE_KEYS } from '../../services/writingToolsStorage'
import { parseMarkdownSections } from '../../utils/writingToolsParser'
import AssistantMessage from '../AssistantMessage'
import ExamTextArea from '../ExamTextArea'
import WritingToolProvider from './WritingToolProvider'

const SECTIONS = [
  'Generated paragraph',
  'Better version',
  'Structure explanation',
  'Useful connectors',
  'Next practice suggestion',
]

const EMPTY_FIELDS = {
  topic: '',
  reason: '',
  example: '',
  explanation: '',
  conclusion: '',
}

export default function WritingParagraphBuilderTab({ provider, onProviderChange, prompts }) {
  const [fields, setFields] = useState(EMPTY_FIELDS)
  const [sections, setSections] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const saveTimer = useRef(null)

  useEffect(() => {
    const saved = loadToolState(TOOL_STORAGE_KEYS.paragraphBuilder)
    if (!saved) return
    setFields({ ...EMPTY_FIELDS, ...(saved.fields || {}) })
    setSections(saved.sections || {})
  }, [])

  const persist = useCallback(
    (overrides = {}) => {
      saveToolState(TOOL_STORAGE_KEYS.paragraphBuilder, {
        fields,
        sections,
        ...overrides,
      })
    },
    [fields, sections],
  )

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => persist(), 400)
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current)
    }
  }, [persist])

  function updateField(key, value) {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  async function handleBuild(event) {
    event.preventDefault()
    if (!fields.topic.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const data = await sendChatMessage({
        message: buildParagraphBuilderMessage(fields),
        track: 'paragraph_builder_coach',
        provider,
      })
      setSections(parseMarkdownSections(data.reply, SECTIONS))
    } catch (err) {
      setError(err.message || 'Paragraph build failed')
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
        track="paragraph_builder_coach"
        onChange={onProviderChange}
      />

      <form onSubmit={handleBuild}>
        <section className="card writing-tool-input">
          <label className="form-field">
            Topic sentence / main idea
            <ExamTextArea
              value={fields.topic}
              onChange={(e) => updateField('topic', e.target.value)}
              rows={2}
              placeholder="Spring is my favorite season."
              disabled={loading}
              examMode
            />
          </label>
          <label className="form-field">
            Reason
            <ExamTextArea
              value={fields.reason}
              onChange={(e) => updateField('reason', e.target.value)}
              rows={2}
              placeholder="The weather becomes warmer."
              disabled={loading}
              examMode
              showExamModeNote={false}
              showAssistantWarning={false}
            />
          </label>
          <label className="form-field">
            Example
            <ExamTextArea
              value={fields.example}
              onChange={(e) => updateField('example', e.target.value)}
              rows={2}
              placeholder="I can walk outside and ride my bike more often."
              disabled={loading}
              examMode
              showExamModeNote={false}
              showAssistantWarning={false}
            />
          </label>
          <label className="form-field">
            Explanation
            <ExamTextArea
              value={fields.explanation}
              onChange={(e) => updateField('explanation', e.target.value)}
              rows={2}
              placeholder="These activities help me feel active and relaxed."
              disabled={loading}
              examMode
              showExamModeNote={false}
              showAssistantWarning={false}
            />
          </label>
          <label className="form-field">
            Conclusion
            <ExamTextArea
              value={fields.conclusion}
              onChange={(e) => updateField('conclusion', e.target.value)}
              rows={2}
              placeholder="Spring gives me energy and motivation."
              disabled={loading}
              examMode
              showExamModeNote={false}
              showAssistantWarning={false}
            />
          </label>

          <button type="submit" className="btn" disabled={loading || !fields.topic.trim()}>
            {loading ? 'Building...' : 'Build paragraph'}
          </button>
        </section>
      </form>

      {error && <p className="error">{error}</p>}

      {hasOutput && (
        <section className="card writing-tool-output">
          <h2>Paragraph builder results</h2>

          {sections['Generated paragraph'] && (
            <div className="writing-tool-block">
              <span className="label">Generated paragraph</span>
              <p className="writing-tool-paragraph">{sections['Generated paragraph']}</p>
            </div>
          )}

          {sections['Better version'] && (
            <div className="writing-tool-block">
              <span className="label">Better version</span>
              <p className="writing-tool-paragraph">{sections['Better version']}</p>
            </div>
          )}

          {sections['Structure explanation'] && (
            <div className="writing-tool-block">
              <span className="label">Structure explanation</span>
              <AssistantMessage content={sections['Structure explanation']} />
            </div>
          )}

          {sections['Useful connectors'] && (
            <div className="writing-tool-block">
              <span className="label">Useful connectors</span>
              <AssistantMessage content={sections['Useful connectors']} />
            </div>
          )}

          {sections['Next practice suggestion'] && (
            <div className="writing-tool-block">
              <span className="label">Next practice suggestion</span>
              <AssistantMessage content={sections['Next practice suggestion']} />
            </div>
          )}
        </section>
      )}
    </div>
  )
}
