import { createContext, useContext, useMemo, useState } from 'react'
import { clearAuth, loadAuth, loginWithApiKey, saveAuth, type AuthPartner } from './api/auth'

type LoginInput = {
  partnerId: string
  apiKey: string
}

type AuthContextValue = {
  auth: AuthPartner | null
  isAuthenticated: boolean
  login: (input: LoginInput) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthPartner | null>(() => loadAuth())

  const value = useMemo<AuthContextValue>(
    () => ({
      auth,
      isAuthenticated: Boolean(auth?.token && auth.apiKey),
      login: async ({ partnerId, apiKey }) => {
        const next = await loginWithApiKey({ partner_id: partnerId, api_key: apiKey })
        setAuth(next)
        saveAuth(next)
      },
      logout: () => {
        setAuth(null)
        clearAuth()
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
