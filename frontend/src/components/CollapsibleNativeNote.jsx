import { useState } from 'react'

export default function CollapsibleNativeNote({
  note,
  notes = [],
  buttonLabel = 'Show native-language note',
  hideLabel = 'Hide native-language note',
  className = '',
}) {
  const [open, setOpen] = useState(false)
  const items = [...notes, note].filter(Boolean)
  if (items.length === 0) return null

  return (
    <div className={`native-note ${className}`.trim()}>
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
          {items.map((item) => (
            <p key={item} className="native-note-text persian">
              {item}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
