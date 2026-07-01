import ProgressBar from './ProgressBar'

export default function HorizontalBarChart({ data, tone = 'warning' }) {
  if (!data?.length) return null

  const max = Math.max(...data.map((row) => row.value), 1)

  return (
    <div className="bar-chart">
      {data.map((row) => (
        <ProgressBar
          key={row.label}
          label={row.label}
          valueLabel={String(row.value)}
          percent={(row.value / max) * 100}
          tone={tone}
          size="sm"
        />
      ))}
    </div>
  )
}
