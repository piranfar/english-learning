import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import CollapsibleNativeNote from '../components/CollapsibleNativeNote'
import { getMistakes } from '../api/client'
import {
  canPracticeCategory,
  categoryExplanation,
  formatMistakeDate,
  groupMistakesByCategory,
  mistakeCardFields,
  practiceRouteForCategory,
  trackLabel,
} from '../utils/mistakeClinic'

function MistakeCard({ mistake, highlighted = false }) {
  const fields = mistakeCardFields(mistake)

  return (
    <article
      id={`mistake-${mistake.id}`}
      className={`mistake-clinic-card card${highlighted ? ' mistake-clinic-card-focus' : ''}`}
    >
      <div className="mistake-clinic-card-meta">
        <span className="muted">{formatMistakeDate(mistake.created_at)}</span>
      </div>

      <div className="mistake-clinic-fields">
        <p><span className="label">Wrong</span> {fields.wrong}</p>
        <p><span className="label">Correct</span> {fields.correct}</p>
        {fields.why && (
          <p><span className="label">Why</span> {fields.why}</p>
        )}
        {fields.example && (
          <p className="muted"><span className="label">Example</span> {fields.example}</p>
        )}
      </div>

      <div className="mistake-clinic-card-footer">
        <span className="label">Source</span> {trackLabel(mistake.track)}
      </div>

      <CollapsibleNativeNote note={mistake.persian_explanation} />

      {fields.isVocab && (
        <p className="muted mistake-clinic-vocab-link">
          <Link to="/vocab?mode=review_mistakes">Review this word in Vocabulary practice →</Link>
        </p>
      )}
    </article>
  )
}

function MistakeGroup({ group, focusId, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)
  const practiceRoute = practiceRouteForCategory(group.category)
  const practiceEnabled = canPracticeCategory(group.category) && Boolean(practiceRoute)
  const countLabel = `${group.mistakes.length} mistake${group.mistakes.length === 1 ? '' : 's'}`
  const panelId = `mistake-examples-${group.category}`

  return (
    <section className="mistake-clinic-group card" id={`mistake-category-${group.category}`}>
      <div className="mistake-clinic-group-header">
        <div>
          <h2 className="mistake-clinic-group-title">
            {group.label}
            <span className="mistake-clinic-group-count"> — {countLabel}</span>
          </h2>
          <p className="muted mistake-clinic-group-explanation">{categoryExplanation(group.category)}</p>
        </div>

        {practiceEnabled ? (
          <Link to={practiceRoute} className="btn btn-secondary btn-sm">
            Practice similar mistakes
          </Link>
        ) : (
          // TODO: Add category-specific practice routes for grammar/writing mistake groups.
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            disabled
            title="Similar-mistake practice for this category is not available yet."
          >
            Practice similar mistakes
          </button>
        )}
      </div>

      <button
        type="button"
        className="mistake-clinic-toggle"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={panelId}
      >
        {open ? 'Hide examples ▴' : `Show ${countLabel} ▾`}
      </button>

      {open && (
        <div className="mistakes-list" id={panelId}>
          {group.mistakes.map((mistake) => (
            <MistakeCard
              key={mistake.id}
              mistake={mistake}
              highlighted={String(mistake.id) === String(focusId)}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default function Mistakes() {
  const [searchParams] = useSearchParams()
  const focusId = searchParams.get('focus')
  const categoryFocus = searchParams.get('category')
  const [mistakes, setMistakes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')
  const scrolledRef = useRef(false)

  useEffect(() => {
    async function load() {
      try {
        const data = await getMistakes()
        setMistakes(data.mistakes)
      } catch (err) {
        setError(err.message || 'Failed to load mistakes')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if ((!focusId && !categoryFocus) || loading || scrolledRef.current) return
    const target = focusId
      ? document.getElementById(`mistake-${focusId}`)
      : document.getElementById(`mistake-category-${categoryFocus}`)
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
      scrolledRef.current = true
    }
  }, [focusId, categoryFocus, loading, mistakes.length])

  const filtered = useMemo(() => {
    if (filter === 'all') return mistakes
    if (filter === 'vocab') return mistakes.filter((m) => m.track === 'vocab_quiz')
    return mistakes.filter((m) => m.track !== 'vocab_quiz')
  }, [mistakes, filter])

  const grouped = useMemo(() => groupMistakesByCategory(filtered), [filtered])

  if (loading) return <p>Loading your mistake clinic...</p>
  if (error) return <p className="error">{error}</p>

  return (
    <div className="page mistake-clinic-page">
      <header className="page-header">
        <h1>Mistake Clinic</h1>
        <p className="page-lead">
          Review your mistakes by pattern, understand why they happened, and practice the skills
          that need the most attention.
        </p>
      </header>

      <div className="form-row card card-compact">
        <label className="form-field">
          Show
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All areas</option>
            <option value="vocab">Vocabulary only</option>
            <option value="coach">Grammar and writing</option>
          </select>
        </label>
      </div>

      {grouped.length === 0 ? (
        <p className="plan-meta">No mistakes in this view yet. Keep practicing — corrections will appear here.</p>
      ) : (
        <div className="mistake-clinic-groups">
          {grouped.map((group, index) => {
            const hasFocusedMistake = group.mistakes.some(
              (mistake) => String(mistake.id) === String(focusId),
            )
            const isFocusedCategory = group.category === categoryFocus
            const defaultOpen = focusId || categoryFocus ? hasFocusedMistake || isFocusedCategory : index === 0
            return (
              <MistakeGroup
                key={group.category}
                group={group}
                focusId={focusId}
                defaultOpen={defaultOpen}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
