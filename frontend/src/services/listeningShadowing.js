const PREFILL_KEY = 'fluentbridge_shadowing_prefill'

export async function sendSentencesToShadowing(sentences, navigate, createShadowingFromSentences) {
  const cleaned = (sentences || []).map((s) => String(s).trim()).filter(Boolean)
  if (!cleaned.length) return

  const data = await createShadowingFromSentences(cleaned)
  const focusItemId = data.items?.[0]?.id
  navigate('/shadowing', { state: { focusItemId, fromListening: true } })
}

export function saveShadowingPrefill(sentences) {
  const cleaned = (sentences || []).map((s) => String(s).trim()).filter(Boolean)
  if (!cleaned.length) return false
  try {
    sessionStorage.setItem(PREFILL_KEY, JSON.stringify(cleaned))
    return true
  } catch {
    return false
  }
}

export function loadShadowingPrefill() {
  try {
    const raw = sessionStorage.getItem(PREFILL_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter(Boolean) : []
  } catch {
    return []
  }
}

export function clearShadowingPrefill() {
  sessionStorage.removeItem(PREFILL_KEY)
}
