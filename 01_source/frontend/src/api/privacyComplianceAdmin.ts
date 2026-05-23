import { api } from './client'

const BASE = '/api/privacy-compliance-admin/v1/privacy-compliance-admin'

export type PrivacyRegulation = {
  id: string
  code: string
  name: string
  jurisdiction: string
  active: boolean
  default_retention_days: number
  response_sla_days: number
  dpo_email?: string
}

export type PrivacyDashboard = {
  regulations: number
  active_policies: number
  pending_deletions: number
  pending_subject_requests: number
  consents_granted: number
  consents_revoked: number
  webhooks_active: number
}

export const privacyComplianceAdminApi = {
  seed: () => api.post(`${BASE}/seed`),
  dashboard: () => api.get<PrivacyDashboard>(`${BASE}/dashboard`),
  listRegulations: () => api.get<{ items: PrivacyRegulation[]; total: number }>(`${BASE}/regulations`),
  listPolicies: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/policy-versions`),
  listConsents: (regulation_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/consents`, {
      params: regulation_code ? { regulation_code } : undefined,
    }),
  listDeletions: (regulation_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/deletion-requests`, {
      params: regulation_code ? { regulation_code } : undefined,
    }),
  listSubjectRequests: (regulation_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/subject-requests`, {
      params: regulation_code ? { regulation_code } : undefined,
    }),
  listWebhooks: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/webhooks`),
  createConsent: (body: Record<string, unknown>) => api.post(`${BASE}/consents`, body),
  createDeletion: (body: Record<string, unknown>) => api.post(`${BASE}/deletion-requests`, body),
  createSubjectRequest: (body: Record<string, unknown>) => api.post(`${BASE}/subject-requests`, body),
  completeDeletion: (id: string) => api.patch(`${BASE}/deletion-requests/${id}`, { status: 'COMPLETED' }),
  upsertWebhook: (body: Record<string, unknown>) => api.put(`${BASE}/webhooks`, body),
  rotateApiKey: (regulationCode: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/regulations/${encodeURIComponent(regulationCode)}/api-keys/rotate`,
    ),
}
