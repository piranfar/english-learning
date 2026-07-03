/**
 * Listening attempt history and progress for summary strip.
 */

const ATTEMPTS_KEY = 'fluentbridge_listening_attempts'
const PROGRESS_KEY = 'fluentbridge_listening_progress'

const SKILL_LABELS = {
  main_idea: 'Main idea',
  detail: 'Detail',
  inference: 'Inference',
  vocabulary: 'Vocabulary',
  function: 'Function',
  attitude: 'Attitude',
}

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

export function formatListeningSkillLabel(skill) {
  if (!skill) return '—'
  return SKILL_LABELS[skill] || skill.replace(/_/g, ' ')
}

export function loadListeningProgress() {
  return safeParse(localStorage.getItem(PROGRESS_KEY)) || {
    last_score: null,
    weakest_skill: null,
    listening_type: 'academic_mini_lecture',
  }
}

export function saveListeningAttempt(attempt) {
  const attempts = safeParse(localStorage.getItem(ATTEMPTS_KEY)) || []
  attempts.unshift({
    id: `ls_${Date.now()}`,
    saved_at: new Date().toISOString(),
    ...attempt,
  })
  safeSet(ATTEMPTS_KEY, attempts.slice(0, 30))
  updateListeningProgress(attempts[0])
}

function updateListeningProgress(latest) {
  const attempts = safeParse(localStorage.getItem(ATTEMPTS_KEY)) || []
  const skillTotals = {}
  const skillCounts = {}

  for (const attempt of attempts) {
    const scores = attempt.skill_scores || {}
    for (const [key, value] of Object.entries(scores)) {
      if (typeof value !== 'number') continue
      skillTotals[key] = (skillTotals[key] || 0) + value
      skillCounts[key] = (skillCounts[key] || 0) + 1
    }
  }

  const skillAverages = {}
  for (const key of Object.keys(skillTotals)) {
    skillAverages[key] = Math.round(skillTotals[key] / skillCounts[key])
  }

  let weakest = null
  let worst = 101
  for (const [key, avg] of Object.entries(skillAverages)) {
    if (avg < worst) {
      worst = avg
      weakest = key
    }
  }

  safeSet(PROGRESS_KEY, {
    last_score: latest?.score_percent ?? null,
    weakest_skill: weakest,
    skill_averages: skillAverages,
    listening_type: latest?.listening_type || 'academic_mini_lecture',
    last_updated: new Date().toISOString(),
  })
}
