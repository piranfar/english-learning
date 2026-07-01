import { Link } from 'react-router-dom'
import { getRoadmapPreviewTopics, STATUS_LABELS } from '../utils/roadmapStatus'

export default function RoadmapPreview({ stage, previewCount = 5 }) {
  const previewTopics = getRoadmapPreviewTopics(stage?.topics, previewCount)
  if (!previewTopics.length) return null

  return (
    <section className="card roadmap-preview-card">
      <div className="roadmap-preview-header">
        <h2>Roadmap preview</h2>
        <p className="muted roadmap-preview-subtitle">{stage.title}</p>
      </div>
      <ul className="roadmap-preview-list">
        {previewTopics.map((topic) => (
          <li
            key={topic.id}
            className={`roadmap-preview-item roadmap-status-${topic.displayStatus}`}
          >
            <span className="roadmap-preview-order">{topic.order}</span>
            <span className="roadmap-preview-title">{topic.title}</span>
            <span className="roadmap-node-badge">{STATUS_LABELS[topic.displayStatus]}</span>
            {!topic.locked && (
              <Link to={`/lesson?topic=${topic.slug}`} className="roadmap-preview-link">
                Open
              </Link>
            )}
          </li>
        ))}
      </ul>
      <Link to="/roadmap" className="btn btn-sm btn-secondary">
        View full roadmap
      </Link>
    </section>
  )
}

export function Stage2LockedCard({ unlocked = false }) {
  if (unlocked) return null

  return (
    <section className="card stage2-locked-card" aria-label="Stage 2 locked">
      <span className="status-pill status-pill-locked">Locked</span>
      <h2 className="stage2-locked-title">Stage 2: Academic English / TOEFL 100+</h2>
      <p className="muted stage2-locked-text">Unlocks after Stage 1</p>
      <Link to="/roadmap" className="btn btn-sm btn-secondary">
        View full roadmap
      </Link>
    </section>
  )
}
