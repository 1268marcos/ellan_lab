export interface Locker {
  id: string
  occupancy: number
  status: 'active' | 'maintenance'
}

export interface Manifest {
  id: string
  status: string
}

export interface SLAMetrics {
  compliance_percent?: number
  sla_percent?: number
  percent?: number
  value?: number
}

export interface OpsDashboardSummary {
  lockersAtivos: number
  pickupsHoje: number
  slaPercent: number
  lockers: Locker[]
}
