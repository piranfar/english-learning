import { withDisplayStatus, STATUS_LABELS } from './roadmapStatus'

export function topicsForModule(topics, module) {
  if (!module || !topics?.length) return []
  return topics.filter(
    (topic) => topic.order >= module.start_order && topic.order <= module.end_order,
  )
}

export function moduleProgress(topics) {
  const enriched = withDisplayStatus(topics)
  const done = enriched.filter(
    (t) => t.displayStatus === 'completed' || t.displayStatus === 'mastered',
  ).length
  return { done, total: enriched.length, percent: enriched.length ? (done / enriched.length) * 100 : 0 }
}

export function findCurrentModule(modules, topics) {
  const enriched = withDisplayStatus(topics)
  const current = enriched.find((t) => t.displayStatus === 'current')
  if (!current) {
    return modules?.[0] || null
  }
  return (
    modules?.find(
      (m) => current.order >= m.start_order && current.order <= m.end_order,
    ) || modules?.[0] || null
  )
}

export function neighborLessons(topics, currentTopic) {
  const sorted = [...(topics || [])].sort((a, b) => a.order - b.order)
  if (!currentTopic) {
    const first = sorted.find((t) => !t.locked)
    return { previous: null, current: first || null, next: sorted[1] || null }
  }
  const index = sorted.findIndex((t) => t.id === currentTopic.id)
  return {
    previous: index > 0 ? sorted[index - 1] : null,
    current: currentTopic,
    next: index >= 0 && index < sorted.length - 1 ? sorted[index + 1] : null,
  }
}

/** Next lesson in order that is not locked (skips locked Stage 2 items). */
export function nextUnlockedLesson(topics, completedTopic) {
  const sorted = [...(topics || [])].sort((a, b) => a.order - b.order)
  const startIndex = completedTopic
    ? sorted.findIndex((t) => t.id === completedTopic.id)
    : -1
  for (let i = startIndex + 1; i < sorted.length; i += 1) {
    if (!sorted[i].locked) return sorted[i]
  }
  return null
}

export { STATUS_LABELS }
