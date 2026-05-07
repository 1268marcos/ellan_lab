import { api } from './client'

/** Resposta de GET /api/v1/coo/widgets/summary */
export type CooWidgetsSummary = {
  sla_violated_24h: number
  avg_pickup_time_min: number | null
  deliveries_today: number
  lockers_offline: number
  cost_per_delivery: number | null
}

const base = '/v1/coo'

export const cooApi = {
  getMeta: () => api.get(`${base}/meta`),
  getWidgetsSummary: () => api.get<CooWidgetsSummary>(`${base}/widgets/summary`),
  getJson: (path: string, params?: Record<string, string | number | undefined>) =>
    api.get(`${base}/${path}`, { params }),
  postApprovalSlaAdjust: (body: { approval_type?: string; subject?: string; payload?: Record<string, unknown> }) =>
    api.post(`${base}/approvals/sla/adjust`, body),
  postApprovalExpansion: (body: { approval_type?: string; subject?: string; payload?: Record<string, unknown> }) =>
    api.post(`${base}/approvals/expansion`, body),
}
