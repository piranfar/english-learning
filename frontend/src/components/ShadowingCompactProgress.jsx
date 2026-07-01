const SCORE_BARS = [
  { key: 'word_accuracy', label: 'Word accuracy' },
  { key: 'fluency', label: 'Fluency' },
  { key: 'pace', label: 'Pace' },
  { key: 'pronunciation_clarity', label: 'Pronunciation clarity' },
  { key: 'intonation', label: 'Intonation' },
]

export default function ShadowingCompactProgress({ latestResult = null, refreshKey = 0 }) {
  void refreshKey
  const scores = latestResult || {}

  return (
    <aside className="card shadowing-compact-progress">
      <h2 className="shadowing-panel-title">Score breakdown</h2>
      <div className="shadowing-score-bars">
        {SCORE_BARS.map(({ key, label }) => {
          const value = scores[key]
          return (
            <div key={key} className="shadowing-score-bar-row">
              <div className="shadowing-score-bar-head">
                <span>{label}</span>
                <span>{value ?? '—'}</span>
              </div>
              <div className="shadowing-score-bar-track">
                <div
                  className="shadowing-score-bar-fill"
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
