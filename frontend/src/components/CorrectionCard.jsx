import CollapsibleNativeNote from './CollapsibleNativeNote'
import TextToSpeechButton from './TextToSpeechButton'

export default function CorrectionCard({ correction }) {
  if (!correction) return null

  const wrong = correction.wrong || correction.original || ''
  const correct = correction.correct || correction.corrected || ''
  const reason = correction.reason || ''
  const nativeNote = correction.persian || correction.persian_explanation || ''
  const review = correction.review || correction.review_sentence || correction.academic || ''

  if (!wrong && !correct) return null

  return (
    <article className="correction-card assistant-correction-card">
      <h3 className="assistant-section-title">Correction</h3>
      {wrong && (
        <div className="correction-row">
          <span className="label">Wrong</span>
          <p>
            {wrong}
            <TextToSpeechButton text={wrong} label="Listen" size="xs" />
          </p>
        </div>
      )}
      {correct && (
        <div className="correction-row">
          <span className="label">Correct</span>
          <p>
            {correct}
            <TextToSpeechButton text={correct} label="Listen" size="xs" />
          </p>
        </div>
      )}
      {reason && (
        <div className="correction-row">
          <span className="label">Reason</span>
          <p>{reason}</p>
        </div>
      )}
      <CollapsibleNativeNote note={nativeNote} />
      {review && (
        <div className="correction-row">
          <span className="label">Practice</span>
          <p>
            {review}
            <TextToSpeechButton text={review} label="Listen" size="xs" />
          </p>
        </div>
      )}
    </article>
  )
}
