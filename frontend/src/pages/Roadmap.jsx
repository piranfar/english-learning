import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLessonTopics, getReadiness } from '../api/client'
import CollapsibleRoadmap, { useCurrentModuleId } from '../components/CollapsibleRoadmap'
import { findCurrentLesson } from '../utils/roadmapStatus'

export default function Roadmap() {
  const [roadmap, setRoadmap] = useState(null)
  const [readiness, setReadiness] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadRoadmap() {
      try {
        const [topicsResult, readinessResult] = await Promise.allSettled([
          getLessonTopics(),
          getReadiness(),
        ])
        if (topicsResult.status === 'fulfilled') {
          setRoadmap(topicsResult.value)
        } else {
          throw topicsResult.reason
        }
        if (readinessResult.status === 'fulfilled') {
          setReadiness(readinessResult.value)
        }
      } catch (err) {
        setError(err.message || 'Failed to load roadmap')
      } finally {
        setLoading(false)
      }
    }
    loadRoadmap()
  }, [])

  const currentModuleId = useCurrentModuleId(roadmap?.stages)

  const stage1 = useMemo(
    () => roadmap?.stages?.find((s) => s.slug === 'b2_toefl_80') || roadmap?.stages?.[0],
    [roadmap],
  )

  const currentLesson = useMemo(
    () => findCurrentLesson(stage1?.topics),
    [stage1],
  )

  if (loading) {
    return (
      <div className="page roadmap-page">
        <p className="muted">Loading curriculum roadmap…</p>
      </div>
    )
  }

  if (error || !roadmap?.stages?.length) {
    return (
      <div className="page roadmap-page">
        <p className="error">{error || 'Roadmap unavailable'}</p>
        <Link to="/dashboard" className="btn btn-secondary btn-sm">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const stage2 = roadmap.stages.find((s) => s.slug === 'academic_toefl_100')
  const stage1Progress = readiness?.progress_percent ?? 0
  const mastered = readiness?.lessons_mastered ?? 0
  const total = readiness?.lessons_total ?? stage1?.topics?.length ?? 0

  return (
    <div className="page roadmap-page roadmap-compact">
      <header className="page-header roadmap-page-header">
        <div>
          <h1>Curriculum roadmap</h1>
        </div>
        <Link to="/dashboard" className="btn btn-secondary btn-sm">
          Back to dashboard
        </Link>
      </header>

      <section className="roadmap-summary-strip" aria-label="Roadmap summary">
        <div className="roadmap-summary-item">
          <span className="roadmap-summary-label">Stage 1 progress</span>
          <strong>{stage1Progress}%</strong>
        </div>
        <div className="roadmap-summary-item">
          <span className="roadmap-summary-label">Lessons mastered</span>
          <strong>{mastered}/{total}</strong>
        </div>
        <div className="roadmap-summary-item">
          <span className="roadmap-summary-label">Stage 2</span>
          <strong>
            {roadmap.stage2_unlocked ? 'Unlocked' : 'Locked until TOEFL 80+ readiness'}
          </strong>
        </div>
        <div className="roadmap-summary-item">
          <span className="roadmap-summary-label">Est. TOEFL</span>
          <strong>{readiness?.estimated_toefl_score ?? '—'}</strong>
        </div>
        {currentLesson && (
          <div className="roadmap-summary-item roadmap-summary-current">
            <span className="roadmap-summary-label">Current lesson</span>
            <strong>
              <Link to={`/lesson?topic=${currentLesson.slug}`}>{currentLesson.title}</Link>
            </strong>
          </div>
        )}
      </section>

      <CollapsibleRoadmap stages={roadmap.stages} currentModuleId={currentModuleId} />

      {stage2?.locked && (
        <p className="muted roadmap-stage2-note">
          Stage 2: Academic English / TOEFL 100+ — expand when you reach TOEFL 80+ readiness.
        </p>
      )}
    </div>
  )
}
