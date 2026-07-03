import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { generateTodayPlan, updatePlanItem } from '../api/client'
import ProgressBar from './ProgressBar'

function getTaskStatus(item) {
  if (item.status === 'done' || item.completed) return 'Done'
  return 'Not started'
}

function getTaskRoute(item) {
  return item.route || '/today'
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

export default function PlanTaskQueue({ plan, onPlanChange, planError, onPlanError }) {
  const [updatingId, setUpdatingId] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [showAllTasks, setShowAllTasks] = useState(false)

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

  async function handleGeneratePlan() {
    setGenerating(true)
    onPlanError('')
    try {
      onPlanChange(await generateTodayPlan())
    } catch (err) {
      onPlanError(err.message || 'Failed to generate plan')
    } finally {
      setGenerating(false)
    }
  }

  async function toggleItem(item) {
    setUpdatingId(item.id)
    onPlanError('')
    try {
      onPlanChange(await updatePlanItem(item.id, !item.completed))
    } catch (err) {
      onPlanError(err.message || 'Failed to update item')
    } finally {
      setUpdatingId(null)
    }
  }

  if (!plan) return null

  const hasPlan = plan.exists !== false && plan.total_count > 0

  return (
    <section className="card today-plan-card" aria-label="Today's study plan">
      <div className="today-plan-header">
        <h2 className="dashboard-section-title">Today&apos;s plan</h2>
        <Link to="/roadmap" className="btn btn-secondary btn-sm">
          View roadmap
        </Link>
      </div>

      <div className="plan-summary-strip" aria-label="Plan summary">
        <div className="plan-summary-item">
          <span className="plan-summary-label">Tasks complete</span>
          <strong>{plan.completed_count ?? 0}/{plan.total_count ?? 0}</strong>
        </div>
        <div className="plan-summary-item">
          <span className="plan-summary-label">Est. time today</span>
          <strong>{estimatedMinutes} min</strong>
        </div>
      </div>

      {planError && <p className="error">{planError}</p>}

      {!hasPlan ? (
        <div className="plan-empty">
          <p className="muted">
            Generate a personalized plan from due vocabulary, recent mistakes, and daily skill practice.
          </p>
          <button type="button" className="btn btn-sm" onClick={handleGeneratePlan} disabled={generating}>
            {generating ? 'Generating…' : "Generate today's plan"}
          </button>
        </div>
      ) : (
        <>
          <div className="plan-progress-compact">
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
          </div>

          <div className="plan-queue-card">
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
          </div>
        </>
      )}
    </section>
  )
}
