import CollapsibleNativeNote from './CollapsibleNativeNote'

export default function VocabFlashcard({
  word,
  partOfSpeech = '',
  category = '',
  cefrLevel = '',
  definition = '',
  persianMeaning = '',
  example = '',
  collocations = [],
  shadowingSentence = '',
  commonMistake = '',
  correction = '',
  revealed = false,
  onReveal,
  onHide,
  progressLabel = '',
  children,
  large = true,
  showCategoryOnFront = true,
}) {
  return (
    <div className={`vocab-flashcard card ${large ? 'vocab-flashcard-large' : ''}`}>
      {progressLabel && <p className="flashcard-progress">{progressLabel}</p>}

      <div className="vocab-flashcard-front">
        <h2 className="flashcard-word">{word}</h2>
        {(partOfSpeech || (showCategoryOnFront && category) || cefrLevel) && (
          <div className="tag-list flashcard-meta">
            {cefrLevel && <span className="tag">{cefrLevel}</span>}
            {showCategoryOnFront && category && (
              <span className="tag">{category.replace(/_/g, ' ')}</span>
            )}
            {partOfSpeech && <span className="tag">{partOfSpeech}</span>}
          </div>
        )}
      </div>

      {!revealed ? (
        <button type="button" className="btn btn-secondary reveal-btn" onClick={onReveal}>
          Reveal answer
        </button>
      ) : (
        <div className="flashcard-back">
          {definition && (
            <div className="flashcard-field">
              <span className="label">Definition</span>
              <p>{definition}</p>
            </div>
          )}
          <CollapsibleNativeNote note={persianMeaning} className="flashcard-native-note" />
          {example && (
            <div className="flashcard-field">
              <span className="label">Example</span>
              <p className="muted">{example}</p>
            </div>
          )}
          {collocations?.length > 0 && (
            <div className="flashcard-field">
              <span className="label">Collocations</span>
              <p>{collocations.join(' · ')}</p>
            </div>
          )}
          {shadowingSentence && (
            <div className="flashcard-field">
              <span className="label">Shadowing sentence</span>
              <p>{shadowingSentence}</p>
            </div>
          )}
          {commonMistake && (
            <div className="flashcard-field">
              <span className="label">Common mistake</span>
              <p className="error-text">{commonMistake}</p>
            </div>
          )}
          {correction && (
            <div className="flashcard-field">
              <span className="label">Correction</span>
              <p>{correction}</p>
            </div>
          )}
          {onHide && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onHide}>
              Hide answer
            </button>
          )}
          {children}
        </div>
      )}
    </div>
  )
}
