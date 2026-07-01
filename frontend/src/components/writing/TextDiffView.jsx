import { diffWords } from '../../utils/textDiff'

function DiffSide({ parts, side }) {
  return (
    <p className="writing-diff-text">
      {parts.map((part, index) => {
        if (part.type === 'pad') return null
        if (part.type === 'same') {
          return <span key={index}>{part.text}</span>
        }
        if (side === 'left' && part.type === 'remove') {
          return (
            <span key={index} className="writing-diff-remove">
              {part.text}
            </span>
          )
        }
        if (side === 'right' && part.type === 'add') {
          return (
            <span key={index} className="writing-diff-add">
              {part.text}
            </span>
          )
        }
        return null
      })}
    </p>
  )
}

export default function TextDiffView({ aiText, learnerText }) {
  const { leftParts, rightParts } = diffWords(aiText, learnerText)

  return (
    <div className="writing-diff-grid">
      <div className="writing-diff-panel">
        <span className="label">AI corrected version</span>
        <DiffSide parts={leftParts} side="left" />
      </div>
      <div className="writing-diff-panel">
        <span className="label">Your edited version</span>
        <DiffSide parts={rightParts} side="right" />
      </div>
    </div>
  )
}
