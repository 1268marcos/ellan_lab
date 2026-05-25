import axios from 'axios'
import { loadAuth } from './auth'
import { opsActorHeaders } from './opsActorHeaders'

export type FinancialKpis = {
  revenue_mtd_brl?: number
  costs_mtd_brl?: number
  profit_mtd_brl?: number
  margin_mtd_pct?: number
  revenue_ltm_brl?: number
  profit_ltm_brl?: number
  total_pickups_ltm?: number
  ltm_margin_pct?: number
  total_active_lockers?: number
  underperforming_lockers?: number
  pct_underperforming?: number
  target_ebitda_margin_pct?: number
  target_payback_months?: number
  max_acceptable_payback?: number
  computed_at?: string
}

export type LockerRoiRow = {
  locker_id: string
  external_id?: string
  display_name?: string
  city?: string
  region?: string
  total_investment_brl?: number
  avg_monthly_profit_brl?: number
  payback_months?: number
  annual_roi_pct?: number
  viability_classification?: string
  recommendation?: string
  alert_status?: string
}

export type LockerPnlRow = {
  month_ref: string
  locker_id: string
  revenue_cents: number
  opex_cents: number
  depreciation_cents: number
  total_cost_cents: number
  net_profit_cents: number
  margin_pct: number
}

export type RevenueTrendPoint = {
  month: string
  revenue_brl: number
  profit_brl: number
  avg_margin_pct: number
}

export type ExpansionMetric = {
  scenario_metric: string
  value: number
  description: string
}

const finApi = axios.create({ baseURL: '/api/v1/financial', timeout: 20_000 })

finApi.interceptors.request.use((config) => {
  const auth = loadAuth()
  config.headers = { ...opsActorHeaders(), ...(config.headers as Record<string, string>) }
  const bearer = auth?.token || auth?.apiKey
  if (bearer) {
    config.headers.Authorization = `Bearer ${bearer}`
  }
  if (auth?.apiKey) {
    config.headers['X-API-Key'] = auth.apiKey
  }
  return config
})

export const financialExecutiveApi = {
  kpis: () => finApi.get<FinancialKpis>('/kpis'),
  lockerRoi: (params?: { city?: string; viability?: string }) =>
    finApi.get<{ items: LockerRoiRow[]; total: number }>('/locker-roi', { params }),
  lockerPnl: (params?: {
    locker_id?: string
    month_from?: string
    month_to?: string
    sort?: string
    order?: 'asc' | 'desc'
  }) => finApi.get<{ items: LockerPnlRow[]; total: number }>('/locker-pnl', { params }),
  partnerRevenue: (params?: { partner_id?: string }) =>
    finApi.get<{
      revenue: Array<Record<string, unknown>>
      settlements: Array<Record<string, unknown>>
      total_revenue_rows: number
      total_settlement_rows: number
    }>('/partner-revenue', { params }),
  revenueTrend: (months = 12) =>
    finApi.get<{ items: RevenueTrendPoint[] }>('/revenue-trend', { params: { months } }),
  simulateExpansion: (body: Record<string, unknown>) =>
    finApi.post<{ items: ExpansionMetric[]; target_city: string }>('/simulate-expansion', body),
  exportUrl: (format: 'csv' | 'pdf', dataset: string) =>
    `/api/v1/financial/export/${format}?dataset=${encodeURIComponent(dataset)}`,
}
