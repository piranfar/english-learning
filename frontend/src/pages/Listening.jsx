import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import CollapsibleNativeNote from '../components/CollapsibleNativeNote'
import DeveloperProviderSelect from '../components/DeveloperProviderSelect'
import ListeningGeneratePracticeTab from '../components/ListeningGeneratePracticeTab'
import ListeningQuizTab from '../components/ListeningQuizTab'
import { useDeveloperMode } from '../hooks/useDeveloperMode'
import { apiRequest, getPrompts, postForm } from '../api/client'
import { DEFAULT_AI_PROVIDER, DEFAULT_STT_PROVIDER, pickDefaultProvider } from '../utils/defaultProvider'

const MODES = [
  { id: 'generate', label: 'Generate practice' },
  { id: 'quiz', label: 'Listening quiz' },
  { id: 'analyze', label: 'Analyze transcript' },
]

export default function Listening() {
  const devMode = useDeveloperMode()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialMode = searchParams.get('mode') || 'generate'
  const [mode, setMode] = useState(MODES.some((entry) => entry.id === initialMode) ? initialMode : 'generate')
  const [transcript, setTranscript] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)
  const [transcriptionProvider, setTranscriptionProvider] = useState(DEFAULT_STT_PROVIDER)
  const [prompts, setPrompts] = useState([])
  const [addedWords, setAddedWords] = useState({})
  const [audioFile, setAudioFile] = useState(null)
  const fileInputRef = useRef(null)

  const isListeningTaskType = (prompt) =>
    ['listening_coach', 'listening_quiz', 'listening_practice_generate'].includes(prompt.task_type)

  useEffect(() => {
    async function loadPrompts() {
      try {
        const data = await getPrompts()
        const listeningPrompts = data.prompts.filter(isListeningTaskType)
        setPrompts(listeningPrompts)
        setProvider(pickDefaultProvider(listeningPrompts, isListeningTaskType))
      } catch {
        // keep default
      }
    }
    loadPrompts()
  }, [])

  useEffect(() => {
    const paramMode = searchParams.get('mode')
    if (paramMode && MODES.some((entry) => entry.id === paramMode)) {
      setMode(paramMode)
    }
  }, [searchParams])

  function handleModeChange(nextMode) {
    setMode(nextMode)
    setError('')
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('mode', nextMode)
    setSearchParams(nextParams, { replace: true })
  }

  async function handleGenerate(event) {
    event.preventDefault()
    const text = transcript.trim()
    if ((!text && !audioFile) || loading) return

    setLoading(true)
    setError('')
    setAnalysis(null)
    setAddedWords({})

    try {
      let data
      if (audioFile) {
        const form = new FormData()
        form.append('audio', audioFile)
        form.append('provider', provider)
        form.append('transcription_provider', transcriptionProvider)
        data = await postForm('/listening/generate/', form)
      } else {
        data = await apiRequest('/listening/generate/', {
          method: 'POST',
          json: { transcript: text, provider },
        })
      }

      if (data.transcript) {
        setTranscript(data.transcript)
      }
      setAnalysis(data.analysis)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  function handleFileChange(event) {
    const file = event.target.files?.[0]
    setAudioFile(file || null)
    if (file) {
      setTranscript('')
    }
  }

  async function handleAddWord(entry) {
    const key = entry.word
    if (addedWords[key]) return

    try {
      await apiRequest('/vocab/', {
        method: 'POST',
        json: {
          word: entry.word,
          definition: entry.definition,
          persian_meaning: entry.persian,
        },
      })
      setAddedWords((prev) => ({ ...prev, [key]: true }))
    } catch (err) {
      setError(err.message || 'Failed to add word')
    }
  }

  return (
    <div className="reading-page">
      <h1>Listening Coach</h1>
      <p className="page-lead">
        Generate original listening practice for your level and goal, take a listening quiz with a
        hidden transcript, or analyze your own transcript.
      </p>

      <div className="tabs">
        {MODES.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className={mode === entry.id ? 'tab tab-active' : 'tab'}
            onClick={() => handleModeChange(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </div>

      {devMode && (
        <div className="selectors">
          <DeveloperProviderSelect
            label="AI provider"
            value={provider}
            options={[...new Set(prompts.map((prompt) => prompt.provider))]}
            onChange={setProvider}
            disabled={loading}
          />
          <DeveloperProviderSelect
            label="STT provider"
            value={transcriptionProvider}
            options={['openai_whisper', 'local_whisper']}
            onChange={setTranscriptionProvider}
            disabled={loading}
          />
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {mode === 'generate' && (
        <ListeningGeneratePracticeTab
          provider={provider}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
        />
      )}

      {mode === 'quiz' && (
        <ListeningQuizTab
          provider={provider}
          transcriptionProvider={transcriptionProvider}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
        />
      )}

      {mode === 'analyze' && (
        <>
          <div className="audio-upload">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
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

          <form onSubmit={handleGenerate}>
            <textarea
              value={transcript}
              onChange={(e) => {
                setTranscript(e.target.value)
                if (e.target.value) setAudioFile(null)
              }}
              placeholder="Paste a transcript here, or upload audio above..."
              rows={12}
              disabled={loading || !!audioFile}
            />
            <button type="submit" disabled={loading || (!transcript.trim() && !audioFile)}>
              {loading ? 'Generating...' : 'Analyze'}
            </button>
          </form>

          {analysis && (
            <div className="reading-results">
              {analysis.intro && (
                <section className="reading-section">
                  <h2>Coach notes</h2>
                  <p>{analysis.intro}</p>
                </section>
              )}

              <section className="reading-section">
                <h2>Comprehension quiz</h2>
                <ol>
                  {analysis.comprehension_questions.map((item, index) => (
                    <li key={index}>
                      <p>{item.question}</p>
                      {item.answer_hint && (
                        <p className="plan-meta">Hint: {item.answer_hint}</p>
                      )}
                    </li>
                  ))}
                </ol>
              </section>

              <section className="reading-section">
                <h2>Vocabulary</h2>
                <div className="vocab-list">
                  {analysis.vocabulary.map((entry) => (
                    <article key={entry.word} className="vocab-entry">
                      <div>
                        <strong>{entry.word}</strong>
                        <p>{entry.definition}</p>
                        <CollapsibleNativeNote note={entry.persian} />
                      </div>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => handleAddWord(entry)}
                        disabled={addedWords[entry.word]}
                      >
                        {addedWords[entry.word] ? 'Added' : 'Add to vocab'}
                      </button>
                    </article>
                  ))}
                </div>
              </section>

              <section className="reading-section">
                <h2>Shadowing sentences</h2>
                <ol>
                  {analysis.shadowing_sentences.map((sentence) => (
                    <li key={sentence}>{sentence}</li>
                  ))}
                </ol>
              </section>

              <section className="reading-section">
                <h2>Key phrases</h2>
                {analysis.key_phrases.map((item) => (
                  <article key={item.phrase} className="grammar-point">
                    <p><strong>{item.phrase}</strong> — {item.meaning}</p>
                    <CollapsibleNativeNote note={item.persian} />
                  </article>
                ))}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  )
}
