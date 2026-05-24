import { api } from './client'

const BASE = '/api/money-cambio-admin/v1/money-cambio-admin'

export type MoneyCurrency = {
  id: number
  code: string
  name: string
  symbol?: string
  is_active: boolean
}

export type FxRate = {
  id: string
  base_currency: string
  quote_currency: string
  rate_date: string
  rate: string
  source: string
}

export const moneyCambioAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  globalDashboard: () => api.get<Record<string, unknown>>(`${BASE}/global-ops/dashboard`),
  listOperatingCountries: () => api.get<{ items: unknown[] }>(`${BASE}/operating-countries`),
  listCurrencies: () => api.get<{ items: MoneyCurrency[]; total: number }>(`${BASE}/currencies`),
  createCurrency: (body: Record<string, unknown>) => api.post(`${BASE}/currencies`, body),
  listMethods: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-method-catalog`),
  createMethod: (body: Record<string, unknown>) => api.post(`${BASE}/payment-method-catalog`, body),
  listMethodMatrix: () => api.get<{ items: unknown[] }>(`${BASE}/method-country-matrix`),
  listAliases: () => api.get<{ items: unknown[] }>(`${BASE}/payment-method-ui-alias`),
  listInterfaces: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-interface-catalog`),
  listWallets: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/wallet-provider-catalog`),
  listCorridors: () => api.get<{ items: unknown[] }>(`${BASE}/payment-corridors`),
  listCompliance: () => api.get<{ items: unknown[] }>(`${BASE}/compliance-limits`),
  listFxAudit: () => api.get<{ items: unknown[] }>(`${BASE}/fx-rate-audit`),
  listLockerPlayers: () => api.get<{ items: unknown[] }>(`${BASE}/locker-players`),
  listEcosystemSegments: () => api.get<{ items: unknown[] }>(`${BASE}/ecosystem-segments`),
  listPlayerRelations: () => api.get<{ items: unknown[] }>(`${BASE}/player-relations`),
  intelligenceDashboard: () => api.get<Record<string, unknown>>(`${BASE}/money-intelligence/dashboard`),
  listReadiness: () => api.get<{ items: unknown[] }>(`${BASE}/money-intelligence/readiness`),
  listInsights: () => api.get<{ items: unknown[] }>(`${BASE}/money-intelligence/insights`),
  analyzeIntelligence: () => api.post(`${BASE}/money-intelligence/analyze`),
  listSettlementSchedules: () => api.get<{ items: unknown[] }>(`${BASE}/money-intelligence/settlement-schedules`),
  listPaymentRails: () => api.get<{ items: unknown[] }>(`${BASE}/payment-rails`),
  treasuryDashboard: () => api.get<Record<string, unknown>>(`${BASE}/treasury/dashboard`),
  listFxLocks: () => api.get<{ items: unknown[] }>(`${BASE}/fx-locks`),
  pricingPreview: (body: Record<string, unknown>) => api.post<Record<string, unknown>>(`${BASE}/pricing/preview`, body),

  listFxRates: (params?: { base_currency?: string; quote_currency?: string }) =>
    api.get<{ items: FxRate[]; total: number }>(`${BASE}/fx-rates`, { params }),
  upsertFxRate: (body: Record<string, unknown>) => api.post(`${BASE}/fx-rates`, body),
  convert: (body: { amount_cents: number; from_currency: string; to_currency: string }) =>
    api.post<{ to_amount_cents: number; from_currency: string; to_currency: string }>(`${BASE}/fx-rates/convert`, body),

  listPartners: () => api.get<{ partners: unknown[]; total: number }>(`${BASE}/integration-partners`),
  createPartner: (body: Record<string, unknown>) => api.post(`${BASE}/integration-partners`, body),
  configureWebhook: (partnerId: string, body: { url: string; secret?: string }) =>
    api.put(`${BASE}/integration-partners/${encodeURIComponent(partnerId)}/webhook`, body),
  rotateApiKey: (partnerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/integration-partners/${encodeURIComponent(partnerId)}/api-keys/rotate`,
    ),
}
