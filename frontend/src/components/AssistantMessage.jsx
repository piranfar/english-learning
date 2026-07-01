import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CollapsibleNativeNote from './CollapsibleNativeNote'
import CorrectionCard from './CorrectionCard'
import TextToSpeechButton from './TextToSpeechButton'
import {
  extractSpeakableEnglishLines,
  normalizeApiCorrection,
  stripCorrectionBlocks,
} from '../utils/messageContent'
import { extractNativeLanguageNotes } from '../utils/nativeLanguageContent'
import { englishTextForSpeech, isPrimarilyPersian } from '../utils/speech'

function plainText(children) {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(plainText).join('')
  if (children?.props?.children) return plainText(children.props.children)
  return ''
}

function MarkdownParagraph({ children }) {
  const text = plainText(children).trim()
  if (!text) return null

  const englishMatch = text.match(/^\*\*English:\*\*\s*(.+)/i)
  const persianMatch = text.match(/^\*\*Persian:\*\*\s*(.+)/i)
  const wrongMatch = text.match(/^\*\*Wrong:\*\*\s*(.+)/i)
  const correctMatch = text.match(/^\*\*Correct:\*\*\s*(.+)/i)

  if (persianMatch || isPrimarilyPersian(text.replace(/\*\*/g, ''))) {
    return null
  }

  if (englishMatch) {
    const sentence = englishMatch[1]
    return (
      <p className="example-english">
        <strong>English:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </p>
    )
  }

  if (wrongMatch) {
    const sentence = wrongMatch[1]
    return (
      <p>
        <strong>Wrong:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </p>
    )
  }

  if (correctMatch) {
    const sentence = correctMatch[1]
    return (
      <p>
        <strong>Correct:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </p>
    )
  }

  return <p>{children}</p>
}

function MarkdownListItem({ children }) {
  const text = plainText(children).trim()
  const englishMatch = text.match(/^\*\*English:\*\*\s*(.+)/i)
  const persianMatch = text.match(/^\*\*Persian:\*\*\s*(.+)/i)
  const wrongMatch = text.match(/^\*\*Wrong:\*\*\s*(.+)/i)
  const correctMatch = text.match(/^\*\*Correct:\*\*\s*(.+)/i)

  if (persianMatch || isPrimarilyPersian(text.replace(/\*\*/g, ''))) {
    return null
  }

  if (englishMatch) {
    const sentence = englishMatch[1]
    return (
      <li className="example-english">
        <strong>English:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </li>
    )
  }
  if (wrongMatch) {
    const sentence = wrongMatch[1]
    return (
      <li>
        <strong>Wrong:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </li>
    )
  }
  if (correctMatch) {
    const sentence = correctMatch[1]
    return (
      <li>
        <strong>Correct:</strong> {sentence}
        <TextToSpeechButton text={sentence} label="Listen" size="xs" />
      </li>
    )
  }
  return <li>{children}</li>
}

export default function AssistantMessage({ content, corrections = [] }) {
  const stripped = stripCorrectionBlocks(content)
  const { cleaned, notes } = extractNativeLanguageNotes(stripped)
  const cleanContent = cleaned
  const speechText = englishTextForSpeech(cleanContent)
  const exampleLines = extractSpeakableEnglishLines(cleanContent)
  const apiCorrections = corrections
    .map(normalizeApiCorrection)
    .filter((item) => item && (item.wrong || item.correct))

  const extraExamples = exampleLines.filter(
    (line) => !apiCorrections.some((c) => c.correct === line || c.wrong === line),
  )

  return (
    <div className="assistant-message">
      <div className="assistant-message-toolbar">
        {speechText && (
          <TextToSpeechButton text={speechText} label="Listen to answer" />
        )}
      </div>

      <div className="assistant-markdown">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: MarkdownParagraph,
            li: MarkdownListItem,
            h3: ({ children }) => (
              <h3 className="assistant-section-title">{children}</h3>
            ),
            h4: ({ children }) => (
              <h4 className="assistant-subsection-title">{children}</h4>
            ),
            code: ({ className, children, ...props }) => {
              const isBlock = className?.includes('language-')
              if (isBlock) {
                return (
                  <pre className="assistant-code-block">
                    <code {...props}>{children}</code>
                  </pre>
                )
              }
              return (
                <code className="assistant-inline-code" {...props}>
                  {children}
                </code>
              )
            },
          }}
        >
          {cleanContent}
        </Markdown>
      </div>

      {extraExamples.length > 0 && (
        <div className="assistant-examples-bar">
          <span className="label">Quick listen</span>
          <div className="assistant-example-buttons">
            {extraExamples.slice(0, 5).map((sentence) => (
              <TextToSpeechButton
                key={sentence}
                text={sentence}
                label={sentence.length > 42 ? `${sentence.slice(0, 42)}…` : sentence}
                size="xs"
              />
            ))}
          </div>
        </div>
      )}

      {apiCorrections.map((correction, index) => (
        <CorrectionCard key={index} correction={correction} />
      ))}

      <CollapsibleNativeNote notes={notes} />
    </div>
  )
}
