import { useState } from 'react'

export default function ShowMeaningPanel({
  englishMeaning = '',
  nativeNote = '',
  buttonLabel = 'Show meaning',
  hideLabel = 'Hide meaning',
}) {
  const [open, setOpen] = useState(false)
  const hasEnglish = Boolean(englishMeaning?.trim())
  const hasNative = Boolean(nativeNote?.trim())
  if (!hasEnglish && !hasNative) return null

  return (
    <div className="show-meaning-panel">
      <button
        type="button"
        className="btn btn-secondary btn-sm native-note-toggle"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        {open ? hideLabel : buttonLabel}
      </button>
      {open && (
        <div className="native-note-panel">
          {hasEnglish && (
            <p className="show-meaning-english">
              <span className="label">Simple meaning</span> {englishMeaning}
            </p>
          )}
          {hasNative && (
            <p className="native-note-text persian">
              <span className="label">Native-language note</span> {nativeNote}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
