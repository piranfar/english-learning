import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function PromptsRedirect() {
  const { user, loading } = useAuth()

  if (loading) {
    return <p>Loading...</p>
  }

  if (user?.is_staff) {
    return <Navigate to="/admin/prompts" replace />
  }

  return <Navigate to="/dashboard" replace />
}
