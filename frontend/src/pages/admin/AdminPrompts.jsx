import { useEffect, useState } from 'react'
import {
  getAdminPrompts,
  resetAdminPrompt,
  updateAdminPrompt,
} from '../../api/client'

function ollamaModelNeedsTagWarning(modelName, provider) {
  if (provider !== 'ollama' || !modelName) return false
  return !modelName.includes(':')
}

export default function AdminPrompts() {
  const [prompts, setPrompts] = useState([])
  const [providerNotes, setProviderNotes] = useState({})
  const [selectedId, setSelectedId] = useState(null)
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [])

  async function loadPrompts() {
    setLoading(true)
    setError('')
    try {
      const data = await getAdminPrompts()
      setPrompts(data.prompts || [])
      setProviderNotes(data.provider_notes || {})
      if (!selectedId && data.prompts?.length) {
        selectPrompt(data.prompts[0])
      }
    } catch (err) {
      setError(err.message || 'Failed to load prompts')
    } finally {
      setLoading(false)
    }
  }

  function selectPrompt(prompt) {
    setSelectedId(prompt.id)
    setDraft({ ...prompt })
    setSuccess('')
    setError('')
  }

  async function handleSave() {
    if (!draft) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const updated = await updateAdminPrompt(draft.id, {
        title: draft.title,
        system_prompt: draft.system_prompt,
        model_name: draft.model_name,
        temperature: draft.temperature,
        max_tokens: draft.max_tokens,
        is_active: draft.is_active,
      })
      setDraft(updated)
      setPrompts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
      setSuccess('Prompt saved.')
    } catch (err) {
      setError(err.message || 'Failed to save prompt')
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    if (!draft) return
    if (
      !window.confirm(
        'Reset this prompt to the default seeded template? Your edits will be lost.',
      )
    ) {
      return
    }
    setResetting(true)
    setError('')
    setSuccess('')
    try {
      const updated = await resetAdminPrompt(draft.id)
      setDraft(updated)
      setPrompts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
      setSuccess('Prompt reset to default.')
    } catch (err) {
      setError(err.message || 'Failed to reset prompt')
    } finally {
      setResetting(false)
    }
  }

  if (loading) {
    return <p className="muted">Loading prompt templates...</p>
  }

  const isEmpty = !draft?.system_prompt?.trim()

  return (
    <div className="page admin-prompts-page">
      <header className="page-header">
        <h2>Prompt management</h2>
        <p className="page-lead muted">
          Staff-only. Learners never see this page. Ollama models need exact tags
          (e.g. qwen2.5:7b).
        </p>
      </header>

      {error && <p className="error">{error}</p>}
      {success && <p className="success-msg">{success}</p>}

      <div className="admin-prompts-layout">
        <aside className="card admin-prompts-list">
          <h3>Templates</h3>
          <ul className="admin-prompt-items">
            {prompts.map((prompt) => (
              <li key={prompt.id}>
                <button
                  type="button"
                  className={`admin-prompt-item${
                    selectedId === prompt.id ? ' active' : ''
                  }`}
                  onClick={() => selectPrompt(prompt)}
                >
                  <strong>{prompt.title}</strong>
                  <span className="muted">
                    {prompt.task_type} · {prompt.provider}
                  </span>
                  {prompt.is_empty && (
                    <span className="prompt-model-warning">Empty</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {draft && (
          <section className="card admin-prompt-editor">
            <div className="admin-prompt-editor-header">
              <div>
                <h3>{draft.title}</h3>
                <p className="muted">
                  Track: <strong>{draft.task_type}</strong> · Provider:{' '}
                  <strong>{draft.provider}</strong>
                </p>
                {providerNotes[draft.provider] && (
                  <p className="admin-provider-note">{providerNotes[draft.provider]}</p>
                )}
                {draft.updated_at && (
                  <p className="muted">Last updated: {new Date(draft.updated_at).toLocaleString()}</p>
                )}
              </div>
              <div className="btn-group">
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={handleSave}
                  disabled={saving || isEmpty}
                >
                  {saving ? 'Saving…' : 'Save'}
                </button>
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={handleReset}
                  disabled={resetting}
                >
                  {resetting ? 'Resetting…' : 'Reset to default'}
                </button>
              </div>
            </div>

            {isEmpty && (
              <p className="error admin-prompt-empty-warning">
                System prompt is empty. Saving is disabled until you add content or reset to
                default.
              </p>
            )}

            {ollamaModelNeedsTagWarning(draft.model_name, draft.provider) && (
              <p className="admin-prompt-empty-warning prompt-model-warning-inline">
                Check Ollama model tag — use names like qwen2.5:7b or llama3.2:3b.
              </p>
            )}

            <label className="form-field">
              Title
              <input
                type="text"
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              />
            </label>

            <div className="form-row">
              <label className="form-field">
                Model
                <input
                  type="text"
                  value={draft.model_name}
                  onChange={(e) => setDraft({ ...draft, model_name: e.target.value })}
                />
              </label>
              <label className="form-field">
                Temperature
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={draft.temperature}
                  onChange={(e) =>
                    setDraft({ ...draft, temperature: Number(e.target.value) })
                  }
                />
              </label>
              <label className="form-field">
                Max tokens
                <input
                  type="number"
                  min="1"
                  value={draft.max_tokens}
                  onChange={(e) =>
                    setDraft({ ...draft, max_tokens: Number(e.target.value) })
                  }
                />
              </label>
            </div>

            <label className="form-field">
              Active
              <select
                value={draft.is_active ? 'yes' : 'no'}
                onChange={(e) =>
                  setDraft({ ...draft, is_active: e.target.value === 'yes' })
                }
              >
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </label>

            <label className="form-field">
              System prompt
              <textarea
                rows={18}
                value={draft.system_prompt}
                onChange={(e) =>
                  setDraft({ ...draft, system_prompt: e.target.value })
                }
              />
            </label>
          </section>
        )}
      </div>
    </div>
  )
}
