import { api } from './client'

/** Prefixo /api/bia evita colisão com o proxy /api/analytics (8127). */
const BASE = '/api/bia/v1/analytics-bi-admin'

export type BiDashboard = {
  facts_count: number
  facts_24h: number
  partners: number
  kpi_definitions: number
  report_catalog: number
  network_players: number
  player_relations: number
  mrr_rows: number
  locker_pnl_rows: number
  partner_revenue_rows: number
  capability_webhooks: number
  open_marts_months: number
  readiness_rows?: number
  readiness_go_live?: number
  readiness_avg_score?: number
  open_kpi_alerts?: number
  mart_jobs_pending?: number
  lineage_edges?: number
  market_presence_rows?: number
  export_jobs_24h?: number
}

export type BiReadinessRow = {
  network_player_code: string
  readiness_band: string
  score_total: number
  blockers: string[]
}

export type BiOpsIntelligence = {
  readiness_rows: number
  avg_readiness_score: number
  go_live_count: number
  open_kpi_alerts: number
  pending_mart_jobs: number
  lineage_edges: number
  export_jobs_24h: number
  market_presence_rows: number
}

export type BiDataPartner = {
  id: string
  name: string
  code: string
  partner_type: string
  region_code?: string
  active: boolean
}

export type BiLockerNetworkPlayer = {
  id: string
  code: string
  name: string
  player_role: string
  parent_group: string
  country: string
  regions: string[]
  bi_priority_score: number
  supports_lockers: boolean
  supports_marketplace: boolean
}

export type AnalyticsFact = {
  id: string
  fact_key: string
  fact_name: string
  order_id: string
  occurred_at: string
  payload: Record<string, unknown>
}

export const biAnalyticsAdminApi = {
  seed: () => api.post(`${BASE}/seed`),
  dashboard: () => api.get<BiDashboard>(`${BASE}/dashboard`),
  integrationLinks: () => api.get<Record<string, unknown>>(`${BASE}/integration-hub/links`),

  listPartners: () => api.get<{ partners: BiDataPartner[]; total: number }>(`${BASE}/bi-data-partners`),
  createPartner: (body: Record<string, unknown>) => api.post<BiDataPartner>(`${BASE}/bi-data-partners`, body),
  configureWebhook: (partnerId: string, body: { url: string; secret?: string }) =>
    api.put(`${BASE}/bi-data-partners/${encodeURIComponent(partnerId)}/webhook`, body),
  rotateApiKey: (partnerId: string) =>
    api.post<{ api_key: string }>(`${BASE}/bi-data-partners/${encodeURIComponent(partnerId)}/api-keys/rotate`),

  listFacts: (params?: { limit?: number; order_id?: string }) =>
    api.get<{ items: AnalyticsFact[]; total: number }>(`${BASE}/analytics-facts`, { params }),
  createFact: (body: Record<string, unknown>) => api.post(`${BASE}/analytics-facts`, body),

  listKpis: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/kpi-definitions`),
  listReports: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/report-catalog`),
  listMarts: () => api.get<{ mrr: unknown[]; locker_pnl: unknown[]; partner_revenue: unknown[] }>(`${BASE}/marts`),

  listPlayers: (priorityOnly?: boolean) =>
    api.get<{ players: BiLockerNetworkPlayer[]; total: number }>(`${BASE}/bi-locker-network-players`, {
      params: priorityOnly ? { priority_only: true } : undefined,
    }),
  seedPlayers: () => api.post(`${BASE}/bi-locker-network-players/seed-global-catalog`),
  tier1Coverage: () => api.get<{ tier1_present: number; tier1_required: number; tier1_codes: string[]; coverage_pct: number }>(
    `${BASE}/bi-locker-network-players/tier1-coverage`,
  ),
  listRelations: () => api.get<{ relations: unknown[]; total: number }>(`${BASE}/bi-locker-network-players/relations`),

  listCapabilityWebhooks: () => api.get<{ webhooks: unknown[]; total: number }>(`${BASE}/bi-capability-webhooks`),
  createCapabilityWebhook: (body: Record<string, unknown>) => api.post(`${BASE}/bi-capability-webhooks`, body),

  opsIntelligence: () => api.get<BiOpsIntelligence>(`${BASE}/ops-intelligence/summary`),
  seedProfessional: () => api.post(`${BASE}/ops-intelligence/seed-professional`),
  listReadiness: (band?: string) =>
    api.get<{ rows: BiReadinessRow[]; total: number; bands: Record<string, number>; avg_score: number }>(
      `${BASE}/data-readiness`,
      { params: band ? { band } : undefined },
    ),
  recomputeReadiness: () => api.post(`${BASE}/data-readiness/recompute`),
  listMartJobs: () => api.get<{ jobs: unknown[]; total: number }>(`${BASE}/mart-refresh-jobs`),
  triggerMartRefresh: (body: { mart_name: string; triggered_by?: string }) =>
    api.post(`${BASE}/mart-refresh-jobs`, body),
  listAlertRules: () => api.get<{ rules: unknown[]; total: number }>(`${BASE}/kpi-alert-rules`),
  listAlertEvents: (status?: string) =>
    api.get<{ events: unknown[]; total: number }>(`${BASE}/kpi-alert-events`, {
      params: status ? { status } : undefined,
    }),
  listLineage: () => api.get<{ edges: unknown[]; total: number }>(`${BASE}/data-lineage`),
  listExportJobs: () => api.get<{ jobs: unknown[]; total: number }>(`${BASE}/export-jobs`),
  createExportJob: (body: { dataset_code: string; export_format?: string }) =>
    api.post(`${BASE}/export-jobs`, body),
  listTaxonomy: () => api.get<{ segments: unknown[]; total: number }>(`${BASE}/player-segment-taxonomy`),
  listMarketPresence: (player_code?: string) =>
    api.get<{ presence: unknown[]; total: number }>(`${BASE}/player-market-presence`, {
      params: player_code ? { player_code } : undefined,
    }),
  listDomainLinks: () => api.get<{ links: unknown[]; total: number }>(`${BASE}/unified-domain-links`),
  listAudit: () => api.get<{ events: unknown[]; total: number }>(`${BASE}/ops-audit-log`),

  efficiencyScorecard: () => api.get<Record<string, unknown>>(`${BASE}/efficiency/scorecard`),
  listDqChecks: () => api.get<{ checks: unknown[]; total: number }>(`${BASE}/efficiency/data-quality-checks`),
  runDqChecks: () => api.post<{ total: number; passed: number; failed: number }>(`${BASE}/efficiency/data-quality-checks/run`),
  listScheduledExports: () => api.get<{ schedules: unknown[]; total: number }>(`${BASE}/efficiency/scheduled-exports`),
  tickScheduledExports: () => api.post(`${BASE}/efficiency/scheduled-exports/tick`),
  listAnomalySignals: (status?: string) =>
    api.get<{ signals: unknown[]; total: number }>(`${BASE}/efficiency/anomaly-signals`, {
      params: status ? { status } : undefined,
    }),
  scanAnomalies: () => api.post(`${BASE}/efficiency/anomaly-signals/scan`),
  listBookmarks: () => api.get<{ bookmarks: unknown[]; total: number }>(`${BASE}/efficiency/bookmarks`),
  listPipelineSync: () => api.get<unknown[]>(`${BASE}/efficiency/pipeline-sync`),
  refreshPipelineSync: () => api.post(`${BASE}/efficiency/pipeline-sync/refresh`),
  unifiedEfficiency: () => api.get<Record<string, unknown>>(`${BASE}/integration-hub/unified-efficiency`),
}
