import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export type EcosystemPartner = {
  id: string
  code: string
  name: string
  player_role: string
  parent_group: string
  country: string
  regions: string[]
  supports_lockers: boolean
  supports_marketplace: boolean
  integration_status?: string
  global_tier?: string
  active: boolean
}

export type PlayerCapability = {
  id: string
  ecosystem_player_id: string
  capability_code: string
  protocol: string
  direction: string
  enabled: boolean
  sandbox_ready: boolean
  production_ready: boolean
}

export type MarketplaceConnection = {
  id: string
  code: string
  name: string
  partner_role: string
  country: string
  active: boolean
  supports_marketplace: boolean
  supports_lockers: boolean
}

export type CarrierRate = {
  id: string
  carrier_code: string
  origin_zone: string
  destination_zone: string
  weight_tier_g: number
  amount_cents: number
  currency: string
  valid_from: string
  is_active: boolean
}

export const integrationsApi = {
  listPartners: (params?: Record<string, string | boolean>) =>
    api.get<{ items: EcosystemPartner[]; total: number }>('/partners', { params }),
  getPartner: (id: string) => api.get<EcosystemPartner>(`/partners/${encodeURIComponent(id)}`),
  createPartner: (body: Partial<EcosystemPartner>) => api.post<EcosystemPartner>('/partners', body),
  updatePartner: (id: string, body: Partial<EcosystemPartner>) =>
    api.put<EcosystemPartner>(`/partners/${encodeURIComponent(id)}`, body),
  deletePartner: (id: string) => api.delete(`/partners/${encodeURIComponent(id)}`),
  listCapabilities: (partnerId: string) =>
    api.get<{ items: PlayerCapability[]; total: number }>(
      `/partners/${encodeURIComponent(partnerId)}/capabilities`,
    ),
  createCapability: (partnerId: string, body: Partial<PlayerCapability>) =>
    api.post<PlayerCapability>(`/partners/${encodeURIComponent(partnerId)}/capabilities`, body),
  listMarketplaceConnections: (params?: Record<string, string>) =>
    api.get<{ items: MarketplaceConnection[]; total: number }>('/marketplaces/connections', { params }),
  listCarrierRates: (params?: Record<string, string>) =>
    api.get<{ items: CarrierRate[]; total: number }>('/carriers/rates', { params }),
  createCarrierRate: (body: Partial<CarrierRate>) => api.post<CarrierRate>('/carriers/rates', body),
  updateRateLimit: (partnerId: string, limit_per_minute: number) =>
    api.put(`/partners/${encodeURIComponent(partnerId)}/rate-limit`, { limit_per_minute }),
  getHealth: (partnerId: string) =>
    api.get<{ items: Array<{ status: string; latency_ms: number; checked_at: string }> }>(
      `/partners/${encodeURIComponent(partnerId)}/health`,
    ),
  runHealthCheck: (partnerId: string, endpoint_url?: string) =>
    api.post(`/partners/${encodeURIComponent(partnerId)}/health/check`, { endpoint_url }),
  testWebhook: (body: Record<string, unknown>) =>
    api.post<{ ok: boolean; http_status: number; signature: string }>('/partners/webhook/test', body),
}
