import { createContext, useContext, useMemo, useState } from 'react'
import { clearAuth, loadAuth, loginWithApiKey, saveAuth, type AuthPartner } from '../api/auth'

type LoginInput = {
  partnerId: string
  apiKey: string
}

type UserProfile = 'admin' | 'partner' | 'ops'

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
  admin: ['/dashboard', '/partners', '/finance', '/ops', '/analytics', '/settings', '/fiscal', '/intelligence', '/lifecycle'],
  partner: [
    '/dashboard/partner',
    '/partners',
    '/intelligence',
    '/lifecycle',
    '/finance/wallet',
    '/finance/transactions',
    '/finance/billing/cycles',
    '/finance/invoices',
    '/finance/credit-notes',
    '/finance/disputes',
    '/settings/profile',
  ],
  ops: ['/dashboard/ops', '/ops', '/analytics', '/settings/profile', '/lifecycle'],
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
        if (!auth?.profile) return false
        const routes = PROFILE_ROUTES[auth.profile]
        return routes.some((p) => path === p || path.startsWith(`${p}/`))
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

