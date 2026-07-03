import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  getShadowingItems,
  submitShadowingAudio,
  submitShadowingText,
} from '../api/client'
import AudioRecorder from '../components/AudioRecorder'
import ShadowingCompactProgress from '../components/ShadowingCompactProgress'
import ShadowingLatestFeedback from '../components/ShadowingLatestFeedback'
import ShadowingQueue from '../components/ShadowingQueue'
import ShadowingSummaryStrip from '../components/ShadowingSummaryStrip'
import TextToSpeechButton from '../components/TextToSpeechButton'
import CollapsibleNativeNote from '../components/CollapsibleNativeNote'
import {
  SHADOWING_MODES,
  SHADOWING_DIFFICULTIES,
  SENTENCE_SETS,
  filterShadowingItems,
} from '../data/shadowingModes'
import { saveShadowingAttempt } from '../services/shadowingStorage'

const TYPED_NOTICE =
  'Typed backup compares words only. Pronunciation, rhythm, and intonation cannot be scored from text.'

function modeLabel(modeId) {
  return SHADOWING_MODES.find((m) => m.id === modeId)?.label || modeId
}

export default function Shadowing() {
  const location = useLocation()
  const focusItemId = location.state?.focusItemId
  const [allItems, setAllItems] = useState([])
  const [shadowingMode, setShadowingMode] = useState('listen_repeat')
  const [difficulty, setDifficulty] = useState('normal')
  const [sentenceSet, setSentenceSet] = useState('core')
  const [activeIndex, setActiveIndex] = useState(0)
  const [showMeaning, setShowMeaning] = useState(false)
  const [typedInput, setTypedInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [voiceLoading, setVoiceLoading] = useState(false)
  const [typedLoading, setTypedLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [progressKey, setProgressKey] = useState(0)

  const items = useMemo(() => {
    let filtered = filterShadowingItems(allItems, { sentenceSet, difficulty })
    if (focusItemId) {
      const focusItem = allItems.find((item) => item.id === focusItemId)
      if (focusItem && !filtered.some((item) => item.id === focusItemId)) {
        filtered = [focusItem, ...filtered]
      }
    }
    return filtered
  }, [allItems, sentenceSet, difficulty, focusItemId])

  const activeItem = items[activeIndex] || null
  const blindMode = shadowingMode === 'blind'

  useEffect(() => {
    async function load() {
      try {
        const data = await getShadowingItems()
        setAllItems(data.items || [])
      } catch (err) {
        setError(err.message || 'Failed to load shadowing items')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    setActiveIndex(0)
    setResult(null)
    setShowMeaning(false)
  }, [sentenceSet, difficulty, shadowingMode])

  useEffect(() => {
    if (!focusItemId || !items.length) return
    const idx = items.findIndex((item) => item.id === focusItemId)
    if (idx >= 0) {
      setActiveIndex(idx)
    }
  }, [focusItemId, items])

  const persistResult = useCallback(
    (data, inputMode) => {
      saveShadowingAttempt({
        item_id: activeItem?.id,
        shadowing_mode: shadowingMode,
        input_mode: inputMode,
        overall_score: data.overall_score ?? data.similarity_score,
        word_accuracy: data.word_accuracy ?? data.similarity_score,
        fluency: data.fluency,
        pace: data.pace,
        pronunciation_clarity: data.pronunciation_clarity,
        intonation: data.intonation,
      })
      setProgressKey((k) => k + 1)
    },
    [activeItem, shadowingMode],
  )

  async function handleSubmit(transcript, inputMode, durationSeconds) {
    if (!activeItem || !transcript) return
    setError('')
    setResult(null)

    try {
      let data
      if (inputMode === 'voice') {
        setVoiceLoading(true)
        data = await submitShadowingAudio(activeItem.id, transcript, durationSeconds)
      } else {
        setTypedLoading(true)
        data = await submitShadowingText(activeItem.id, transcript)
      }
      setResult(data)
      persistResult(data, inputMode)
    } catch (err) {
      setError(err.message || 'Attempt failed')
    } finally {
      setVoiceLoading(false)
      setTypedLoading(false)
    }
  }

  async function handleVoiceSubmit(audioBlob, durationSeconds) {
    await handleSubmit(audioBlob, 'voice', durationSeconds)
  }

  async function handleTypedSubmit(event) {
    event.preventDefault()
    const text = typedInput.trim()
    if (!text) return
    setTypedInput('')
    await handleSubmit(text, 'typed')
  }

  function handleRefreshSet() {
    setActiveIndex(0)
    setResult(null)
    setShowMeaning(false)
    setProgressKey((k) => k + 1)
  }

  function handleNextSentence() {
    if (activeIndex < items.length - 1) {
      setActiveIndex((i) => i + 1)
      setResult(null)
      setShowMeaning(false)
    }
  }

  function handleRetry() {
    setResult(null)
  }

  if (loading) return <p>Loading shadowing items...</p>
  if (error && !items.length) return <p className="error">{error}</p>

  return (
    <div className="page shadowing-page shadowing-compact">
      <header className="shadowing-header-compact">
        <h1>Shadowing Coach</h1>
      </header>

      <ShadowingSummaryStrip refreshKey={progressKey} shadowingMode={modeLabel(shadowingMode)} />

      <section className="card shadowing-controls-row">
        <label className="form-field">
          Shadowing mode
          <select value={shadowingMode} onChange={(e) => setShadowingMode(e.target.value)}>
            {SHADOWING_MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          Difficulty
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {SHADOWING_DIFFICULTIES.map((d) => (
              <option key={d.id} value={d.id}>{d.label}</option>
            ))}
          </select>
        </label>
        <label className="form-field">
          Sentence set
          <select value={sentenceSet} onChange={(e) => setSentenceSet(e.target.value)}>
            {SENTENCE_SETS.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-secondary" onClick={handleRefreshSet}>
          Refresh set
        </button>
      </section>

      {items.length === 0 ? (
        <p className="muted">No shadowing sentences yet. Add items in Django admin.</p>
      ) : (
        <div className="shadowing-workspace-layout">
          <div className="shadowing-workspace-main">
            {activeItem && (
              <section className="card shadowing-active-sentence">
                <div className="shadowing-active-head">
                  <h2>Sentence {activeIndex + 1} of {items.length}</h2>
                  <span className="tag">{modeLabel(shadowingMode)}</span>
                </div>

                {!blindMode && (
                  <p className="shadowing-target-text">{activeItem.target_text}</p>
                )}
                {blindMode && (
                  <p className="muted">Target sentence hidden — listen or recall, then speak.</p>
                )}

                <div className="shadowing-active-actions">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowMeaning((v) => !v)}
                  >
                    {showMeaning ? 'Hide meaning' : 'Show meaning'}
                  </button>
                  {!blindMode && (
                    <>
                      <TextToSpeechButton text={activeItem.target_text} label="Normal audio" size="sm" />
                      <TextToSpeechButton
                        text={activeItem.target_text}
                        label="Slow audio"
                        size="sm"
                        rate={0.75}
                      />
                    </>
                  )}
                </div>

                {showMeaning && activeItem.persian_meaning && (
                  <CollapsibleNativeNote note={activeItem.persian_meaning} />
                )}

                <div className="shadowing-recorder-inline">
                  <AudioRecorder
                    onSubmit={handleVoiceSubmit}
                    loading={voiceLoading}
                    submitLabel="Submit"
                    disabled={typedLoading}
                    passDuration
                  />
                </div>

                <div className="shadowing-inline-actions">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleRetry}
                    disabled={voiceLoading || typedLoading}
                  >
                    Retry
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={handleNextSentence}
                    disabled={activeIndex >= items.length - 1}
                  >
                    Next sentence
                  </button>
                </div>

                <details className="shadowing-typed-backup">
                  <summary>Typed backup if microphone fails</summary>
                  <p className="muted">{TYPED_NOTICE}</p>
                  <form onSubmit={handleTypedSubmit}>
                    <input
                      type="text"
                      value={typedInput}
                      onChange={(e) => setTypedInput(e.target.value)}
                      placeholder="Type what you said..."
                      disabled={typedLoading || voiceLoading}
                    />
                    <button type="submit" disabled={typedLoading || voiceLoading || !typedInput.trim()}>
                      Submit typed attempt
                    </button>
                  </form>
                </details>
              </section>
            )}

            {error && <p className="error">{error}</p>}
            {result && (
              <ShadowingLatestFeedback result={result} onRetry={handleRetry} />
            )}
          </div>

          <div className="shadowing-workspace-side">
            <ShadowingCompactProgress latestResult={result} refreshKey={progressKey} />
            <ShadowingQueue
              items={items}
              activeIndex={activeIndex}
              onSelect={setActiveIndex}
              refreshKey={progressKey}
            />
          </div>
        </div>
      )}
    </div>
  )
}
