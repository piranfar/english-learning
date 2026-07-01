import { getItemAttemptState } from '../services/shadowingStorage'
import { sentencePreview } from '../data/shadowingModes'

const STATUS_LABELS = {
  not_started: 'Not started',
  tried: 'Tried',
  passed: 'Passed',
  needs_retry: 'Needs retry',
}

export default function ShadowingQueue({ items, activeIndex, onSelect, refreshKey = 0 }) {
  void refreshKey

  return (
    <section className="card shadowing-queue">
      <h2 className="shadowing-panel-title">Sentence queue</h2>
      <ul className="shadowing-queue-list">
        {items.map((item, index) => {
          const state = getItemAttemptState(item.id)
          const isActive = index === activeIndex
          return (
            <li key={item.id} className={`shadowing-queue-row ${isActive ? 'is-active' : ''}`}>
              <span className="shadowing-queue-num">{index + 1}</span>
              <span className="shadowing-queue-preview">{sentencePreview(item.target_text)}</span>
              <span className={`tag shadowing-status-${state.status}`}>{STATUS_LABELS[state.status]}</span>
              <span className="shadowing-queue-score">{state.score != null ? `${state.score}%` : '—'}</span>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => onSelect(index)}>
                {isActive ? 'Active' : 'Start'}
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
