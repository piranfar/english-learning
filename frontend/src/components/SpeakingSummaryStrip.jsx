import { formatAreaLabel, loadSpeakingAttempts, loadSpeakingProgress } from '../services/speakingStorage'

export function attemptsTodayCount() {
  const today = new Date().toISOString().slice(0, 10)
  return loadSpeakingAttempts().filter((item) => (item.saved_at || '').slice(0, 10) === today).length
}

export default function SpeakingSummaryStrip({ refreshKey = 0, evaluationMode = 'normal' }) {
  void refreshKey
  const progress = loadSpeakingProgress()

  return (
    <div className="speaking-summary-strip">
      <div className="speaking-summary-item">
        <span className="speaking-summary-label">Attempts today</span>
        <strong>{attemptsTodayCount()}</strong>
      </div>
      <div className="speaking-summary-item">
        <span className="speaking-summary-label">Average score</span>
        <strong>{progress.average_score ?? '—'}</strong>
      </div>
      <div className="speaking-summary-item">
        <span className="speaking-summary-label">Current mode</span>
        <strong>{evaluationMode}</strong>
      </div>
      <div className="speaking-summary-item">
        <span className="speaking-summary-label">Weakest area</span>
        <strong>{formatAreaLabel(progress.weakest_area)}</strong>
      </div>
      <div className="speaking-summary-item speaking-summary-target">
        <span className="speaking-summary-label">Target</span>
        <strong>TOEFL 80+ / B2 speaking</strong>
      </div>
    </div>
  )
}
