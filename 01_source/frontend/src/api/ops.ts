import { api } from './client'
import type { Locker, Manifest, SLAMetrics } from '../types'

type LockerOccupancyResponse = {
  occupancy?: number
  occupied_ratio?: number
  occupancy_ratio?: number
}

export const opsApi = {
  getLockers: () => api.get<Locker[]>('/v1/inventory/lockers'),
  getPendingManifests: () =>
    api.get<Manifest[]>('/v1/logistics/manifests', { params: { status: 'pending' } }),
  getSlaCompliance: () => api.get<SLAMetrics>('/v1/order-lifecycle/sla/compliance'),
  getLockerOccupancy: (lockerId: string) =>
    api.get<LockerOccupancyResponse>(`/v1/inventory/lockers/${lockerId}/occupancy`),
}
