import { useDeveloperMode } from '../hooks/useDeveloperMode'

export default function DeveloperProviderSelect({
  label = 'AI provider',
  value,
  options = [],
  onChange,
  disabled = false,
  className = '',
}) {
  const devMode = useDeveloperMode()
  const uniqueOptions = [...new Set(options.filter(Boolean))]

  if (!devMode || uniqueOptions.length === 0) {
    return null
  }

  return (
    <label className={`form-field developer-provider-select ${className}`.trim()}>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        {uniqueOptions.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}
