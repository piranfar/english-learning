import { formatReadingSkillLabel, loadReadingProgress } from '../services/readingStorage'

const MODE_LABELS = {
  general: 'General reading',
  toefl_2026: 'TOEFL 2026',
  classic_toefl: 'Classic TOEFL academic',
}

export default function ReadingSummaryStrip({
  refreshKey = 0,
  currentLesson = '—',
  level = 'B1',
  readingMode = 'general',
}) {
  void refreshKey
  const progress = loadReadingProgress()

  return (
    <div className="reading-summary-strip">
      <div className="reading-summary-item">
        <span className="reading-summary-label">Current lesson</span>
        <strong>{currentLesson}</strong>
      </div>
      <div className="reading-summary-item">
        <span className="reading-summary-label">Level</span>
        <strong>{level}</strong>
      </div>
      <div className="reading-summary-item">
        <span className="reading-summary-label">Reading mode</span>
        <strong>{MODE_LABELS[readingMode] || readingMode}</strong>
      </div>
      <div className="reading-summary-item">
        <span className="reading-summary-label">Last score</span>
        <strong>{progress.last_score != null ? `${progress.last_score}%` : '—'}</strong>
      </div>
      <div className="reading-summary-item">
        <span className="reading-summary-label">Weakest skill</span>
        <strong>{formatReadingSkillLabel(progress.weakest_skill)}</strong>
      </div>
    </div>
  )
}
