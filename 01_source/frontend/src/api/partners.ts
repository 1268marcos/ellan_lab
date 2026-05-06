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

export type LockerSummaryResponse = {
  locker_id: string
  display_name?: string | null
  region?: string | null
  city?: string | null
  state?: string | null
  active: boolean
  slots_count: number
  slots_available: number
  active_pickups: number
  updated_at?: string | null
}

export type ActivePickupItem = {
  pickup_id: string
  order_id: string
  locker_id?: string | null
  slot?: string | null
  status?: string | null
  lifecycle_stage?: string | null
  ready_at?: string | null
  expires_at?: string | null
  updated_at?: string | null
}

export type ActivePickupsResponse = {
  partner_id: string
  total: number
  limit: number
  items: ActivePickupItem[]
}

export const partnersApi = {
  getProducts: (id: string) => api.get<unknown>(`/v1/partners/${id}/products`),

  getLockerSummary: (lockerId: string, partnerId: string) =>
    api.get<LockerSummaryResponse>(
      `/partner/v1/lockers/${encodeURIComponent(lockerId)}/summary`,
      { params: { partner_id: partnerId } },
    ),

  getActivePickups: (partnerId: string, limit = 50) =>
    api.get<ActivePickupsResponse>('/partner/v1/pickups/active', {
      params: { partner_id: partnerId, limit },
    }),

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
