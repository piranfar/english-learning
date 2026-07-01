/**
 * localStorage for Writing tool tabs (Phase 1).
 */

const KEYS = {
  activeTab: 'fluentbridge_writing_active_tab',
  editing: 'fluentbridge_writing_editing',
  paraphrasing: 'fluentbridge_writing_paraphrasing',
  sentenceBuilder: 'fluentbridge_sentence_builder',
  paragraphBuilder: 'fluentbridge_paragraph_builder',
}

function safeParse(raw) {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false
  }
}

export function loadActiveTab() {
  const tab = localStorage.getItem(KEYS.activeTab)
  const valid = ['practice', 'editing', 'paraphrasing', 'sentence', 'paragraph', 'lessons']
  return valid.includes(tab) ? tab : 'practice'
}

export function saveActiveTab(tab) {
  try {
    localStorage.setItem(KEYS.activeTab, tab)
  } catch {
    // ignore
  }
}

export function loadToolState(key) {
  return safeParse(localStorage.getItem(key))
}

export function saveToolState(key, state) {
  return safeSet(key, { ...state, lastUpdatedAt: new Date().toISOString() })
}

export const TOOL_STORAGE_KEYS = KEYS
