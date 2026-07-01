import { useEffect, useRef, useState } from 'react'

const SPEED_OPTIONS = [
  { value: 0.75, label: 'Slow' },
  { value: 1, label: 'Normal' },
  { value: 1.15, label: 'TOEFL-like' },
]

const RATE_BY_SPEED = { slow: 0.75, normal: 1, toefl_like: 1.15 }

export default function ListeningPlayer({ text, defaultSpeed = 'normal' }) {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const [playing, setPlaying] = useState(false)
  const [paused, setPaused] = useState(false)
  const [rate, setRate] = useState(RATE_BY_SPEED[defaultSpeed] ?? 1)
  const utteranceRef = useRef(null)

  useEffect(() => {
    if (!supported) return undefined
    return () => {
      window.speechSynthesis.cancel()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handlePlay() {
    if (!supported || !text) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US'
    utterance.rate = rate
    utterance.onend = () => {
      setPlaying(false)
      setPaused(false)
    }
    utterance.onerror = () => {
      setPlaying(false)
      setPaused(false)
    }
    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
    setPlaying(true)
    setPaused(false)
  }

  function handlePauseResume() {
    if (!supported) return
    if (paused) {
      window.speechSynthesis.resume()
      setPaused(false)
    } else {
      window.speechSynthesis.pause()
      setPaused(true)
    }
  }

  function handleStop() {
    if (!supported) return
    window.speechSynthesis.cancel()
    setPlaying(false)
    setPaused(false)
  }

  if (!supported) {
    return (
      <p className="muted">
        Audio playback is not supported in this browser. Try Chrome, Edge, or Safari.
      </p>
    )
  }

  return (
    <div className="listening-player">
      <div className="listening-player-controls">
        <button type="button" className="btn btn-sm" onClick={handlePlay} disabled={!text}>
          {playing ? 'Replay' : 'Play audio'}
        </button>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={handlePauseResume}
          disabled={!playing}
        >
          {paused ? 'Resume' : 'Pause'}
        </button>
        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={handleStop}
          disabled={!playing}
        >
          Stop
        </button>
        <label className="listening-player-speed form-field">
          Speed
          <select value={rate} onChange={(event) => setRate(Number(event.target.value))}>
            {SPEED_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="muted listening-player-note">
        Uses your browser&apos;s built-in text-to-speech voice. Change speed before pressing Play.
      </p>
    </div>
  )
}
