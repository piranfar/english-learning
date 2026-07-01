/**
 * Reading attempt history and progress for summary strip.
 */

const ATTEMPTS_KEY = 'fluentbridge_reading_attempts'
const PROGRESS_KEY = 'fluentbridge_reading_progress'

const SKILL_LABELS = {
  main_idea: 'Main idea',
  detail: 'Detail',
  inference: 'Inference',
  vocabulary: 'Vocabulary',
  complete_words: 'Complete the words',
  sentence_meaning: 'Sentence meaning',
  grammar_context: 'Grammar/context',
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

export function formatReadingSkillLabel(skill) {
  if (!skill) return '—'
  return SKILL_LABELS[skill] || skill.replace(/_/g, ' ')
}

export function loadReadingAttempts() {
  return safeParse(localStorage.getItem(ATTEMPTS_KEY)) || []
}

export function loadReadingProgress() {
  return safeParse(localStorage.getItem(PROGRESS_KEY)) || {
    last_score: null,
    weakest_skill: null,
    skill_averages: {},
    reading_mode: 'general',
  }
}

export function saveReadingAttempt(attempt) {
  const attempts = loadReadingAttempts()
  attempts.unshift({
    id: `rd_${Date.now()}`,
    saved_at: new Date().toISOString(),
    ...attempt,
  })
  safeSet(ATTEMPTS_KEY, attempts.slice(0, 30))
  updateReadingProgress(attempts[0])
}

function updateReadingProgress(latest) {
  const attempts = loadReadingAttempts()
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
    reading_mode: latest?.reading_mode || 'general',
    last_updated: new Date().toISOString(),
  })
}
