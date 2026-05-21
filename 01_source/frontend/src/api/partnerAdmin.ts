import { api } from './client'

const BASE = '/api/partner-admin/v1/partner-admin'

export type EcommercePartner = {
  id: string
  name: string
  code: string
  integration_type: string
  api_base_url?: string
  active: boolean
  status: string
  country: string
  sla_pickup_hours: number
  support_email?: string
}

export type LogisticsPartner = {
  id: string
  name: string
  code: string
  integration_type: string
  api_base_url?: string
  active: boolean
  country: string
  default_sla_hours: number
}

export type UserSummary = { id: string; full_name: string; email: string; is_active: boolean }

export type UserRole = {
  id: string
  user_id: string
  role: string
  scope_type: string
  scope_id?: string
  is_active: boolean
  granted_at: string
  revoked_at?: string
}

export const partnerAdminApi = {
  listEcommerce: (params?: { active_only?: boolean }) =>
    api.get<{ partners: EcommercePartner[]; total: number }>(`${BASE}/ecommerce-partners`, { params }),
  createEcommerce: (body: Record<string, unknown>) => api.post<EcommercePartner>(`${BASE}/ecommerce-partners`, body),
  updateEcommerce: (id: string, body: Record<string, unknown>) =>
    api.patch<EcommercePartner>(`${BASE}/ecommerce-partners/${encodeURIComponent(id)}`, body),
  deleteEcommerce: (id: string) => api.delete(`${BASE}/ecommerce-partners/${encodeURIComponent(id)}`),

  listLogistics: (params?: { active_only?: boolean }) =>
    api.get<{ partners: LogisticsPartner[]; total: number }>(`${BASE}/logistics-partners`, { params }),
  createLogistics: (body: Record<string, unknown>) => api.post<LogisticsPartner>(`${BASE}/logistics-partners`, body),
  updateLogistics: (id: string, body: Record<string, unknown>) =>
    api.patch<LogisticsPartner>(`${BASE}/logistics-partners/${encodeURIComponent(id)}`, body),
  deleteLogistics: (id: string) => api.delete(`${BASE}/logistics-partners/${encodeURIComponent(id)}`),

  listUsers: () => api.get<{ users: UserSummary[]; total: number }>(`${BASE}/users`),
  listUserRoles: (params?: { user_id?: string; active_only?: boolean }) =>
    api.get<{ roles: UserRole[]; total: number }>(`${BASE}/user-roles`, { params }),
  createUserRole: (body: { user_id: string; role: string; scope_type?: string; scope_id?: string }) =>
    api.post<UserRole>(`${BASE}/user-roles`, body),
  revokeUserRole: (roleId: string) => api.post<UserRole>(`${BASE}/user-roles/${encodeURIComponent(roleId)}/revoke`),
  deleteUserRole: (roleId: string) => api.delete(`${BASE}/user-roles/${encodeURIComponent(roleId)}`),

  configureWebhook: (partnerId: string, partnerType: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/partners/${encodeURIComponent(partnerId)}/webhook`, body, { params: { partner_type: partnerType } }),
  rotateApiKey: (partnerId: string, partnerType: string) =>
    api.post<{ api_key: string; key_prefix: string }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/api-keys/rotate`, null, {
      params: { partner_type: partnerType },
    }),
  seed: () => api.post(`${BASE}/seed`),
}
