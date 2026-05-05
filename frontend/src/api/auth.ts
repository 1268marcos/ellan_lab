import { api } from './client'

export const AUTH_STORAGE_KEY = 'ellan.auth'

export type AuthPartner = {
  partnerId: string
  partnerName: string
  apiKey: string
  token: string
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
}

export async function loginWithApiKey(payload: LoginPayload): Promise<AuthPartner> {
  const { data } = await api.post<LoginResponse>('/v1/partners/login', payload)
  return {
    partnerId: payload.partner_id,
    partnerName: String(data.partner_name ?? data.name ?? payload.partner_id),
    apiKey: payload.api_key,
    token: String(data.token ?? data.access_token ?? payload.api_key),
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
