import { createContext, useContext, useMemo, useState } from 'react'
import { clearAuth, loadAuth, loginWithApiKey, saveAuth, type AuthPartner } from '../api/auth'

type LoginInput = {
  partnerId: string
  apiKey: string
}

export type UserProfile = 'admin' | 'partner' | 'ops' | 'ceo' | 'coo'

type AuthContextValue = {
  auth: AuthPartner | null
  profile: UserProfile | null
  isAuthenticated: boolean
  login: (input: LoginInput) => Promise<AuthPartner>
  logout: () => void
  canAccess: (path: string) => boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const PROFILE_ROUTES: Record<UserProfile, string[]> = {
  admin: ['*'],
  ceo: ['*'],
  coo: ['/coo/*'],
  partner: [
    '/dashboard/partner',
    '/partners',
    '/finance/wallet',
    '/finance/billing/cycles',
    '/finance/invoices',
    '/intelligence/compatibility',
    '/settings/profile',
  ],
  ops: [
    '/dashboard/ops',
    '/ops',
    '/analytics',
    '/settings/profile',
    '/intelligence/predictive-health',
    '/partners/ops',
  ],
}

function normalizePath(path: string): string {
  const raw = String(path || '').trim()
  if (!raw) return '/'
  const collapsed = raw.replace(/\/+/g, '/')
  const withLeading = collapsed.startsWith('/') ? collapsed : `/${collapsed}`
  if (withLeading.length > 1 && withLeading.endsWith('/')) {
    return withLeading.slice(0, -1)
  }
  return withLeading
}

function matchesRoute(path: string, route: string): boolean {
  const normalizedPath = normalizePath(path)
  const normalizedRoute = normalizePath(route)
  if (normalizedRoute === '*') return true
  if (normalizedRoute.endsWith('/*')) {
    const base = normalizedRoute.slice(0, -2)
    return normalizedPath === base || normalizedPath.startsWith(`${base}/`)
  }
  return normalizedPath === normalizedRoute || normalizedPath.startsWith(`${normalizedRoute}/`)
}

export function canAccess(path: string, profile: UserProfile | null | undefined): boolean {
  if (!profile) return false
  const normalizedPath = normalizePath(path)
  const isCooPath = normalizedPath === '/coo' || normalizedPath.startsWith('/coo/')
  if (isCooPath) {
    if (profile !== 'coo') return false
    return PROFILE_ROUTES.coo.some((route) => matchesRoute(normalizedPath, route))
  }
  if (profile === 'coo') {
    return PROFILE_ROUTES.coo.some((route) => matchesRoute(normalizedPath, route))
  }
  if (profile === 'admin' || profile === 'ceo') return true
  const routes = PROFILE_ROUTES[profile] || []
  return routes.some((route) => matchesRoute(normalizedPath, route))
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthPartner | null>(() => loadAuth())

  const value = useMemo<AuthContextValue>(
    () => ({
      auth,
      profile: auth?.profile ?? null,
      isAuthenticated: Boolean(auth?.token && auth.apiKey),
      login: async ({ partnerId, apiKey }) => {
        const next = await loginWithApiKey({ partner_id: partnerId, api_key: apiKey })
        setAuth(next)
        saveAuth(next)
        return next
      },
      logout: () => {
        setAuth(null)
        clearAuth()
      },
      canAccess: (path: string) => {
        return canAccess(path, auth?.profile)
      },
    }),
    [auth],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

