import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { getDashboard } from '../api/client'
import { loadRecentSessions, progressPercent } from '../services/learningSessionStorage'

export default function Profile() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [recentSessions, setRecentSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const dashboard = await getDashboard()
        setData(dashboard)
        setRecentSessions(loadRecentSessions(3))
      } catch (err) {
        setError(err.message || 'Failed to load profile')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <p>Loading profile...</p>
  if (error) return <p className="error">{error}</p>

  const profile = data?.profile

  return (
    <div className="page">
      <header className="page-header">
        <h1>Profile</h1>
        <p className="page-lead">Your account and learning summary.</p>
      </header>

      <section className="card">
        <h2>Account</h2>
        <dl className="settings-list">
          <div>
            <dt>Username</dt>
            <dd>{user?.username}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user?.email || 'Not set'}</dd>
          </div>
          <div>
            <dt>Account type</dt>
            <dd>{user?.is_staff ? 'Staff / admin' : 'Learner'}</dd>
          </div>
        </dl>
        {user?.is_staff && (
          <p className="muted">
            <Link to="/admin">Open admin area</Link> for prompt management.
          </p>
        )}
      </section>

      <section className="card">
        <h2>Learner profile</h2>
        {profile ? (
          <dl className="settings-list">
            <div>
              <dt>Level</dt>
              <dd>{profile.level}</dd>
            </div>
            <div>
              <dt>Goal</dt>
              <dd>{profile.goal || 'Not set'}</dd>
            </div>
            <div>
              <dt>Native language</dt>
              <dd>{profile.native_language}</dd>
            </div>
            <div>
              <dt>Weak areas</dt>
              <dd>
                {profile.weak_areas?.length > 0
                  ? profile.weak_areas.join(', ')
                  : 'None set'}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="muted">Profile data unavailable.</p>
        )}
        <p className="muted">
          Edit learner profile in Django admin under User profiles.
        </p>
      </section>

      {data && (
        <section className="card">
          <h2>Learning summary</h2>
          <dl className="settings-list">
            <div>
              <dt>Day streak</dt>
              <dd>{data.streak ?? 0}</dd>
            </div>
            <div>
              <dt>Vocabulary due</dt>
              <dd>{data.vocab_due ?? 0}</dd>
            </div>
            <div>
              <dt>Mistakes due</dt>
              <dd>{data.mistakes_due ?? 0}</dd>
            </div>
          </dl>
        </section>
      )}

      {recentSessions.length > 0 && (
        <section className="card">
          <h2>Saved sessions (this device)</h2>
          <ul className="recent-sessions-list">
            {recentSessions.map((session) => (
              <li key={session.id}>
                <div className="recent-session-meta">
                  <strong>{session.courseTitle || session.title || session.track}</strong>
                  <span className="muted">
                    {progressPercent(session.progress)}% complete
                  </span>
                </div>
              </li>
            ))}
          </ul>
          <p className="muted">
            <Link to="/lesson">Continue on the Lesson page</Link>
          </p>
        </section>
      )}
    </div>
  )
}
