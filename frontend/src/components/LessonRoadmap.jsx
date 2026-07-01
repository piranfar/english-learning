import { Link } from 'react-router-dom'
import ProgressBar from './ProgressBar'
import { withDisplayStatus, STATUS_LABELS } from '../utils/roadmapStatus'

function StageBlock({ stage, interactive, onStart, starting }) {
  const topics = withDisplayStatus(stage.topics)
  const masteredCount = topics.filter(
    (topic) => topic.displayStatus === 'mastered' || topic.displayStatus === 'completed',
  ).length
  const total = topics.length
  const percent = total ? (masteredCount / total) * 100 : 0

  return (
    <section className="roadmap-stage" aria-label={stage.title}>
      <div className="roadmap-stage-header">
        <h3>{stage.title}</h3>
        {stage.locked && <span className="status-pill status-pill-locked">Locked</span>}
      </div>
      <ProgressBar
        percent={percent}
        valueLabel={`${masteredCount}/${total} mastered`}
        ariaLabel={`${stage.title} progress`}
        size="sm"
      />
      <ul className="roadmap-nodes">
        {topics.map((topic) => (
          <li key={topic.id} className={`roadmap-node roadmap-status-${topic.displayStatus}`}>
            <div className="roadmap-node-main">
              <span className="roadmap-node-order">{topic.order}</span>
              <span className="roadmap-node-title">{topic.title}</span>
              <span className="roadmap-node-badge">{STATUS_LABELS[topic.displayStatus]}</span>
            </div>
            {interactive ? (
              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => onStart?.(topic.id)}
                disabled={starting || topic.locked}
              >
                {topic.locked ? 'Locked' : 'Start'}
              </button>
            ) : (
              !topic.locked && (
                <Link to={`/lesson?topic=${topic.slug}`} className="roadmap-node-link">
                  View →
                </Link>
              )
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function LessonRoadmap({ stages, interactive = false, onStart, starting = false }) {
  if (!stages?.length) return null

  return (
    <div className="roadmap">
      <div className="roadmap-legend" aria-hidden="true">
        {Object.entries(STATUS_LABELS).map(([key, label]) => (
          <span key={key} className={`roadmap-legend-item roadmap-status-${key}`}>
            {label}
          </span>
        ))}
      </div>
      {stages.map((stage) => (
        <StageBlock
          key={stage.slug || stage.title}
          stage={stage}
          interactive={interactive}
          onStart={onStart}
          starting={starting}
        />
      ))}
    </div>
  )
}
