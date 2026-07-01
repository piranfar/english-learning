import DeveloperProviderSelect from '../DeveloperProviderSelect'
import { useDeveloperMode } from '../../hooks/useDeveloperMode'

export default function WritingToolProvider({ provider, prompts, track, tracks, onChange }) {
  const devMode = useDeveloperMode()
  const trackList = tracks || (track ? [track] : [])
  const options = [
    ...new Set(
      prompts.filter((p) => trackList.includes(p.task_type)).map((p) => p.provider),
    ),
  ]

  if (!devMode || options.length === 0) {
    return null
  }

  return (
    <div className="card card-compact writing-tool-provider">
      <DeveloperProviderSelect
        label="AI provider"
        value={provider}
        options={options}
        onChange={onChange}
      />
    </div>
  )
}
