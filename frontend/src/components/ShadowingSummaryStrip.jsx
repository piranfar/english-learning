import { loadShadowingProgress } from '../services/shadowingStorage'

export default function ShadowingSummaryStrip({ refreshKey = 0, shadowingMode = 'listen and repeat' }) {
  void refreshKey
  const progress = loadShadowingProgress()
  const metrics = progress.latest_metrics || {}

  return (
    <div className="shadowing-summary-strip">
      <div className="shadowing-summary-item">
        <span className="shadowing-summary-label">Sentences completed</span>
        <strong>{progress.sentences_completed ?? 0}</strong>
      </div>
      <div className="shadowing-summary-item">
        <span className="shadowing-summary-label">Average match</span>
        <strong>{progress.average_score ?? '—'}</strong>
      </div>
      <div className="shadowing-summary-item">
        <span className="shadowing-summary-label">Pronunciation clarity</span>
        <strong>{metrics.pronunciation_clarity ?? '—'}</strong>
      </div>
      <div className="shadowing-summary-item">
        <span className="shadowing-summary-label">Pace / rhythm</span>
        <strong>{metrics.pace ?? '—'}</strong>
      </div>
      <div className="shadowing-summary-item">
        <span className="shadowing-summary-label">Current mode</span>
        <strong>{shadowingMode}</strong>
      </div>
    </div>
  )
}
