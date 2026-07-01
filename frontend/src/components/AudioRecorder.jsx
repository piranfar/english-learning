import { useEffect, useRef, useState } from 'react'

const MIC_DENIED_MESSAGE =
  'Microphone permission was denied. Please allow microphone access in your browser.'

function formatTimer(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function AudioRecorder({
  onSubmit,
  loading = false,
  submitLabel = 'Submit recording',
  disabled = false,
  passDuration = false,
}) {
  const [recording, setRecording] = useState(false)
  const [recordedBlob, setRecordedBlob] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [timer, setTimer] = useState(0)
  const [error, setError] = useState('')
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const timerRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
      streamRef.current?.getTracks().forEach((track) => track.stop())
    }
  }, [previewUrl])

  function clearPreview() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl('')
    setRecordedBlob(null)
  }

  async function startRecording() {
    setError('')
    clearPreview()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        streamRef.current = null
        setRecording(false)
        if (timerRef.current) {
          clearInterval(timerRef.current)
          timerRef.current = null
        }

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        if (!blob.size) {
          setError('No audio captured. Try recording again.')
          return
        }
        setRecordedBlob(blob)
        setPreviewUrl(URL.createObjectURL(blob))
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setRecording(true)
      setTimer(0)
      timerRef.current = setInterval(() => {
        setTimer((value) => value + 1)
      }, 1000)
    } catch (err) {
      const name = err?.name || ''
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setError(MIC_DENIED_MESSAGE)
      } else {
        setError(err.message || MIC_DENIED_MESSAGE)
      }
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  async function handleSubmit() {
    if (!recordedBlob || loading || disabled) return
    setError('')
    try {
      if (passDuration) {
        await onSubmit(recordedBlob, timer)
      } else {
        await onSubmit(recordedBlob)
      }
    } catch (err) {
      setError(err.message || 'Upload failed')
    }
  }

  return (
    <div className="audio-recorder">
      <div className="voice-controls">
        {!recording ? (
          <button
            type="button"
            className="record-btn"
            onClick={startRecording}
            disabled={loading || disabled}
          >
            Record
          </button>
        ) : (
          <button type="button" className="record-btn recording" onClick={stopRecording}>
            Stop
          </button>
        )}
        {recording && <span className="recorder-timer">{formatTimer(timer)}</span>}
      </div>

      {previewUrl && !recording && (
        <div className="recorder-preview">
          <audio controls src={previewUrl}>
            Your browser does not support audio playback.
          </audio>
          <button type="button" className="secondary" onClick={clearPreview} disabled={loading}>
            Clear
          </button>
        </div>
      )}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!recordedBlob || loading || disabled || recording}
      >
        {loading ? 'Uploading...' : submitLabel}
      </button>

      {error && <p className="error">{error}</p>}
    </div>
  )
}
