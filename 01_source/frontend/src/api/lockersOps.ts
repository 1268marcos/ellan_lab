import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1/ops', timeout: 30000 })

export type OpsLocker = {
  id: string
  external_id?: string
  display_name?: string
  region?: string
  city?: string
  address_line?: string
  latitude?: number
  longitude?: number
  active?: boolean
  occupancy_pct?: number
  occupancy_level?: string
  health_score?: number
  health_status?: string
  ops_status?: string
  last_telemetry_at?: string
}

export type TelemetryPoint = {
  occurred_at: string
  temperature_celsius?: number
  battery_pct?: number
  signal_rssi?: number
  humidity_pct?: number
  event_type?: string
}

export type MaintenanceTicket = {
  id: string
  locker_id: string
  title: string
  description?: string
  status: string
  priority: string
  assigned_to?: string
  created_at: string
  updated_at: string
}

export type NocAlert = {
  alert_type: string
  alert_id: string
  severity: string
  breach_type?: string
  detected_at: string
  locker_display_name?: string
  reference_id?: string
  priority: number
  resolved_at?: string | null
}

export const lockersOpsApi = {
  listLockers: (params?: Record<string, string | number | boolean>) =>
    client.get<{ items: OpsLocker[] }>('/lockers', { params }),
  getLocker: (id: string) => client.get<OpsLocker>(`/lockers/${encodeURIComponent(id)}`),
  getTelemetry: (id: string, hours = 24) =>
    client.get<{ items: TelemetryPoint[] }>(`/lockers/${encodeURIComponent(id)}/telemetry`, {
      params: { hours },
    }),
  getMaintenance: (id: string) =>
    client.get<{ items: MaintenanceTicket[] }>(`/lockers/${encodeURIComponent(id)}/maintenance`),
  createMaintenance: (
    id: string,
    body: { title: string; description?: string; priority?: string; assigned_to?: string },
  ) => client.post<MaintenanceTicket>(`/lockers/${encodeURIComponent(id)}/maintenance`, body),
  getPickups: (id: string) =>
    client.get<{ items: Record<string, unknown>[] }>(`/lockers/${encodeURIComponent(id)}/pickups`),
  getOccupancy: () => client.get<{ items: Record<string, unknown>[] }>('/lockers/occupancy'),
  getAlerts: (params?: Record<string, string | number>) =>
    client.get<{ items: NocAlert[] }>('/alerts', { params }),
}

export function opsRealtimeWsUrl(path: '/ws/ops/realtime' | '/ws/ops/alerts') {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}${path}`
}
