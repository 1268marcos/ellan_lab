import axios from 'axios'

const client = axios.create({
  baseURL: '/api/op',
  timeout: 30000,
})

function authHeaders(token?: string | null) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export type OpsMonitoringAlert = {
  code: string
  severity: string
  message: string
}

export type OpsMonitoringSummary = {
  ok: boolean
  as_of: string
  alerts: OpsMonitoringAlert[]
  credits_health: Record<string, unknown>
  reconciliation_lag: Record<string, unknown>
  runtime_deadlocks: Record<string, unknown>
}

export async function fetchOpsMonitoringSummary(token?: string | null) {
  const { data } = await client.get<OpsMonitoringSummary>('/ops/monitoring/summary', {
    headers: authHeaders(token),
  })
  return data
}
