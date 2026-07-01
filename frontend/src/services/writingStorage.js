/**
 * Writing draft autosave and attempt history.
 */

const DRAFT_KEY = 'fluentbridge_writing_draft'
const ATTEMPTS_KEY = 'fluentbridge_writing_attempts'

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false
  }
}

export function loadWritingDraft() {
  return safeParse(localStorage.getItem(DRAFT_KEY))
}

export function saveWritingDraft(draft) {
  return safeSet(DRAFT_KEY, {
    ...draft,
    lastUpdatedAt: new Date().toISOString(),
  })
}

export function clearWritingDraft() {
  localStorage.removeItem(DRAFT_KEY)
}

export function saveWritingAttempt(attempt) {
  const attempts = loadWritingAttempts()
  attempts.unshift({
    id: `wr_${Date.now()}`,
    saved_at: new Date().toISOString(),
    ...attempt,
  })
  safeSet(ATTEMPTS_KEY, attempts.slice(0, 30))
  updateWritingProgress(attempts[0])
}

function updateWritingProgress(latest) {
  const attempts = loadWritingAttempts()
  const scores = attempts.map((a) => a.score).filter((s) => typeof s === 'number')

  const metricTotals = {}
  const metricCounts = {}
  for (const attempt of attempts) {
    const s = attempt.scores || {}
    for (const [key, value] of Object.entries(s)) {
      if (typeof value !== 'number') continue
      metricTotals[key] = (metricTotals[key] || 0) + value
      metricCounts[key] = (metricCounts[key] || 0) + 1
    }
  }
  const averages = {}
  for (const key of Object.keys(metricTotals)) {
    averages[key] = Math.round(metricTotals[key] / metricCounts[key])
  }

  let weakest = null
  let worst = 101
  for (const [key, avg] of Object.entries(averages)) {
    if (avg < worst) {
      worst = avg
      weakest = key
    }
  }

  safeSet('fluentbridge_writing_progress', {
    average_score: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null,
    last_score: latest?.score ?? null,
    weakest_area: weakest,
    latest_scores: latest?.scores || null,
    last_mode: latest?.evaluation_mode || latest?.mode || null,
    last_level: latest?.level || null,
  })
}

export function loadWritingProgress() {
  return (
    safeParse(localStorage.getItem('fluentbridge_writing_progress')) || {
      average_score: null,
      last_score: null,
      weakest_area: null,
      latest_scores: null,
      last_mode: null,
      last_level: null,
    }
  )
}

export function formatWritingAreaLabel(key) {
  if (!key) return '—'
  const labels = {
    task_response: 'Task response',
    organization: 'Organization',
    grammar: 'Grammar',
    vocabulary: 'Vocabulary',
    cohesion: 'Cohesion',
    sentence_control: 'Sentence control',
  }
  return labels[key] || key.replace(/_/g, ' ')
}

export function loadWritingAttempts() {
  const data = safeParse(localStorage.getItem(ATTEMPTS_KEY))
  return Array.isArray(data) ? data : []
}
