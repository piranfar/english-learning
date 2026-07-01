const SCORE_BARS = [
  { key: 'task_response', label: 'Task response' },
  { key: 'organization', label: 'Organization' },
  { key: 'grammar', label: 'Grammar accuracy' },
  { key: 'vocabulary', label: 'Vocabulary precision' },
  { key: 'cohesion', label: 'Cohesion' },
  { key: 'sentence_control', label: 'Sentence control' },
]

export default function WritingCompactProgress({ latestScores = null, refreshKey = 0 }) {
  void refreshKey
  const scores = latestScores || {}

  return (
    <aside className="card writing-compact-progress">
      <h2 className="writing-panel-title">Score breakdown</h2>
      <div className="writing-score-bars">
        {SCORE_BARS.map(({ key, label }) => {
          const value = scores[key]
          return (
            <div key={key} className="writing-score-bar-row">
              <div className="writing-score-bar-head">
                <span>{label}</span>
                <span>{value ?? '—'}</span>
              </div>
              <div className="writing-score-bar-track">
                <div
                  className="writing-score-bar-fill"
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
