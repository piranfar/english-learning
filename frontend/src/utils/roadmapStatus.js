const STATUS_LABELS = {
  locked: 'Locked',
  needs_review: 'Needs review',
  mastered: 'Mastered',
  completed: 'Completed',
  current: 'Current',
  upcoming: 'Upcoming',
}

const MASTERY_SCORE_THRESHOLD = 85

export { STATUS_LABELS }

export function withDisplayStatus(topics) {
  let currentAssigned = false
  return (topics || []).map((topic) => {
    let displayStatus
    if (topic.locked) {
      displayStatus = 'locked'
    } else if (topic.status === 'needs_review') {
      displayStatus = 'needs_review'
    } else if (topic.status === 'completed') {
      displayStatus = topic.score >= MASTERY_SCORE_THRESHOLD ? 'mastered' : 'completed'
    } else if (!currentAssigned) {
      currentAssigned = true
      displayStatus = 'current'
    } else {
      displayStatus = 'upcoming'
    }
    return { ...topic, displayStatus }
  })
}

/** Show completed/current/upcoming slice (3–5 items) centered on the current lesson. */
export function getRoadmapPreviewTopics(topics, maxItems = 5) {
  const enriched = withDisplayStatus(topics)
  if (!enriched.length) return []

  const currentIndex = enriched.findIndex((topic) => topic.displayStatus === 'current')
  if (currentIndex === -1) {
    const completed = enriched.filter(
      (topic) => topic.displayStatus === 'completed' || topic.displayStatus === 'mastered',
    )
    if (completed.length === enriched.length) {
      return enriched.slice(-Math.min(maxItems, enriched.length))
    }
    return enriched.slice(0, maxItems)
  }

  const before = 1
  const start = Math.max(0, currentIndex - before)
  const end = Math.min(enriched.length, start + maxItems)
  return enriched.slice(start, end)
}

export function findCurrentLesson(topics) {
  return withDisplayStatus(topics).find((topic) => topic.displayStatus === 'current') || null
}
