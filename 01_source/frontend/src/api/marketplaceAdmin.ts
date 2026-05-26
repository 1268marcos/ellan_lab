import { api } from './client'

const BASE = '/api/marketplace-admin/v1/marketplace-admin'

export type MarketplaceSeller = {
  id: string
  legal_name: string
  trade_name?: string
  tax_id: string
  email: string
  phone?: string
  website?: string
  status: string
  commission_pct: string | number
  monthly_fee_cents: number
  seller_rating?: string | number
  total_sales_cents: number
  total_orders: number
}

export type SellerProduct = {
  id: string
  seller_id: string
  locker_id: string
  product_id: string
  seller_sku?: string
  price_cents: number
  quantity: number
  status: string
}

export type MarketplaceCommission = {
  id: string
  seller_id: string
  order_id: string
  commission_amount_cents: number
  net_to_seller_cents: number
  status: string
}

export type SellerReview = {
  id: string
  seller_id: string
  order_id: string
  rating: number
  comment?: string
}

export const marketplaceAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listSellers: (params?: { active_only?: boolean }) =>
    api.get<{ sellers: MarketplaceSeller[]; total: number }>(`${BASE}/sellers`, { params }),
  createSeller: (body: Record<string, unknown>) => api.post<MarketplaceSeller>(`${BASE}/sellers`, body),
  updateSeller: (id: string, body: Record<string, unknown>) =>
    api.patch<MarketplaceSeller>(`${BASE}/sellers/${encodeURIComponent(id)}`, body),
  deleteSeller: (id: string) => api.delete(`${BASE}/sellers/${encodeURIComponent(id)}`),

  listProducts: (params?: { seller_id?: string; locker_id?: string }) =>
    api.get<{ products: SellerProduct[]; total: number }>(`${BASE}/seller-products`, { params }),
  createProduct: (body: Record<string, unknown>) => api.post<SellerProduct>(`${BASE}/seller-products`, body),
  deleteProduct: (id: string) => api.delete(`${BASE}/seller-products/${encodeURIComponent(id)}`),

  commissionNetPreview: (price_cents: number, commission_pct: number | string) =>
    api.get<{
      price_cents: number
      commission_pct: number
      commission_cents: number
      ellan_fee_cents: number
      gateway_fee_cents: number
      net_cents: number
    }>(`${BASE}/commissions/net-preview`, { params: { price_cents, commission_pct } }),

  listCommissions: (params?: { seller_id?: string; status?: string }) =>
    api.get<{ commissions: MarketplaceCommission[]; total: number }>(`${BASE}/commissions`, { params }),
  createCommission: (body: Record<string, unknown>) => api.post(`${BASE}/commissions`, body),
  updateCommission: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/commissions/${encodeURIComponent(id)}`, body),

  listReviews: (params?: { seller_id?: string }) =>
    api.get<{ reviews: SellerReview[]; total: number }>(`${BASE}/seller-reviews`, { params }),
  createReview: (body: Record<string, unknown>) => api.post(`${BASE}/seller-reviews`, body),

  configureWebhook: (sellerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/sellers/${encodeURIComponent(sellerId)}/webhook`, body),
  rotateApiKey: (sellerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/api-keys/rotate`,
    ),
  listApiKeys: (sellerId: string) =>
    api.get<{ seller_id: string; keys: { id: string; key_prefix: string; label?: string; revoked_at?: string; created_at: string }[] }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/api-keys`,
    ),
  getSellerWebhook: (sellerId: string) =>
    api.get<{ id: string; url: string; events_json: string; active: boolean }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/webhook`,
    ),

  listSettlementItems: (batchId: string) =>
    api.get<{ items: { id: string; commission_id: string; order_id: string; net_to_seller_cents: number }[]; total: number }>(
      `${BASE}/seller-settlement-batches/${encodeURIComponent(batchId)}/items`,
    ),
  listSyncAuditLog: (limit = 50) =>
    api.get<{ items: { id: string; event_type: string; entity_type: string; summary: string; created_at: string }[]; total: number }>(
      `${BASE}/sync-audit-log`,
      { params: { limit } },
    ),

  seedSellerProfessional: () => api.post(`${BASE}/seller-professional/seed`),
  sellerProfessionalSummary: (seller_id?: string) =>
    api.get<{
      tier_enrollments_active: number
      compliance_profiles_verified: number
      agreements_signed: number
      latest_risk_band?: string
      latest_risk_score?: number
      performance_rows: number
    }>(`${BASE}/seller-professional/summary`, { params: seller_id ? { seller_id } : undefined }),

  listTierDefinitions: () => api.get<{ tiers: unknown[]; total: number }>(`${BASE}/seller-tier-definitions`),
  listTierEnrollments: (seller_id?: string) =>
    api.get<{ enrollments: unknown[]; total: number }>(`${BASE}/seller-tier-enrollments`, {
      params: seller_id ? { seller_id } : undefined,
    }),
  createTierEnrollment: (body: Record<string, unknown>) => api.post(`${BASE}/seller-tier-enrollments`, body),

  listComplianceProfiles: (seller_id?: string) =>
    api.get<{ profiles: unknown[]; total: number }>(`${BASE}/seller-compliance-profiles`, {
      params: seller_id ? { seller_id } : undefined,
    }),
  createComplianceProfile: (body: Record<string, unknown>) => api.post(`${BASE}/seller-compliance-profiles`, body),
  updateComplianceProfile: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-compliance-profiles/${encodeURIComponent(id)}`, body),

  listPerformanceMonthly: (seller_id?: string) =>
    api.get<{ rows: unknown[]; total: number }>(`${BASE}/seller-performance-monthly`, {
      params: seller_id ? { seller_id } : undefined,
    }),
  upsertPerformanceMonthly: (body: Record<string, unknown>) => api.put(`${BASE}/seller-performance-monthly`, body),

  listAgreements: (seller_id?: string) =>
    api.get<{ agreements: unknown[]; total: number }>(`${BASE}/seller-agreements`, {
      params: seller_id ? { seller_id } : undefined,
    }),
  createAgreement: (body: Record<string, unknown>) => api.post(`${BASE}/seller-agreements`, body),
  updateAgreement: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-agreements/${encodeURIComponent(id)}`, body),

  listRiskAssessments: (seller_id?: string) =>
    api.get<{ assessments: unknown[]; total: number }>(`${BASE}/seller-risk-assessments`, {
      params: seller_id ? { seller_id } : undefined,
    }),
  createRiskAssessment: (body: Record<string, unknown>) => api.post(`${BASE}/seller-risk-assessments`, body),

  listWorldPriorityPlayers: () =>
    api.get<{
      players: {
        code: string
        role: string
        regions: string[]
        in_catalog: boolean
        readiness_band?: string
        score_total?: number
        notes: string
      }[]
      total: number
    }>(`${BASE}/priority-players/world-locker-marketplace`),
  getSellerPlayerCoverage: (sellerId: string) =>
    api.get<{
      seller_id: string
      coverage_complete_count: number
      coverage_pct: number
      players: {
        partner_code: string
        has_marketplace_listing: boolean
        has_locker_network: boolean
        coverage_complete: boolean
        external_store_id?: string
        locker_id?: string
      }[]
    }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/player-coverage`),
  seedPriorityPlayerLinks: async (sellerId = 'mk-seller-demo-001') => {
    const paths = [
      `${BASE}/priority-players/seed-seller-links`,
      `${BASE}/channel-partners/seed-seller-priority-links`,
    ]
    let lastErr: unknown
    for (const path of paths) {
      try {
        return await api.post(path, null, { params: { seller_id: sellerId } })
      } catch (err) {
        lastErr = err
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status !== 404) throw err
      }
    }
    return api.post(`${BASE}/seed`)
  },

  getExtendedWorldPlayers: () =>
    api.get<{ players: unknown[]; total: number }>(`${BASE}/priority-players/extended-world`),
  seedPlayerEcosystem: () => api.post(`${BASE}/player-ecosystem/seed`),
  getPlayerEcosystemMap: () => api.get<Record<string, unknown>>(`${BASE}/player-ecosystem/world-map`),
  listPlayerSegments: () => api.get<{ segments: unknown[]; total: number }>(`${BASE}/player-ecosystem/segments`),
  listPlayerRelationships: (partner_id?: string) =>
    api.get<{ relationships: unknown[]; total: number }>(`${BASE}/player-ecosystem/relationships`, {
      params: partner_id ? { partner_id } : undefined,
    }),
  listCorridors: () => api.get<{ corridors: unknown[]; total: number }>(`${BASE}/player-ecosystem/corridors`),
  getCorridor: (code: string) => api.get<Record<string, unknown>>(`${BASE}/player-ecosystem/corridors/${encodeURIComponent(code)}`),
  listSellerIntegrationPlans: (sellerId: string) =>
    api.get<{ plans: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/integration-plans`),

  seedOpsIntelligence: () => api.post(`${BASE}/ops-intelligence/seed`),
  getOpsIntelligenceSummary: () => api.get<Record<string, number>>(`${BASE}/ops-intelligence/summary`),
  listOpsPlaybooks: (trigger_type?: string) =>
    api.get<{ playbooks: unknown[]; total: number }>(`${BASE}/ops-intelligence/playbooks`, {
      params: trigger_type ? { trigger_type } : undefined,
    }),
  computeSellerHealth: (sellerId: string) =>
    api.post<Record<string, unknown>>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/health/compute`),
  listSellerHealth: (sellerId: string) =>
    api.get<{ snapshots: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/health`),
  listSellerChannelQuotas: (sellerId: string) =>
    api.get<{ quotas: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/channel-quotas`),
  listCatalogSyncJobs: (params?: { seller_id?: string; status?: string }) =>
    api.get<{ jobs: unknown[]; total: number }>(`${BASE}/seller-catalog-sync-jobs`, { params }),
  createCatalogSyncJob: (body: Record<string, unknown>) => api.post(`${BASE}/seller-catalog-sync-jobs`, body),
  runCatalogSyncJob: (jobId: string) => api.post(`${BASE}/seller-catalog-sync-jobs/${encodeURIComponent(jobId)}/run`),
  listCrossBorderProfiles: (sellerId: string) =>
    api.get<{ profiles: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/cross-border-profiles`),
  listPartnerApiHealth: (degraded_only?: boolean) =>
    api.get<{ snapshots: unknown[]; total: number }>(`${BASE}/ops-intelligence/partner-api-health`, {
      params: degraded_only ? { degraded_only: true } : undefined,
    }),
  listSellerPromotions: (sellerId: string, status?: string) =>
    api.get<{ campaigns: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/promotions`, {
      params: status ? { status } : undefined,
    }),

  seedSellerOperations: (sellerId = 'mk-seller-demo-001') =>
    api.post(`${BASE}/seller-operations/seed`, null, { params: { seller_id: sellerId } }),
  getSellerOperationsSummary: (sellerId: string) =>
    api.get<Record<string, unknown>>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/operations-summary`),
  listOnboardingTasks: (sellerId: string) =>
    api.get<{ tasks: unknown[]; total: number; progress_pct: number }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/onboarding-tasks`,
    ),
  completeOnboardingTask: (taskId: string, body: Record<string, unknown>) =>
    api.post(`${BASE}/onboarding-tasks/${encodeURIComponent(taskId)}/complete`, body),
  listChannelSkuMaps: (sellerId: string) =>
    api.get<{ maps: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/channel-sku-maps`),
  listSellerPricingRules: (sellerId: string) =>
    api.get<{ rules: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/pricing-rules`),
  getPricingPreview: (sellerId: string, params: { internal_sku: string; base_price_cents: number; channel_partner_id?: string }) =>
    api.get<Record<string, unknown>>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/pricing-preview`, { params }),
  listReturnPolicies: (sellerId: string) =>
    api.get<{ policies: unknown[]; total: number }>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/return-policies`),
  listNotificationSubscriptions: (sellerId: string) =>
    api.get<{ subscriptions: unknown[]; total: number }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/notification-subscriptions`,
    ),
  listInventoryAllocations: (sellerId: string) =>
    api.get<{ allocations: unknown[]; total: number }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/inventory-allocations`,
    ),
  getFulfillmentPreferences: (sellerId: string) =>
    api.get<Record<string, unknown> | null>(`${BASE}/sellers/${encodeURIComponent(sellerId)}/fulfillment-preferences`),

  getDashboard: () => api.get<Record<string, number | null>>(`${BASE}/dashboard`),
  listCategories: () => api.get<{ categories: unknown[]; total: number }>(`${BASE}/categories`),
  createCategory: (body: Record<string, unknown>) => api.post(`${BASE}/categories`, body),
  listContacts: (seller_id?: string) =>
    api.get<{ contacts: unknown[]; total: number }>(`${BASE}/seller-contacts`, { params: { seller_id } }),
  createContact: (body: Record<string, unknown>) => api.post(`${BASE}/seller-contacts`, body),
  listPayoutAccounts: (seller_id?: string) =>
    api.get<{ accounts: unknown[]; total: number }>(`${BASE}/seller-payout-accounts`, { params: { seller_id } }),
  createPayoutAccount: (body: Record<string, unknown>) => api.post(`${BASE}/seller-payout-accounts`, body),
  listSettlementBatches: (seller_id?: string) =>
    api.get<{ batches: unknown[]; total: number }>(`${BASE}/seller-settlement-batches`, { params: { seller_id } }),
  createSettlementBatch: (body: Record<string, unknown>) => api.post(`${BASE}/seller-settlement-batches`, body),
  updateSettlementBatch: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-settlement-batches/${encodeURIComponent(id)}`, body),
  listKyc: (seller_id?: string) =>
    api.get<{ documents: unknown[]; total: number }>(`${BASE}/seller-kyc-documents`, { params: { seller_id } }),
  createKyc: (body: Record<string, unknown>) => api.post(`${BASE}/seller-kyc-documents`, body),
  updateKyc: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-kyc-documents/${encodeURIComponent(id)}`, body),
  listDisputes: (seller_id?: string) =>
    api.get<{ disputes: unknown[]; total: number }>(`${BASE}/seller-commission-disputes`, { params: { seller_id } }),
  createDispute: (body: Record<string, unknown>) => api.post(`${BASE}/seller-commission-disputes`, body),
  resolveDispute: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-commission-disputes/${encodeURIComponent(id)}`, body),

  listChannelPartners: (params?: { lockers_only?: boolean; active_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/channel-partners`, { params }),
  seedChannelPlayers: () => api.post(`${BASE}/channel-partners/seed-players`),
  getChannelPartner: (id: string) => api.get(`${BASE}/channel-partners/${encodeURIComponent(id)}`),
  integrationMatrix: () => api.get(`${BASE}/integration-hub/summary`),

  listIntegrationReadiness: (params?: { band?: string; limit?: number }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-readiness`, { params }),
  recomputeIntegrationReadiness: () => api.post(`${BASE}/integration-readiness/recompute`),
  integrationHubSummary: () => api.get<Record<string, unknown>>(`${BASE}/integration-hub/summary`),
  listReadinessAlerts: (open_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/readiness-alerts`, { params: { open_only } }),
  acknowledgeReadinessAlert: (alertId: string) =>
    api.post(`${BASE}/readiness-alerts/${encodeURIComponent(alertId)}/acknowledge`),
  listCapabilityWebhooks: (channel_partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/capability-webhooks`, {
      params: channel_partner_id ? { channel_partner_id } : undefined,
    }),
  upsertCapabilityWebhook: (body: Record<string, unknown>) => api.put(`${BASE}/capability-webhooks`, body),
  testCapabilityWebhook: (webhookId: string) =>
    api.post(`${BASE}/capability-webhooks/${encodeURIComponent(webhookId)}/test`),
  simulateScoreDrop: (partner_code: string, new_score: number) =>
    api.post(`${BASE}/integration-readiness/simulate-drop`, { partner_code, new_score }),
  listIntegrationIncidents: (open_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-incidents`, { params: { open_only } }),
  seedGlobalOps: () =>
    api.post<{ certifications: number; corridors: number; corridor_steps: number }>(`${BASE}/global-ops/seed`),
  globalOpsSummary: () =>
    api.get<{ certifications_valid: number; corridors_active: number; corridor_steps: number }>(
      `${BASE}/global-ops/summary`,
    ),
  mirrorCertificationsFromPartner: () =>
    api.post<Record<string, number>>(`${BASE}/global-ops/certifications/mirror`),
  listCorridorSla: (compliance_status?: string) =>
    api.get<
      { corridor_code: string; compliance_status: string; uptime_target_pct: number; max_transit_hours: number }[]
    >(`${BASE}/global-ops/corridor-sla`, { params: compliance_status ? { compliance_status } : undefined }),
  listCapabilityDeliveries: (params?: { status?: string; webhook_id?: string }) =>
    api.get<{ id: string; status: string; success: boolean; event_type: string }[]>(
      `${BASE}/capability-webhooks/deliveries`,
      { params },
    ),
  replayCapabilityDelivery: (deliveryId: string) =>
    api.post(`${BASE}/capability-webhooks/deliveries/${encodeURIComponent(deliveryId)}/replay`),
  replayDeadLetterBatch: (limit = 25) =>
    api.post<{ requested: number; replayed: number; succeeded: number }>(
      `${BASE}/capability-webhooks/deliveries/replay-dead-letter`,
      null,
      { params: { limit } },
    ),
  listGlobalCorridors: (origin?: string, dest?: string) =>
    api.get<
      {
        corridor_code: string
        name: string
        origin_country: string
        dest_country: string
        primary_partner_code: string
        steps: { partner_code: string; step_role: string }[]
      }[]
    >(`${BASE}/global-ops/corridors`, { params: { origin, dest } }),
}
