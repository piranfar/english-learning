import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReadiness } from '../api/client'
import ProgressBar from '../components/ProgressBar'

function scoreDisplay(item) {
  if (item.key.includes('toefl')) {
    return String(item.score)
  }
  return `${item.score}/100`
}

function barPercent(item) {
  if (item.key.includes('toefl')) {
    return Math.min(100, Math.round((item.score / 100) * 100))
  }
  return Math.min(100, Math.max(0, item.score))
}

function statusBadge(item) {
  if (item.ready) {
    return { label: 'Ready', tone: 'ready' }
  }
  if (item.key.includes('toefl')) {
    return item.score >= 75
      ? { label: 'Almost ready', tone: 'almost' }
      : { label: 'Needs work', tone: 'needs' }
  }
  if (item.score >= 60) {
    return { label: 'Almost ready', tone: 'almost' }
  }
  return { label: 'Needs work', tone: 'needs' }
}

function helperText(item) {
  if (item.key === 'estimated_toefl_score') {
    return 'Practice estimate, not official ETS score'
  }
  if (item.key === 'grammar_control' || item.key.includes('lessons')) {
    return item.detail
  }
  if (item.detail?.toLowerCase().includes('placeholder')) {
    return null
  }
  return item.detail
}

const NEXT_ACTIONS = [
  {
    key: 'grammar',
    label: 'Practice grammar',
    getTo: (data) =>
      data?.next_lesson?.slug
        ? `/lesson?topic=${data.next_lesson.slug}`
        : '/lesson',
  },
  { key: 'vocab', label: 'Review vocabulary', to: '/vocab' },
  { key: 'reading', label: 'Start reading practice', to: '/reading' },
  { key: 'listening', label: 'Start listening practice', to: '/listening?mode=generate' },
  { key: 'mistakes', label: 'Open mistake clinic', to: '/mistakes' },
]

export default function Readiness() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadReadiness() {
      try {
        setData(await getReadiness())
      } catch (err) {
        setError(err.message || 'Failed to load readiness check')
      } finally {
        setLoading(false)
      }
    }
    loadReadiness()
  }, [])

  if (loading) {
    return <p className="muted">Loading readiness check…</p>
  }

  if (error || !data) {
    return <p className="error">{error || 'Readiness check unavailable'}</p>
  }

  const goal = data.current_goal
  const criteria = data.criteria || []
  const readyCount = criteria.filter((item) => item.ready).length
  const totalCount = criteria.length
  const skillsReview = data.skills_needing_review || []

  return (
    <div className="page readiness-page readiness-compact">
      <header className="readiness-header-compact">
        <h1>Readiness Check</h1>
      </header>

      <section className="card readiness-goal-card">
        <p className="dashboard-focus-kicker">Current goal</p>
        <h2 className="readiness-goal-title">{goal?.name}</h2>
        <ProgressBar
          label="Lessons mastered"
          valueLabel={`${data.lessons_mastered}/${data.lessons_total}`}
          percent={data.progress_percent}
          size="sm"
        />
        {data.next_lesson && (
          <p className="readiness-next-lesson">
            Next lesson:{' '}
            <Link to={`/lesson?topic=${data.next_lesson.slug}`}>{data.next_lesson.title}</Link>
          </p>
        )}
      </section>

      <section className="readiness-summary-strip" aria-label="Readiness summary">
        <div className="readiness-summary-item">
          <span className="readiness-summary-label">Overall readiness</span>
          <strong>{readyCount}/{totalCount} ready</strong>
        </div>
        <div className="readiness-summary-item">
          <span className="readiness-summary-label">Estimated TOEFL</span>
          <strong>{data.estimated_toefl_score}</strong>
        </div>
        <div className="readiness-summary-item">
          <span className="readiness-summary-label">Stage 2</span>
          <strong>
            {data.stage2_unlocked ? 'Unlocked' : 'Locked until TOEFL 80+ readiness'}
          </strong>
        </div>
        {skillsReview.length > 0 && (
          <div className="readiness-summary-item readiness-summary-skills">
            <span className="readiness-summary-label">Skills needing review</span>
            <strong>{skillsReview.join(', ')}</strong>
          </div>
        )}
      </section>

      <section className="card readiness-chart-card">
        <h2 className="readiness-chart-title">Readiness chart</h2>
        <div className="readiness-grid">
          {criteria.map((item) => {
            const badge = statusBadge(item)
            const hint = helperText(item)
            return (
              <div key={item.key} className="readiness-bar-row">
                <div className="readiness-bar-head">
                  <span className="readiness-bar-label">{item.label}</span>
                  <span className="readiness-bar-score">{scoreDisplay(item)}</span>
                  <span className={`readiness-status readiness-status-${badge.tone}`}>
                    {badge.label}
                  </span>
                </div>
                <div
                  className="readiness-bar-track"
                  role="progressbar"
                  aria-valuenow={barPercent(item)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={item.label}
                >
                  <div
                    className={`readiness-bar-fill readiness-bar-fill-${badge.tone}`}
                    style={{ width: `${barPercent(item)}%` }}
                  />
                </div>
                {hint && <p className="readiness-bar-hint muted">{hint}</p>}
              </div>
            )
          })}
        </div>
      </section>

      <section className="card readiness-actions-card">
        <h2 className="readiness-actions-title">Next actions</h2>
        <p className="muted readiness-actions-lead">
          Jump straight into practice for your weakest areas.
        </p>
        <div className="readiness-actions-grid">
          {NEXT_ACTIONS.map((action) => (
            <Link
              key={action.key}
              to={action.getTo ? action.getTo(data) : action.to}
              className="btn btn-sm btn-secondary readiness-action-btn"
            >
              {action.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
