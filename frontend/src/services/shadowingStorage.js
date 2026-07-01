const ATTEMPTS_KEY = 'fluentbridge_shadowing_attempts'
const PROGRESS_KEY = 'fluentbridge_shadowing_progress'

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function loadShadowingAttempts() {
  const data = safeParse(localStorage.getItem(ATTEMPTS_KEY))
  return Array.isArray(data) ? data : []
}

export function getItemAttemptState(itemId) {
  const attempts = loadShadowingAttempts().filter((a) => a.item_id === itemId)
  if (!attempts.length) return { status: 'not_started', score: null }
  const best = attempts.reduce((max, a) => Math.max(max, a.overall_score || 0), 0)
  const latest = attempts[0]
  if (best >= 85) return { status: 'passed', score: best, latest }
  if (attempts.length >= 1) return { status: 'needs_retry', score: best, latest }
  return { status: 'tried', score: best, latest }
}

export function saveShadowingAttempt(attempt) {
  const attempts = loadShadowingAttempts()
  attempts.unshift({
    id: `sh_${Date.now()}`,
    saved_at: new Date().toISOString(),
    ...attempt,
  })
  localStorage.setItem(ATTEMPTS_KEY, JSON.stringify(attempts.slice(0, 80)))
  updateShadowingProgress(attempts[0])
}

function updateShadowingProgress(latest) {
  const attempts = loadShadowingAttempts()
  const scores = attempts.map((a) => a.overall_score).filter((s) => typeof s === 'number')
  const completed = new Set(attempts.filter((a) => (a.overall_score || 0) >= 70).map((a) => a.item_id)).size

  const metricTotals = { word_accuracy: 0, fluency: 0, pace: 0, pronunciation_clarity: 0 }
  const metricCounts = { word_accuracy: 0, fluency: 0, pace: 0, pronunciation_clarity: 0 }

  for (const attempt of attempts) {
    for (const key of Object.keys(metricTotals)) {
      if (typeof attempt[key] === 'number') {
        metricTotals[key] += attempt[key]
        metricCounts[key] += 1
      }
    }
  }

  const averages = {}
  for (const key of Object.keys(metricTotals)) {
    if (metricCounts[key]) {
      averages[key] = Math.round(metricTotals[key] / metricCounts[key])
    }
  }

  localStorage.setItem(
    PROGRESS_KEY,
    JSON.stringify({
      sentences_completed: completed,
      average_score: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null,
      latest_metrics: averages,
      last_mode: latest?.shadowing_mode || null,
    }),
  )
}

export function loadShadowingProgress() {
  return (
    safeParse(localStorage.getItem(PROGRESS_KEY)) || {
      sentences_completed: 0,
      average_score: null,
      latest_metrics: {},
      last_mode: null,
    }
  )
}
