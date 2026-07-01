import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import DeveloperProviderSelect from '../components/DeveloperProviderSelect'
import ReadingGenerateTab from '../components/ReadingGenerateTab'
import ReadingSummaryStrip from '../components/ReadingSummaryStrip'
import { useDeveloperMode } from '../hooks/useDeveloperMode'

const TABS = [
  { id: 'generate', label: 'Generate Practice' },
  { id: 'simulation', label: 'TOEFL Simulation' },
]

const VALID_TABS = new Set(TABS.map((entry) => entry.id))

function resolveTab(rawTab) {
  if (!rawTab || rawTab === 'analyze' || !VALID_TABS.has(rawTab)) {
    return 'generate'
  }
  return rawTab
}

export default function Reading() {
  const devMode = useDeveloperMode()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = resolveTab(searchParams.get('tab') || searchParams.get('mode'))
  const [tab, setTab] = useState(initialTab)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [provider, setProvider] = useState('openai')
  const [summaryRefresh, setSummaryRefresh] = useState(0)
  const [summaryMeta, setSummaryMeta] = useState({
    currentLesson: '—',
    level: 'B1',
    readingMode: 'general',
  })

  useEffect(() => {
    const rawTab = searchParams.get('tab') || searchParams.get('mode')
    const resolved = resolveTab(rawTab)

    if (rawTab !== resolved) {
      const nextParams = new URLSearchParams(searchParams)
      nextParams.set('tab', resolved)
      nextParams.delete('mode')
      setSearchParams(nextParams, { replace: true })
    }

    setTab(resolved)
  }, [searchParams, setSearchParams])

  const handleSessionChange = useCallback((session, meta) => {
    setSummaryMeta({
      currentLesson: meta?.contextNote || '—',
      level: meta?.level || 'B1',
      readingMode: session?.reading_mode || meta?.readingMode || 'general',
    })
  }, [])

  function handleTabChange(nextTab) {
    setTab(nextTab)
    setError('')
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('tab', nextTab)
    nextParams.delete('mode')
    setSearchParams(nextParams, { replace: true })
  }

  return (
    <div className="reading-page reading-page-compact">
      <h1>Reading Coach</h1>

      <ReadingSummaryStrip
        refreshKey={summaryRefresh}
        currentLesson={summaryMeta.currentLesson}
        level={summaryMeta.level}
        readingMode={summaryMeta.readingMode}
      />

      <div className="tabs reading-tabs">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className={tab === entry.id ? 'tab tab-active' : 'tab'}
            onClick={() => handleTabChange(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </div>

      {devMode && (
        <div className="selectors">
          <DeveloperProviderSelect
            label="AI provider (dev)"
            value={provider}
            options={['openai', 'ollama']}
            onChange={setProvider}
            disabled={loading}
          />
        </div>
      )}

      {error && <p className="error reading-error">{error}</p>}

      <ReadingGenerateTab
        key={tab}
        provider={devMode ? provider : undefined}
        loading={loading}
        setLoading={setLoading}
        setError={setError}
        onSessionChange={handleSessionChange}
        onProgressSaved={() => setSummaryRefresh((value) => value + 1)}
        defaultReadingMode={tab === 'simulation' ? 'toefl_2026' : 'general'}
        tabVariant={tab}
      />
    </div>
  )
}
