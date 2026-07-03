import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, getLessonTopics, getReadiness, getTodayPlan } from '../api/client'
import HorizontalBarChart from '../components/HorizontalBarChart'
import PlanTaskQueue from '../components/PlanTaskQueue'
import ProgressBar from '../components/ProgressBar'
import RoadmapPreview, { Stage2LockedCard } from '../components/RoadmapPreview'
import { extractSkillBars } from '../utils/skillBars'
import { findCurrentLesson } from '../utils/roadmapStatus'

const QUICK_ACTIONS = [
  { to: '/reading', label: 'Reading' },
  { to: '/listening', label: 'Listening' },
  { to: '/speaking', label: 'Speaking' },
  { to: '/shadowing', label: 'Shadowing' },
  { to: '/vocab', label: 'Vocabulary' },
  { to: '/writing', label: 'Writing' },
]

export default function Today() {
  const [data, setData] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [roadmap, setRoadmap] = useState(null)
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [planError, setPlanError] = useState('')

  useEffect(() => {
    async function loadToday() {
      const [dashboardResult, readinessResult, roadmapResult, planResult] = await Promise.allSettled([
        getDashboard(),
        getReadiness(),
        getLessonTopics(),
        getTodayPlan(),
      ])

      if (dashboardResult.status === 'fulfilled') {
        setData(dashboardResult.value)
      } else {
        setError(dashboardResult.reason?.message || 'Failed to load today')
      }
      if (readinessResult.status === 'fulfilled') {
        setReadiness(readinessResult.value)
      }
      if (roadmapResult.status === 'fulfilled') {
        setRoadmap(roadmapResult.value)
      }
      if (planResult.status === 'fulfilled') {
        setPlan(planResult.value)
      }
      setLoading(false)
    }
    loadToday()
  }, [])

  const stage1 = useMemo(
    () => roadmap?.stages?.find((stage) => stage.slug === 'b2_toefl_80') || roadmap?.stages?.[0],
    [roadmap],
  )

  const currentLesson = useMemo(
    () => findCurrentLesson(stage1?.topics) || null,
    [stage1],
  )

  if (loading) {
    return <p className="muted">Loading today…</p>
  }

  if (error || !data) {
    return <p className="error">{error || 'Today unavailable'}</p>
  }

  const {
    journey,
    coach_focus: coachFocus,
    streak,
    vocab_due: vocabDue,
    mistakes_due: mistakesDue,
    analytics,
  } = data

  const emptyStates = coachFocus?.empty_states || {}
  const todayFocus = coachFocus?.today_focus
  const focusAction = coachFocus?.focus_action
  const focusTitle = todayFocus?.title || coachFocus?.main_weakness || 'Balanced daily practice'
  const focusWhy = todayFocus?.why_it_matters || coachFocus?.why_it_matters
  const focusTaskTitle = focusAction?.title || coachFocus?.recommended_action
  const focusRoute = focusAction?.route || coachFocus?.action_route || '/today'
  const focusButtonLabel = focusAction?.label || coachFocus?.action_label || 'Start focus task'
  const vocabDueMessage = emptyStates.vocab_due_message

  const skillBars = extractSkillBars(readiness?.criteria)
  const weaknessData = (analytics?.mistakes_by_category || []).slice(0, 6).map((row) => ({
    label: row.label,
    value: row.count,
  }))

  const weakSkills = journey?.skills_needing_review || []

  return (
    <div className="page dashboard-page dashboard-compact today-page">
      <header className="dashboard-header-compact">
        <h1>Today</h1>
      </header>

      <div className="dashboard-top-grid">
        {journey && (
          <section className="card dashboard-journey-card dashboard-journey-compact">
            <p className="dashboard-focus-kicker">Stage {journey.current_stage}</p>
            <h2 className="dashboard-journey-title">{journey.current_goal?.name}</h2>
            <ProgressBar
              label={`TOEFL ${journey.target_toefl_score}+ readiness`}
              valueLabel={`${journey.progress_percent}%`}
              percent={journey.progress_percent}
              size="sm"
            />
            <dl className="dashboard-journey-meta">
              <div>
                <dt>Current lesson</dt>
                <dd>
                  {currentLesson ? (
                    <Link to={`/lesson?topic=${currentLesson.slug}`}>{currentLesson.title}</Link>
                  ) : journey.next_lesson ? (
                    <Link to={`/lesson?topic=${journey.next_lesson.slug}`}>
                      {journey.next_lesson.title}
                    </Link>
                  ) : (
                    <span className="muted">All lessons complete</span>
                  )}
                </dd>
              </div>
              <div>
                <dt>Lessons</dt>
                <dd>
                  {journey.lessons_mastered}/{journey.lessons_total} mastered
                </dd>
              </div>
            </dl>
            {weakSkills.length > 0 && (
              <div className="dashboard-skills-review dashboard-skills-review-compact">
                <span className="label">Weak skills</span>
                <div className="tag-list tag-list-compact">
                  {weakSkills.map((skill) => (
                    <span key={skill} className="tag tag-sm">{skill}</span>
                  ))}
                </div>
              </div>
            )}
            <Link to="/progress" className="btn btn-sm btn-secondary">
              Open progress check
            </Link>
          </section>
        )}

        <section className="card dashboard-focus-card dashboard-focus-compact">
          <p className="dashboard-focus-kicker">Today&apos;s Focus</p>
          <h2 className="dashboard-focus-title">{focusTitle}</h2>
          {focusWhy && (
            <p className="dashboard-focus-why">
              <span className="label">Reason</span> {focusWhy}
            </p>
          )}
          <div className="dashboard-focus-recommendation">
            <span className="label">Recommended task</span>
            <p className="dashboard-focus-task-title">{focusTaskTitle}</p>
          </div>
          <div className="dashboard-focus-links">
            <Link to={focusRoute} className="btn btn-sm">
              {focusButtonLabel}
            </Link>
          </div>
          {vocabDueMessage && (
            <p className="muted dashboard-vocab-due dashboard-vocab-due-compact">{vocabDueMessage}</p>
          )}
          {(emptyStates.no_mistakes_yet || emptyStates.needs_diagnostic) && (
            <ul className="dashboard-empty-states dashboard-empty-states-compact">
              {emptyStates.no_mistakes_yet && (
                <li>No mistakes yet — keep practicing.</li>
              )}
              {emptyStates.needs_diagnostic && (
                <li>Complete a diagnostic to personalize your plan.</li>
              )}
            </ul>
          )}
        </section>
      </div>

      <PlanTaskQueue
        plan={plan}
        onPlanChange={setPlan}
        planError={planError}
        onPlanError={setPlanError}
      />

      <section className="card dashboard-quick-start-compact">
        <h2 className="dashboard-section-title">Quick start</h2>
        <div className="btn-group btn-group-compact">
          {QUICK_ACTIONS.map((action) => (
            <Link key={action.to} to={action.to} className="btn btn-sm">
              {action.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="card-grid dashboard-stat-grid">
        <div className="stat-card stat-card-compact">
          <span className="stat-value">{streak}</span>
          <span className="stat-label">Day streak</span>
        </div>
        <div className="stat-card stat-card-compact">
          <span className="stat-value">{vocabDue}</span>
          <span className="stat-label">Vocab due</span>
        </div>
        <div className="stat-card stat-card-compact">
          <span className="stat-value">{mistakesDue}</span>
          <span className="stat-label">Mistakes due</span>
        </div>
        <div className="stat-card stat-card-compact">
          <span className="stat-value">{analytics?.vocab_learned ?? 0}</span>
          <span className="stat-label">Words in deck</span>
        </div>
      </section>

      {(skillBars.length > 0 || weaknessData.length > 0) && (
        <div className="dashboard-columns">
          {skillBars.length > 0 && (
            <section className="card dashboard-chart-card">
              <h2 className="dashboard-section-title">Skills snapshot</h2>
              <div className="skill-bars skill-bars-compact">
                {skillBars.map((skill) => (
                  <ProgressBar
                    key={skill.label}
                    label={skill.label}
                    valueLabel={`${skill.score}/100`}
                    percent={skill.score}
                    tone={skill.score >= 70 ? 'success' : 'warning'}
                    size="sm"
                  />
                ))}
              </div>
              <Link to="/progress" className="btn btn-sm btn-secondary">
                Full progress check
              </Link>
            </section>
          )}
          {weaknessData.length > 0 && (
            <section className="card dashboard-chart-card">
              <h2 className="dashboard-section-title">Weakness chart</h2>
              <p className="muted dashboard-chart-subtitle">Last 30 days</p>
              <HorizontalBarChart data={weaknessData} />
            </section>
          )}
        </div>
      )}

      {stage1 && (
        <div className="dashboard-roadmap-row">
          <RoadmapPreview stage={stage1} previewCount={5} />
          <Stage2LockedCard unlocked={journey?.stage2_unlocked} />
        </div>
      )}
    </div>
  )
}
