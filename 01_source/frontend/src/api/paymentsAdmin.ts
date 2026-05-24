import { api } from './client'

const BASE = '/api/payments-admin/v1/payments-admin'

export type PaymentIntelligenceSummary = {
  transactions_total: number
  transactions_approved: number
  reconciliation_pending: number
  open_batches: number
  webhook_pending: number
  holds_active_cents: number
  ecosystem_players_live: number
  ecosystem_players_total: number
  player_relations_total: number
  priority_players_live: number
  orders_with_context: number
  segments: Record<string, number>
  priority_player_codes: string[]
  ecosystem_segments_defined: number
  country_coverage_rows: number
  integrations_production_ready: number
  integrations_avg_readiness: number
  open_integration_incidents: number
  active_settlement_corridors: number
  routing_rules_active: number
  milestones_in_progress: number
  external_references_total: number
  pending_domain_obligations: number
  blocking_domain_obligations: number
  cross_domain_gaps_detected: number
  cross_domain_events_pending: number
}

export type PaymentDomainRegistry = {
  code: string
  name: string
  description: string | null
  ops_base_path: string | null
}

export type PaymentExternalReference = {
  id: string
  order_id: string | null
  payment_entity_type: string
  payment_entity_id: string
  external_domain: string
  external_entity_type: string
  external_entity_id: string
  link_role: string
  sync_status: string
}

export type PaymentDomainObligation = {
  id: string
  order_id: string
  domain_code: string
  obligation_type: string
  status: string
  blocking_payment: boolean
  priority: number
  external_ref_id: string | null
  notes: string | null
}

export type DomainGap = {
  order_id: string
  gap_type: string
  domain_code: string
  message: string
  severity: string
}

export type PaymentOrder360 = {
  order_id: string
  payment_summary: Record<string, unknown>
  domains: {
    domain_code: string
    domain_name: string
    ops_path: string | null
    references: PaymentExternalReference[]
    obligations: PaymentDomainObligation[]
  }[]
  pending_obligations: number
  blocking_obligations: number
  external_refs_total: number
  cross_domain_events_pending: number
}

export type GlobalReadiness = {
  players_total: number
  production_integrations: number
  avg_readiness: number
  open_incidents: number
  critical_incidents: number
  milestones_in_progress: number
  milestones_blocked: number
  active_corridors: number
  compliance_approved: number
  active_routing_rules: number
  top_risk_players: string[]
}

export type EcosystemGraphPayload = {
  nodes: {
    id: string
    code: string
    label: string
    segment: string
    integration_status: string
    readiness_score: number | null
  }[]
  edges: { from_code: string; to_code: string; relation_type: string }[]
  node_count: number
  edge_count: number
}

export type IntegrationMilestone = {
  id: string
  player_code: string
  phase: string
  title: string
  status: string
  target_date: string | null
  completed_at: string | null
  owner_team: string | null
  blockers_json: string[]
}

export type RoutingRule = {
  id: string
  rule_code: string
  tenant_id: string | null
  country_code: string
  payment_method: string
  sales_channel: string | null
  primary_player_code: string
  fallback_player_code: string | null
  priority: number
  min_amount_cents: number | null
  max_amount_cents: number | null
  is_active: boolean
  rationale: string | null
}

export type RoutingSuggestion = {
  country_code: string
  payment_method: string
  primary_player_code: string
  fallback_player_code: string | null
  rule_code: string
  rationale: string | null
  readiness_score: number | null
}

export const paymentsAdminApi = {
  seed: () => api.post<Record<string, number>>(`${BASE}/seed`),

  intelligenceSummary: () => api.get<PaymentIntelligenceSummary>(`${BASE}/intelligence/summary`),
  globalReadiness: () => api.get<GlobalReadiness>(`${BASE}/intelligence/global-readiness`),
  ecosystemGraph: () => api.get<EcosystemGraphPayload>(`${BASE}/intelligence/ecosystem-graph`),
  routingSuggest: (params: {
    country_code: string
    payment_method: string
    amount_cents?: number
    sales_channel?: string
  }) => api.get<RoutingSuggestion>(`${BASE}/intelligence/routing-suggest`, { params }),

  listIntegrationMilestones: (params?: { player_code?: string; status?: string }) =>
    api.get<{ items: IntegrationMilestone[]; total: number }>(
      `${BASE}/integration-milestones`,
      { params },
    ),

  createIntegrationMilestone: (body: {
    player_code: string
    phase: string
    title: string
    status?: string
    target_date?: string
    owner_team?: string
  }) => api.post<IntegrationMilestone>(`${BASE}/integration-milestones`, body),

  updateIntegrationMilestone: (
    id: string,
    body: Partial<{
      phase: string
      title: string
      status: string
      target_date: string | null
      owner_team: string
    }>,
  ) => api.patch<IntegrationMilestone>(`${BASE}/integration-milestones/${encodeURIComponent(id)}`, body),

  deleteIntegrationMilestone: (id: string) =>
    api.delete(`${BASE}/integration-milestones/${encodeURIComponent(id)}`),

  listSettlementCorridors: (params?: { origin_country?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/settlement-corridors`, { params }),

  listPlayerCompliance: (params?: { player_code?: string; country_code?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/player-compliance`, { params }),

  listRoutingRules: (params?: {
    country_code?: string
    payment_method?: string
    active_only?: boolean
  }) => api.get<{ items: RoutingRule[]; total: number }>(`${BASE}/routing-rules`, { params }),

  createRoutingRule: (body: {
    rule_code: string
    country_code: string
    payment_method: string
    primary_player_code: string
    fallback_player_code?: string
    sales_channel?: string
    priority?: number
    rationale?: string
    is_active?: boolean
  }) => api.post<RoutingRule>(`${BASE}/routing-rules`, body),

  updateRoutingRule: (
    id: string,
    body: Partial<{
      country_code: string
      payment_method: string
      primary_player_code: string
      fallback_player_code: string | null
      sales_channel: string | null
      priority: number
      rationale: string
      is_active: boolean
    }>,
  ) => api.patch<RoutingRule>(`${BASE}/routing-rules/${encodeURIComponent(id)}`, body),

  deleteRoutingRule: (id: string) =>
    api.delete(`${BASE}/routing-rules/${encodeURIComponent(id)}`),

  listIntegrationIncidents: (params?: { status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-incidents`, { params }),

  orderGraph: (orderId: string) =>
    api.get<{ order_id: string; context: unknown; transactions: unknown[] }>(
      `${BASE}/intelligence/order-graph/${encodeURIComponent(orderId)}`,
    ),

  listEcosystemPlayers: (params?: { segment?: string; active_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem-players`, { params }),

  listEcosystemSegments: () =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem-segments`),

  listPlayerIntegrations: (params?: { min_readiness?: number; production_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/player-integrations`, { params }),

  getPlayerIntegration: (playerCode: string) =>
    api.get(`${BASE}/player-integrations/${encodeURIComponent(playerCode)}`),

  integrationPlaybook: (segmentCode: string) =>
    api.get(`${BASE}/player-integrations/playbook/${encodeURIComponent(segmentCode)}`),

  listPlayerCountryCoverage: (params?: { country_code?: string; player_code?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/player-country-coverage`, { params }),

  listPlayerRelations: (params?: { from_player?: string; to_player?: string; relation_type?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/player-relations`, { params }),

  listOrderContext: (params?: { tenant_id?: string; locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/order-context`, { params }),
  getOrderContextByOrder: (orderId: string) =>
    api.get(`${BASE}/order-context/by-order/${encodeURIComponent(orderId)}`),

  listReconciliationBatches: (params?: { status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/reconciliation-batches`, { params }),

  listWebhookDeliveries: (params?: { endpoint_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/webhook-deliveries`, { params }),
  retryWebhookDelivery: (id: string) =>
    api.post(`${BASE}/webhook-deliveries/${encodeURIComponent(id)}/retry`),

  listPartnerHolds: (params?: { partner_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/partner-holds`, { params }),

  listSavedMethods: (params?: { user_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/saved-payment-methods`, { params }),

  listTransactions: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-transactions`, { params }),

  listInstructions: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-instructions`, { params }),

  listSplits: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-splits`, { params }),

  listPayments: (params?: { order_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/payments`, { params }),

  listWebhooks: (params?: { partner_type?: string; partner_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/webhook-endpoints`, { params }),

  rotateWebhookSecret: (id: string) =>
    api.post<{ secret: string; secret_ref: string }>(
      `${BASE}/webhook-endpoints/${encodeURIComponent(id)}/rotate-secret`,
    ),

  listGatewayEvents: (params?: { order_id?: string; locker_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/gateway-events`, { params }),

  listDomainRegistry: () =>
    api.get<{ items: PaymentDomainRegistry[]; total: number }>(`${BASE}/cross-domain/registry`),

  listExternalReferences: (params?: { order_id?: string; external_domain?: string }) =>
    api.get<{ items: PaymentExternalReference[]; total: number }>(
      `${BASE}/cross-domain/external-references`,
      { params },
    ),

  listDomainObligations: (params?: { order_id?: string; status?: string; blocking_only?: boolean }) =>
    api.get<{ items: PaymentDomainObligation[]; total: number }>(
      `${BASE}/cross-domain/obligations`,
      { params },
    ),

  updateDomainObligation: (id: string, body: { status?: string }) =>
    api.patch<PaymentDomainObligation>(
      `${BASE}/cross-domain/obligations/${encodeURIComponent(id)}`,
      body,
    ),

  listCrossDomainGaps: (limit?: number) =>
    api.get<{ items: DomainGap[]; total: number }>(`${BASE}/cross-domain/gaps`, {
      params: limit ? { limit } : undefined,
    }),

  order360: (orderId: string) =>
    api.get<PaymentOrder360>(`${BASE}/cross-domain/order-360/${encodeURIComponent(orderId)}`),

  publishCrossDomainEvent: (eventId: string) =>
    api.post(`${BASE}/cross-domain/events/${encodeURIComponent(eventId)}/publish`),

  listCrossDomainEvents: (params?: { order_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/cross-domain/events`, { params }),
}
