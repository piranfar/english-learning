import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function StaffRoute({ children }) {
  const { authenticated, loading, user } = useAuth()

  if (loading) {
    return <p>Loading...</p>
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />
  }

  if (!user?.is_staff) {
    return (
      <div className="page">
        <section className="card">
          <h1>Access denied</h1>
          <p className="muted">
            Prompt management and admin tools are available to staff accounts only.
          </p>
        </section>
      </div>
    )
  }

  return children
}
