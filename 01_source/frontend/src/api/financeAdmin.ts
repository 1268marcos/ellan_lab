import { api } from './client'

const BASE = '/api/finance-admin/v1/finance-admin'

export type FinancePartner = {
  id: string
  code: string
  name: string
  partner_type: string
  country_code?: string
  currency: string
  active: boolean
}

export type BillingPlan = {
  id: string
  partner_id: string
  plan_name: string
  billing_model: string
  monthly_fee_cents?: number
  is_active: boolean
}

export type BillingCycle = {
  id: string
  partner_id: string
  billing_plan_id: string
  period_start: string
  period_end: string
  total_amount_cents: number
  status: string
}

export type B2bInvoice = {
  id: string
  cycle_id: string
  partner_id: string
  invoice_number?: string
  amount_cents: number
  status: string
}

export type SettlementBatch = {
  id: string
  partner_id: string
  period_start: string
  period_end: string
  gross_revenue_cents: number
  net_amount_cents: number
  status: string
}

export type CreditNote = {
  id: string
  partner_id: string
  reason_code: string
  amount_cents: number
  status: string
}

export type PaymentHold = {
  id: string
  partner_id: string
  invoice_id: string
  hold_amount_cents: number
  status: string
}

export type FiscalGap = {
  id: string
  gap_type: string
  severity: string
  status: string
  order_id?: string
}

export type CostCenterMonthly = {
  id: string
  locker_id: string
  month: string
  total_opex_cents: number
  total_costs_cents: number
}

export type LockerNetworkPlayer = {
  id: string
  code: string
  name: string
  player_role: string
  parent_group: string
  country_code: string
  global_tier: string
  integration_status: string
  finance_partner_id?: string | null
  finance_partner_code?: string | null
  supports_lockers: boolean
  supports_marketplace: boolean
  estimated_locker_count?: number | null
  default_billing_model: string
}

export const financeAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listPartners: () => api.get<{ items: FinancePartner[]; total: number }>(`${BASE}/finance-partners`),
  createPartner: (body: Record<string, unknown>) => api.post(`${BASE}/finance-partners`, body),
  configureWebhook: (partnerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/finance-partners/${encodeURIComponent(partnerId)}/webhook`, body),
  rotateApiKey: (partnerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/finance-partners/${encodeURIComponent(partnerId)}/api-keys/rotate`,
    ),

  listPlans: (partner_id?: string) =>
    api.get<{ items: BillingPlan[]; total: number }>(`${BASE}/billing-plans`, { params: { partner_id } }),
  listCycles: (partner_id?: string) =>
    api.get<{ items: BillingCycle[]; total: number }>(`${BASE}/billing-cycles`, { params: { partner_id } }),
  listLineItems: (params?: { cycle_id?: string; partner_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/billing-line-items`, { params }),

  listB2bInvoices: (partner_id?: string) =>
    api.get<{ items: B2bInvoice[]; total: number }>(`${BASE}/b2b-invoices`, { params: { partner_id } }),

  listSettlements: (partner_id?: string) =>
    api.get<{ items: SettlementBatch[]; total: number }>(`${BASE}/settlement-batches`, { params: { partner_id } }),
  listSettlementItems: (batch_id: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/settlement-batches/${encodeURIComponent(batch_id)}/items`),

  listCreditNotes: (partner_id?: string) =>
    api.get<{ items: CreditNote[]; total: number }>(`${BASE}/credit-notes`, { params: { partner_id } }),
  listPaymentHolds: (partner_id?: string) =>
    api.get<{ items: PaymentHold[]; total: number }>(`${BASE}/payment-holds`, { params: { partner_id } }),
  listCommissions: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/commission-structures`, { params: { partner_id } }),

  listCostCenters: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/cost-centers`),
  listCostCenterMonthly: (locker_id?: string) =>
    api.get<{ items: CostCenterMonthly[]; total: number }>(`${BASE}/cost-center-monthly`, { params: { locker_id } }),

  listFiscalGaps: (status?: string) =>
    api.get<{ items: FiscalGap[]; total: number }>(`${BASE}/fiscal-reconciliation-gaps`, { params: { status } }),
  patchFiscalGap: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/fiscal-reconciliation-gaps/${encodeURIComponent(id)}`, body),

  listWebhookDeliveries: (params?: { endpoint_id?: string; failed_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/webhook-deliveries`, { params }),

  listWalletProviders: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/wallet-providers`),
  listWalletTransactions: (wallet_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/wallet-transactions`, { params: { wallet_id } }),

  listOpsInvoices: (order_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ops-invoices`, { params: { order_id } }),
  listBillingEvents: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/billing-processed-events`),

  listLockerNetworkCatalog: (params?: {
    parent_group?: string
    segment_code?: string
    country_code?: string
    linked_only?: boolean
  }) =>
    api.get<{ items: LockerNetworkPlayer[]; total: number; by_parent_group: Record<string, number> }>(
      `${BASE}/locker-network-catalog`,
      { params },
    ),
  listEcosystemSegments: () =>
    api.get<{ items: { code: string; name: string }[]; total: number }>(
      `${BASE}/locker-network-catalog/segments`,
    ),
  listPlayerRelations: (catalog_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-network-catalog/relations`, {
      params: { catalog_code },
    }),
  syncLockerNetworkCatalog: () => api.post(`${BASE}/locker-network-catalog/sync`),

  worldPriorityIndex: () =>
    api.get<{ items: { code: string; segment: string; countries: string[] }[]; total: number }>(
      `${BASE}/locker-network-catalog/world-priority-index`,
    ),
  integrationBlueprints: () =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/locker-network-catalog/integration-blueprints`),
  ecosystemMatrix: () =>
    api.get<{
      segments: { code: string; name: string }[]
      matrix: Record<string, Record<string, number>>
      total_players: number
      total_relations: number
      total_aliases: number
    }>(`${BASE}/locker-network-catalog/ecosystem-matrix`),
  resolveCatalogCode: (codeOrAlias: string) =>
    api.get<{ input: string; catalog_code: string | null }>(
      `${BASE}/locker-network-catalog/resolve/${encodeURIComponent(codeOrAlias)}`,
    ),

  playerIntegrationGuide: (catalogCode: string) =>
    api.get<{
      catalog_code: string
      name: string
      segment_code: string
      parent_group: string
      integration_status: string
      finance_partner_code: string | null
      blueprint: {
        code: string
        name: string
        auth_type: string
        primary_capability: string
        webhook_events: string[]
        docs_hint: string | null
      } | null
      integration_steps: string[]
      capabilities: { capability_code: string; protocol: string; direction: string }[]
      relations: { from_catalog_code: string; to_catalog_code: string; relation_type: string; notes: string | null }[]
      country_coverage: {
        country_code: string
        locker_service: boolean
        pudo_service: boolean
        marketplace_channel: boolean
        food_pickup: boolean
      }[]
      readiness: {
        readiness_score: number
        grade: string
        integration_blueprint_code: string | null
        blueprint_score: number
        blockers_json: string
      } | null
      cross_refs: Record<string, string>
    }>(`${BASE}/locker-network-catalog/players/${encodeURIComponent(catalogCode)}/integration-guide`),

  intelligenceDashboard: () =>
    api.get<{
      open_insights: number
      critical_insights: number
      players_analyzed: number
      avg_readiness: number
      avg_composite_score: number
      top_benchmarks: unknown[]
      recent_insights: unknown[]
      health_summary: Record<string, number>
    }>(`${BASE}/ecosystem-intelligence/dashboard`),

  listEcosystemInsights: (params?: { catalog_code?: string; severity?: string }) =>
    api.get<{ items: unknown[]; total: number; open_count: number }>(`${BASE}/ecosystem-intelligence/insights`, {
      params,
    }),

  listPlayerBenchmarks: (segment_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ecosystem-intelligence/benchmarks`, {
      params: segment_code ? { segment_code } : undefined,
    }),

  analyzeEcosystem: () => api.post<{ benchmarks_computed: number; insights_created: number; health_checks_run: number }>(
    `${BASE}/ecosystem-intelligence/analyze`,
  ),

  resolveInsight: (insightId: string) => api.post(`${BASE}/ecosystem-intelligence/insights/${insightId}/resolve`),

  ecosystemSummary: () =>
    api.get<{
      total_players: number
      live_count: number
      pilot_count: number
      linked_partners: number
      total_relations: number
      total_capabilities: number
      readiness_average: number
      by_segment: Record<string, number>
      by_integration_status: Record<string, number>
      top_ready: { catalog_code: string; readiness_score: number; grade: string }[]
    }>(`${BASE}/locker-network-catalog/ecosystem-summary`),

  listPartnerReadiness: (params?: { min_score?: number; grade?: string }) =>
    api.get<{ items: { catalog_code: string; readiness_score: number; grade: string; blockers_json: string }[]; total: number; average_score: number }>(
      `${BASE}/partner-readiness`,
      { params },
    ),
  recomputeReadiness: () => api.post<{ recomputed: number; average_score: number }>(`${BASE}/partner-readiness/recompute`),

  listCommercialContracts: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/commercial-contracts`, { params: { partner_id } }),

  listIntegrationMilestones: (catalog_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-milestones`, { params: { catalog_code } }),

  listSlaDefinitions: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/sla-definitions`, { params: { partner_id } }),
  listSlaBreaches: (params?: { partner_id?: string; status?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/sla-breaches`, { params }),

  closeBillingCycle: (cycleId: string) =>
    api.post<{ cycle_id: string; status: string; total_amount_cents: number; invoice_id?: string }>(
      `${BASE}/billing-cycles/${encodeURIComponent(cycleId)}/close`,
    ),

  replayWebhookDelivery: (deliveryId: string) =>
    api.post<{ delivery_id: string; status: string; attempt_count: number }>(
      `${BASE}/webhook-deliveries/${encodeURIComponent(deliveryId)}/replay`,
    ),

  listPaymentTerms: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/payment-terms`, { params: { partner_id } }),
  listFxRates: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/fx-rates`),
  listCommercialTiers: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/commercial-tiers`),
  listTierAssignments: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/tier-assignments`, { params: { partner_id } }),
  listDunningCases: (status?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/dunning-cases`, { params: { status } }),
  scanDunning: () => api.post<{ cases_opened: number; invoices_scanned: number }>(`${BASE}/dunning/scan`),
  listTaxCorridors: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/tax-corridors`, { params: { partner_id } }),
  listInvoiceDocuments: (invoice_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/invoice-documents`, { params: { invoice_id } }),
  reconcileSettlement: (batchId: string) =>
    api.post<{ run: { matched_count: number; variance_cents: number } }>(
      `${BASE}/settlement-batches/${encodeURIComponent(batchId)}/reconcile`,
    ),
  listAuditLog: (params?: { entity_type?: string; entity_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/audit-log`, { params }),

  listRevenueSchedules: (partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/revenue-schedules`, { params: { partner_id } }),
  listRevenueEntries: (params?: { schedule_id?: string; partner_id?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/revenue-recognition-entries`, { params }),
  runRevenueRecognition: (sync_fiscal = false) =>
    api.post<{ entries_created: number; schedules_updated: number }>(
      `${BASE}/revenue-recognition/run`,
      {},
      { params: { sync_fiscal } },
    ),

  listJobRuns: (job_code?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/jobs/runs`, { params: { job_code } }),
  runJob: (job_code: string) => api.post<{ job_run_id: string; status: string }>(`${BASE}/jobs/run/${job_code}`),
  runAllJobs: () => api.post<{ jobs: unknown[] }>(`${BASE}/jobs/run-all`),

  emitB2bFiscal: (invoiceId: string) =>
    api.post<{ invoice_id: string; access_key?: string; fiscal_status?: string; mode?: string }>(
      `${BASE}/b2b-invoices/${encodeURIComponent(invoiceId)}/emit-fiscal`,
    ),
  closeBillingCycle: (cycleId: string, createRevenueSchedule = true, emitFiscal = false) =>
    api.post(`${BASE}/billing-cycles/${encodeURIComponent(cycleId)}/close`, {}, {
      params: { create_revenue_schedule: createRevenueSchedule, emit_fiscal: emitFiscal },
    }),
}
