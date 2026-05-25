import { api } from './client'

const BASE = '/api/partner-admin/v1/partner-admin'

export type CriticalTableRegistry = {
  table_name: string
  schema_name: string
  rls_enabled: boolean
  enforcement_layer: string
  description?: string
}

export type CriticalTablePolicy = {
  id: string
  table_name: string
  operation: string
  role: string
  scope_type: string
  allowed: boolean
  priority: number
}

export type CriticalAccessLogRow = {
  id: string
  table_name: string
  operation: string
  actor_id?: string
  target_user_id?: string
  decision: string
  reason?: string
  service_name?: string
  occurred_at: string
}

export type PublicAuditLogRow = {
  id: string
  actor_id?: string
  actor_role?: string
  action: string
  target_type: string
  target_id: string
  occurred_at: string
  source_service?: string
}

export const criticalTableSecurityApi = {
  listRegistry: () =>
    api.get<{ items: CriticalTableRegistry[]; total: number }>(`${BASE}/critical-table-security/registry`),
  listPolicies: (table_name?: string) =>
    api.get<{ items: CriticalTablePolicy[]; total: number }>(`${BASE}/critical-table-security/policies`, {
      params: table_name ? { table_name } : {},
    }),
  listAccessLog: (params?: { table_name?: string; limit?: number }) =>
    api.get<{ items: CriticalAccessLogRow[]; total: number }>(`${BASE}/critical-table-security/access-log`, {
      params,
    }),
  listPublicAuditLogs: (limit = 80) =>
    api.get<{ items: PublicAuditLogRow[]; total: number }>(`${BASE}/critical-audit-logs`, { params: { limit } }),
}
