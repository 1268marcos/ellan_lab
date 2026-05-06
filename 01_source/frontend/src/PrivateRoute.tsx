import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function PrivateRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, canAccess, profile } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!canAccess(location.pathname)) {
    const fallbackByProfile = profile ? `/dashboard/${profile}` : '/dashboard'
    if (location.pathname === fallbackByProfile) {
      return (
        <div className="p-6 text-center text-sm text-red-400">
          Acesso Negado
        </div>
      )
    }
    return <Navigate to={fallbackByProfile} replace />
  }

  return children
}
