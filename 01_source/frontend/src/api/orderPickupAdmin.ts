import { api } from './client'

const BASE = '/api/order-pickup-admin/v1/order-pickup-admin'

export type EcommercePartner = {
  id: string
  name: string
  code: string
  status: string
  active: boolean
}

export type LogisticsPartner = {
  id: string
  name: string
  code: string
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
  listLogistics: () => api.get<{ partners: LogisticsPartner[]; total: number }>(`${BASE}/logistics-partners`),
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
  updateOrder: (orderId: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/orders/${encodeURIComponent(orderId)}`, body),

  listPickups: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/pickups`, { params }),
  createPickup: (body: Record<string, unknown>) => api.post(`${BASE}/pickups`, body),

  listCredits: (params?: { order_id?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/credits`, { params }),
  createCredit: (body: Record<string, unknown>) => api.post(`${BASE}/credits`, body),

  listOutbox: (params?: { status?: string }) => api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-outbox`, { params }),
  replayOutbox: (outboxId: string) => api.post(`${BASE}/integration-outbox/${encodeURIComponent(outboxId)}/replay`),

  listFulfillment: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fulfillment-tracking`),
  updateFulfillment: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/fulfillment-tracking/${encodeURIComponent(id)}`, body),

  listOrderItems: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/order-items`, { params }),
  listPickupEvents: (params?: { pickup_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-events`, { params }),
  listPickupTokens: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-tokens`, { params }),
  listPickupAttempts: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/pickup-attempts`, { params }),
  listDomainOutbox: (params?: { status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/domain-event-outbox`, { params }),
  replayDomainOutbox: (id: string) => api.post(`${BASE}/domain-event-outbox/${encodeURIComponent(id)}/replay`),
}
