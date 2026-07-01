import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getPrompts } from '../api/client'
import { WRITING_TOOL_TRACKS } from '../data/writingTools'
import { loadActiveTab, saveActiveTab } from '../services/writingToolsStorage'
import { DEFAULT_AI_PROVIDER, pickDefaultProvider } from '../utils/defaultProvider'
import WritingCoach from '../components/WritingCoach'
import WritingEditingTab from '../components/writing/WritingEditingTab'
import WritingParaphraseTab from '../components/writing/WritingParaphraseTab'
import WritingSentenceBuilderTab from '../components/writing/WritingSentenceBuilderTab'
import WritingParagraphBuilderTab from '../components/writing/WritingParagraphBuilderTab'
import WritingLessonsTab from '../components/writing/WritingLessonsTab'

const TABS = [
  { id: 'practice', label: 'Practice' },
  { id: 'editing', label: 'Edit draft' },
  { id: 'paraphrasing', label: 'Paraphrase' },
  { id: 'sentence', label: 'Sentence builder' },
  { id: 'paragraph', label: 'Paragraph builder' },
  { id: 'lessons', label: 'Lessons' },
]

const PRACTICE_TRACKS = ['writing_coach', 'toefl_writing']

export default function Writing() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const [tab, setTab] = useState(() => {
    if (requestedTab && TABS.some((entry) => entry.id === requestedTab)) {
      return requestedTab
    }
    return loadActiveTab()
  })
  const [provider, setProvider] = useState(DEFAULT_AI_PROVIDER)
  const [prompts, setPrompts] = useState([])

  useEffect(() => {
    if (requestedTab && TABS.some((entry) => entry.id === requestedTab)) {
      setTab(requestedTab)
    }
  }, [requestedTab])

  useEffect(() => {
    saveActiveTab(tab)
  }, [tab])

  useEffect(() => {
    async function loadPrompts() {
      try {
        const data = await getPrompts()
        const writingPrompts = data.prompts.filter(
          (prompt) =>
            PRACTICE_TRACKS.includes(prompt.task_type) ||
            WRITING_TOOL_TRACKS.includes(prompt.task_type),
        )
        setPrompts(writingPrompts)
        const preferred = writingPrompts.find((p) => p.task_type === 'writing_edit_coach')
        setProvider(
          preferred?.provider ||
            pickDefaultProvider(writingPrompts, () => true),
        )
      } catch {
        // keep default provider
      }
    }
    loadPrompts()
  }, [])

  function handleTabChange(nextTab) {
    setTab(nextTab)
    setSearchParams({ tab: nextTab })
  }

  return (
    <div className="page writing-page-shell writing-compact-shell">
      <header className="writing-header-compact">
        <h1>Writing Coach</h1>
      </header>

      <div className="tabs writing-tabs writing-tabs-compact">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={tab === item.id ? 'tab tab-active' : 'tab'}
            onClick={() => handleTabChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'practice' && <WritingCoach />}

      {tab === 'editing' && (
        <WritingEditingTab provider={provider} onProviderChange={setProvider} prompts={prompts} />
      )}

      {tab === 'paraphrasing' && (
        <WritingParaphraseTab provider={provider} onProviderChange={setProvider} prompts={prompts} />
      )}

      {tab === 'sentence' && (
        <WritingSentenceBuilderTab provider={provider} onProviderChange={setProvider} prompts={prompts} />
      )}

      {tab === 'paragraph' && (
        <WritingParagraphBuilderTab provider={provider} onProviderChange={setProvider} prompts={prompts} />
      )}

      {tab === 'lessons' && (
        <WritingLessonsTab provider={provider} onProviderChange={setProvider} prompts={prompts} />
      )}
    </div>
  )
}
