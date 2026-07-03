import { formatListeningSkillLabel, loadListeningProgress } from '../services/listeningStorage'

const TYPE_LABELS = {
  academic_mini_lecture: 'Academic mini-lecture',
  campus_conversation: 'Campus conversation',
  daily_academic_life: 'Daily academic life',
  toefl_style_lecture: 'TOEFL-style lecture',
  toefl_style_conversation: 'TOEFL-style conversation',
}

export default function ListeningSummaryStrip({
  refreshKey = 0,
  currentLesson = '—',
  level = 'B1',
  listeningType = 'academic_mini_lecture',
}) {
  void refreshKey
  const progress = loadListeningProgress()

  return (
    <div className="listening-summary-strip">
      <div className="listening-summary-item">
        <span className="listening-summary-label">Current lesson</span>
        <strong>{currentLesson}</strong>
      </div>
      <div className="listening-summary-item">
        <span className="listening-summary-label">Level</span>
        <strong>{level}</strong>
      </div>
      <div className="listening-summary-item">
        <span className="listening-summary-label">Listening type</span>
        <strong>{TYPE_LABELS[listeningType] || listeningType}</strong>
      </div>
      <div className="listening-summary-item">
        <span className="listening-summary-label">Last score</span>
        <strong>{progress.last_score != null ? `${progress.last_score}%` : '—'}</strong>
      </div>
      <div className="listening-summary-item">
        <span className="listening-summary-label">Weakest skill</span>
        <strong>{formatListeningSkillLabel(progress.weakest_skill)}</strong>
      </div>
    </div>
  )
}
