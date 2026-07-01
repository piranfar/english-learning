import { loadSpeakingProgress } from '../services/speakingStorage'

const SCORE_BARS = [
  { key: 'delivery', label: 'Delivery', fallback: 'fluency' },
  { key: 'language_use', label: 'Language use', fallback: 'grammar' },
  { key: 'topic_development', label: 'Topic development', fallback: 'organization' },
  { key: 'fluency', label: 'Fluency', fallback: 'fluency' },
  { key: 'pronunciation_clarity', label: 'Pronunciation clarity', fallback: 'fluency' },
]

function scoreValue(scores, key, fallback) {
  if (!scores) return null
  if (typeof scores[key] === 'number') return scores[key]
  if (typeof scores[fallback] === 'number') return scores[fallback]
  return null
}

export default function SpeakingCompactProgress({
  refreshKey = 0,
  latestScores = null,
  variant = 'sidebar',
}) {
  void refreshKey
  const progress = loadSpeakingProgress()
  const scores = latestScores || progress.latest_scores || {}

  return (
    <aside className="speaking-compact-progress card">
      <h2 className="speaking-panel-title">Score breakdown</h2>

      {variant === 'full' && (
        <div className="speaking-mini-stats">
          <div className="speaking-mini-stat">
            <span className="speaking-mini-label">Attempts</span>
            <strong>{progress.attempts_completed ?? 0}</strong>
          </div>
          <div className="speaking-mini-stat">
            <span className="speaking-mini-label">Average score</span>
            <strong>{progress.average_score ?? '—'}</strong>
          </div>
        </div>
      )}

      <div className="speaking-score-bars">
        {SCORE_BARS.map(({ key, label, fallback }) => {
          const value = scoreValue(scores, key, fallback)
          return (
            <div key={key} className="speaking-score-bar-row">
              <div className="speaking-score-bar-head">
                <span>{label}</span>
                <span>{value ?? '—'}</span>
              </div>
              <div className="speaking-score-bar-track">
                <div
                  className="speaking-score-bar-fill"
                  style={{ width: value != null ? `${Math.min(100, value)}%` : '0%' }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
