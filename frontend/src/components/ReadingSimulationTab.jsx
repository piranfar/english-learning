import { useEffect, useState } from 'react'
import ReadingSessionPanel from './ReadingSessionPanel'
import { apiRequest } from '../api/client'

const STAGES = [
  { value: 'b2_toefl_80', label: 'B2 / TOEFL 80+ Readiness' },
  { value: 'academic_toefl_100', label: 'TOEFL 100+ Readiness' },
]

const SIMULATION_TYPES = [
  {
    value: 'complete_the_words',
    label: 'Complete the Words',
    description: 'TOEFL-style practice with word-choice questions in context.',
  },
  {
    value: 'daily_life_reading',
    label: 'Read in Daily Life',
    description: 'Practical notices, emails, and campus-style texts.',
  },
  {
    value: 'academic_passage',
    label: 'Read an Academic Passage',
    description: 'Academic passage with mixed comprehension questions.',
  },
]

export default function ReadingSimulationTab({ provider, loading, setLoading, setError }) {
  const [stage, setStage] = useState('b2_toefl_80')
  const [simulationType, setSimulationType] = useState('academic_passage')
  const [session, setSession] = useState(null)

  useEffect(() => {
    async function loadContext() {
      try {
        const data = await apiRequest('/reading/context/')
        if (data.context?.stage) setStage(data.context.stage)
      } catch {
        // keep default
      }
    }
    loadContext()
  }, [])

  async function handleGenerate(event) {
    event.preventDefault()
    if (loading) return

    setLoading(true)
    setError('')
    setSession(null)

    try {
      const data = await apiRequest('/reading/generate/', {
        method: 'POST',
        json: {
          stage,
          simulation_type: simulationType,
          length: 'toefl_style',
          lesson_focus: 'none',
          question_focus: 'mixed',
          provider,
        },
      })
      setSession(data.session)
    } catch (err) {
      setError(err.message || 'Failed to generate TOEFL-style reading practice')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="reading-simulation-panel">
      <p className="muted reading-disclaimer">
        Original TOEFL-style practice — not official ETS/TOEFL questions.
      </p>

      {!session ? (
        <form onSubmit={handleGenerate} className="card card-compact">
          <div className="form-row">
            <label className="form-field">
              Stage
              <select value={stage} onChange={(e) => setStage(e.target.value)} disabled={loading}>
                {STAGES.map((entry) => (
                  <option key={entry.value} value={entry.value}>{entry.label}</option>
                ))}
              </select>
            </label>
          </div>

          <fieldset className="reading-simulation-types">
            <legend>Task type</legend>
            {SIMULATION_TYPES.map((entry) => (
              <label key={entry.value} className="reading-simulation-option">
                <input
                  type="radio"
                  name="simulation_type"
                  value={entry.value}
                  checked={simulationType === entry.value}
                  onChange={() => setSimulationType(entry.value)}
                  disabled={loading}
                />
                <span>
                  <strong>{entry.label}</strong>
                  <span className="muted"> — {entry.description}</span>
                </span>
              </label>
            ))}
          </fieldset>

          <button type="submit" disabled={loading}>
            {loading ? 'Generating…' : 'Start TOEFL-style reading simulation'}
          </button>
        </form>
      ) : (
        <ReadingSessionPanel
          session={session}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
          onReset={() => setSession(null)}
        />
      )}
    </div>
  )
}
