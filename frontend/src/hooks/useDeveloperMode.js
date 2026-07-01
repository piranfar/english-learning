import { useEffect, useState } from 'react'
import { isDeveloperMode } from '../utils/developerMode'

export function useDeveloperMode() {
  const [devMode, setDevMode] = useState(isDeveloperMode)

  useEffect(() => {
    function syncDeveloperMode() {
      setDevMode(isDeveloperMode())
    }

    window.addEventListener('storage', syncDeveloperMode)
    window.addEventListener('fluentbridge-dev-mode', syncDeveloperMode)
    return () => {
      window.removeEventListener('storage', syncDeveloperMode)
      window.removeEventListener('fluentbridge-dev-mode', syncDeveloperMode)
    }
  }, [])

  return devMode
}
