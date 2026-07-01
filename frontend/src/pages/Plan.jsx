import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { generateTodayPlan, getTodayPlan, updatePlanItem } from '../api/client'
import ProgressBar from '../components/ProgressBar'

function getTaskStatus(item) {
  if (item.status === 'done' || item.completed) return 'Done'
  return 'Not started'
}

function getTaskRoute(item) {
  return item.route || '/dashboard'
}

function getSkillLabel(item) {
  return item.skill || 'Practice'
}

function groupTasks(items) {
  const priority = []
  const skill = []
  const optional = []

  for (const item of items) {
    const type = item.type || ''
    if (type === 'vocab' || type === 'mistake' || type === 'reading' || type === 'listening') {
      priority.push(item)
    } else if (type === 'track') {
      skill.push(item)
    } else {
      optional.push(item)
    }
  }
  return { priority, skill, optional }
}

function PlanTaskRow({ item, updatingId, onToggle }) {
  const status = getTaskStatus(item)
  const route = getTaskRoute(item)

  return (
    <tr className={`plan-queue-row ${item.completed ? 'is-done' : ''}`}>
      <td className="plan-queue-check">
        <input
          type="checkbox"
          checked={Boolean(item.completed)}
          onChange={() => onToggle(item)}
          disabled={updatingId === item.id}
          aria-label={`Mark ${item.title} as complete`}
        />
      </td>
      <td className="plan-queue-title">{item.title}</td>
      <td className="plan-queue-skill">
        <span className="skill-badge">{getSkillLabel(item)}</span>
      </td>
      <td className="plan-queue-time">{item.minutes} min</td>
      <td className="plan-queue-status">
        <span className={`plan-status plan-status-${status === 'Done' ? 'done' : 'pending'}`}>
          {status}
        </span>
      </td>
      <td className="plan-queue-action">
        <Link to={route} className="btn btn-sm">
          Start
        </Link>
      </td>
    </tr>
  )
}

function TaskSection({ title, items, limit, showAll, updatingId, onToggle }) {
  if (!items.length) return null
  const visible = showAll ? items : items.slice(0, limit)
  const hiddenCount = showAll ? 0 : Math.max(0, items.length - limit)

  return (
    <section className="plan-queue-section">
      <h3 className="plan-queue-section-title">{title}</h3>
      <div className="plan-queue-table-wrap">
        <table className="plan-queue-table">
          <thead>
            <tr>
              <th scope="col" aria-label="Complete" />
              <th scope="col">Task</th>
              <th scope="col">Skill</th>
              <th scope="col">Time</th>
              <th scope="col">Status</th>
              <th scope="col" aria-label="Action" />
            </tr>
          </thead>
          <tbody>
            {visible.map((item) => (
              <PlanTaskRow
                key={item.id}
                item={item}
                updatingId={updatingId}
                onToggle={onToggle}
              />
            ))}
          </tbody>
        </table>
      </div>
      {hiddenCount > 0 && (
        <p className="muted plan-queue-more-hint">+{hiddenCount} more in this section</p>
      )}
    </section>
  )
}

export default function Plan() {
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [showAllTasks, setShowAllTasks] = useState(false)

  useEffect(() => {
    loadPlan()
  }, [])

  async function loadPlan() {
    setLoading(true)
    setError('')
    try {
      setPlan(await getTodayPlan())
    } catch (err) {
      setError(err.message || 'Failed to load plan')
    } finally {
      setLoading(false)
    }
  }

  async function handleGeneratePlan() {
    setGenerating(true)
    setError('')
    try {
      setPlan(await generateTodayPlan())
    } catch (err) {
      setError(err.message || 'Failed to generate plan')
    } finally {
      setGenerating(false)
    }
  }

  async function toggleItem(item) {
    setUpdatingId(item.id)
    setError('')
    try {
      setPlan(await updatePlanItem(item.id, !item.completed))
    } catch (err) {
      setError(err.message || 'Failed to update item')
    } finally {
      setUpdatingId(null)
    }
  }

  const progressPercent = useMemo(() => {
    if (!plan?.total_count) return 0
    return Math.round((plan.completed_count / plan.total_count) * 100)
  }, [plan])

  const orderedItems = useMemo(() => {
    if (!plan?.items?.length) return []
    const order = plan.summary?.recommended_order || []
    if (!order.length) return plan.items
    const rank = new Map(order.map((id, index) => [id, index]))
    return [...plan.items].sort((left, right) => {
      const leftRank = rank.has(left.id) ? rank.get(left.id) : Number.MAX_SAFE_INTEGER
      const rightRank = rank.has(right.id) ? rank.get(right.id) : Number.MAX_SAFE_INTEGER
      return leftRank - rightRank
    })
  }, [plan])

  const grouped = useMemo(() => groupTasks(orderedItems), [orderedItems])

  const estimatedMinutes = useMemo(
    () => orderedItems.reduce((sum, item) => sum + (item.minutes || 0), 0),
    [orderedItems],
  )

  const focusRoute = useMemo(() => {
    const firstOpen = orderedItems.find((item) => !item.completed)
    return firstOpen ? getTaskRoute(firstOpen) : '/plan'
  }, [orderedItems])

  if (loading) {
    return (
      <div className="page plan-page plan-compact">
        <p className="muted">Loading today&apos;s plan…</p>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="page plan-page plan-compact">
        <p className="error">{error || 'Plan unavailable'}</p>
      </div>
    )
  }

  const hasPlan = plan.exists !== false && plan.total_count > 0
  const summary = plan.summary || {}

  return (
    <div className="page plan-page plan-compact">
      <header className="page-header plan-page-header">
        <h1>Today&apos;s Study Plan</h1>
        <Link to="/roadmap" className="btn btn-secondary btn-sm plan-roadmap-link">
          View curriculum roadmap
        </Link>
      </header>

      <section className="plan-summary-strip" aria-label="Plan summary">
        <div className="plan-summary-item">
          <span className="plan-summary-label">Vocabulary due</span>
          <strong>{plan.vocab_due ?? 0}</strong>
        </div>
        <div className="plan-summary-item">
          <span className="plan-summary-label">Mistakes due</span>
          <strong>{plan.mistakes_due ?? 0}</strong>
        </div>
        <div className="plan-summary-item">
          <span className="plan-summary-label">Tasks complete</span>
          <strong>{plan.completed_count ?? 0}/{plan.total_count ?? 0}</strong>
        </div>
        <div className="plan-summary-item">
          <span className="plan-summary-label">Est. time today</span>
          <strong>{estimatedMinutes} min</strong>
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      {!hasPlan ? (
        <section className="card plan-empty">
          <h2>No plan yet</h2>
          <p className="muted">
            Generate a personalized plan from due vocabulary, recent mistakes, and daily skill practice.
          </p>
          <button type="button" className="btn btn-sm" onClick={handleGeneratePlan} disabled={generating}>
            {generating ? 'Generating…' : "Generate today's plan"}
          </button>
        </section>
      ) : (
        <>
          <section className="card plan-focus-card plan-focus-compact">
            <p className="plan-focus-kicker">Today&apos;s main focus</p>
            <h2 className="plan-focus-title">{summary.main_focus || 'Balanced daily practice'}</h2>
            {summary.why_it_matters && (
              <p className="plan-focus-why muted">{summary.why_it_matters}</p>
            )}
            {summary.recommended_order?.length > 0 && (
              <p className="plan-focus-order muted">Recommended order: top to bottom in the task queue.</p>
            )}
            <Link to={focusRoute} className="btn btn-sm">
              Start focus task
            </Link>
          </section>

          <section className="card plan-progress-compact">
            <ProgressBar
              label={`${plan.completed_count}/${plan.total_count} tasks complete`}
              valueLabel={`${progressPercent}%`}
              percent={progressPercent}
              tone={plan.progress?.completed ? 'success' : 'primary'}
              size="sm"
            />
            {plan.progress?.completed && (
              <p className="plan-complete-msg muted">Day complete — great work!</p>
            )}
          </section>

          <section className="card plan-queue-card">
            <TaskSection
              title="Priority tasks"
              items={grouped.priority}
              limit={3}
              showAll={showAllTasks}
              updatingId={updatingId}
              onToggle={toggleItem}
            />
            <TaskSection
              title="Skill practice"
              items={grouped.skill}
              limit={3}
              showAll={showAllTasks}
              updatingId={updatingId}
              onToggle={toggleItem}
            />
            {grouped.optional.length > 0 && (
              <TaskSection
                title="Optional extras"
                items={grouped.optional}
                limit={showAllTasks ? grouped.optional.length : 0}
                showAll={showAllTasks}
                updatingId={updatingId}
                onToggle={toggleItem}
              />
            )}
            {!showAllTasks &&
              (grouped.priority.length > 3 ||
                grouped.skill.length > 3 ||
                grouped.optional.length > 0) && (
              <button
                type="button"
                className="btn btn-sm btn-secondary plan-show-more"
                onClick={() => setShowAllTasks(true)}
              >
                Show more tasks
              </button>
            )}
          </section>
        </>
      )}
    </div>
  )
}
