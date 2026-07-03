import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import CollapsibleNativeNote from '../components/CollapsibleNativeNote'
import DeveloperProviderSelect from '../components/DeveloperProviderSelect'
import ListeningGeneratePracticeTab from '../components/ListeningGeneratePracticeTab'
import ListeningQuizTab from '../components/ListeningQuizTab'
import ListeningSummaryStrip from '../components/ListeningSummaryStrip'
import { useDeveloperMode } from '../hooks/useDeveloperMode'
import { apiRequest, getPrompts, postForm } from '../api/client'
import { DEFAULT_AI_PROVIDER, DEFAULT_STT_PROVIDER, pickDefaultProvider } from '../utils/defaultProvider'

const TABS = [
  { id: 'generate', label: 'Generate Practice' },
  { id: 'quiz', label: 'Listening Quiz' },
  { id: 'analyze', label: 'Analyze Transcript' },
]

const VALID_TABS = new Set(TABS.map((entry) => entry.id))

function resolveTab(rawTab) {
  if (!rawTab || !VALID_TABS.has(rawTab)) {
    return 'generate'
  }
  return rawTab
}

export default function Listening() {
  const devMode = useDeveloperMode()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = resolveTab(searchParams.get('tab') || searchParams.get('mode'))
  const [tab, setTab] = useState(initialTab)
  const [transcript, setTranscript] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)
  const [transcriptionProvider, setTranscriptionProvider] = useState(DEFAULT_STT_PROVIDER)
  const [prompts, setPrompts] = useState([])
  const [addedWords, setAddedWords] = useState({})
  const [audioFile, setAudioFile] = useState(null)
  const [summaryRefresh, setSummaryRefresh] = useState(0)
  const [summaryMeta, setSummaryMeta] = useState({
    currentLesson: '—',
    level: 'B1',
    listeningType: 'academic_mini_lecture',
  })
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
    const rawTab = searchParams.get('tab') || searchParams.get('mode')
    const resolved = resolveTab(rawTab)

    if (rawTab !== resolved) {
      const nextParams = new URLSearchParams(searchParams)
      nextParams.set('tab', resolved)
      nextParams.delete('mode')
      setSearchParams(nextParams, { replace: true })
    }

    setTab(resolved)
  }, [searchParams, setSearchParams])

  const handleSessionChange = useCallback((_session, meta) => {
    setSummaryMeta({
      currentLesson: meta?.contextNote || '—',
      level: meta?.level || 'B1',
      listeningType: meta?.listeningType || 'academic_mini_lecture',
    })
  }, [])

  function handleTabChange(nextTab) {
    setTab(nextTab)
    setError('')
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('tab', nextTab)
    nextParams.delete('mode')
    setSearchParams(nextParams, { replace: true })
  }

  async function handleAnalyze(event) {
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
      setError(err.message || 'Could not analyze this transcript. Please try again.')
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
    <div className="listening-page listening-page-compact">
      <h1>Listening Coach</h1>

      <ListeningSummaryStrip
        refreshKey={summaryRefresh}
        currentLesson={summaryMeta.currentLesson}
        level={summaryMeta.level}
        listeningType={summaryMeta.listeningType}
      />

      <div className="tabs listening-tabs">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className={tab === entry.id ? 'tab tab-active' : 'tab'}
            onClick={() => handleTabChange(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </div>

      {devMode && (
        <div className="selectors">
          <DeveloperProviderSelect
            label="AI provider (dev)"
            value={provider}
            options={[...new Set(prompts.map((prompt) => prompt.provider))]}
            onChange={setProvider}
            disabled={loading}
          />
          <DeveloperProviderSelect
            label="STT provider (dev)"
            value={transcriptionProvider}
            options={['openai_whisper', 'local_whisper']}
            onChange={setTranscriptionProvider}
            disabled={loading}
          />
        </div>
      )}

      {error && <p className="error listening-error">{error}</p>}

      {tab === 'generate' && (
        <ListeningGeneratePracticeTab
          provider={devMode ? provider : undefined}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
          onSessionChange={handleSessionChange}
          onProgressSaved={() => setSummaryRefresh((value) => value + 1)}
          tabVariant="generate"
        />
      )}

      {tab === 'quiz' && (
        <ListeningQuizTab
          provider={devMode ? provider : undefined}
          transcriptionProvider={transcriptionProvider}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
        />
      )}

      {tab === 'analyze' && (
        <div className="listening-analyze-panel">
          {!analysis ? (
            <form onSubmit={handleAnalyze} className="card card-compact">
              <p className="muted listening-helper">
                Paste a transcript or upload audio to get vocabulary, comprehension prompts, and shadowing sentences.
              </p>
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
              <textarea
                value={transcript}
                onChange={(e) => {
                  setTranscript(e.target.value)
                  if (e.target.value) setAudioFile(null)
                }}
                placeholder="Paste a transcript here, or upload audio above..."
                rows={10}
                disabled={loading || !!audioFile}
              />
              <button type="submit" disabled={loading || (!transcript.trim() && !audioFile)}>
                {loading ? 'Analyzing…' : 'Analyze transcript'}
              </button>
            </form>
          ) : (
            <div className="reading-results">
              {analysis.intro && (
                <section className="reading-section card">
                  <h2>Coach notes</h2>
                  <p>{analysis.intro}</p>
                </section>
              )}

              <section className="reading-section card">
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

              <section className="reading-section card">
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

              <section className="reading-section card">
                <h2>Shadowing sentences</h2>
                <ol>
                  {analysis.shadowing_sentences.map((sentence) => (
                    <li key={sentence}>{sentence}</li>
                  ))}
                </ol>
              </section>

              <button type="button" className="btn btn-secondary" onClick={() => setAnalysis(null)}>
                Analyze another transcript
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
