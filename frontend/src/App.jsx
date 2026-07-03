import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/AppShell'
import AdminLayout from './components/AdminLayout'
import PromptsRedirect from './components/PromptsRedirect'
import { AuthProvider, useAuth } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import StaffRoute from './auth/StaffRoute'
import Today from './pages/Today'
import Progress from './pages/Progress'
import Lesson from './pages/Lesson'
import Login from './pages/Login'
import Mistakes from './pages/Mistakes'
import Roadmap from './pages/Roadmap'
import Profile from './pages/Profile'
import Reading from './pages/Reading'
import Listening from './pages/Listening'
import Speaking from './pages/Speaking'
import Shadowing from './pages/Shadowing'
import Vocab from './pages/Vocab'
import Writing from './pages/Writing'
import AdminHome from './pages/admin/AdminHome'
import AdminPrompts from './pages/admin/AdminPrompts'
import './App.css'

function AppRoutes() {
  const { authenticated, loading } = useAuth()

  if (loading) {
    return <p>Loading...</p>
  }

  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to={authenticated ? '/today' : '/login'} replace />}
      />
      <Route path="/login" element={<Login />} />
      <Route path="/today" element={<ProtectedRoute><Today /></ProtectedRoute>} />
      <Route path="/progress" element={<ProtectedRoute><Progress /></ProtectedRoute>} />
      <Route path="/dashboard" element={<Navigate to="/today" replace />} />
      <Route path="/plan" element={<Navigate to="/today" replace />} />
      <Route path="/readiness" element={<Navigate to="/progress" replace />} />
      <Route path="/lesson" element={<ProtectedRoute><Lesson /></ProtectedRoute>} />
      <Route path="/roadmap" element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
      <Route path="/speaking" element={<ProtectedRoute><Speaking /></ProtectedRoute>} />
      <Route path="/shadowing" element={<ProtectedRoute><Shadowing /></ProtectedRoute>} />
      <Route path="/writing" element={<ProtectedRoute><Writing /></ProtectedRoute>} />
      <Route path="/reading" element={<ProtectedRoute><Reading /></ProtectedRoute>} />
      <Route path="/listening" element={<ProtectedRoute><Listening /></ProtectedRoute>} />
      <Route path="/vocab" element={<ProtectedRoute><Vocab /></ProtectedRoute>} />
      <Route path="/mistakes" element={<ProtectedRoute><Mistakes /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/settings" element={<Navigate to="/profile" replace />} />
      <Route path="/prompts" element={<ProtectedRoute><PromptsRedirect /></ProtectedRoute>} />
      <Route
        path="/admin"
        element={
          <StaffRoute>
            <AdminLayout />
          </StaffRoute>
        }
      >
        <Route index element={<AdminHome />} />
        <Route path="prompts" element={<AdminPrompts />} />
      </Route>
    </Routes>
  )
}

function AppContent() {
  const location = useLocation()
  const isLogin = location.pathname === '/login'
  const isAdmin = location.pathname.startsWith('/admin')

  return (
    <AppShell showNav={!isLogin && !isAdmin}>
      <AppRoutes />
    </AppShell>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
