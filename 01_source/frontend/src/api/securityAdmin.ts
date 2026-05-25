import { api } from './client'

const BASE = '/api/partner-admin/v1/partner-admin'

export type SecuritySummary = {
  users: number
  active_roles: number
  permission_groups: number
  webhook_endpoints: number
  active_api_keys: number
  audit_logs: number
  domain_links: number
  domain_catalog?: number
  role_catalog?: number
  cross_domain_grants?: number
  active_sessions?: number
  webhook_deliveries?: number
  identity_providers?: number
  policy_snapshots?: number
  domains_reachable?: number
  domains_total?: number
}

export type SecurityUser = {
  id: string
  full_name: string
  email: string
  phone?: string
  is_active: boolean
  created_at: string
}

export type PermissionGroup = {
  id: string
  name: string
  description?: string
  is_system: boolean
  created_at: string
}

export type SecurityWebhook = {
  id: string
  url: string
  events: string[]
  active: boolean
  secret_prefix?: string
}

export type SecurityApiKeyMeta = {
  id: string
  user_id: string
  key_prefix: string
  label?: string
  revoked_at?: string
}

export type AuditLogRow = {
  id: string
  action: string
  target_type: string
  target_id: string
  actor_id?: string
  occurred_at: string
}

export type DomainLink = {
  id: string
  user_id: string
  domain: string
  entity_type: string
  entity_id: string
  relation: string
}

export const securityAdminApi = {
  summary: () => api.get<SecuritySummary>(`${BASE}/security-admin/summary`),
  listUsers: () => api.get<{ users: SecurityUser[]; total: number }>(`${BASE}/users`),
  createUser: (body: { full_name: string; email: string; phone?: string; is_active?: boolean }) =>
    api.post<SecurityUser>(`${BASE}/users`, body),
  listPermissionGroups: () =>
    api.get<{ items: PermissionGroup[]; total: number }>(`${BASE}/security-admin/permission-groups`),
  listWebhooks: () =>
    api.get<{ items: SecurityWebhook[]; total: number }>(`${BASE}/security-admin/webhook-endpoints`),
  rotateWebhook: (id: string) =>
    api.post<{ webhook_secret: string }>(`${BASE}/security-admin/webhook-endpoints/${id}/rotate-secret`),
  listApiKeys: () => api.get<{ items: SecurityApiKeyMeta[]; total: number }>(`${BASE}/security-admin/api-keys`),
  rotateApiKey: (user_id: string) =>
    api.post<{ api_key: string }>(`${BASE}/security-admin/api-keys/rotate`, { user_id }),
  listAudit: (limit = 80) =>
    api.get<{ items: AuditLogRow[]; total: number }>(`${BASE}/security-admin/audit-logs`, { params: { limit } }),
  listDomainLinks: () =>
    api.get<{ items: DomainLink[]; total: number }>(`${BASE}/security-admin/domain-links`),
  seed: () => api.post(`${BASE}/security-admin/seed`),
  listDomainCatalog: () => api.get<{ items: Array<{ code: string; label: string; admin_route?: string }>; total: number }>(`${BASE}/security-admin/domain-catalog`),
  listRoleCatalog: () => api.get<{ items: Array<{ code: string; label: string; default_scope_type: string }>; total: number }>(`${BASE}/security-admin/role-catalog`),
  domainHealth: () => api.get<{ items: Array<{ domain: string; label: string; reachable: boolean }>; reachable_count: number; total: number }>(`${BASE}/security-admin/cross-domain/health`),
  ecosystemMap: () => api.get<{ entities: Array<{ domain: string; entity_type: string; entity_id: string; label: string; source: string }>; remote_entities: number }>(`${BASE}/security-admin/cross-domain/ecosystem-map`),
  listGrants: (user_id?: string) => api.get<{ items: CrossDomainGrant[]; total: number }>(`${BASE}/security-admin/cross-domain-grants`, { params: user_id ? { user_id } : {} }),
  user360: (userId: string) => api.get<User360>(`${BASE}/security-admin/users/${userId}/360`),
  listSessions: () => api.get<{ items: Array<{ id: string; user_id: string; auth_method: string; expires_at: string }>; total: number }>(`${BASE}/security-admin/sessions`),
  listDeliveries: () => api.get<{ items: Array<{ id: string; event_name: string; status: string }>; total: number }>(`${BASE}/security-admin/webhook-deliveries`),
  listIdentityProviders: () => api.get<{ items: Array<{ code: string; name: string; provider_type: string; is_active: boolean }>; total: number }>(`${BASE}/security-admin/identity-providers`),
  listPolicySnapshots: () => api.get<{ items: Array<{ id: string; version_label: string; policy_kind: string }>; total: number }>(`${BASE}/security-admin/policy-snapshots`),
  createPolicySnapshot: (body: { version_label: string; created_by?: string }) => api.post(`${BASE}/security-admin/policy-snapshots`, body),
  listLockerPlayers: (priorityOnly = false) =>
    api.get<{ items: LockerPlayer[]; total: number; priority_count: number }>(
      `${BASE}/security-admin/locker-players${priorityOnly ? '/priority' : ''}`,
    ),
  lockerPlayerProfile: (code: string) =>
    api.get<{ player: LockerPlayer; suggested_grants: CrossDomainGrant[] }>(
      `${BASE}/security-admin/locker-players/${code}/security-profile`,
    ),
  intelligence: () => api.get<{
    overall_posture: string
    average_user_risk: number
    open_alerts: number
    pending_reviews: number
    recommendations: string[]
  }>(`${BASE}/security-admin/value/intelligence`),
  listAlerts: () => api.get<{ items: Array<{ id: string; title: string; severity: string; status: string }>; open_count: number }>(`${BASE}/security-admin/value/alerts`),
  listCompliance: () => api.get<{ items: unknown[]; coverage_pct: number }>(`${BASE}/security-admin/value/compliance`),
  listRoleTemplates: () => api.get<{ items: Array<{ code: string; name: string; roles: string[]; target_segment?: string }> }>(`${BASE}/security-admin/value/role-templates`),
  listAccessReviews: () =>
    api.get<{
      items: Array<{
        id: string
        name: string
        status: string
        pending_items: number
        approved_items?: number
        revoked_items?: number
        due_at?: string
      }>
    }>(`${BASE}/security-admin/value/access-reviews`),
  listAccessReviewItems: (campaignId: string, pendingOnly = true) =>
    api.get<{
      items: Array<{
        id: string
        campaign_id: string
        user_id: string
        subject_type: string
        subject_id: string
        subject_label?: string
        decision?: string | null
      }>
    }>(`${BASE}/security-admin/value/access-reviews/${campaignId}/items`, {
      params: { pending_only: pendingOnly },
    }),
  decideAccessReviewItem: (itemId: string, body: { decision: 'APPROVE' | 'REVOKE' | 'ESCALATE'; reviewer_id?: string; notes?: string }) =>
    api.post(`${BASE}/security-admin/value/access-reviews/items/${itemId}/decide`, body),
  listBreakGlass: (activeOnly = true) =>
    api.get<{
      items: Array<{
        id: string
        user_id: string
        reason: string
        status: string
        granted_roles: string[]
        expires_at: string
      }>
    }>(`${BASE}/security-admin/value/break-glass`, { params: { active_only: activeOnly } }),
  openBreakGlass: (body: {
    user_id: string
    reason: string
    granted_roles?: string[]
    approved_by?: string
    duration_hours?: number
  }) => api.post(`${BASE}/security-admin/value/break-glass`, body),
  revokeBreakGlass: (eventId: string, body?: { revoked_by?: string; reason?: string }) =>
    api.post(`${BASE}/security-admin/value/break-glass/${eventId}/revoke`, body ?? {}),
  accessMatrix: () => api.get<{ users: string[]; domains: string[]; cells: unknown[] }>(`${BASE}/security-admin/value/access-matrix`),
  listAccessRequests: (status?: string) =>
    api.get<{ items: Array<{ id: string; user_id: string; domain_code: string; status: string; permission_key: string }>; pending_count: number }>(
      `${BASE}/security-admin/cross-ops/access-requests`,
      { params: status ? { status } : {} },
    ),
  decideAccessRequest: (id: string, body: { decision: 'APPROVE' | 'DENY'; reviewer_id?: string }) =>
    api.post(`${BASE}/security-admin/cross-ops/access-requests/${id}/decide`, body),
  listJitGrants: () => api.get<{ items: Array<{ id: string; user_id: string; domain_code: string; expires_at: string }> }>(`${BASE}/security-admin/cross-ops/jit-grants`),
  listDelegations: () => api.get<{ items: Array<{ id: string; delegate_user_id: string; target_domain: string; target_entity_id: string }> }>(`${BASE}/security-admin/cross-ops/delegations`),
  syncEntitlements: () => api.post(`${BASE}/security-admin/cross-ops/entitlements/sync`),
  listEntitlements: () => api.get<{ items: unknown[]; domains_synced: number }>(`${BASE}/security-admin/cross-ops/entitlements`),
  domainAccessReport: (userId: string) =>
    api.get<{ user_id: string; roles: string[]; active_grants: unknown[]; pending_requests: number }>(
      `${BASE}/security-admin/cross-ops/users/${userId}/domain-access-report`,
    ),
  listUserPlayerAccess: (user_id?: string) =>
    api.get<{ items: UserPlayerAccess[]; total: number }>(`${BASE}/security-admin/user-player-access`, {
      params: user_id ? { user_id } : {},
    }),
}

export type LockerPlayer = {
  player_code: string
  name: string
  segment: string
  primary_domain: string
  related_domains: string[]
  regions: string[]
  global_tier: string
  grants_count?: number
}

export type UserPlayerAccess = {
  id: string
  user_id: string
  player_code: string
  access_role: string
}

export type CrossDomainGrant = {
  id: string
  user_id: string
  domain_code: string
  entity_type: string
  entity_id: string
  entity_label?: string
  permission_key: string
}

export type User360 = {
  user_id: string
  full_name: string
  email: string
  roles: string[]
  permission_groups: string[]
  active_sessions: number
  cross_domain_grants: CrossDomainGrant[]
}
