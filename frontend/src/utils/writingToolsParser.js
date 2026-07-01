import { stripCorrectionBlocks } from './messageContent'

export function extractSection(markdown, heading) {
  if (!markdown) return ''
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`##\\s*${escaped}\\s*\\n([\\s\\S]*?)(?=\\n##\\s|$)`, 'i')
  const match = markdown.match(regex)
  return match ? match[1].trim() : ''
}

export function parseMarkdownSections(markdown, headings) {
  const clean = stripCorrectionBlocks(markdown)
  const result = {}
  for (const heading of headings) {
    result[heading] = extractSection(clean, heading)
  }
  return result
}

export function parseCorrectionTable(markdown) {
  const section = extractSection(markdown, 'Sentence-level corrections')
  if (!section) return []

  const rows = []
  const lines = section.split('\n').filter((line) => line.includes('|'))
  for (const line of lines) {
    if (/^\|?\s*-+\s*\|/.test(line)) continue
    const cells = line
      .split('|')
      .map((cell) => cell.trim())
      .filter(Boolean)
    if (cells.length >= 3 && !/^original$/i.test(cells[0])) {
      rows.push({ original: cells[0], corrected: cells[1], why: cells[2] })
    }
  }
  return rows
}
