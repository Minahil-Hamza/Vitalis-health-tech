import { Navigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { Layout } from './Layout'

export function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()

  if (loading) return <p className="route-loading">Loading...</p>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />

  return <Layout>{children}</Layout>
}
