import { isPrimarilyPersian } from './speech'

function stripMarkdownInline(text) {
  return (text || '').replace(/\*\*/g, '').trim()
}

export function extractNativeLanguageNotes(content) {
  if (!content) return { cleaned: '', notes: [] }

  const notes = []
  const kept = []
  let skipSection = false

  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim()

    if (/^#{1,6}\s*.*persian/i.test(line)) {
      skipSection = true
      continue
    }

    if (skipSection) {
      if (/^#{1,6}\s/.test(line)) {
        skipSection = false
      } else if (line) {
        notes.push(stripMarkdownInline(line.replace(/^[-*]\s*/, '')))
        continue
      } else {
        continue
      }
    }

    const persianMatch =
      line.match(/^\*\*Persian:\*\*\s*(.+)/i) ||
      line.match(/^[-*]\s*\*\*Persian:\*\*\s*(.+)/i) ||
      line.match(/^[-*]\d+\.\s*\*\*Persian:\*\*\s*(.+)/i)

    if (persianMatch) {
      notes.push(stripMarkdownInline(persianMatch[1]))
      continue
    }

    const plain = stripMarkdownInline(line.replace(/^[-*]\s*/, ''))
    if (plain && isPrimarilyPersian(plain)) {
      notes.push(plain)
      continue
    }

    kept.push(rawLine)
  }

  const uniqueNotes = [...new Set(notes.filter(Boolean))]
  return { cleaned: kept.join('\n').trim(), notes: uniqueNotes }
}
