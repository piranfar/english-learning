import { useEffect, useMemo, useState } from 'react'
import { getPrompts, sendChatMessage } from '../api/client'
import AssistantMessage from './AssistantMessage'
import DeveloperProviderSelect from './DeveloperProviderSelect'
import WritingCoach from './WritingCoach'
import { DEFAULT_AI_PROVIDER } from '../utils/defaultProvider'

export default function Chat({
  sessionId: externalSessionId = null,
  onSessionIdChange,
  messages: externalMessages = null,
  onMessagesChange,
  lockTrack = null,
  defaultProvider = DEFAULT_AI_PROVIDER,
  provider: externalProvider = null,
  onProviderChange = null,
}) {
  const [input, setInput] = useState('')
  const [internalMessages, setInternalMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [internalSessionId, setInternalSessionId] = useState(null)
  const [prompts, setPrompts] = useState([])
  const [taskType, setTaskType] = useState(lockTrack || 'grammar_coach')
  const [internalProvider, setInternalProvider] = useState(defaultProvider)

  const isControlledProvider = typeof onProviderChange === 'function'
  const provider = isControlledProvider ? externalProvider ?? defaultProvider : internalProvider

  useEffect(() => {
    if (!isControlledProvider) {
      setInternalProvider(defaultProvider)
    }
  }, [defaultProvider, isControlledProvider])

  const isControlledSession = typeof onSessionIdChange === 'function'
  const isControlledMessages = typeof onMessagesChange === 'function'
  const sessionId = isControlledSession ? externalSessionId : internalSessionId
  const messages = isControlledMessages ? externalMessages || [] : internalMessages

  const setSessionId = (value) => {
    if (isControlledSession) {
      onSessionIdChange(value)
    } else {
      setInternalSessionId(value)
    }
  }

  const setMessages = (updater) => {
    const next = typeof updater === 'function' ? updater(messages) : updater
    if (isControlledMessages) {
      onMessagesChange(next)
    } else {
      setInternalMessages(next)
    }
  }

  const setProvider = (value) => {
    if (isControlledProvider) {
      onProviderChange(value)
    } else {
      setInternalProvider(value)
    }
  }

  const isWritingMode = taskType === 'writing_coach'

  useEffect(() => {
    async function loadPrompts() {
      try {
        const data = await getPrompts()
        setPrompts(data.prompts)
        const lessonTypes = [
          ...new Set(data.prompts.map((prompt) => prompt.task_type)),
        ].filter(
          (type) =>
            ![
              'vocab_builder',
              'reading_coach',
              'listening_coach',
              'speaking_coach',
              'toefl_speaking',
              'toefl_writing',
            ].includes(type),
        )
        if (lockTrack) {
          setTaskType(lockTrack)
        } else if (lessonTypes.length > 0) {
          setTaskType(
            lessonTypes.includes('grammar_coach') ? 'grammar_coach' : lessonTypes[0],
          )
        }
      } catch (err) {
        setError(err.message || 'Failed to load prompts')
      }
    }

    loadPrompts()
  }, [lockTrack])

  const lessonTaskTypes = useMemo(
    () =>
      [...new Set(prompts.map((prompt) => prompt.task_type))].filter(
        (type) =>
          ![
            'vocab_builder',
            'reading_coach',
            'listening_coach',
            'speaking_coach',
            'toefl_speaking',
            'toefl_writing',
          ].includes(type),
      ),
    [prompts],
  )

  const providersForTask = useMemo(
    () =>
      prompts
        .filter((prompt) => prompt.task_type === taskType)
        .map((prompt) => prompt.provider),
    [prompts, taskType],
  )

  useEffect(() => {
    if (providersForTask.length > 0 && !providersForTask.includes(provider)) {
      setProvider(providersForTask[0])
    }
  }, [providersForTask, provider])

  function handleTaskChange(nextTaskType) {
    if (lockTrack) return
    setTaskType(nextTaskType)
    if (!isControlledSession) setSessionId(null)
    if (!isControlledMessages) setMessages([])
    setError('')
  }

  function handleProviderChange(nextProvider) {
    setProvider(nextProvider)
    if (!isControlledSession && !isControlledMessages) {
      setSessionId(null)
      setMessages([])
    }
    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const payload = {
        message: text,
        track: taskType,
        provider,
      }
      if (sessionId) {
        payload.session_id = sessionId
      }

      const data = await sendChatMessage(payload)
      setSessionId(data.session_id)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          corrections: data.corrections || [],
        },
      ])
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat">
      <div className="selectors">
        <label>
          Track
          <select
            value={taskType}
            onChange={(e) => handleTaskChange(e.target.value)}
            disabled={loading || lessonTaskTypes.length === 0 || Boolean(lockTrack)}
          >
            {lessonTaskTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <DeveloperProviderSelect
          label="AI provider"
          value={provider}
          options={providersForTask}
          onChange={handleProviderChange}
          disabled={loading || providersForTask.length === 0}
        />
      </div>

      {error && <p className="error">{error}</p>}

      {isWritingMode ? (
        <WritingCoach provider={provider} />
      ) : (
        <>
          <div className="message-list">
            {messages.length === 0 && (
              <p style={{ color: '#6b7280', margin: 0 }}>
                Start a grammar lesson from the recommendation above, or type your own question.
              </p>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <AssistantMessage
                    content={msg.content}
                    corrections={msg.corrections}
                  />
                ) : (
                  msg.content
                )}
              </div>
            ))}
          </div>
          {sessionId && (
            <p className="session-meta">Session #{sessionId}</p>
          )}
          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </>
      )}
    </div>
  )
}
