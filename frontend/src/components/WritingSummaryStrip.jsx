import { formatWritingAreaLabel, loadWritingProgress } from '../services/writingStorage'

export default function WritingSummaryStrip({
  refreshKey = 0,
  evaluationMode = 'normal',
  level = 'normal',
  targetWords = '—',
  timerLabel = '—',
}) {
  void refreshKey
  const progress = loadWritingProgress()

  return (
    <div className="writing-summary-strip">
      <div className="writing-summary-item">
        <span className="writing-summary-label">Current mode</span>
        <strong>{evaluationMode.replace(/_/g, ' ')}</strong>
      </div>
      <div className="writing-summary-item">
        <span className="writing-summary-label">Level</span>
        <strong>{level}</strong>
      </div>
      <div className="writing-summary-item">
        <span className="writing-summary-label">Target words</span>
        <strong>{targetWords}</strong>
      </div>
      <div className="writing-summary-item">
        <span className="writing-summary-label">Timer</span>
        <strong>{timerLabel}</strong>
      </div>
      <div className="writing-summary-item">
        <span className="writing-summary-label">Last score</span>
        <strong>{progress.last_score ?? '—'}</strong>
      </div>
      <div className="writing-summary-item">
        <span className="writing-summary-label">Main weakness</span>
        <strong>{formatWritingAreaLabel(progress.weakest_area)}</strong>
      </div>
    </div>
  )
}
