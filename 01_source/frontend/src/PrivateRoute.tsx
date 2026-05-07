import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, type UserProfile } from './AuthContext'

function homeForProfile(profile: UserProfile | null): string {
  if (!profile) return '/dashboard'
  if (profile === 'ceo') return '/dashboard/ceo'
  if (profile === 'coo') return '/coo/dashboard'
  if (profile === 'ops') return '/dashboard/ops'
  if (profile === 'partner') return '/dashboard/partner'
  return '/dashboard/admin'
}

export default function PrivateRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, canAccess, profile } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!canAccess(location.pathname)) {
    const fallbackByProfile = homeForProfile(profile)
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
