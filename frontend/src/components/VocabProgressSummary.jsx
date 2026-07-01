export default function VocabProgressSummary({ summary, reviewQueueCount = 0 }) {
  if (!summary) return null

  return (
    <aside className="card vocab-progress-summary">
      <h2 className="vocab-section-title">Progress</h2>
      <div className="vocab-progress-grid">
        <div className="vocab-stat">
          <span className="vocab-stat-value">{summary.learned}</span>
          <span className="vocab-stat-label">Learned (quiz)</span>
        </div>
        <div className="vocab-stat">
          <span className="vocab-stat-value">{summary.learning}</span>
          <span className="vocab-stat-label">Learning</span>
        </div>
        <div className="vocab-stat">
          <span className="vocab-stat-value">{summary.review}</span>
          <span className="vocab-stat-label">To review (quiz)</span>
        </div>
        <div className="vocab-stat">
          <span className="vocab-stat-value">
            {summary.accuracy !== null ? `${summary.accuracy}%` : '—'}
          </span>
          <span className="vocab-stat-label">Accuracy</span>
        </div>
      </div>
      <p className="vocab-review-queue-summary muted">
        {reviewQueueCount > 0
          ? `Review queue: ${reviewQueueCount} word${reviewQueueCount === 1 ? '' : 's'} will repeat soon`
          : 'Review queue: clear'}
      </p>
    </aside>
  )
}
