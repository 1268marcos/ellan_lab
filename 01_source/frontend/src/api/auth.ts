import axios from 'axios'

export const AUTH_STORAGE_KEY = 'ellan.auth'

export type AuthPartner = {
  partnerId: string
  partnerName: string
  apiKey: string
  token: string
  profile: 'admin' | 'partner' | 'ops'
}

export type LoginPayload = {
  partner_id: string
  api_key: string
}

export type LoginResponse = {
  token?: string
  access_token?: string
  partner_name?: string
  name?: string
  partner?: {
    id?: string
    name?: string
    role?: 'admin' | 'partner' | 'ops'
  }
  profile?: 'admin' | 'partner' | 'ops'
  role?: 'admin' | 'partner' | 'ops'
}

function inferProfile(partnerId: string): 'admin' | 'partner' | 'ops' {
  const p = partnerId.toLowerCase()
  if (p.includes('admin')) return 'admin'
  if (p.includes('ops')) return 'ops'
  return 'partner'
}

function formatLoginError(error: unknown): string {
  const ax = error as {
    response?: { status?: number; data?: { detail?: unknown; message?: string } }
    message?: string
  }
  const detail = ax.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        const row = item as { msg?: string; loc?: unknown[] }
        const loc = Array.isArray(row.loc) ? row.loc.join('.') : ''
        return [loc, row.msg].filter(Boolean).join(': ')
      })
      .join(' | ')
  }
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in (detail as object)) {
    return String((detail as { message?: string }).message)
  }
  return ax.response?.data?.message || ax.message || 'Falha no login'
}

export async function loginWithApiKey(payload: LoginPayload): Promise<AuthPartner> {
  let data: LoginResponse
  try {
    const primary = await axios.post<LoginResponse>('/auth/v1/login', payload, { timeout: 15_000 })
    data = primary.data
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status !== 404 && status !== 422 && status !== 502 && status !== 503) {
      throw new Error(formatLoginError(error))
    }
    try {
      const fallback = await axios.post<LoginResponse>('/api/v1/partners/login', payload, {
        timeout: 15_000,
      })
      data = fallback.data
    } catch (fallbackError: unknown) {
      throw new Error(formatLoginError(fallbackError))
    }
  }
  return {
    partnerId: String(data.partner?.id ?? payload.partner_id),
    partnerName: String(data.partner?.name ?? data.partner_name ?? data.name ?? payload.partner_id),
    apiKey: payload.api_key,
    token: String(data.token ?? data.access_token ?? payload.api_key),
    profile: (data.profile ?? data.role ?? data.partner?.role ?? inferProfile(payload.partner_id)) as
      | 'admin'
      | 'partner'
      | 'ops',
  }
}

export function saveAuth(auth: AuthPartner): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth))
}

export function loadAuth(): AuthPartner | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as AuthPartner
    if (!parsed.partnerId || !parsed.apiKey) return null
    return parsed
  } catch {
    return null
  }
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}
