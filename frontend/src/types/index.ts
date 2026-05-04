export interface Locker {
  id: string
  occupancy: number
  status: 'active' | 'maintenance'
}

export interface Pickup {
  id: string
  status: 'ready' | 'opened' | 'redeemed'
}

export interface OpsDashboardSummary {
  lockersAtivos: number
  pickupsHoje: number
  slaPercent: number
  lockers: Locker[]
}
