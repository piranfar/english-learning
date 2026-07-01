import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { sendChatMessage } from '../api/client'
import AssistantMessage from './AssistantMessage'
import CollapsibleNativeNote from './CollapsibleNativeNote'
import ExamTextArea from './ExamTextArea'
import TextToSpeechButton from './TextToSpeechButton'
import {
  computeProgressSummary,
  loadAllProgress,
  loadQuizState,
  markAnswer,
  saveQuizState,
  CLEAR_REVIEW_STREAK,
  wordKey,
} from '../services/vocabProgressStorage'
import { syncVocabQuizMistake } from '../services/vocabMistakeSync'
import {
  advanceSession,
  appendPendingReviewWords,
  canFinishAnyway,
  countSessionReviewPending,
  createPracticeSession,
  deserializeSession,
  extendReviewOnlySession,
  getCompletionMessage,
  getCurrentQueueItem,
  getReviewHint,
  isSessionComplete,
  processSessionAnswer,
  queueItemWord,
  serializeSession,
} from '../utils/vocabPracticeEngine'
import {
  QUIZ_MODES,
  buildQuestion,
  buildWritingPrompt,
  checkSpellingAnswer,
} from '../utils/vocabQuiz'

const QUIZ_LENGTH = 10
const ADAPTIVE_MODES = new Set([
  'multiple_choice',
  'spelling',
  'sentence_completion',
  'word_meaning',
  'meaning_to_word',
  'review_mistakes',
])

function usesAdaptiveReview(mode) {
  return ADAPTIVE_MODES.has(mode)
}

export default function VocabPractice({
  words,
  focusWord = null,
  initialMode = null,
  onFocusHandled,
  onProgressChange,
  onReviewQueueChange,
}) {
  const [mode, setMode] = useState(initialMode || 'multiple_choice')
  const [active, setActive] = useState(false)
  const [session, setSession] = useState(null)
  const [question, setQuestion] = useState(null)
  const [selected, setSelected] = useState(null)
  const [spellingInput, setSpellingInput] = useState('')
  const [writingInput, setWritingInput] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [writingLoading, setWritingLoading] = useState(false)
  const [writingReply, setWritingReply] = useState('')
  const [progressVersion, setProgressVersion] = useState(0)
  const [showFinishAnyway, setShowFinishAnyway] = useState(false)

  useEffect(() => {
    if (initialMode && QUIZ_MODES.some((item) => item.id === initialMode)) {
      setMode(initialMode)
    }
  }, [initialMode])

  const progressMap = useMemo(() => {
    void progressVersion
    return loadAllProgress()
  }, [progressVersion])

  const summary = useMemo(
    () => computeProgressSummary(words, progressMap),
    [words, progressMap],
  )

  const reviewQueueCount = active && session ? countSessionReviewPending(session) : 0

  useEffect(() => {
    onReviewQueueChange?.(reviewQueueCount)
  }, [reviewQueueCount, onReviewQueueChange])

  const refreshProgress = useCallback(() => {
    setProgressVersion((v) => v + 1)
    onProgressChange?.()
  }, [onProgressChange])

  const loadQuestionForSession = useCallback(
    (nextSession) => {
      const item = getCurrentQueueItem(nextSession)
      if (!item) {
        setQuestion(null)
        return
      }
      setQuestion(buildQuestion(nextSession.mode, queueItemWord(item), words))
    },
    [words],
  )

  const resetQuestionState = useCallback(() => {
    setSelected(null)
    setSpellingInput('')
    setWritingInput('')
    setWritingReply('')
    setFeedback(null)
    setShowFinishAnyway(false)
  }, [])

  const finishQuiz = useCallback(
    (finalSession, forced = false) => {
      setActive(false)
      setSession(null)
      setQuestion(null)
      const message = forced
        ? `Quiz ended. Score: ${finalSession.score.originalCorrect}/${finalSession.score.originalTotal} original` +
          (finalSession.score.reviewTotal
            ? ` · Review: ${finalSession.score.reviewCorrect}/${finalSession.score.reviewTotal}`
            : '')
        : getCompletionMessage(finalSession)
      setFeedback({ type: 'info', message: message || 'Quiz complete!' })
      saveQuizState({ mode, active: false })
    },
    [mode],
  )

  const startQuiz = useCallback(
    (wordOverride = null, modeOverride = null) => {
      const quizMode = modeOverride || mode
      const modeConfig = QUIZ_MODES.find((m) => m.id === quizMode)
      if (!modeConfig?.implemented) return

      const newSession = createPracticeSession({
        mode: quizMode,
        words,
        progressMap,
        length: QUIZ_LENGTH,
        focusWord: wordOverride,
        reviewOnly: quizMode === 'review_mistakes',
      })

      if (!newSession) {
        setFeedback({
          type: 'info',
          message:
            quizMode === 'review_mistakes'
              ? 'No words marked for review yet. Answer some questions incorrectly to build your review list.'
              : 'No vocabulary words available for quiz.',
        })
        return
      }

      setSession(newSession)
      setActive(true)
      resetQuestionState()
      loadQuestionForSession(newSession)
    },
    [mode, words, progressMap, resetQuestionState, loadQuestionForSession],
  )

  useEffect(() => {
    const saved = loadQuizState()
    if (saved?.mode) setMode(saved.mode)
    if (saved?.active && saved.session) {
      const restored = deserializeSession(saved.session)
      if (restored) {
        setSession(restored)
        setActive(true)
        loadQuestionForSession(restored)
      }
    }
  }, [loadQuestionForSession])

  useEffect(() => {
    if (active && session) {
      saveQuizState({ mode, active: true, session: serializeSession(session) })
    } else if (!active) {
      saveQuizState({ mode, active: false })
    }
  }, [active, mode, session])

  useEffect(() => {
    if (!focusWord || words.length === 0) return
    setMode('multiple_choice')
    startQuiz(focusWord, 'multiple_choice')
    onFocusHandled?.()
  }, [focusWord, words.length, startQuiz, onFocusHandled])

  function handleStart() {
    startQuiz(null)
  }

  function revealChoiceFeedback(isCorrect, userAnswer = '') {
    const word = question.word
    const item = getCurrentQueueItem(session)
    const isReview = Boolean(item?.isReview)
    const adaptive = usesAdaptiveReview(session.mode)

    let message = isCorrect ? 'Correct!' : `Incorrect. The correct answer is "${word.word}".`
    if (!isCorrect && adaptive) {
      message = `Incorrect. The correct answer is "${word.word}". This word will appear again later in this quiz.`
    } else if (isCorrect && isReview && adaptive) {
      const hint = getReviewHint(session, word)
      if (hint) message = `Correct! ${hint}.`
    }

    setFeedback({
      type: isCorrect ? 'correct' : 'incorrect',
      message,
      explanation: question.explanation,
      persian: question.persian,
      example: question.example,
      word: word.word,
      showRepeatNote: !isCorrect && adaptive,
    })

    if (adaptive && session.mode !== 'sentence_writing') {
      const result = processSessionAnswer(session, word, isCorrect)
      setSession(result.session)
      if (!isCorrect) {
        syncVocabQuizMistake(word, { userAnswer, quizMode: mode })
      }
    } else if (isCorrect) {
      markAnswer(word, true)
    } else {
      markAnswer(word, false)
      syncVocabQuizMistake(word, { userAnswer, quizMode: mode })
    }

    refreshProgress()
  }

  function handleChoice(choice) {
    if (selected !== null || !question?.choices) return
    setSelected(choice.label)
    revealChoiceFeedback(choice.isCorrect, choice.label)
  }

  function handleSpellingSubmit(event) {
    event.preventDefault()
    if (selected !== null || !question) return
    const isCorrect = checkSpellingAnswer(spellingInput, question.correctAnswer)
    setSelected(spellingInput)
    revealChoiceFeedback(isCorrect, spellingInput)
  }

  async function handleWritingSubmit(event) {
    event.preventDefault()
    if (writingLoading || !question || !writingInput.trim()) return

    setWritingLoading(true)
    setFeedback({ type: 'info', message: 'Checking your sentence with the writing coach...' })

    try {
      const prompt = buildWritingPrompt(question.word, writingInput)
      const data = await sendChatMessage({
        message: prompt,
        track: 'writing_coach',
        provider: 'ollama',
      })
      setWritingReply(data.reply || '')
      markAnswer(question.word, true)
      refreshProgress()
      setFeedback({
        type: 'correct',
        message: 'Sentence submitted for review.',
        word: question.word.word,
        example: question.example,
      })
    } catch (err) {
      setFeedback({
        type: 'incorrect',
        message: err.message || 'Failed to check sentence. Try again.',
      })
    } finally {
      setWritingLoading(false)
    }
  }

  function handleNextQuestion() {
    if (!session) return

    let nextSession = advanceSession(session)

    if (nextSession.reviewOnly && nextSession.index >= nextSession.queue.length) {
      nextSession = extendReviewOnlySession(nextSession, words, loadAllProgress())
    }

    if (nextSession.index >= nextSession.queue.length) {
      nextSession = appendPendingReviewWords(nextSession, words)
    }

    if (nextSession.index >= nextSession.queue.length) {
      if (isSessionComplete(nextSession)) {
        finishQuiz(nextSession)
        return
      }
      if (canFinishAnyway(nextSession)) {
        setShowFinishAnyway(true)
        setSession(nextSession)
        return
      }
    }

    setSession(nextSession)
    resetQuestionState()
    loadQuestionForSession(nextSession)
  }

  function handleFinishAnyway() {
    if (session) finishQuiz(session, true)
  }

  const implementedModes = QUIZ_MODES.filter((m) => m.implemented)
  const todoModes = QUIZ_MODES.filter((m) => !m.implemented)
  const canAdvance =
    active &&
    ((selected !== null && question?.mode !== 'sentence_writing') ||
      (question?.mode === 'sentence_writing' && writingReply))

  const currentItem = session ? getCurrentQueueItem(session) : null
  const reviewHint =
    session && currentItem && session.reviewOnly
      ? getReviewHint(session, queueItemWord(currentItem)) ||
        `Needs ${CLEAR_REVIEW_STREAK} correct answers in a row to clear`
      : currentItem?.isReview
        ? getReviewHint(session, queueItemWord(currentItem))
        : null

  const reviewPoolSize = session?.reviewOnly
    ? words.filter((w) => progressMap[wordKey(w)]?.needs_review).length
    : reviewQueueCount

  return (
    <div className="vocab-practice">
      <div className="card vocab-practice-setup">
        <h2 className="vocab-section-title">Vocabulary Practice</h2>
        <p className="muted">Choose a practice type and start a focused quiz session.</p>

        <label className="form-field">
          Practice type
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            disabled={active}
          >
            {implementedModes.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>

        {todoModes.length > 0 && (
          <p className="muted vocab-todo-note">
            Coming soon: {todoModes.map((m) => m.label).join(', ')}
          </p>
        )}

        {!active && (
          <button type="button" className="btn" onClick={handleStart}>
            Start Quiz
          </button>
        )}

        {active && session && (
          <p className="quiz-progress-label">
            {session.reviewOnly ? (
              <>
                Review word: {session.index + 1} of {Math.max(session.queue.length, reviewPoolSize)}
              </>
            ) : (
              <>Question {session.index + 1} of {session.queue.length}</>
            )}
            {currentItem?.isReview && !session.reviewOnly && (
              <span className="tag tag-sm tag-learning"> Review repeat</span>
            )}
            {session.score.originalTotal > 0 && (
              <span className="muted">
                {' '}
                · Score {session.score.originalCorrect}/{session.score.originalTotal}
                {session.score.reviewTotal > 0 &&
                  ` · Review ${session.score.reviewCorrect}/${session.score.reviewTotal}`}
              </span>
            )}
          </p>
        )}

        {active && reviewQueueCount > 0 && (
          <p className="muted vocab-review-queue-note">
            Review queue: {reviewQueueCount} word{reviewQueueCount === 1 ? '' : 's'} will repeat soon
          </p>
        )}

        {active && reviewQueueCount === 0 && session?.finishedOriginal && (
          <p className="muted vocab-review-queue-note">Review queue: clear</p>
        )}

        {reviewHint && active && (
          <p className="muted">{reviewHint}</p>
        )}
      </div>

      {active && question && (
        <div className="card vocab-quiz-card">
          {question.mode === 'sentence_writing' ? (
            <form onSubmit={handleWritingSubmit}>
              <p className="quiz-prompt">{question.prompt}</p>
              {question.meaning && (
                <p className="quiz-hint">
                  <span className="label">Meaning</span> {question.meaning}
                </p>
              )}
              <ExamTextArea
                value={writingInput}
                onChange={(e) => setWritingInput(e.target.value)}
                rows={3}
                placeholder={`Write a sentence using "${question.word.word}"...`}
                disabled={writingLoading || Boolean(writingReply)}
                examMode
              />
              <button
                type="submit"
                className="btn"
                disabled={writingLoading || !writingInput.trim() || Boolean(writingReply)}
              >
                {writingLoading ? 'Checking...' : 'Submit sentence'}
              </button>
            </form>
          ) : question.mode === 'spelling' ? (
            <form onSubmit={handleSpellingSubmit}>
              <p className="quiz-prompt">{question.prompt}</p>
              {question.meaning && (
                <p className="quiz-hint">
                  <span className="label">Meaning</span> {question.meaning}
                  <TextToSpeechButton text={question.meaning} label="" size="xs" />
                </p>
              )}
              {question.sentence && (
                <p className="quiz-sentence">
                  {question.sentence}
                  <TextToSpeechButton
                    text={question.sentence.replace('______', 'blank')}
                    label=""
                    size="xs"
                  />
                </p>
              )}
              <input
                type="text"
                value={spellingInput}
                onChange={(e) => setSpellingInput(e.target.value)}
                placeholder="Type the word..."
                disabled={selected !== null}
                autoComplete="off"
                spellCheck={false}
              />
              <button
                type="submit"
                className="btn"
                disabled={selected !== null || !spellingInput.trim()}
              >
                Check spelling
              </button>
            </form>
          ) : (
            <>
              <p className="quiz-prompt">
                {question.prompt}
                {question.word?.word && (
                  <TextToSpeechButton text={question.word.word} label="" size="xs" />
                )}
              </p>
              {question.sentence && <p className="quiz-sentence">{question.sentence}</p>}
              <div className="quiz-choices">
                {question.choices?.map((choice) => {
                  const isSelected = selected === choice.label
                  const showResult = selected !== null
                  let className = 'quiz-choice-btn'
                  if (showResult && choice.isCorrect) className += ' quiz-choice-correct'
                  if (showResult && isSelected && !choice.isCorrect) {
                    className += ' quiz-choice-wrong'
                  }
                  if (isSelected) className += ' quiz-choice-selected'

                  return (
                    <button
                      key={choice.label}
                      type="button"
                      className={className}
                      disabled={selected !== null}
                      onClick={() => handleChoice(choice)}
                    >
                      {choice.label}
                    </button>
                  )
                })}
              </div>
            </>
          )}
        </div>
      )}

      {feedback && (
        <div className={`card vocab-feedback-card vocab-feedback-${feedback.type}`}>
          <p className="vocab-feedback-message">{feedback.message}</p>
          {feedback.explanation && (
            <p>
              <span className="label">Meaning</span> {feedback.explanation}
            </p>
          )}
          <CollapsibleNativeNote note={feedback.persian} />
          {feedback.example && (
            <p className="quiz-example">
              <span className="label">Example</span> {feedback.example}
              <TextToSpeechButton text={feedback.example} label="" size="xs" />
            </p>
          )}
          {feedback.showRepeatNote && (
            <p className="muted">This word will appear again later in this quiz.</p>
          )}
          {feedback.word && (
            <div className="vocab-feedback-actions">
              <TextToSpeechButton text={feedback.word} label="Hear word" size="sm" />
            </div>
          )}
          {writingReply && (
            <div className="vocab-writing-feedback">
              <AssistantMessage content={writingReply} />
            </div>
          )}
          {canAdvance && !showFinishAnyway && (
            <button type="button" className="btn btn-secondary" onClick={handleNextQuestion}>
              Next question
            </button>
          )}
          {showFinishAnyway && (
            <div className="vocab-finish-anyway">
              <p className="muted">
                {reviewQueueCount} review word{reviewQueueCount === 1 ? '' : 's'} still pending.
              </p>
              <button type="button" className="btn" onClick={handleNextQuestion}>
                Continue review
              </button>
              <button type="button" className="btn btn-secondary" onClick={handleFinishAnyway}>
                Finish anyway
              </button>
            </div>
          )}
        </div>
      )}

      {!active && summary.review > 0 && mode !== 'review_mistakes' && (
        <p className="muted">
          {summary.review} word{summary.review === 1 ? '' : 's'} marked for review.
          Try &ldquo;Review vocab mistakes&rdquo; or visit{' '}
          <Link to="/mistakes">Mistakes</Link>.
        </p>
      )}
    </div>
  )
}
