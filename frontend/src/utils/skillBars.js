const SKILL_KEY_MAP = [
  ['grammar_control', 'Grammar'],
  ['vocabulary_readiness', 'Vocabulary'],
  ['advanced_vocabulary', 'Vocabulary'],
  ['reading_readiness', 'Reading'],
  ['listening_readiness', 'Listening'],
  ['speaking_readiness', 'Speaking'],
  ['speaking_fluency', 'Speaking'],
  ['writing_readiness', 'Writing'],
  ['academic_writing_strength', 'Writing'],
]

const SKILL_ORDER = ['Grammar', 'Vocabulary', 'Reading', 'Listening', 'Speaking', 'Writing']

export function extractSkillBars(criteria) {
  if (!criteria?.length) return []

  const byLabel = new Map()
  for (const [key, label] of SKILL_KEY_MAP) {
    if (byLabel.has(label)) continue
    const match = criteria.find((item) => item.key === key)
    if (match) {
      byLabel.set(label, match.score)
    }
  }

  return SKILL_ORDER.filter((label) => byLabel.has(label)).map((label) => ({
    label,
    score: byLabel.get(label),
  }))
}
