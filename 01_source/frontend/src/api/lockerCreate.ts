import { api } from './client'

const BASE = '/api/locker-create/v1/locker-create/lockers'

export type SlotConfig = {
  slot_size: string
  slot_count: number
  available_count?: number
  width_mm?: number
  height_mm?: number
  depth_mm?: number
  max_weight_g?: number
}

export type LockerCreatePayload = {
  id: string
  display_name: string
  region: string
  city: string
  state: string
  country?: string
  timezone?: string
  operator_id?: string
  temperature_zone?: string
  security_level?: string
  has_camera?: boolean
  has_alarm?: boolean
  has_kiosk?: boolean
  has_printer?: boolean
  has_card_reader?: boolean
  has_nfc?: boolean
  slot_configs?: SlotConfig[]
  copy_product_configs_from?: string
}

export type LockerOut = LockerCreatePayload & {
  active: boolean
  slots_count: number
  slots_available: number
  slot_configs: SlotConfig[]
  created_at: string
  updated_at: string
}

export type WebhookConfigurePayload = {
  url: string
  secret?: string
  events?: string[]
  active?: boolean
}

export const lockerCreateApi = {
  list: (params?: { region?: string; active_only?: boolean }) =>
    api.get<{ lockers: LockerOut[]; total: number }>(BASE, { params }),
  get: (lockerId: string) => api.get<LockerOut>(`${BASE}/${encodeURIComponent(lockerId)}`),
  create: (body: LockerCreatePayload) => api.post<LockerOut>(BASE, body),
  bulkCreate: (lockers: LockerCreatePayload[]) =>
    api.post<{ created: LockerOut[]; failed: Array<{ id: string; detail: unknown }> }>(`${BASE}/bulk`, {
      lockers,
    }),
  update: (lockerId: string, body: Partial<LockerCreatePayload> & { active?: boolean }) =>
    api.patch<LockerOut>(`${BASE}/${encodeURIComponent(lockerId)}`, body),
  delete: (lockerId: string) => api.delete(`${BASE}/${encodeURIComponent(lockerId)}`),
  configureWebhook: (lockerId: string, body: WebhookConfigurePayload) =>
    api.put(`${BASE}/${encodeURIComponent(lockerId)}/webhook`, body),
  getWebhook: (lockerId: string) => api.get(`${BASE}/${encodeURIComponent(lockerId)}/webhook`),
  rotateApiKey: (lockerId: string) =>
    api.post<{ locker_id: string; api_key: string; key_prefix: string }>(
      `${BASE}/${encodeURIComponent(lockerId)}/api-keys/rotate`,
    ),
  listApiKeys: (lockerId: string) =>
    api.get<{ locker_id: string; keys: Array<{ id: number; key_prefix: string; active: boolean }> }>(
      `${BASE}/${encodeURIComponent(lockerId)}/api-keys`,
    ),
}
