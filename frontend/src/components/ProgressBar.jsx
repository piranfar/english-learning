function clampPercent(value) {
  if (Number.isNaN(value)) return 0
  return Math.min(100, Math.max(0, value))
}

export default function ProgressBar({
  label,
  valueLabel,
  percent,
  tone = 'primary',
  size = 'md',
  ariaLabel,
}) {
  const safePercent = clampPercent(percent)

  return (
    <div className={`progress-bar-row progress-bar-${size}`}>
      {(label || valueLabel) && (
        <div className="progress-bar-labels">
          {label && <span className="progress-bar-label">{label}</span>}
          {valueLabel && <span className="progress-bar-value">{valueLabel}</span>}
        </div>
      )}
      <div
        className="progress-bar-track"
        role="progressbar"
        aria-valuenow={Math.round(safePercent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={ariaLabel || label || 'Progress'}
      >
        <div
          className={`progress-bar-fill progress-bar-fill-${tone}`}
          style={{ width: `${safePercent}%` }}
        />
      </div>
    </div>
  )
}
