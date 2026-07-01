import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import ProgressBar from './ProgressBar'
import { moduleProgress, topicsForModule } from '../utils/roadmapModules'
import { withDisplayStatus, STATUS_LABELS } from '../utils/roadmapStatus'

function ModuleCard({
  module,
  topics,
  defaultExpanded,
  stageLocked,
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const moduleTopics = topicsForModule(topics, module)
  const enriched = withDisplayStatus(moduleTopics)
  const progress = moduleProgress(moduleTopics)

  if (!moduleTopics.length) return null

  const currentCount = enriched.filter((t) => t.displayStatus === 'current').length
  const needsReview = enriched.filter((t) => t.displayStatus === 'needs_review').length

  return (
    <section className={`roadmap-module-card ${expanded ? 'is-expanded' : 'is-collapsed'}`}>
      <button
        type="button"
        className="roadmap-module-header"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
      >
        <div className="roadmap-module-header-text">
          <h3>{module.title}</h3>
          <p className="muted roadmap-module-meta">
            {moduleTopics.length} lessons · {progress.done}/{progress.total} complete
            {currentCount > 0 && ' · current lesson in module'}
            {needsReview > 0 && ` · ${needsReview} need review`}
          </p>
        </div>
        <span className="roadmap-module-toggle">{expanded ? 'Collapse' : 'Expand'}</span>
      </button>
      <ProgressBar
        percent={progress.percent}
        valueLabel={`${progress.done}/${progress.total}`}
        size="sm"
        ariaLabel={`${module.title} progress`}
      />
      {expanded && (
        <ul className="roadmap-module-lessons">
          {enriched.map((topic) => (
            <li
              key={topic.id}
              className={`roadmap-module-lesson roadmap-status-${topic.displayStatus}`}
            >
              <span className="roadmap-preview-order">{topic.order}</span>
              <span className="roadmap-preview-title">{topic.title}</span>
              <span className="roadmap-node-badge">{STATUS_LABELS[topic.displayStatus]}</span>
              {!stageLocked && !topic.locked && (
                <Link to={`/lesson?topic=${topic.slug}`} className="roadmap-preview-link">
                  {topic.displayStatus === 'current' ? 'Start' : 'View'}
                </Link>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function Stage2Section({ stage }) {
  const [expanded, setExpanded] = useState(false)
  const enriched = withDisplayStatus(stage.topics || [])

  return (
    <section className="card stage2-locked-card roadmap-stage2-collapsed">
      <div className="roadmap-stage-block-header">
        <h2>{stage.title}</h2>
        <span className="status-pill status-pill-locked">Locked until TOEFL 80+ readiness</span>
      </div>
      <p className="muted stage2-locked-text">
        Stage 2: Academic English / TOEFL 100+ — unlocks after Stage 1 readiness.
      </p>
      <button
        type="button"
        className="btn btn-sm btn-secondary"
        onClick={() => setExpanded((open) => !open)}
      >
        {expanded ? 'Hide Stage 2 lessons' : 'Show Stage 2 lessons'}
      </button>
      {expanded && (
        <ul className="roadmap-module-lessons roadmap-stage2-lessons">
          {enriched.map((topic) => (
            <li key={topic.id} className="roadmap-module-lesson roadmap-status-locked">
              <span className="roadmap-preview-order">{topic.order}</span>
              <span className="roadmap-preview-title">{topic.title}</span>
              <span className="roadmap-node-badge">Locked</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default function CollapsibleRoadmap({ stages, currentModuleId }) {
  if (!stages?.length) return null

  return (
    <div className="collapsible-roadmap">
      {stages.map((stage) => {
        const isStage2 = stage.slug === 'academic_toefl_100'
        const defaultExpandedModule =
          stage.modules?.find((m) => m.id === currentModuleId)?.id || stage.modules?.[0]?.id

        if (isStage2 && stage.locked) {
          return <Stage2Section key={stage.slug} stage={stage} />
        }

        return (
          <div key={stage.slug} className="roadmap-stage-block">
            <div className="roadmap-stage-block-header">
              <h2>{stage.title}</h2>
              {stage.locked && (
                <span className="status-pill status-pill-locked">Locked</span>
              )}
            </div>
            {stage.modules?.length ? (
              stage.modules.map((module) => (
                <ModuleCard
                  key={module.id}
                  module={module}
                  topics={stage.topics}
                  defaultExpanded={!isStage2 && module.id === defaultExpandedModule}
                  stageLocked={stage.locked}
                />
              ))
            ) : (
              <ModuleCard
                module={{ title: stage.title, start_order: 1, end_order: 9999 }}
                topics={stage.topics}
                defaultExpanded={!isStage2}
                stageLocked={stage.locked}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

export function useCurrentModuleId(stages) {
  return useMemo(() => {
    const stage1 = stages?.find((s) => s.slug === 'b2_toefl_80') || stages?.[0]
    if (!stage1?.modules?.length || !stage1.topics?.length) return null
    const enriched = withDisplayStatus(stage1.topics)
    const current = enriched.find((t) => t.displayStatus === 'current')
    if (!current) return stage1.modules[0].id
    const mod = stage1.modules.find(
      (m) => current.order >= m.start_order && current.order <= m.end_order,
    )
    return mod?.id || stage1.modules[0].id
  }, [stages])
}
