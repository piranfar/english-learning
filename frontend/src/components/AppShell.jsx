import { Link, NavLink } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { useTheme } from '../hooks/useTheme'

const NAV_ITEMS = [
  { to: '/today', label: 'Today', end: true },
  { to: '/progress', label: 'Progress', end: true },
  { to: '/lesson', label: 'Lesson', end: true },
  { to: '/speaking', label: 'Speaking', end: true },
  { to: '/shadowing', label: 'Shadowing', end: true },
  { to: '/writing', label: 'Writing', end: true },
  { to: '/reading', label: 'Reading', end: true },
  { to: '/listening', label: 'Listening', end: true },
  { to: '/vocab', label: 'Vocab', end: true },
  { to: '/mistakes', label: 'Mistake Clinic', end: true },
]

const FOOTER_TEXT =
  '© 2026 FluentBridge AI · Local-first English learning system · Built with Django and React.'

export default function AppShell({ children, showNav = true }) {
  const { authenticated, loading, user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [profileOpen, setProfileOpen] = useState(false)
  const profileRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <Link to={authenticated ? '/today' : '/login'} className="app-title">
              FluentBridge AI
            </Link>
            <p className="app-subtitle">
              Local-first AI tutor for academic English, TOEFL, speaking, shadowing, and vocabulary review.
            </p>
          </div>
          <div className="header-auth">
            <button
              type="button"
              className="theme-toggle"
              onClick={toggleTheme}
              aria-pressed={theme === 'dark'}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              <span className="theme-toggle-track">
                <span className="theme-toggle-thumb" />
              </span>
            </button>
            {loading ? (
              <span className="header-auth-meta">...</span>
            ) : authenticated ? (
              <>
                <div className="profile-menu" ref={profileRef}>
                  <button
                    type="button"
                    className="profile-menu-trigger"
                    onClick={() => setProfileOpen((open) => !open)}
                    aria-expanded={profileOpen}
                    aria-haspopup="true"
                  >
                    {user?.username} ▾
                  </button>
                  {profileOpen && (
                    <div className="profile-menu-dropdown">
                      <Link to="/profile" onClick={() => setProfileOpen(false)}>
                        Profile
                      </Link>
                      {user?.is_staff && (
                        <Link to="/admin" onClick={() => setProfileOpen(false)}>
                          Admin
                        </Link>
                      )}
                      <button
                        type="button"
                        className="profile-menu-logout"
                        onClick={() => {
                          setProfileOpen(false)
                          logout()
                        }}
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <Link to="/login" className="btn btn-secondary btn-sm">
                Login
              </Link>
            )}
          </div>
        </div>
      </header>

      {showNav && authenticated && (
        <nav className="app-nav" aria-label="Main navigation">
          <div className="nav-inner">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end !== false}
                className={({ isActive }) =>
                  isActive ? 'nav-link nav-link-active' : 'nav-link'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}

      <main className="app-main">
        <div className="content-container">{children}</div>
      </main>

      <footer className="app-footer">
        <div className="footer-inner">{FOOTER_TEXT}</div>
      </footer>
    </div>
  )
}
