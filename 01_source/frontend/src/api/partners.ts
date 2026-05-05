import { api } from './client'

export type BulkProductItem = {
  partner_sku: string
  name: string
  category_id: string
  dimensions?: { width_mm?: number; height_mm?: number; depth_mm?: number; weight_g?: number }
  price_cents: number
  currency?: string
  images?: string[]
  compatibility_rules?: {
    requires_signature?: boolean
    is_fragile?: boolean
    temperature_zone?: string
  }
}

export const partnersApi = {
  getProducts: (id: string) => api.get<unknown>(`/v1/partners/${id}/products`),

  createProduct: (id: string, data: Record<string, unknown>) =>
    api.post(`/v1/partners/${id}/products`, data),

  bulkUpload: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/v1/partners/${id}/products/bulk`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  checkCompatibility: (id: string, productSku: string, lockerId: string) =>
    api.post<{ compatible: boolean; reason?: string | null; recommended_slot_size?: string | null }>(
      `/v1/partners/${id}/check-compatibility`,
      { partner_sku: productSku, locker_id: lockerId },
    ),

  getWebhooks: (id: string) => api.get<unknown>(`/v1/partners/${id}/webhooks`),

  createWebhook: (id: string, url: string, events: string[]) =>
    api.post(`/v1/partners/${id}/webhooks`, { url, events }),

  getDeliveries: (id: string) => api.get<WebhookDeliveryRow[]>(`/v1/partners/${id}/webhooks/deliveries`),
}

export type WebhookDeliveryRow = {
  id: string
  subscription_id: string
  event_type: string
  status: string
  attempts: number
  last_error: string | null
  created_at: string
}

export type WebhookSubscriptionRow = {
  id: string
  partner_id: string
  url: string
  events: string[]
  is_active: boolean
  created_at: string
}
