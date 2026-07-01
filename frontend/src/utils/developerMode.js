const STORAGE_KEY = 'fluentbridge_dev_mode'

export function isDeveloperMode() {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

export function setDeveloperMode(enabled) {
  try {
    localStorage.setItem(STORAGE_KEY, enabled ? 'true' : 'false')
  } catch {
    // ignore storage failures
  }
}

export function developerModeStorageKey() {
  return STORAGE_KEY
}
