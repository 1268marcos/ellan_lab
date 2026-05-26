import { api } from './client'

const BASE = '/api/capability-admin/v1/capability-admin'

export type CapabilityDashboard = {
  channels: number
  contexts: number
  regions: number
  profiles: number
  active_profiles: number
  payment_methods: number
  countries: number
  provinces: number
  locker_locations: number
  webhooks: number
  ecosystem_segments: number
  ecosystem_players: number
  player_bindings: number
  matrix_coverage_pct: number
  audit_events_24h: number
}

export type CapabilityProfile = {
  id: number
  profile_code: string
  name: string
  region_id: number
  channel_id: number
  context_id: number
  currency: string
  priority: number
  is_active: boolean
}

export type MatrixResponse = {
  regions: { code: string; name: string }[]
  channels: { code: string; name: string }[]
  cells: {
    region_code: string
    channel_code: string
    context_code: string
    has_profile: boolean
    profile_code: string | null
    is_active: boolean
    currency: string
  }[]
  coverage_pct: number
}

export const capabilityAdminApi = {
  health: () => api.get(`${BASE}/health`),
  dashboard: () => api.get<CapabilityDashboard>(`${BASE}/dashboard`),
  seed: () => api.post<Record<string, number>>(`${BASE}/seed`),
  matrix: () => api.get<MatrixResponse>(`${BASE}/matrix`),

  listChannels: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/channels`),
  listContexts: (channel_id?: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/contexts`, { params: { channel_id } }),
  listRegions: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/regions`),
  listProfiles: (active_only?: boolean) =>
    api.get<{ items: CapabilityProfile[]; total: number }>(`${BASE}/profiles`, { params: { active_only } }),
  getProfile: (id: number) => api.get<Record<string, unknown>>(`${BASE}/profiles/${id}`),
  createProfile: (body: Record<string, unknown>) => api.post(`${BASE}/profiles`, body),
  snapshotProfile: (id: number, created_by?: string) =>
    api.post(`${BASE}/profiles/${id}/snapshots`, null, { params: { created_by } }),
  listSnapshots: (profileId: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/profiles/${profileId}/snapshots/list`),

  listProfileActions: (profileId: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/profiles/${profileId}/actions`),
  listProfileMethods: (profileId: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/profiles/${profileId}/methods`),
  listProfileConstraints: (profileId: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/profiles/${profileId}/constraints`),
  listProfileTargets: (profileId: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/profiles/${profileId}/targets`),

  listPaymentMethods: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-methods`),
  listInterfaces: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-interfaces`),
  listWallets: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/wallet-providers`),
  listRequirements: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/requirements`),

  listCountries: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/geo/countries`),
  listProvinces: (country_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/geo/provinces`, { params: { country_code } }),
  listLockerLocations: (province_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/geo/locker-locations`, { params: { province_code } }),

  listSegments: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/segments`),
  listEcosystemPlayers: (segment_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/players`, { params: { segment_code } }),
  listBindings: (profile_id?: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/bindings`, { params: { profile_id } }),
  createBinding: (body: { profile_id: number; player_id: number; binding_role?: string }) =>
    api.post(`${BASE}/ecosystem/bindings`, body),
  listAuditLog: (profile_id?: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/audit-log`, { params: { profile_id } }),

  listWebhooks: (profile_id?: number) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/webhooks`, { params: { profile_id } }),
  upsertWebhook: (body: { profile_id: number; url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/webhooks`, body),
  testWebhook: (webhookId: string) => api.post(`${BASE}/webhooks/${encodeURIComponent(webhookId)}/test`),
  listWebhookDeliveries: (params?: { webhook_id?: string; dead_letter_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/webhooks/deliveries`, { params }),
  rotateApiKey: (profileId: number) =>
    api.post<{ api_key: string; key_prefix: string }>(`${BASE}/profiles/${profileId}/api-keys/rotate`),

  worldReport: () => api.get<Record<string, unknown>>(`${BASE}/intelligence/world-report`),
  recomputeIntelligence: () => api.post<Record<string, number>>(`${BASE}/intelligence/recompute`),
  listReadiness: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/intelligence/readiness`),
  listInsights: (status = 'OPEN') =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/intelligence/insights`, { params: { status } }),
  listRecommendations: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/intelligence/recommendations`),
  listCorridors: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/intelligence/corridors`),
  listFeatureFlags: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/intelligence/feature-flags`),
  listLockerPresence: (player_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/locker-presence`, { params: { player_code } }),

  resolveProfile: (body: { region_code: string; channel_code: string; context_code: string }) =>
    api.post<Record<string, unknown>>(`${BASE}/ops/resolve`, body),
  cloneProfile: (body: Record<string, unknown>) => api.post(`${BASE}/ops/profiles/clone`, body),
  compareProfiles: (profile_id_a: number, profile_id_b: number) =>
    api.get<Record<string, unknown>>(`${BASE}/ops/profiles/compare`, { params: { profile_id_a, profile_id_b } }),
  simulateFlow: (profileId: number, flow = 'pay') =>
    api.post<Record<string, unknown>>(`${BASE}/ops/profiles/${profileId}/simulate`, null, { params: { flow } }),
  exportProfile: (profileId: number) => api.get<Record<string, unknown>>(`${BASE}/ops/profiles/${profileId}/export`),
  listTemplates: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ops/templates`),
  listOpsJobs: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ops/jobs`),
}
