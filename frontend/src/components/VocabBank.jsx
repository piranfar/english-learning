import { useMemo, useState } from 'react'
import TextToSpeechButton from './TextToSpeechButton'
import {
  filterWordsByStatus,
  getWordProgress,
  loadAllProgress,
  markLearned,
} from '../services/vocabProgressStorage'

const PAGE_SIZE = 15

export default function VocabBank({
  words,
  categories,
  onPracticeWord,
  onProgressChange,
  defaultOpen = false,
}) {
  const [open, setOpen] = useState(defaultOpen)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(0)
  const [progressVersion, setProgressVersion] = useState(0)

  const progressMap = useMemo(() => {
    void progressVersion
    return loadAllProgress()
  }, [progressVersion])

  const filtered = useMemo(() => {
    let list = words

    if (category) {
      list = list.filter((w) => w.category === category)
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(
        (w) =>
          w.word.toLowerCase().includes(q) ||
          (w.meaning_en || '').toLowerCase().includes(q),
      )
    }

    list = filterWordsByStatus(list, statusFilter, progressMap)
    return list
  }, [words, category, search, statusFilter, progressMap])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageWords = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  function handleMarkLearned(word) {
    markLearned(word)
    setProgressVersion((v) => v + 1)
    onProgressChange?.()
  }

  function handlePractice(word) {
    onPracticeWord?.(word)
  }

  function resetPage() {
    setPage(0)
  }

  return (
    <section className="vocab-bank-section">
      <button
        type="button"
        className="vocab-bank-toggle"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span>Vocabulary Bank</span>
        <span className="muted">{filtered.length} words</span>
        <span>{open ? '▾' : '▸'}</span>
      </button>

      {open && (
        <div className="card vocab-bank">
          <div className="vocab-bank-filters form-row">
            <label className="form-field">
              Search
              <input
                type="search"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  resetPage()
                }}
                placeholder="Search word or meaning..."
              />
            </label>
            <label className="form-field">
              Category
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value)
                  resetPage()
                }}
              >
                <option value="">All categories</option>
                {categories.map((cat) => (
                  <option key={cat.key} value={cat.key}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              Status
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value)
                  resetPage()
                }}
              >
                <option value="all">All</option>
                <option value="new">New</option>
                <option value="learning">Learning</option>
                <option value="learned">Learned</option>
                <option value="review">Review</option>
              </select>
            </label>
          </div>

          {pageWords.length === 0 ? (
            <p className="muted">No words match your filters.</p>
          ) : (
            <ul className="vocab-bank-list">
              {pageWords.map((word) => {
                const progress = getWordProgress(word.id)
                return (
                  <li key={word.id} className="vocab-bank-item">
                    <div className="vocab-bank-item-main">
                      <div className="vocab-bank-item-head">
                        <strong>{word.word}</strong>
                        <TextToSpeechButton text={word.word} label="" size="xs" />
                        {word.level && <span className="tag tag-sm">{word.level}</span>}
                        {progress.status !== 'new' && (
                          <span className={`tag tag-sm tag-${progress.status}`}>
                            {progress.needs_review ? 'review' : progress.status}
                          </span>
                        )}
                      </div>
                      <p className="vocab-bank-meaning">{word.meaning_en || '—'}</p>
                    </div>
                    <div className="vocab-bank-item-actions">
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => handlePractice(word)}
                      >
                        Practice
                      </button>
                      {progress.status !== 'learned' && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleMarkLearned(word)}
                        >
                          Mark learned
                        </button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}

          {filtered.length > PAGE_SIZE && (
            <div className="vocab-bank-pagination">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span className="muted">
                Page {page + 1} of {totalPages}
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
