/**
 * Local speaking attempt history and progress.
 */

const KEYS = {
  attempts: 'fluentbridge_speaking_attempts',
  progress: 'fluentbridge_speaking_progress',
}

const MAX_ATTEMPTS = 50

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
  } catch (error) {
    console.warn('[speakingStorage]', error)
    return false
  }
}

export function loadSpeakingAttempts() {
  const data = safeParse(localStorage.getItem(KEYS.attempts))
  return Array.isArray(data) ? data : []
}

export function saveSpeakingAttempt(attempt) {
  const attempts = loadSpeakingAttempts()
  attempts.unshift({
    id: attempt.id || `sp_${Date.now()}`,
    saved_at: new Date().toISOString(),
    ...attempt,
  })
  safeSet(KEYS.attempts, attempts.slice(0, MAX_ATTEMPTS))
  updateSpeakingProgress(attempts[0])
  return attempts[0]
}

function updateSpeakingProgress(latest) {
  const attempts = loadSpeakingAttempts()
  const scores = attempts
    .map((a) => a.overall_score)
    .filter((s) => typeof s === 'number')

  const breakdownTotals = {}
  const breakdownCounts = {}

  for (const attempt of attempts) {
    const bd = attempt.breakdown || {}
    for (const [key, value] of Object.entries(bd)) {
      if (typeof value !== 'number') continue
      breakdownTotals[key] = (breakdownTotals[key] || 0) + value
      breakdownCounts[key] = (breakdownCounts[key] || 0) + 1
    }
    const scores = attempt.scores || {}
    for (const [key, value] of Object.entries(scores)) {
      if (typeof value !== 'number') continue
      breakdownTotals[key] = (breakdownTotals[key] || 0) + value
      breakdownCounts[key] = (breakdownCounts[key] || 0) + 1
    }
  }

  const averages = {}
  for (const key of Object.keys(breakdownTotals)) {
    averages[key] = Math.round(breakdownTotals[key] / breakdownCounts[key])
  }

  let strongest = null
  let weakest = null
  let best = -1
  let worst = 101
  for (const [key, avg] of Object.entries(averages)) {
    if (avg > best) {
      best = avg
      strongest = key
    }
    if (avg < worst) {
      worst = avg
      weakest = key
    }
  }

  safeSet(KEYS.progress, {
    attempts_completed: attempts.length,
    average_score: scores.length
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : null,
    strongest_area: strongest,
    weakest_area: weakest,
    recommended_next_task: latest?.recommended_next_task || null,
    last_level: latest?.level || null,
    last_type: latest?.task_type || null,
    last_mode: latest?.evaluation_mode || null,
    latest_scores: latest?.scores || null,
  })
}

export function loadSpeakingProgress() {
  return (
    safeParse(localStorage.getItem(KEYS.progress)) || {
      attempts_completed: 0,
      average_score: null,
      strongest_area: null,
      weakest_area: null,
      recommended_next_task: null,
    }
  )
}

export function formatAreaLabel(key) {
  if (!key) return '—'
  const labels = {
    fluency: 'Fluency',
    grammar: 'Grammar',
    vocabulary: 'Vocabulary',
    organization: 'Organization',
    delivery: 'Delivery',
    language_use: 'Language use',
    topic_development: 'Topic development',
    pronunciation_clarity: 'Pronunciation clarity',
    intonation: 'Intonation',
    intonation_rhythm: 'Fluency',
    task_completion: 'Organization',
  }
  return labels[key] || key.replace(/_/g, ' ')
}
