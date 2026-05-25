import { api } from './client'
import { opsActorHeaders } from './opsActorHeaders'

export type LockerProfitabilityRow = {
  locker_id: string
  month: string
  sales_revenue_cents: number
  rental_revenue_cents: number
  marketplace_commission_cents: number
  total_revenue_cents: number
  total_opex_cents: number
  depreciation_cents: number
  total_costs_cents: number
  net_profit_cents: number
  net_margin_pct: number
  total_pickups: number
  active_rentals: number
  avg_revenue_per_pickup_cents: number
  computed_at: string
}

export type FinancialDashboard = {
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

export type RealtimeKpis = {
  snapshot_time?: string
  orders_last_hour?: number
  revenue_last_hour?: number
  orders_last_24h?: number
  unique_customers_24h?: number
  revenue_last_24h?: number
  avg_pickup_minutes?: number
  offline_lockers?: number
  active_sellers?: number
  pending_payment?: number
  expired_pickup?: number
  critical_alerts?: number
  high_alerts?: number
}

export type RefreshStatusRow = {
  view_name: string
  status: string
  started_at: string
  finished_at?: string | null
  duration_ms?: number | null
  error_message?: string | null
  triggered_by?: string
}

const analyticsHeaders = () => opsActorHeaders()

export const financialAnalyticsApi = {
  lockerProfitability: (params?: { locker_id?: string; month?: string }) =>
    api.get<{ items: LockerProfitabilityRow[]; total: number }>(
      '/analytics/v1/analytics/locker-profitability',
      { params, headers: analyticsHeaders() },
    ),

  financialDashboard: () =>
    api.get<FinancialDashboard>('/analytics/v1/analytics/financial-dashboard', {
      headers: analyticsHeaders(),
    }),

  realtimeKpis: () =>
    api.get<RealtimeKpis>('/analytics/v1/analytics/realtime-kpis', {
      headers: analyticsHeaders(),
    }),

  refreshStatus: () =>
    api.get<{ items: RefreshStatusRow[] }>('/analytics/v1/analytics/refresh-status', {
      headers: analyticsHeaders(),
    }),

  triggerRefresh: (view: 'all' | 'mv_locker_monthly_profitability' | 'mv_realtime_kpis' | 'v_financial_dashboard' = 'all') =>
    api.post('/analytics/v1/analytics/refresh', { view }, { headers: analyticsHeaders() }),
}
