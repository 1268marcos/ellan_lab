import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function PrivateRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, canAccess } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!canAccess(location.pathname)) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}
