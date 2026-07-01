import { ensureCsrf, postForm } from '../api/client'

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^|;)\\s*${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

export async function transcribeAudio(blob, provider = '') {
  const form = new FormData()
  form.append('audio', blob, 'recording.webm')
  if (provider) {
    form.append('provider', provider)
  }
  const data = await postForm('/transcribe/', form)
  return data.transcript || data.text || ''
}

export async function playSpeech(text, provider = '') {
  await ensureCsrf()
  const headers = { 'Content-Type': 'application/json' }
  const token = getCookie('csrftoken')
  if (token) {
    headers['X-CSRFToken'] = token
  }

  const response = await fetch('/api/tts/', {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify({
      text,
      ...(provider ? { provider } : {}),
    }),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `TTS failed (${response.status})`)
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  await audio.play()
  audio.onended = () => URL.revokeObjectURL(url)
}
