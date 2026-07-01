import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getMe, login as apiLogin, logout as apiLogout } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authenticated, setAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    const data = await getMe()
    setAuthenticated(data.authenticated)
    setUser(data.user)
    return data
  }, [])

  useEffect(() => {
    refresh()
      .catch(() => {
        setAuthenticated(false)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [refresh])

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password)
    setAuthenticated(true)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(async () => {
    await apiLogout()
    setAuthenticated(false)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      authenticated,
      loading,
      login,
      logout,
      refresh,
    }),
    [user, authenticated, loading, login, logout, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
