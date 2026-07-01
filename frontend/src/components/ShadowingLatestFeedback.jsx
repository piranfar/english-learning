import CollapsibleNativeNote from './CollapsibleNativeNote'

export default function ShadowingLatestFeedback({ result, onRetry }) {
  if (!result) return null

  return (
    <section className="card shadowing-latest-feedback">
      <h2 className="shadowing-panel-title">Shadowing feedback</h2>

      <div className="shadowing-feedback-grid">
        <p><span className="label">Target</span> {result.target_sentence || result.target_text}</p>
        <p><span className="label">Transcript</span> {result.transcript}</p>
        <p><span className="label">Word match</span> {result.word_accuracy ?? result.similarity_score}%</p>
      </div>

      {result.missing_words?.length > 0 && (
        <p><span className="label">Missing words</span> {result.missing_words.join(', ')}</p>
      )}
      {result.changed_words?.length > 0 && (
        <p>
          <span className="label">Changed words</span>{' '}
          {result.changed_words.map((item) => `${item.expected}→${item.spoken}`).join(', ')}
        </p>
      )}
      {result.extra_words?.length > 0 && (
        <p><span className="label">Extra words</span> {result.extra_words.join(', ')}</p>
      )}

      {result.feedback && <p>{result.feedback}</p>}
      {result.retry_instruction && <p className="muted">{result.retry_instruction}</p>}

      {result.next_drill?.instruction && (
        <div className="shadowing-practice-continues">
          <h3>Practice continues</h3>
          {result.next_drill.title && <p className="shadowing-drill-title">{result.next_drill.title}</p>}
          <p>{result.next_drill.instruction}</p>
        </div>
      )}

      <button type="button" className="btn btn-primary btn-sm" onClick={onRetry}>
        Retry sentence
      </button>

      <CollapsibleNativeNote note={result.persian_feedback} />
    </section>
  )
}
