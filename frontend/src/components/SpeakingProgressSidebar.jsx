import { formatAreaLabel, loadSpeakingAttempts, loadSpeakingProgress } from '../services/speakingStorage'

export default function SpeakingProgressSidebar({ refreshKey = 0 }) {
  void refreshKey
  const progress = loadSpeakingProgress()
  const recent = loadSpeakingAttempts().slice(0, 5)

  return (
    <aside className="card speaking-progress-sidebar">
      <h2 className="vocab-section-title">Speaking progress</h2>
      <dl className="settings-list">
        <div>
          <dt>Attempts</dt>
          <dd>{progress.attempts_completed}</dd>
        </div>
        <div>
          <dt>Average score</dt>
          <dd>{progress.average_score ?? '—'}</dd>
        </div>
        <div>
          <dt>Strongest area</dt>
          <dd>{formatAreaLabel(progress.strongest_area)}</dd>
        </div>
        <div>
          <dt>Weakest area</dt>
          <dd>{formatAreaLabel(progress.weakest_area)}</dd>
        </div>
      </dl>

      {progress.recommended_next_task && (
        <p className="muted">
          <span className="label">Recommended</span> {progress.recommended_next_task}
        </p>
      )}

      {recent.length > 0 && (
        <>
          <h3 className="speaking-recent-title">Recent attempts</h3>
          <ul className="speaking-recent-list">
            {recent.map((item) => (
              <li key={item.id}>
                <strong>{item.task_title || item.task_type}</strong>
                <span className="muted">
                  {' '}
                  · {item.level} · {item.overall_score ?? '—'}/100
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </aside>
  )
}
