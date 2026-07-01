import { useCallback, useEffect, useRef, useState } from 'react'

function formatTimer(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function SpeakingTimer({
  prepSeconds = 20,
  speakSeconds = 60,
  active = false,
  onPrepComplete,
  onSpeakComplete,
  onReset,
}) {
  const [phase, setPhase] = useState('idle')
  const [remaining, setRemaining] = useState(0)
  const timerRef = useRef(null)

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const startPrep = useCallback(() => {
    clearTimer()
    setPhase('prep')
    setRemaining(prepSeconds)
    timerRef.current = setInterval(() => {
      setRemaining((value) => {
        if (value <= 1) {
          clearTimer()
          setPhase('speak')
          setRemaining(speakSeconds)
          onPrepComplete?.()
          timerRef.current = setInterval(() => {
            setRemaining((speakValue) => {
              if (speakValue <= 1) {
                clearTimer()
                setPhase('done')
                onSpeakComplete?.()
                return 0
              }
              return speakValue - 1
            })
          }, 1000)
          return 0
        }
        return value - 1
      })
    }, 1000)
  }, [prepSeconds, speakSeconds, clearTimer, onPrepComplete, onSpeakComplete])

  useEffect(() => {
    if (!active) {
      clearTimer()
      setPhase('idle')
      setRemaining(0)
    }
  }, [active, clearTimer])

  useEffect(() => () => clearTimer(), [clearTimer])

  const total = phase === 'prep' ? prepSeconds : phase === 'speak' ? speakSeconds : 0
  const progress = total > 0 ? ((total - remaining) / total) * 100 : 0

  if (!active && phase === 'idle') {
    return (
      <div className="speaking-timer">
        <button type="button" className="btn btn-secondary btn-sm" onClick={startPrep}>
          Start preparation timer
        </button>
      </div>
    )
  }

  return (
    <div className="speaking-timer">
      <div className="speaking-timer-header">
        <span className="label">
          {phase === 'prep' && 'Preparation'}
          {phase === 'speak' && 'Speaking'}
          {phase === 'done' && 'Time complete'}
          {phase === 'idle' && 'Timer'}
        </span>
        <span className="speaking-timer-count">{formatTimer(remaining)}</span>
      </div>
      <div className="speaking-timer-bar" aria-hidden="true">
        <div className="speaking-timer-fill" style={{ width: `${progress}%` }} />
      </div>
      <div className="speaking-timer-actions">
        {phase === 'prep' && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              clearTimer()
              setPhase('speak')
              setRemaining(speakSeconds)
              onPrepComplete?.()
            }}
          >
            Skip to speaking
          </button>
        )}
        {phase === 'speak' && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              clearTimer()
              setPhase('done')
              onSpeakComplete?.()
            }}
          >
            Skip timer
          </button>
        )}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => {
            clearTimer()
            setPhase('idle')
            setRemaining(0)
            onReset?.()
          }}
        >
          Reset timer
        </button>
      </div>
    </div>
  )
}
