function CorrectionRow({ item, index }) {
  return (
    <article key={index} className="writing-correction-row">
      {item.type && <span className="tag">{item.type}</span>}
      {item.original && <p><span className="label">Original</span> {item.original}</p>}
      {item.corrected && <p><span className="label">Corrected</span> {item.corrected}</p>}
      {item.explanation && <p className="muted">{item.explanation}</p>}
    </article>
  )
}

export default function WritingLatestFeedback({ feedback, onRewriteDrill }) {
  if (!feedback) return null

  const wf = feedback.writingFeedback || {}
  const scores = wf.scores || {}
  const corrections = wf.priority_corrections?.length
    ? wf.priority_corrections
    : wf.main_mistakes || []
  const drill = wf.next_rewrite_drill || {}

  return (
    <section className="card writing-latest-feedback">
      <h2 className="writing-panel-title">Latest feedback</h2>

      {wf.estimated_toefl_writing != null && (
        <p className="writing-toefl-estimate">
          TOEFL writing estimate: <strong>{wf.estimated_toefl_writing}/30</strong>
        </p>
      )}
      {wf.overall_score != null && (
        <p className="writing-overall-score">
          Overall: <strong>{wf.overall_score}/100</strong>
        </p>
      )}

      {wf.strengths?.length > 0 && (
        <div className="writing-feedback-block">
          <h3>Strengths</h3>
          <ul>{wf.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
        </div>
      )}

      {corrections.length > 0 && (
        <div className="writing-feedback-block">
          <h3>Priority corrections</h3>
          {corrections.slice(0, 3).map((item, index) => (
            <CorrectionRow key={index} item={item} index={index} />
          ))}
        </div>
      )}

      {wf.corrected_version && (
        <div className="writing-feedback-block">
          <h3>Corrected version</h3>
          <p>{wf.corrected_version}</p>
        </div>
      )}

      {wf.overall_feedback && <p className="muted">{wf.overall_feedback}</p>}

      <div className="writing-feedback-actions">
        {drill.instruction && (
          <button type="button" className="btn btn-secondary" onClick={onRewriteDrill}>
            Start rewrite drill
          </button>
        )}
      </div>

      {drill.instruction && (
        <section className="writing-rewrite-practice">
          <h3>Rewrite practice</h3>
          {drill.title && <p className="writing-drill-title">{drill.title}</p>}
          <p>{drill.instruction}</p>
          {drill.target && <p className="muted">Target: {drill.target}</p>}
        </section>
      )}

      {Object.keys(scores).length > 0 && (
        <div className="writing-inline-scores">
          {Object.entries(scores).map(([key, value]) => (
            <span key={key} className="tag">{key.replace(/_/g, ' ')}: {value}</span>
          ))}
        </div>
      )}
    </section>
  )
}
