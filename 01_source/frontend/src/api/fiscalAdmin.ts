import { api } from './client'

const BASE = '/api/fiscal-admin/v1/fiscal-admin'

export type UnifiedGap = {
  id: string
  source: 'admin' | 'billing'
  dedupe_key?: string | null
  gap_type: string
  severity: string
  status: string
  order_id?: string | null
  invoice_id?: string | null
  details?: Record<string, unknown> | null
  first_detected_at?: string | null
  last_detected_at?: string | null
  resolved_at?: string | null
}

export type GapWorkbenchResponse = {
  items: UnifiedGap[]
  total: number
  summary: {
    admin_count: number
    billing_count: number
    by_severity: Record<string, number>
    by_gap_type: Record<string, number>
  }
  billing_available: boolean
  billing_error?: string | null
  billing_scan?: Record<string, unknown> | null
  snapshot?: Record<string, unknown> | null
}

export type FiscalIssuer = {
  id: string
  name: string
  code: string
  issuer_type: string
  country: string
  active: boolean
}

export const fiscalAdminApi = {
  seed: () => api.post<Record<string, number>>(`${BASE}/seed`),

  listIssuers: () => api.get<{ issuers: FiscalIssuer[]; total: number }>(`${BASE}/fiscal-issuer-partners`),
  createIssuer: (body: Record<string, unknown>) => api.post<FiscalIssuer>(`${BASE}/fiscal-issuer-partners`, body),
  configureWebhook: (issuerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/fiscal-issuer-partners/${encodeURIComponent(issuerId)}/webhook`, body),
  rotateApiKey: (issuerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/fiscal-issuer-partners/${encodeURIComponent(issuerId)}/api-keys/rotate`,
    ),

  listDocuments: (order_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-documents`, { params: { order_id } }),
  listGaps: (status?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/reconciliation-gaps`, { params: { status } }),
  listGapsWorkbench: (params?: {
    status?: string
    date?: string
    refresh_billing?: boolean
    include_snapshot?: boolean
    limit?: number
  }) => api.get<GapWorkbenchResponse>(`${BASE}/fiscal-ops/reconciliation-gaps/workbench`, { params }),
  patchGap: (gapId: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/fiscal-ops/reconciliation-gaps/${encodeURIComponent(gapId)}`, body),
  patchGapWorkbench: (gapId: string, source: 'admin' | 'billing', body: Record<string, unknown>) =>
    api.patch(`${BASE}/fiscal-ops/reconciliation-gaps/workbench/${encodeURIComponent(gapId)}`, body, {
      params: { source },
    }),
  listProviderHealth: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/provider-health`),
  listTenants: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/tenant-config`),
  listProducts: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/product-fiscal-config`),
  listApprovals: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/accounting-approvals`),
  listCallbacks: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/authority-callbacks`),
  listClassificationLogs: (order_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-ops/classification-logs`, { params: { order_id } }),

  globalSummary: () => api.get<Record<string, number>>(`${BASE}/fiscal-global-ops/summary`),
  seedGlobal: () => api.post<Record<string, number>>(`${BASE}/fiscal-global-ops/seed-global`),
  listJurisdictions: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/jurisdictions`),
  listCorridors: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/corridors`),
  listCertifications: (issuer_id?: string, enriched = false) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/certifications`, {
      params: { issuer_id, enriched: enriched || undefined },
    }),
  getCorridor: (corridorCode: string) =>
    api.get<Record<string, unknown>>(`${BASE}/fiscal-global-ops/corridors/${encodeURIComponent(corridorCode)}`),
  retryWebhook: (deliveryId: string) =>
    api.post(`${BASE}/fiscal-global-ops/webhook-deliveries/${encodeURIComponent(deliveryId)}/retry`),
  testClassifySku: (sku: string, country = 'BR') =>
    api.post<Record<string, unknown>>(`${BASE}/fiscal-global-ops/classification-rules/test-classify`, null, {
      params: { sku, country },
    }),
  intelligenceDashboard: () => api.get<Record<string, number>>(`${BASE}/fiscal-intelligence/dashboard`),
  analyzeIntelligence: () => api.post<Record<string, number>>(`${BASE}/fiscal-intelligence/analyze`),
  listIntelligenceInsights: (status = 'OPEN') =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-intelligence/insights`, { params: { status } }),
  listContingencies: (active_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-intelligence/contingency-events`, {
      params: { active_only },
    }),
  registerContingency: (body: Record<string, unknown>) =>
    api.post(`${BASE}/fiscal-intelligence/contingency-events`, body),
  closeContingency: (eventId: string) =>
    api.post(`${BASE}/fiscal-intelligence/contingency-events/${encodeURIComponent(eventId)}/close`),
  listSloPolicies: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/slo-policies`),
  listClassRules: (country?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/classification-rules`, { params: { country } }),
  listWebhookDlq: (failed_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/webhook-deliveries`, {
      params: { failed_only },
    }),
  listReadiness: (band?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/fiscal-global-ops/integration-readiness`, { params: { band } }),
  recomputeReadiness: () => api.post(`${BASE}/fiscal-global-ops/integration-readiness/recompute`),
}
