import { api } from './client'

const BASE = '/api/payment-gateway-admin/v1/payment-gateway-admin'

export type PaymentMethodCatalog = {
  id: number
  code: string
  name: string
  family?: string
  is_active: boolean
}

export type PaymentProviderPartner = {
  id: string
  name: string
  code: string
  provider_type: string
  region_code?: string
  active: boolean
}

export const paymentGatewayAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listMethods: (params?: { active_only?: boolean }) =>
    api.get<{ items: PaymentMethodCatalog[]; total: number }>(`${BASE}/payment-method-catalog`, { params }),
  createMethod: (body: Record<string, unknown>) => api.post(`${BASE}/payment-method-catalog`, body),
  deleteMethod: (id: number) => api.delete(`${BASE}/payment-method-catalog/${id}`),

  listInterfaces: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-interface-catalog`),
  listAliases: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-method-ui-alias`),
  listLockerMethods: (locker_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-payment-methods`, { params: { locker_id } }),

  listProviders: () =>
    api.get<{ partners: PaymentProviderPartner[]; total: number }>(`${BASE}/payment-provider-partners`),
  createProvider: (body: Record<string, unknown>) => api.post(`${BASE}/payment-provider-partners`, body),
  configureWebhook: (providerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/payment-provider-partners/${encodeURIComponent(providerId)}/webhook`, body),
  rotateApiKey: (providerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/payment-provider-partners/${encodeURIComponent(providerId)}/api-keys/rotate`,
    ),

  listDevices: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/gateway-ops/devices`),
  listIdempotency: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/gateway-ops/idempotency-keys`),
  listRiskEvents: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/gateway-ops/risk-events`),
  purgeExpiredIdempotency: () => api.post(`${BASE}/gateway-ops/idempotency-keys/purge-expired`),
}
