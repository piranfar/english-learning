import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import VocabFlashcard from '../components/VocabFlashcard'
import VocabBank from '../components/VocabBank'
import VocabPractice from '../components/VocabPractice'
import VocabProgressSummary from '../components/VocabProgressSummary'
import {
  addRandomFromCategory,
  addVocabFromSeed,
  getDueVocab,
  getVocabCategories,
  getVocabCategoryStats,
  getVocabSeeds,
  reviewVocabItem,
} from '../api/client'
import {
  computeProgressSummary,
  loadAllProgress,
} from '../services/vocabProgressStorage'
import { normalizeVocabWord } from '../utils/vocabQuiz'

const RATING_BUTTONS = [
  { quality: 0, label: 'Again', shortcut: '1' },
  { quality: 2, label: 'Hard', shortcut: '2' },
  { quality: 4, label: 'Good', shortcut: '3' },
  { quality: 5, label: 'Easy', shortcut: '4' },
]

function ReviewFlashcardsTab({ active }) {
  const [items, setItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [rating, setRating] = useState(false)

  const loadDue = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getDueVocab()
      setItems(data.items)
      setCurrentIndex(0)
      setRevealed(false)
    } catch (err) {
      setError(err.message || 'Failed to load vocabulary')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDue()
  }, [loadDue])

  const current = items[currentIndex]

  const handleRate = useCallback(
    async (quality) => {
      if (!current || rating || !revealed) return
      setRating(true)
      setError('')
      try {
        await reviewVocabItem(current.id, quality)
        const nextItems = items.filter((entry) => entry.id !== current.id)
        setItems(nextItems)
        setCurrentIndex((index) => Math.min(index, Math.max(nextItems.length - 1, 0)))
        setRevealed(false)
      } catch (err) {
        setError(err.message || 'Failed to save review')
      } finally {
        setRating(false)
      }
    },
    [current, rating, revealed, items],
  )

  useEffect(() => {
    if (!active || loading || !current) return

    function onKeyDown(event) {
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return

      if (event.code === 'Space') {
        event.preventDefault()
        setRevealed((value) => !value)
        return
      }

      if (!revealed || rating) return

      const map = { '1': 0, '2': 2, '3': 4, '4': 5 }
      if (map[event.key] !== undefined) {
        event.preventDefault()
        handleRate(map[event.key])
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [active, loading, current, revealed, rating, handleRate])

  if (loading) return <p>Loading due cards...</p>

  if (items.length === 0) {
    return (
      <div className="card">
        <p>No vocabulary due now. Use the practice quiz or add words from the vocabulary bank.</p>
      </div>
    )
  }

  return (
    <div className="vocab-review-section">
      {error && <p className="error">{error}</p>}

      <VocabFlashcard
        word={current.word}
        partOfSpeech={current.part_of_speech}
        category={current.category}
        cefrLevel={current.cefr_level}
        definition={current.definition}
        persianMeaning={current.persian_meaning}
        example={current.example}
        collocations={current.collocations}
        shadowingSentence={current.shadowing_sentence}
        commonMistake={current.common_mistake}
        correction={current.correction}
        revealed={revealed}
        onReveal={() => setRevealed(true)}
        onHide={() => setRevealed(false)}
        progressLabel={`Card ${currentIndex + 1} of ${items.length}`}
      >
        <div className="rating-row">
          <span className="label">How well did you recall it?</span>
          <div className="rating-buttons rating-buttons-primary">
            {RATING_BUTTONS.map((btn) => (
              <button
                key={btn.quality}
                type="button"
                className="rating-btn rating-btn-labeled"
                disabled={rating}
                onClick={() => handleRate(btn.quality)}
              >
                <span>{btn.label}</span>
                <small>{btn.shortcut}</small>
              </button>
            ))}
          </div>
          <p className="rating-hint">Space to reveal · 1 Again · 2 Hard · 3 Good · 4 Easy</p>
        </div>
      </VocabFlashcard>
    </div>
  )
}

function CategoryDecksTab() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeDeck, setActiveDeck] = useState(null)
  const [deckSeeds, setDeckSeeds] = useState([])
  const [deckIndex, setDeckIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [deckLoading, setDeckLoading] = useState(false)
  const [addingId, setAddingId] = useState(null)
  const [addStatus, setAddStatus] = useState({})
  const [randomLoading, setRandomLoading] = useState(null)

  const loadStats = useCallback(async () => {
    try {
      setStats(await getVocabCategoryStats())
    } catch (err) {
      setError(err.message || 'Failed to load category stats')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  async function startDeck(cat) {
    setActiveDeck(cat)
    setDeckLoading(true)
    setError('')
    setSuccess('')
    setDeckIndex(0)
    setRevealed(false)
    setAddStatus({})
    try {
      const data = await getVocabSeeds({ category: cat.category, limit: 50 })
      setDeckSeeds(data.seeds)
    } catch (err) {
      setError(err.message || 'Failed to load deck')
      setActiveDeck(null)
    } finally {
      setDeckLoading(false)
    }
  }

  async function handleAddRandom(cat) {
    setRandomLoading(cat.category)
    setError('')
    setSuccess('')
    try {
      const result = await addRandomFromCategory({
        category: cat.category,
        count: 10,
        cefrLevel: 'B1',
      })
      setSuccess(
        `${result.created_count} ${cat.label} word${result.created_count === 1 ? '' : 's'} added to your review cards.`,
      )
      await loadStats()
    } catch (err) {
      setError(err.message || 'Failed to add random words')
    } finally {
      setRandomLoading(null)
    }
  }

  async function handleAddSeed(seed) {
    setAddingId(seed.id)
    try {
      const result = await addVocabFromSeed(seed.id)
      setAddStatus((prev) => ({
        ...prev,
        [seed.id]: result.already_exists ? 'exists' : 'added',
      }))
      await loadStats()
    } catch (err) {
      setError(err.message || 'Failed to add word')
    } finally {
      setAddingId(null)
    }
  }

  function nextCard() {
    setRevealed(false)
    setDeckIndex((index) => Math.min(index + 1, deckSeeds.length - 1))
  }

  if (loading) return <p>Loading category decks...</p>

  if (activeDeck) {
    const seed = deckSeeds[deckIndex]
    if (deckLoading) return <p>Loading deck...</p>
    if (!seed) {
      return (
        <div className="card">
          <p className="muted">No approved words in this deck yet.</p>
          <button type="button" className="btn btn-secondary" onClick={() => setActiveDeck(null)}>
            Back to decks
          </button>
        </div>
      )
    }

    return (
      <div className="deck-session">
        <div className="deck-session-header">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setActiveDeck(null)}>
            ← All decks
          </button>
          <h2>{activeDeck.label}</h2>
        </div>
        {error && <p className="error">{error}</p>}

        <VocabFlashcard
          word={seed.word}
          partOfSpeech={seed.part_of_speech}
          cefrLevel={seed.cefr_level}
          definition={seed.definition}
          persianMeaning={seed.persian_meaning}
          example={seed.example}
          collocations={seed.collocations}
          shadowingSentence={seed.shadowing_sentence}
          commonMistake={seed.common_mistake}
          correction={seed.correction}
          revealed={revealed}
          onReveal={() => setRevealed(true)}
          onHide={() => setRevealed(false)}
          progressLabel={`Card ${deckIndex + 1} of ${deckSeeds.length}`}
          showCategoryOnFront={false}
        >
          <div className="deck-flashcard-actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={addingId === seed.id || addStatus[seed.id]}
              onClick={() => handleAddSeed(seed)}
            >
              {addStatus[seed.id] === 'added'
                ? 'Added to review cards'
                : addStatus[seed.id] === 'exists'
                  ? 'Already in your review cards'
                  : addingId === seed.id
                    ? 'Adding...'
                    : 'Add to My Review Cards'}
            </button>
          </div>
        </VocabFlashcard>

        <div className="deck-nav">
          <button
            type="button"
            className="btn"
            disabled={deckIndex >= deckSeeds.length - 1}
            onClick={nextCard}
          >
            Next
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      {error && <p className="error">{error}</p>}
      {success && <p className="success-msg">{success}</p>}
      <div className="deck-grid">
        {stats.map((cat) => (
          <article key={cat.category} className="card deck-card">
            <h3>{cat.label}</h3>
            <p className="muted">{cat.approved} approved words</p>
            <p className="muted">{cat.personal_cards} in your review cards</p>
            <div className="deck-card-actions">
              <button
                type="button"
                className="btn"
                disabled={cat.approved === 0}
                onClick={() => startDeck(cat)}
              >
                Study Deck
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={cat.approved === 0 || randomLoading === cat.category}
                onClick={() => handleAddRandom(cat)}
              >
                {randomLoading === cat.category ? 'Adding...' : 'Add 10 Random'}
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

export default function Vocab() {
  const [searchParams] = useSearchParams()
  const initialPracticeMode = searchParams.get('mode')
  const wordParam = searchParams.get('word')
  const [tab, setTab] = useState('practice')
  const [words, setWords] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [practiceFocus, setPracticeFocus] = useState(null)
  const [progressVersion, setProgressVersion] = useState(0)
  const [reviewQueueCount, setReviewQueueCount] = useState(0)

  const loadWords = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [seedData, categoryData] = await Promise.all([
        getVocabSeeds({ limit: 500 }),
        getVocabCategories(),
      ])
      setWords(seedData.seeds.map(normalizeVocabWord))
      setCategories(categoryData)
    } catch (err) {
      setError(err.message || 'Failed to load vocabulary')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadWords()
  }, [loadWords])

  useEffect(() => {
    if (initialPracticeMode === 'review_mistakes') {
      setTab('practice')
    }
  }, [initialPracticeMode])

  useEffect(() => {
    if (!wordParam) return

    if (/^\d+$/.test(wordParam)) {
      setTab('review')
      return
    }

    setTab('practice')
    setPracticeFocus({ word: wordParam })
  }, [wordParam])

  const progressMap = useMemo(() => {
    void progressVersion
    return loadAllProgress()
  }, [progressVersion])

  const summary = useMemo(
    () => computeProgressSummary(words, progressMap),
    [words, progressMap],
  )

  function handlePracticeWord(word) {
    setTab('practice')
    setPracticeFocus(word)
  }

  function handleFocusHandled() {
    setPracticeFocus(null)
  }

  function handleProgressChange() {
    setProgressVersion((v) => v + 1)
  }

  return (
    <div className="page vocab-page">
      <header className="page-header">
        <h1>Vocabulary</h1>
        <p className="page-lead">
          Practice with quizzes, track progress locally, and browse a compact vocabulary bank.
        </p>
      </header>

      <div className="tabs">
        <button
          type="button"
          className={tab === 'practice' ? 'tab tab-active' : 'tab'}
          onClick={() => setTab('practice')}
        >
          Practice
        </button>
        <button
          type="button"
          className={tab === 'review' ? 'tab tab-active' : 'tab'}
          onClick={() => setTab('review')}
        >
          Flashcard Review
        </button>
        <button
          type="button"
          className={tab === 'decks' ? 'tab tab-active' : 'tab'}
          onClick={() => setTab('decks')}
        >
          Category Decks
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {tab === 'practice' && (
        <div className="vocab-practice-layout">
          {loading ? (
            <p>Loading vocabulary...</p>
          ) : (
            <>
              <div className="vocab-practice-main">
                <VocabPractice
                  words={words}
                  focusWord={practiceFocus}
                  initialMode={initialPracticeMode}
                  onFocusHandled={handleFocusHandled}
                  onProgressChange={handleProgressChange}
                  onReviewQueueChange={setReviewQueueCount}
                />
              </div>
              <VocabProgressSummary summary={summary} reviewQueueCount={reviewQueueCount} />
              <VocabBank
                words={words}
                categories={categories}
                onPracticeWord={handlePracticeWord}
                onProgressChange={handleProgressChange}
              />
            </>
          )}
        </div>
      )}

      {tab === 'review' && <ReviewFlashcardsTab active={tab === 'review'} />}
      {tab === 'decks' && <CategoryDecksTab />}
    </div>
  )
}
