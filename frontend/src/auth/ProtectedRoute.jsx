import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function ProtectedRoute({ children }) {
  const { authenticated, loading } = useAuth()

  if (loading) {
    return <p>Loading...</p>
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}
