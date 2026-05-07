import { api } from './client'

export type ExecutiveGlobalKpis = {
  total_revenue_mtd: number
  total_revenue_mtd_formatted: string
  occupancy_rate: number
  nps: number
  critical_incidents: number
  expanding_lockers: number
  as_of: string
}

export type ExecutiveMrr = {
  total_mrr: number
  total_mrr_formatted: string
  by_region: Array<{ region: string; mrr: number; percentage: number }>
}

export type ExecutiveForecast = {
  historical: Array<{ month: string; revenue: number }>
  forecast: Array<{ month: string; forecast_revenue: number }>
}

export type ExecutiveExpansion = {
  pipeline_count: number
  pending_approvals: number
  roi_by_location: Array<{
    city: string
    region: string
    annual_revenue: number
    installation_cost: number
    roi_percent: number
  }>
}

export type ExecutivePartners = {
  top_partners: Array<{ name: string; total_revenue: number }>
  partner_churn_rate: number
  sla_compliance: number
  as_of: string
}

export const executiveApi = {
  getGlobalKpis: () => api.get<ExecutiveGlobalKpis>('/v1/executive/kpis/globals'),
  getMrr: () => api.get<ExecutiveMrr>('/v1/executive/finance/mrr'),
  getForecast: () => api.get<ExecutiveForecast>('/v1/executive/finance/forecast'),
  getExpansion: () => api.get<ExecutiveExpansion>('/v1/executive/expansion/pipeline'),
  getTopPartners: (limit = 10) =>
    api.get<ExecutivePartners>('/v1/executive/partners/top', { params: { limit } }),
}
