export const SHADOWING_MODES = [
  { id: 'listen_repeat', label: 'Listen and repeat' },
  { id: 'read_aloud', label: 'Read aloud' },
  { id: 'blind', label: 'Blind shadowing' },
  { id: 'academic', label: 'Academic sentence practice' },
  { id: 'toefl_lecture', label: 'TOEFL lecture sentence practice' },
]

export const SHADOWING_DIFFICULTIES = [
  { id: 'easy', label: 'Easy' },
  { id: 'normal', label: 'Normal' },
  { id: 'hard', label: 'Hard' },
]

export const SENTENCE_SETS = [
  { id: 'core', label: 'Core set' },
  { id: 'academic', label: 'Academic sentences' },
  { id: 'short', label: 'Short phrases' },
]

export function filterShadowingItems(items, { sentenceSet = 'core', difficulty = 'normal' } = {}) {
  let filtered = [...items]

  if (sentenceSet === 'academic') {
    filtered = filtered.filter((item) => wordCount(item.target_text) >= 9)
  } else if (sentenceSet === 'short') {
    filtered = filtered.filter((item) => wordCount(item.target_text) <= 8)
  }

  if (difficulty === 'easy') {
    filtered = filtered.filter((item) => wordCount(item.target_text) <= 10)
  } else if (difficulty === 'hard') {
    filtered = filtered.filter((item) => wordCount(item.target_text) >= 8)
  }

  return filtered.length ? filtered : items
}

function wordCount(text) {
  return (text || '').trim().split(/\s+/).filter(Boolean).length
}

export function sentencePreview(text, max = 42) {
  const value = (text || '').trim()
  if (value.length <= max) return value
  return `${value.slice(0, max)}…`
}
