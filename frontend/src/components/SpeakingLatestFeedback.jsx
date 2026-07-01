import TextToSpeechButton from './TextToSpeechButton'

function CorrectionRow({ item, index }) {
  return (
    <article key={index} className="speaking-correction-row">
      {item.type && <span className="tag">{item.type}</span>}
      {item.original && (
        <p>
          <span className="label">Original</span> {item.original}
        </p>
      )}
      {item.corrected && (
        <p>
          <span className="label">Corrected</span> {item.corrected}
        </p>
      )}
      {item.explanation && (
        <p className="muted">{item.explanation}</p>
      )}
    </article>
  )
}

export default function SpeakingLatestFeedback({
  feedback,
  onRetryTask,
  onNextDrill,
}) {
  if (!feedback) return null

  const sf = feedback.speakingFeedback || {}
  const deliveryNotes = sf.delivery_notes || {}
  const nextDrill = sf.next_drill || {}
  const corrections = sf.priority_corrections?.length
    ? sf.priority_corrections
    : sf.main_mistakes || []

  return (
    <section className="card speaking-latest-feedback">
      <h2 className="speaking-panel-title">Latest feedback</h2>

      <div className="speaking-feedback-scores">
        {sf.estimated_toefl_speaking != null && (
          <p className="speaking-toefl-estimate">
            TOEFL speaking estimate: <strong>{sf.estimated_toefl_speaking}/30</strong>
            {sf.rubric_score_0_4 != null && (
              <span className="muted"> · Rubric {sf.rubric_score_0_4}/4</span>
            )}
          </p>
        )}
        {sf.overall_score != null && (
          <p className="speaking-overall-score">
            Overall: <strong>{sf.overall_score}/100</strong>
          </p>
        )}
      </div>

      {sf.strengths?.length > 0 && (
        <div className="speaking-feedback-block">
          <h3>Strengths</h3>
          <ul>
            {sf.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {corrections.length > 0 && (
        <div className="speaking-feedback-block">
          <h3>Main corrections</h3>
          {corrections.slice(0, 3).map((item, index) => (
            <CorrectionRow key={index} item={item} index={index} />
          ))}
        </div>
      )}

      {(deliveryNotes.pronunciation || deliveryNotes.intonation || sf.pronunciation_notes) && (
        <div className="speaking-feedback-block">
          <h3>Pronunciation / intonation</h3>
          {deliveryNotes.pronunciation && <p>{deliveryNotes.pronunciation}</p>}
          {deliveryNotes.intonation && <p>{deliveryNotes.intonation}</p>}
          {deliveryNotes.pace && <p className="muted">Pace: {deliveryNotes.pace}</p>}
          {!deliveryNotes.pronunciation && sf.pronunciation_notes && (
            <p>{sf.pronunciation_notes}</p>
          )}
        </div>
      )}

      {sf.corrected_version && (
        <div className="speaking-feedback-block">
          <h3>Corrected answer</h3>
          <p>{sf.corrected_version}</p>
        </div>
      )}

      {feedback.transcript && (
        <div className="speaking-feedback-block">
          <h3>Transcript</h3>
          <p>{feedback.transcript}</p>
        </div>
      )}

      <div className="speaking-feedback-actions">
        {nextDrill.instruction && (
          <button type="button" className="btn btn-secondary" onClick={onNextDrill}>
            Next drill
          </button>
        )}
        <button type="button" className="btn btn-primary" onClick={onRetryTask}>
          Retry same task
        </button>
        {nextDrill.instruction && (
          <TextToSpeechButton text={nextDrill.instruction} label="Listen to drill" size="sm" />
        )}
      </div>

      {nextDrill.instruction && (
        <section className="speaking-practice-continues">
          <h3>Practice continues</h3>
          {nextDrill.title && <p className="speaking-drill-title">{nextDrill.title}</p>}
          <p>{nextDrill.instruction}</p>
          {nextDrill.target && (
            <p className="muted">Target: {nextDrill.target}</p>
          )}
        </section>
      )}

      {sf.retry_recommendation && (
        <p className="muted speaking-retry-note">{sf.retry_recommendation}</p>
      )}

      {sf.overall_feedback && (
        <p className="speaking-overall-note">{sf.overall_feedback}</p>
      )}
    </section>
  )
}
