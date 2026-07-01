const CORRECTION_BLOCK =
  /---CORRECTION---\s*(\{[\s\S]*?\})\s*---END_CORRECTION---/g

const SPEAKING_FEEDBACK_BLOCK =
  /---SPEAKING_FEEDBACK---[\s\S]*?---END_SPEAKING_FEEDBACK---/g

const WRITING_FEEDBACK_BLOCK =
  /---WRITING_FEEDBACK---[\s\S]*?---END_WRITING_FEEDBACK---/g

const TOEFL_WRITING_FEEDBACK_BLOCK =
  /---TOEFL_WRITING_FEEDBACK---[\s\S]*?---END_TOEFL_WRITING_FEEDBACK---/g

const LOOSE_JSON_CORRECTION =
  /\{[\s\S]*?"(?:wrong|original)"[\s\S]*?"(?:correct|corrected)"[\s\S]*?\}/g

export function stripCorrectionBlocks(text) {
  if (!text) return ''
  return text
    .replace(CORRECTION_BLOCK, '')
    .replace(SPEAKING_FEEDBACK_BLOCK, '')
    .replace(WRITING_FEEDBACK_BLOCK, '')
    .replace(TOEFL_WRITING_FEEDBACK_BLOCK, '')
    .replace(LOOSE_JSON_CORRECTION, '')
    .trim()
}

const WRITING_REVISION_COMPARE_BLOCK =
  /---WRITING_REVISION_COMPARE---[\s\S]*?---END_WRITING_REVISION_COMPARE---/g

export function stripWritingFeedbackBlock(text) {
  if (!text) return ''
  return text
    .replace(WRITING_FEEDBACK_BLOCK, '')
    .replace(TOEFL_WRITING_FEEDBACK_BLOCK, '')
    .replace(WRITING_REVISION_COMPARE_BLOCK, '')
    .trim()
}

export function stripSpeakingFeedbackBlock(text) {
  if (!text) return ''
  return text.replace(SPEAKING_FEEDBACK_BLOCK, '').trim()
}

export function normalizeApiCorrection(item) {
  if (!item) return null
  return {
    wrong: item.wrong || item.original || item.wrong_text || '',
    correct: item.correct || item.corrected || item.correct_text || '',
    reason: item.reason || '',
    persian: item.persian || item.persian_explanation || '',
    review: item.review_sentence || item.academic || '',
  }
}

export function extractSpeakableEnglishLines(markdown) {
  const clean = stripCorrectionBlocks(markdown)
  const lines = []
  const seen = new Set()

  for (const rawLine of clean.split('\n')) {
    const line = rawLine.trim()
    if (!line) continue

    const patterns = [
      /^[-*]\s*\*\*English:\*\*\s*(.+)/i,
      /^[-*]\s*English:\s*(.+)/i,
      /^\d+\.\s*\*\*English:\*\*\s*(.+)/i,
      /^[-*]\s*\*\*Correct:\*\*\s*(.+)/i,
      /^[-*]\s*\*\*Wrong:\*\*\s*(.+)/i,
    ]

    for (const pattern of patterns) {
      const match = line.match(pattern)
      if (match) {
        const sentence = match[1].replace(/\*\*/g, '').trim()
        if (sentence && !seen.has(sentence)) {
          seen.add(sentence)
          lines.push(sentence)
        }
      }
    }
  }

  return lines
}
