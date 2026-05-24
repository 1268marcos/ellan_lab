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

  listCurrencies: () => api.get<{ items: MoneyCurrency[]; total: number }>(`${BASE}/currencies`),
  createCurrency: (body: Record<string, unknown>) => api.post(`${BASE}/currencies`, body),

  listMethods: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-method-catalog`),
  createMethod: (body: Record<string, unknown>) => api.post(`${BASE}/payment-method-catalog`, body),

  listInterfaces: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-interface-catalog`),
  listWallets: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/wallet-provider-catalog`),

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
