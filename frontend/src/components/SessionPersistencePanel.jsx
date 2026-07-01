import {
  clearAllSessions,
  clearCurrentSession,
  formatLastActivity,
  loadRecentSessions,
  progressPercent,
} from '../services/learningSessionStorage'

export default function SessionPersistencePanel({
  savedSession,
  recentSessions,
  showWelcomeBack,
  welcomeMessage,
  onContinue,
  onStartNew,
  onStartOver,
  onClearAll,
  onLoadSession,
}) {
  const progress = savedSession?.progress
  const percent = progressPercent(progress)

  function handleClearAll() {
    if (
      window.confirm(
        'Clear all saved sessions and progress? This cannot be undone.',
      )
    ) {
      onClearAll()
    }
  }

  return (
    <section className="card session-persistence-panel">
      <div className="session-panel-header">
        <h2>Your learning session</h2>
        {progress && (
          <div className="course-progress-indicator">
            <span>
              Course progress: {progress.completed_steps?.length || 0} /{' '}
              {progress.total_steps || 6} steps completed
              {progress.total_practice_questions > 0 && (
                <>
                  {' '}
                  · Practice {progress.completed_practice_questions} /{' '}
                  {progress.total_practice_questions}
                </>
              )}
            </span>
            <div className="course-progress-bar" aria-hidden="true">
              <div className="course-progress-fill" style={{ width: `${percent}%` }} />
            </div>
            <span className="course-progress-percent">{percent}%</span>
          </div>
        )}
      </div>

      {showWelcomeBack && welcomeMessage && (
        <div className="welcome-back-banner">
          <p>{welcomeMessage}</p>
          <div className="btn-group">
            <button type="button" className="btn btn-sm" onClick={onContinue}>
              Continue previous session
            </button>
            <button type="button" className="btn btn-sm btn-secondary" onClick={onStartOver}>
              Start over this course
            </button>
          </div>
        </div>
      )}

      {!showWelcomeBack && savedSession?.messages?.length > 0 && (
        <div className="btn-group session-actions">
          <button type="button" className="btn btn-sm btn-secondary" onClick={onStartNew}>
            Start new session
          </button>
          <button type="button" className="btn btn-sm btn-secondary" onClick={onStartOver}>
            Start over this course
          </button>
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleClearAll}>
            Clear saved sessions
          </button>
        </div>
      )}

      {!savedSession?.messages?.length && (
        <div className="btn-group session-actions">
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleClearAll}>
            Clear saved sessions
          </button>
        </div>
      )}

      {recentSessions.length > 0 && (
        <div className="recent-sessions">
          <h3>Recent sessions</h3>
          <ul className="recent-sessions-list">
            {recentSessions.map((item) => {
              const pct = progressPercent(item.progress)
              const isActive = savedSession?.id === item.id
              return (
                <li key={item.id} className={isActive ? 'active' : ''}>
                  <div className="recent-session-meta">
                    <strong>{item.courseTitle || item.title || item.track}</strong>
                    <span className="muted">
                      {item.track} · {formatLastActivity(item.lastUpdatedAt)} · {pct}% complete
                    </span>
                  </div>
                  {!isActive && (
                    <button
                      type="button"
                      className="btn btn-sm btn-secondary"
                      onClick={() => onLoadSession(item.id)}
                    >
                      Open
                    </button>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </section>
  )
}

export { clearAllSessions, clearCurrentSession }
