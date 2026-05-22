import { api } from './client'

const BASE = '/api/ml-admin/v1/ml-admin'

export type MlDataPartner = {
  id: string
  name: string
  code: string
  partner_type: string
  region_code?: string
  network_player_code?: string | null
  api_base_url?: string
  active: boolean
}

export type MlLockerNetworkPlayer = {
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
  marketplace_channel_code?: string | null
  ml_scoring_weight: number
  global_tier?: string
  integration_status?: string
  sort_order: number
  active: boolean
}

export type MlNetworkMlProfile = {
  id: string
  network_player_id: string
  network_player_code?: string | null
  use_case_id?: string | null
  use_case_code?: string | null
  telemetry_density: string
  drift_baseline_psi?: number | null
  feature_pack: string[]
  active: boolean
}

export type MlNetworkSeedResult = {
  inserted: number
  updated: number
  profiles_created: number
  partners_linked: number
  catalog_size: number
}

export type MlModelMetadata = {
  id: number
  model_version: string
  trained_at: string
  metrics_json: string
  status: string
}

export type MlDashboard = {
  active_models: number
  predictions_24h: number
  features_rows: number
  feedback_rows: number
  partners: number
  use_cases?: number
  registry_production?: number
  training_running?: number
  drift_critical?: number
  feature_definitions?: number
  alert_rules?: number
  deployments_7d?: number
  locker_network_players?: number
  locker_network_priority?: number
  network_ml_profiles?: number
  player_capabilities?: number
  player_relations?: number
  market_presence_rows?: number
  tier1_players?: number
  ml_readiness_rows?: number
  ml_readiness_go_live?: number
  ml_readiness_avg_score?: number
  ml_readiness_alerts_open?: number
}

export type MlReadinessRow = {
  id: string
  network_player_code: string
  score_total: number
  readiness_band: string
  blockers?: string[]
}

export type MlReadinessAlert = {
  id: string
  network_player_code: string
  alert_type: string
  severity: string
  score_delta: number
  previous_score: number | null
  new_score: number
  status: string
  webhook_dispatched: boolean
  created_at: string
}

export type MlCapabilityWebhook = {
  id: string
  network_player_code: string
  capability_code: string
  url: string
  active: boolean
  last_http_status?: number | null
}

export type MlPlayerCapability = {
  id: string
  network_player_code: string
  capability_code: string
  capability_name: string
  protocol: string
  direction: string
  production_ready: boolean
}

export type MlPlayerRelation = {
  id: string
  from_player_code: string | null
  to_player_code: string | null
  relation_type: string
  strength: string
}

export type MlUseCase = {
  id: string
  code: string
  name: string
  domain: string
  tier: string
  active: boolean
}

export const mlAdminApi = {
  seed: () => api.post(`${BASE}/seed`),
  dashboard: () => api.get<MlDashboard>(`${BASE}/dashboard`),
  validateFeedback: () => api.post(`${BASE}/ops/validate-feedback`),

  listPartners: (params?: { active_only?: boolean }) =>
    api.get<{ partners: MlDataPartner[]; total: number }>(`${BASE}/ml-data-partners`, { params }),
  createPartner: (body: Record<string, unknown>) => api.post<MlDataPartner>(`${BASE}/ml-data-partners`, body),
  configureWebhook: (partnerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/ml-data-partners/${encodeURIComponent(partnerId)}/webhook`, body),
  rotateApiKey: (partnerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/ml-data-partners/${encodeURIComponent(partnerId)}/api-keys/rotate`,
    ),

  listModels: () => api.get<{ items: MlModelMetadata[]; total: number }>(`${BASE}/ml-model-metadata`),
  createModel: (body: Record<string, unknown>) => api.post<MlModelMetadata>(`${BASE}/ml-model-metadata`, body),
  updateModel: (id: number, body: Record<string, unknown>) =>
    api.patch<MlModelMetadata>(`${BASE}/ml-model-metadata/${id}`, body),

  listFeatures: (params?: { locker_id?: string; limit?: number }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-features-daily`, { params }),
  createFeature: (body: Record<string, unknown>) => api.post(`${BASE}/ml-features-daily`, body),

  listPredictions: (params?: { locker_id?: string; limit?: number }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-predictions-log`, { params }),
  createPrediction: (body: Record<string, unknown>) => api.post(`${BASE}/ml-predictions-log`, body),

  listFeedback: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-prediction-feedback`),

  listUseCases: () => api.get<{ items: MlUseCase[]; total: number }>(`${BASE}/ml-use-cases`),
  createUseCase: (body: Record<string, unknown>) => api.post<MlUseCase>(`${BASE}/ml-use-cases`, body),
  listRegistry: (params?: { use_case_id?: string; stage?: string }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-model-registry`, { params }),
  createRegistry: (body: Record<string, unknown>) => api.post(`${BASE}/ml-model-registry`, body),
  promoteRegistry: (entryId: string, body?: Record<string, unknown>) =>
    api.post(`${BASE}/ml-model-registry/${encodeURIComponent(entryId)}/promote`, body ?? {}),
  listTrainingRuns: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-training-runs`),
  listFeatureCatalog: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-feature-definitions`),
  listDrift: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-drift-reports`),
  listSlos: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-inference-slo`),
  listAlerts: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-alert-rules`),
  listDeployments: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-deployment-events`),

  listLockerNetworks: (params?: { active_only?: boolean; priority_only?: boolean; country?: string }) =>
    api.get<{ items: MlLockerNetworkPlayer[]; total: number; priority_codes: string[] }>(
      `${BASE}/ml-locker-network-players`,
      { params },
    ),
  seedLockerNetworks: () => api.post<MlNetworkSeedResult>(`${BASE}/ml-locker-network-players/seed-from-catalog`),
  listNetworkMlProfiles: (params?: { network_player_id?: string }) =>
    api.get<{ items: MlNetworkMlProfile[]; total: number }>(`${BASE}/ml-network-ml-profiles`, { params }),
  listPlayerCapabilities: () =>
    api.get<{ items: MlPlayerCapability[]; total: number }>(`${BASE}/ml-player-capabilities`),
  listPlayerRelations: () => api.get<{ items: MlPlayerRelation[]; total: number }>(`${BASE}/ml-player-relations`),

  listMlReadiness: () => api.get<{ items: MlReadinessRow[]; total: number }>(`${BASE}/ml-integration-readiness`),
  mlReadinessHub: () =>
    api.get<{ readiness_rows: number; avg_score: number; open_readiness_alerts: number }>(
      `${BASE}/ml-readiness-hub/summary`,
    ),
  recomputeMlReadiness: () => api.post(`${BASE}/ml-integration-readiness/recompute`),
  listMlReadinessAlerts: (open_only = true) =>
    api.get<{ items: MlReadinessAlert[]; total: number }>(`${BASE}/ml-readiness-alerts`, {
      params: { open_only },
    }),
  listMlCapabilityWebhooks: (network_player_id?: string) =>
    api.get<{ items: MlCapabilityWebhook[]; total: number }>(`${BASE}/ml-capability-webhooks`, {
      params: network_player_id ? { network_player_id } : undefined,
    }),
  upsertMlCapabilityWebhook: (body: {
    network_player_id: string
    capability_code: string
    url: string
    secret?: string
    events?: string[]
  }) => api.put(`${BASE}/ml-capability-webhooks`, body),

  createTrainingRun: (body: Record<string, unknown>) => api.post(`${BASE}/ml-training-runs`, body),
  createFeatureCatalog: (body: Record<string, unknown>) => api.post(`${BASE}/ml-feature-definitions`, body),
  createDrift: (body: Record<string, unknown>) => api.post(`${BASE}/ml-drift-reports`, body),
  createSlo: (body: Record<string, unknown>) => api.post(`${BASE}/ml-inference-slo`, body),
  createAlertRule: (body: Record<string, unknown>) => api.post(`${BASE}/ml-alert-rules`, body),
  listGrants: () => api.get<{ items: unknown[]; total: number }>(`${BASE}/ml-partner-access-grants`),
  createGrant: (body: Record<string, unknown>) => api.post(`${BASE}/ml-partner-access-grants`, body),
}
