import { useState } from 'react'
import { isSpeechSupported, speakEnglish, stopSpeech } from '../utils/speech'

export default function TextToSpeechButton({
  text,
  label = 'Listen',
  className = '',
  size = 'sm',
  rate = 0.85,
}) {
  const [speaking, setSpeaking] = useState(false)

  if (!isSpeechSupported() || !text?.trim()) {
    return null
  }

  function handleClick(event) {
    event.preventDefault()
    event.stopPropagation()
    if (speaking) {
      stopSpeech()
      setSpeaking(false)
      return
    }
    setSpeaking(true)
    speakEnglish(text, rate)
    window.setTimeout(() => setSpeaking(false), Math.max(1500, text.length * 60))
  }

  return (
    <button
      type="button"
      className={`tts-btn tts-btn-${size} ${className}`.trim()}
      onClick={handleClick}
      title={label}
      aria-label={label}
    >
      {speaking ? '⏹' : '🔊'} {label !== 'Listen' ? label : ''}
    </button>
  )
}
