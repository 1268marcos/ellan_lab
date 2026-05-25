import { api } from './client'

const BASE = '/api/hardware-admin/v1/hardware-admin'

export type HardwareVendorPartner = {
  id: string
  name: string
  code: string
  vendor_type: string
  region_code?: string
  active: boolean
}

export type HardwareAsset = {
  id: string
  asset_code: string
  asset_category: string
  description: string
  locker_id?: string
  status: string
}

export type HardwareCrossDomainDashboard = {
  vendors: number
  operators: number
  runtime_lockers: number
  assets: number
  ecosystem_players: number
  marketplace_links: number
  payment_bindings: number
  carrier_bindings: number
  domain_references: number
  capex_records: number
  opex_records: number
  locker_features: number
  locker_slots: number
  devices: number
  sync_pending: number
  telemetry_24h: number
}

export type HardwareIntegrationHubSummary = {
  segments: number
  ecosystem_players: number
  capabilities: number
  player_relations: number
  locker_channel_bindings: number
  food_delivery_bindings: number
  aggregator_bindings: number
  marketplace_bindings: number
  readiness_rows: number
  avg_score: number
  bands: Record<string, number>
  partners_with_blockers: number
  marketplace_partners_linked: number
  capabilities_in_sync: number
  marketplace_capability_gaps: number
}

export const hardwareAdminApi = {
  seed: () => api.post(`${BASE}/seed`),
  seedDomainFull: (mirrorExternal = false) =>
    api.post<Record<string, unknown>>(`${BASE}/seed/domain-full`, null, {
      params: { mirror_external: mirrorExternal },
    }),

  getDashboard: () => api.get<HardwareCrossDomainDashboard>(`${BASE}/cross-domain/dashboard`),

  listVendors: () => api.get<{ vendors: HardwareVendorPartner[]; total: number }>(`${BASE}/hardware-vendors`),
  createVendor: (body: Record<string, unknown>) => api.post<HardwareVendorPartner>(`${BASE}/hardware-vendors`, body),
  configureWebhook: (vendorId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/hardware-vendors/${encodeURIComponent(vendorId)}/webhook`, body),
  rotateApiKey: (vendorId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/hardware-vendors/${encodeURIComponent(vendorId)}/api-keys/rotate`,
    ),

  listAssets: (params?: { locker_id?: string; vendor_id?: string }) =>
    api.get<{ items: HardwareAsset[]; total: number }>(`${BASE}/hardware-assets`, { params }),
  listOperators: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-operators`),
  listRuntimeLockers: (params?: { vendor_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/runtime-lockers`, { params }),

  listEcosystemPlayers: (params?: { segment?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/ecosystem-players`, { params }),
  seedEcosystemCatalog: () =>
    api.post<{ inserted: number }>(`${BASE}/cross-domain/ecosystem-players/seed-catalog`),
  listMarketplaceLinks: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/marketplace-links`, { params }),
  listPaymentBindings: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/payment-bindings`, { params }),
  listCarrierBindings: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/carrier-bindings`, { params }),
  listDomainReferences: (params?: { locker_id?: string; domain_type?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/domain-references`, { params }),

  getLocker360: (lockerId: string) =>
    api.get<Record<string, unknown>>(`${BASE}/cross-domain/lockers/${encodeURIComponent(lockerId)}/360`),
  scanCrossDomainGaps: (params?: { locker_id?: string }) =>
    api.get<Record<string, unknown>>(`${BASE}/cross-domain/gaps-scan`, { params }),
  verifyDomainReferences: (params?: { locker_id?: string }) =>
    api.post<unknown[]>(`${BASE}/cross-domain/domain-references/verify`, null, { params }),
  syncPaymentBindingsFromGateway: (params?: { locker_id?: string; dry_run?: boolean }) =>
    api.post<Record<string, unknown>>(`${BASE}/cross-domain/payment-bindings/sync-from-gateway`, null, { params }),
  alignEcosystemWithPartner: (apply = false) =>
    api.post<Record<string, unknown>>(`${BASE}/cross-domain/ecosystem-players/align-partner`, null, {
      params: { apply },
    }),

  getIntegrationHubSummary: () =>
    api.get<HardwareIntegrationHubSummary>(`${BASE}/integration-hub/summary`),
  listIntegrationSegments: () =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-hub/segments`),
  listIntegrationCapabilities: (params?: { player_code?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-hub/capabilities`, { params }),
  listPlayerRelations: (params?: { player_code?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-hub/player-relations`, { params }),
  listChannelBindings: (params?: { locker_id?: string; channel_type?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-hub/channel-bindings`, { params }),
  listIntegrationReadiness: (params?: { band?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-hub/integration-readiness`, { params }),
  getMarketplaceBridge: () =>
    api.get<{ items: unknown[]; marketplace_partners_linked: number; capabilities_in_sync: number }>(
      `${BASE}/integration-hub/marketplace-bridge`,
    ),
  syncMarketplaceMirror: () => api.post<Record<string, unknown>>(`${BASE}/integration-hub/sync-marketplace-mirror`),
  mirrorMarketplaceChannelPartners: () =>
    api.post<Record<string, unknown>>(`${BASE}/integration-hub/mirror-marketplace-channel-partners`),

  runtimeReconcileDiff: () => api.get<Record<string, unknown>>(`${BASE}/runtime-lockers/reconcile/diff`),
  runtimeReconcilePull: (params?: { locker_id?: string }) =>
    api.post<Record<string, unknown>>(`${BASE}/runtime-lockers/reconcile/pull`, null, { params }),
  runtimeReconcilePush: (params?: { locker_id?: string; enqueue_only?: boolean }) =>
    api.post<Record<string, unknown>>(`${BASE}/runtime-lockers/reconcile/push`, null, { params }),

  updatePaymentBinding: (bindingId: string, body: Record<string, unknown>) =>
    api.patch<Record<string, unknown>>(`${BASE}/cross-domain/payment-bindings/${encodeURIComponent(bindingId)}`, body),
  deletePaymentBinding: (bindingId: string) =>
    api.delete(`${BASE}/cross-domain/payment-bindings/${encodeURIComponent(bindingId)}`),

  getProfessionalOpsSummary: () => api.get<Record<string, unknown>>(`${BASE}/professional-ops/summary`),
  listCertifications: (params?: { player_code?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/professional-ops/certifications`, { params }),
  listCorridors: () => api.get<unknown[]>(`${BASE}/professional-ops/corridors`),
  listIncidents: (open_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/professional-ops/incidents`, { params: { open_only } }),
  listOnboardingRuns: () => api.get<unknown[]>(`${BASE}/professional-ops/onboarding/runs`),
  listAuditLog: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/professional-ops/audit-log`),
  listWebhookDeliveries: (params?: { status?: string; webhook_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/professional-ops/capability-webhooks/deliveries`, { params }),
  replayWebhookDelivery: (deliveryId: string) =>
    api.post<Record<string, unknown>>(`${BASE}/professional-ops/capability-webhooks/deliveries/${encodeURIComponent(deliveryId)}/replay`),
  replayDeadLetterBatch: (limit = 25) =>
    api.post<Record<string, unknown>>(`${BASE}/professional-ops/capability-webhooks/deliveries/replay-dead-letter`, null, {
      params: { limit },
    }),
  seedDlqDemo: () => api.post<Record<string, unknown>>(`${BASE}/professional-ops/capability-webhooks/seed-dlq-demo`),
  mirrorMarketplaceCertifications: () =>
    api.post<Record<string, unknown>>(`${BASE}/professional-ops/certifications/mirror-marketplace`),
  recomputeReadiness: () => api.post<Record<string, unknown>>(`${BASE}/professional-ops/readiness/recompute`),

  listCapex: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-capex`, { params }),
  listOpex: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-opex`, { params }),
  listFeatures: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-features`, { params }),
  listSlots: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-slots`, { params }),

  listDevices: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/hardware-ops/devices`, { params }),
  listSyncQueue: (params?: { status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/hardware-ops/sync-queue`, { params }),
  listTelemetry: (params?: { locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/hardware-ops/telemetry`, { params }),
}
