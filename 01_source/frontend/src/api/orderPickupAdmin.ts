import { api } from './client'

const BASE = '/api/order-pickup-admin/v1/order-pickup-admin'

export type EcommercePartner = {
  id: string
  name: string
  code: string
  status: string
  active: boolean
}

export type OrderRow = {
  id: string
  status: string
  payment_status: string
  amount_cents: number
  ecommerce_partner_id?: string
  locker_id?: string
}

export const orderPickupAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listEcommerce: () => api.get<{ partners: EcommercePartner[]; total: number }>(`${BASE}/ecommerce-partners`),
  listLogistics: () => api.get<{ partners: unknown[]; total: number }>(`${BASE}/logistics-partners`),
  createEcommerce: (body: Record<string, unknown>) => api.post(`${BASE}/ecommerce-partners`, body),
  createLogistics: (body: Record<string, unknown>) => api.post(`${BASE}/logistics-partners`, body),
  configureWebhook: (partnerId: string, partnerType: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/partners/${encodeURIComponent(partnerId)}/webhook`, body, { params: { partner_type: partnerType } }),
  rotateApiKey: (partnerId: string, partnerType: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/partners/${encodeURIComponent(partnerId)}/api-keys/rotate`,
      null,
      { params: { partner_type: partnerType } },
    ),

  listOrders: (params?: { status?: string; partner_id?: string }) =>
    api.get<{ items: OrderRow[]; total: number }>(`${BASE}/orders`, { params }),
  createOrder: (body: Record<string, unknown>) => api.post(`${BASE}/orders`, body),

  listPickups: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/pickups`, { params }),
  listCredits: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/credits`, { params }),
  listOutbox: (params?: { status?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-outbox`, { params }),
  replayOutbox: (outboxId: string) => api.post(`${BASE}/integration-outbox/${encodeURIComponent(outboxId)}/replay`),
  listFulfillment: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fulfillment-tracking`),
}
