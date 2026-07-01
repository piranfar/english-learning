import { useCallback, useEffect, useRef, useState } from 'react'

function formatTimer(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function WritingTimer({
  totalSeconds = 600,
  onTimeUp,
  onStateChange,
  initialRemaining = null,
  initialRunning = false,
  label = 'Writing timer',
}) {
  const [remaining, setRemaining] = useState(initialRemaining ?? totalSeconds)
  const [running, setRunning] = useState(initialRunning)
  const [finished, setFinished] = useState(false)
  const intervalRef = useRef(null)

  useEffect(() => {
    setRemaining(initialRemaining ?? totalSeconds)
    setFinished(false)
  }, [totalSeconds, initialRemaining])

  const clearIntervalRef = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => {
    onStateChange?.({ remaining, running, finished })
  }, [remaining, running, finished, onStateChange])

  useEffect(() => {
    if (!running || finished) {
      clearIntervalRef()
      return undefined
    }

    intervalRef.current = setInterval(() => {
      setRemaining((value) => {
        if (value <= 1) {
          clearIntervalRef()
          setRunning(false)
          setFinished(true)
          onTimeUp?.()
          return 0
        }
        return value - 1
      })
    }, 1000)

    return clearIntervalRef
  }, [running, finished, clearIntervalRef, onTimeUp])

  useEffect(() => () => clearIntervalRef(), [clearIntervalRef])

  const progress = totalSeconds > 0 ? ((totalSeconds - remaining) / totalSeconds) * 100 : 0

  return (
    <div className="writing-timer">
      <div className="writing-timer-header">
        <span className="label">{label}</span>
        <span className="writing-timer-count">{formatTimer(remaining)}</span>
      </div>
      <div className="writing-timer-bar" aria-hidden="true">
        <div className="writing-timer-fill" style={{ width: `${progress}%` }} />
      </div>
      {finished && (
        <p className="writing-timer-done muted">
          Time is finished. You can still continue writing or submit now.
        </p>
      )}
      <div className="writing-timer-actions">
        {!running && !finished && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRunning(true)}>
            Start timer
          </button>
        )}
        {running && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRunning(false)}>
            Pause
          </button>
        )}
        {!running && !finished && remaining < totalSeconds && remaining > 0 && (
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setRunning(true)}>
            Resume
          </button>
        )}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => {
            clearIntervalRef()
            setRunning(false)
            setFinished(false)
            setRemaining(totalSeconds)
          }}
        >
          Reset
        </button>
      </div>
    </div>
  )
}
