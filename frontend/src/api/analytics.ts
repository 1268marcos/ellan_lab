import { api } from './client'

export type Period = '7d' | '30d' | '90d'

export type QueryFilter = {
  partner_id?: string
  locker_id?: string
  period?: Period
}

export type SLOPoint = {
  date?: string
  value?: number
  percent?: number
  rate?: number
}

export type HourPoint = {
  hour: number | string
  pickups: number
}

export type LockerTurnover = {
  locker_id: string
  turnover: number
}

export type PartnerSLA = {
  partner_id: string
  compliance: number
}

export const analyticsApi = {
  getErrorRate: (params?: QueryFilter) =>
    api.get<SLOPoint[] | { current?: number; history?: SLOPoint[] }>('/v1/order-lifecycle/slo/error-rate', { params }),

  getLatencyP95: (params?: QueryFilter) =>
    api.get<SLOPoint[] | { current?: number; history?: SLOPoint[] }>('/v1/order-lifecycle/slo/latency-p95', { params }),

  getDivergence: (params?: QueryFilter) =>
    api.get<SLOPoint[] | { current?: number; history?: SLOPoint[] }>('/v1/order-lifecycle/slo/divergence', { params }),

  getPickupsByHour: (params?: QueryFilter) =>
    api.get<HourPoint[]>('/v1/order-lifecycle/analytics/pickups-by-hour', { params }),

  getInventoryTurnover: (params?: QueryFilter) =>
    api.get<LockerTurnover[]>('/v1/inventory/analytics/turnover', { params }),

  getLogisticsSlaCompliance: (params?: QueryFilter) =>
    api.get<PartnerSLA[]>('/v1/logistics/analytics/sla-compliance', { params }),
}

