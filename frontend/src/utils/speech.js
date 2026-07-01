export function isSpeechSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

export function speakEnglish(text, rate = 0.85) {
  if (!isSpeechSupported() || !text?.trim()) return

  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text.trim())
  utterance.lang = 'en-US'
  utterance.rate = rate
  window.speechSynthesis.speak(utterance)
}

export function stopSpeech() {
  if (isSpeechSupported()) {
    window.speechSynthesis.cancel()
  }
}

/** Strip lines/paragraphs that are primarily Persian for English TTS. */
export function englishTextForSpeech(markdown) {
  if (!markdown) return ''

  const withoutBlocks = markdown
    .replace(/---CORRECTION---[\s\S]*?---END_CORRECTION---/g, '')
    .trim()

  const paragraphs = withoutBlocks.split(/\n{2,}/)
  const englishParts = []

  for (const paragraph of paragraphs) {
    const lines = paragraph.split('\n').filter((line) => line.trim())
    const englishLines = lines.filter((line) => {
      const trimmed = line.trim()
      if (/^\*\*Persian:\*\*/i.test(trimmed)) return false
      if (/^#{1,6}\s*2\.\s*Persian/i.test(trimmed)) return false
      if (/^-\s*\*\*Persian:\*\*/i.test(trimmed)) return false
      return !isPrimarilyPersian(stripMarkdown(trimmed))
    })

    if (englishLines.length === 0) continue

    const chunk = englishLines
      .map((line) => {
        const englishLabel = line.match(/^[-*]\s*\*\*English:\*\*\s*(.+)/i)
        if (englishLabel) return englishLabel[1].trim()
        const wrong = line.match(/^[-*]\s*\*\*Wrong:\*\*\s*(.+)/i)
        if (wrong) return wrong[1].trim()
        const correct = line.match(/^[-*]\s*\*\*Correct:\*\*\s*(.+)/i)
        if (correct) return correct[1].trim()
        return stripMarkdown(line)
      })
      .join(' ')
      .trim()

    if (chunk && !isPrimarilyPersian(chunk)) {
      englishParts.push(chunk)
    }
  }

  return englishParts.join('. ').replace(/\s+/g, ' ').trim()
}

export function isPrimarilyPersian(text) {
  if (!text) return false
  const letters = text.replace(/[\s\d\p{P}]/gu, '')
  if (!letters.length) return false
  const persianCount = (letters.match(/[\u0600-\u06FF]/g) || []).length
  return persianCount / letters.length > 0.35
}

function stripMarkdown(text) {
  return text
    .replace(/^#{1,6}\s+/, '')
    .replace(/^[-*]\s+/, '')
    .replace(/^\d+\.\s+/, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .trim()
}
