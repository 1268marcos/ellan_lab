import { api } from './client'

const BASE = '/api/partner-admin/v1/partner-admin'

export type EcommercePartner = {
  id: string
  name: string
  code: string
  integration_type: string
  api_base_url?: string
  active: boolean
  status: string
  country: string
  sla_pickup_hours: number
  support_email?: string
}

export type LogisticsPartner = {
  id: string
  name: string
  code: string
  integration_type: string
  api_base_url?: string
  active: boolean
  country: string
  default_sla_hours: number
}

export type UserSummary = { id: string; full_name: string; email: string; is_active: boolean }

export type UserRole = {
  id: string
  user_id: string
  role: string
  scope_type: string
  scope_id?: string
  is_active: boolean
  granted_at: string
  revoked_at?: string
}

export type PartnerContact = {
  id: string
  partner_id: string
  partner_type: string
  contact_type: string
  name: string
  email?: string
  phone?: string
  is_primary: boolean
}

export type SettlementBatch = {
  id: string
  partner_id: string
  period_start: string
  period_end: string
  status: string
  net_amount_cents: number
  currency: string
  total_orders: number
}

export type PartnerDashboard = {
  kpis: { total_events: number; error_rate_pct: number; paid_batches?: number }
  compare: {
    total_previous: number
    total_delta_count: number
    total_delta_pct: number
    confidence_level: string
    data_quality_flags: string[]
  }
  changes_series: Array<{ label: string; value: number }>
}

export type Partner360 = {
  partner_id: string
  partner_type: string
  settlements_draft: number
  settlements_paid: number
  open_billing_cycles: number
  pending_invoices: number
  pending_outbox: number
  webhook_failures_24h: number
  integration_status: string
  onboarding_progress_pct: number
  sla_active: boolean
  ecosystem_links?: number
  ecosystem_priority_links?: number
}

export type EcosystemPlayer = {
  id: string
  code: string
  name: string
  player_role: string
  parent_group: string
  country: string
  regions: string[]
  supports_lockers: boolean
  supports_marketplace: boolean
  integration_mode: string
  global_tier: string
  locker_operator_ref?: string
  marketplace_channel_code?: string
  active: boolean
}

export type EcosystemLink = {
  id: string
  partner_id: string
  player_code: string
  player_name: string
  parent_group: string
  global_tier: string
  link_role: string
  integration_status: string
  is_primary: boolean
  locker_operator_ref?: string
}

export type OnboardingMilestone = {
  id: string
  milestone_code: string
  milestone_label: string
  status: string
  sort_order: number
}

export const partnerAdminApi = {
  listEcommerce: (params?: { active_only?: boolean }) =>
    api.get<{ partners: EcommercePartner[]; total: number }>(`${BASE}/ecommerce-partners`, { params }),
  createEcommerce: (body: Record<string, unknown>) => api.post<EcommercePartner>(`${BASE}/ecommerce-partners`, body),
  updateEcommerce: (id: string, body: Record<string, unknown>) =>
    api.patch<EcommercePartner>(`${BASE}/ecommerce-partners/${encodeURIComponent(id)}`, body),
  deleteEcommerce: (id: string) => api.delete(`${BASE}/ecommerce-partners/${encodeURIComponent(id)}`),

  listLogistics: (params?: { active_only?: boolean }) =>
    api.get<{ partners: LogisticsPartner[]; total: number }>(`${BASE}/logistics-partners`, { params }),
  createLogistics: (body: Record<string, unknown>) => api.post<LogisticsPartner>(`${BASE}/logistics-partners`, body),
  updateLogistics: (id: string, body: Record<string, unknown>) =>
    api.patch<LogisticsPartner>(`${BASE}/logistics-partners/${encodeURIComponent(id)}`, body),
  deleteLogistics: (id: string) => api.delete(`${BASE}/logistics-partners/${encodeURIComponent(id)}`),

  listUsers: () => api.get<{ users: UserSummary[]; total: number }>(`${BASE}/users`),
  listUserRoles: (params?: { user_id?: string; active_only?: boolean }) =>
    api.get<{ roles: UserRole[]; total: number }>(`${BASE}/user-roles`, { params }),
  createUserRole: (body: { user_id: string; role: string; scope_type?: string; scope_id?: string }) =>
    api.post<UserRole>(`${BASE}/user-roles`, body),
  revokeUserRole: (roleId: string) => api.post<UserRole>(`${BASE}/user-roles/${encodeURIComponent(roleId)}/revoke`),
  deleteUserRole: (roleId: string) => api.delete(`${BASE}/user-roles/${encodeURIComponent(roleId)}`),

  configureWebhook: (partnerId: string, partnerType: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/partners/${encodeURIComponent(partnerId)}/webhook`, body, { params: { partner_type: partnerType } }),
  rotateApiKey: (partnerId: string, partnerType: string) =>
    api.post<{ api_key: string; key_prefix: string }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/api-keys/rotate`, null, {
      params: { partner_type: partnerType },
    }),
  listContacts: (partnerId: string, partnerType: string) =>
    api.get<{ contacts: PartnerContact[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/contacts`, {
      params: { partner_type: partnerType },
    }),
  createContact: (
    partnerId: string,
    partnerType: string,
    body: { name: string; email?: string; phone?: string; contact_type?: string; is_primary?: boolean },
  ) =>
    api.post<PartnerContact>(`${BASE}/partners/${encodeURIComponent(partnerId)}/contacts`, body, {
      params: { partner_type: partnerType },
    }),

  listSettlements: (partnerId: string, params?: { status?: string }) =>
    api.get<{ items: SettlementBatch[]; total: number }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/settlements`, {
      params,
    }),
  generateSettlement: (partnerId: string, body: Record<string, unknown>) =>
    api.post<SettlementBatch>(`${BASE}/partners/${encodeURIComponent(partnerId)}/settlements/generate`, body),
  approveSettlement: (partnerId: string, batchId: string, body: Record<string, unknown>) =>
    api.patch<SettlementBatch>(
      `${BASE}/partners/${encodeURIComponent(partnerId)}/settlements/${encodeURIComponent(batchId)}/approve`,
      body,
    ),
  listPerformance: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/performance`),
  listServiceAreas: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/service-areas`),
  listBillingPlans: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/billing-plans`),
  listBillingCycles: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/billing-cycles`),
  listStores: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/partner-stores`),
  opsDashboard: (params?: { partner_id?: string }) =>
    api.get<PartnerDashboard>(`${BASE}/partners/ops/dashboard`, { params }),

  partner360: (partnerId: string, partnerType: string) =>
    api.get<Partner360>(`${BASE}/partners/${encodeURIComponent(partnerId)}/360`, {
      params: { partner_type: partnerType },
    }),
  listOnboarding: (partnerId: string, partnerType: string) =>
    api.get<{ items: OnboardingMilestone[]; progress_pct: number }>(
      `${BASE}/partners/${encodeURIComponent(partnerId)}/onboarding`,
      { params: { partner_type: partnerType } },
    ),
  patchOnboarding: (partnerId: string, milestoneId: string, body: { status: string; notes?: string }) =>
    api.patch(`${BASE}/partners/${encodeURIComponent(partnerId)}/onboarding/${encodeURIComponent(milestoneId)}`, body),
  listWebhookDeliveries: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/webhook-deliveries`),
  listIntegrationHealth: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/integration-health`),
  probeIntegration: (partnerId: string, partnerType: string) =>
    api.post(`${BASE}/partners/${encodeURIComponent(partnerId)}/integration-health/probe`, null, {
      params: { partner_type: partnerType },
    }),
  listOutbox: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/outbox`),
  listInvoices: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/invoices`),
  listBillingLineItems: (partnerId: string, cycleId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/billing-line-items`, {
      params: cycleId ? { cycle_id: cycleId } : undefined,
    }),
  listCreditNotes: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/credit-notes`),
  listPaymentHolds: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/payment-holds`),
  listCommissions: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/commissions`),
  listSla: (partnerId: string) => api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/sla-agreements`),
  listStatusHistory: (partnerId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/partners/${encodeURIComponent(partnerId)}/status-history`),

  seed: () => api.post(`${BASE}/seed`),

  listEcosystemPlayers: (params?: {
    priority_only?: boolean
    parent_group?: string
    country?: string
    supports_lockers?: boolean
  }) =>
    api.get<{ items: EcosystemPlayer[]; total: number; priority_count: number }>(`${BASE}/ecosystem/players`, {
      params,
    }),
  syncEcosystemCatalog: () =>
    api.post<{ inserted: number; updated: number; total: number }>(`${BASE}/ecosystem/players/sync-catalog`),
  listEcosystemLinks: (partnerId: string, partnerType?: string) =>
    api.get<{ items: EcosystemLink[]; total: number }>(
      `${BASE}/partners/${encodeURIComponent(partnerId)}/ecosystem-links`,
      { params: partnerType ? { partner_type: partnerType } : undefined },
    ),
  createEcosystemLink: (partnerId: string, body: Record<string, unknown>) =>
    api.post<EcosystemLink>(`${BASE}/partners/${encodeURIComponent(partnerId)}/ecosystem-links`, body),
  deleteEcosystemLink: (partnerId: string, linkId: string) =>
    api.delete(`${BASE}/partners/${encodeURIComponent(partnerId)}/ecosystem-links/${encodeURIComponent(linkId)}`),

  ecosystemSummary: () =>
    api.get<{
      total_players: number
      by_parent_group: Record<string, number>
      player_relations: number
      market_presence_rows: number
      priority_players: number
    }>(`${BASE}/ecosystem/players/summary`),
  ecosystemMatrix: () =>
    api.get<{ parent_group: string; total: number; players: unknown[] }[]>(`${BASE}/ecosystem/players/integration-matrix`),
  ecosystemRelations: (playerCode?: string) =>
    api.get<{ id: string; from_player_code?: string; to_player_code?: string; relation_type: string; strength: string }[]>(
      `${BASE}/ecosystem/players/relations`,
      { params: playerCode ? { player_code: playerCode } : undefined },
    ),
  seedProfessionalEcosystem: () => api.post<Record<string, number>>(`${BASE}/ecosystem/players/seed-professional`),
  listCapabilityWebhooks: (params?: { player_code?: string; ecosystem_player_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem/capability-webhooks`, { params }),
  mirrorCapabilityWebhooks: () =>
    api.post<{ created: number; updated: number; mirrored_from_marketplace: number; total: number }>(
      `${BASE}/ecosystem/capability-webhooks/mirror-from-capabilities`,
    ),
  testCapabilityWebhook: (webhookId: string) =>
    api.post<{ success: boolean }>(`${BASE}/ecosystem/capability-webhooks/${encodeURIComponent(webhookId)}/test`),

  globalOpsSummary: () =>
    api.get<{
      certifications: number
      certifications_valid: number
      corridors_active: number
      readiness_by_band: Record<string, number>
      relation_health: Record<string, number>
    }>(`${BASE}/ecosystem/global-ops/summary`),
  seedGlobalOps: () =>
    api.post<{ certifications: number; corridors: number; readiness_rows: number; relation_health_rows: number }>(
      `${BASE}/ecosystem/global-ops/seed`,
    ),
  listGlobalCertifications: (playerCode?: string) =>
    api.get<{ id: string; player_code: string; certification_type: string; status: string }[]>(
      `${BASE}/ecosystem/global-ops/certifications`,
      { params: playerCode ? { player_code: playerCode } : undefined },
    ),
  listGlobalCorridors: (origin?: string, dest?: string) =>
    api.get<
      {
        corridor_code: string
        name: string
        origin_country: string
        dest_country: string
        primary_player_code: string
        fallback_player_code?: string
        service_level: string
      }[]
    >(`${BASE}/ecosystem/global-ops/corridors`, { params: { origin, dest } }),
  listEcosystemReadiness: (band?: string) =>
    api.get<
      {
        player_code: string
        readiness_band: string
        score_total: number
        blockers: string[]
      }[]
    >(`${BASE}/ecosystem/global-ops/readiness`, { params: band ? { band } : undefined }),
  listRelationHealth: (status?: string) =>
    api.get<{ from_player_code: string; to_player_code: string; health_status: string; cascade_from_player_code?: string }[]>(
      `${BASE}/ecosystem/global-ops/relation-health`,
      { params: status ? { status } : undefined },
    ),
  mirrorCertifications: () =>
    api.post<{ from_marketplace: Record<string, number>; to_marketplace: Record<string, number> }>(
      `${BASE}/ecosystem/global-ops/certifications/mirror`,
    ),
  listCorridorSla: (compliance_status?: string) =>
    api.get<
      {
        corridor_code: string
        compliance_status: string
        uptime_target_pct: number
        max_transit_hours: number
      }[]
    >(`${BASE}/ecosystem/global-ops/corridor-sla`, { params: compliance_status ? { compliance_status } : undefined }),
  listCapabilityDeliveries: (params?: { status?: string; webhook_id?: string }) =>
    api.get<{ items: { id: string; status: string; success: boolean; event_type: string }[]; total: number }>(
      `${BASE}/ecosystem/capability-webhooks/deliveries`,
      { params },
    ),
  replayCapabilityDelivery: (deliveryId: string) =>
    api.post(`${BASE}/ecosystem/capability-webhooks/deliveries/${encodeURIComponent(deliveryId)}/replay`),
  replayDeadLetterBatch: (limit = 25) =>
    api.post<{ requested: number; replayed: number; succeeded: number }>(
      `${BASE}/ecosystem/capability-webhooks/deliveries/replay-dead-letter`,
      null,
      { params: { limit } },
    ),
}
