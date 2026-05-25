import { api } from './client'

const BASE = '/api/v1/security'

export type SecurityUser = {
  id: string
  full_name: string
  email: string
  phone?: string
  is_active: boolean
  created_at: string
}

export type SecurityRole = {
  id: string
  user_id: string
  role: string
  scope_type: string
  scope_id?: string
  is_active: boolean
  granted_at: string
  revoked_at?: string
}

export type PermissionGroup = {
  id: string
  name: string
  description?: string
  is_system: boolean
  created_at: string
}

export type Permission = {
  id: string
  group_id: string
  object_key: string
  created_at: string
}

export type PermissionMatrix = {
  groups: Array<{
    group_id: string
    group_name: string
    permissions: Permission[]
    member_user_ids: string[]
  }>
  total_permissions: number
}

export type ApiKeyMeta = {
  id: string
  user_id: string
  key_prefix: string
  label?: string
  scopes: string[]
  revoked_at?: string
  created_at: string
}

export type WebhookEndpoint = {
  id: string
  url: string
  events: string[]
  active: boolean
  secret_prefix?: string
}

export const securityCrudApi = {
  seed: () => api.post<Record<string, number>>(`${BASE}/seed`),
  listUsers: () => api.get<{ users: SecurityUser[]; total: number }>(`${BASE}/users`),
  getUser: (id: string) => api.get<SecurityUser>(`${BASE}/users/${id}`),
  createUser: (body: { full_name: string; email: string; phone?: string; is_active?: boolean }) =>
    api.post<SecurityUser>(`${BASE}/users`, body),
  updateUser: (id: string, body: Partial<{ full_name: string; email: string; phone: string; is_active: boolean }>) =>
    api.patch<SecurityUser>(`${BASE}/users/${id}`, body),
  deleteUser: (id: string) => api.delete(`${BASE}/users/${id}`),
  listRoles: (userId?: string) =>
    api.get<{ roles: SecurityRole[]; total: number }>(`${BASE}/roles`, { params: userId ? { user_id: userId } : {} }),
  getRole: (id: string) => api.get<SecurityRole>(`${BASE}/roles/${id}`),
  createRole: (body: { user_id: string; role: string; scope_type?: string; scope_id?: string }) =>
    api.post<SecurityRole>(`${BASE}/roles`, body),
  updateRole: (id: string, body: Partial<{ role: string; is_active: boolean }>) =>
    api.patch<SecurityRole>(`${BASE}/roles/${id}`, body),
  deleteRole: (id: string) => api.delete(`${BASE}/roles/${id}`),
  matrix: () => api.get<PermissionMatrix>(`${BASE}/permissions/matrix`),
  listGroups: () => api.get<{ items: PermissionGroup[]; total: number }>(`${BASE}/groups`),
  createGroup: (body: { name: string; description?: string }) => api.post<PermissionGroup>(`${BASE}/groups`, body),
  listPermissions: (groupId?: string) =>
    api.get<{ items: Permission[]; total: number }>(`${BASE}/permissions`, {
      params: groupId ? { group_id: groupId } : {},
    }),
  createPermission: (body: { group_id: string; object_key: string }) =>
    api.post<Permission>(`${BASE}/permissions`, body),
  listApiKeys: (userId?: string) =>
    api.get<{ items: ApiKeyMeta[]; total: number }>(`${BASE}/api-keys`, {
      params: userId ? { user_id: userId } : {},
    }),
  rotateApiKey: (body: { user_id: string; label?: string; scopes?: string[] }) =>
    api.post<{ api_key: string; meta: ApiKeyMeta }>(`${BASE}/api-keys/rotate`, body),
  listWebhooks: () => api.get<{ items: WebhookEndpoint[]; total: number }>(`${BASE}/webhooks`),
  webhookConfig: (body: {
    id?: string
    url: string
    events?: string[]
    active?: boolean
    owner_type?: string
  }) => api.post<{ endpoint: WebhookEndpoint; webhook_secret?: string }>(`${BASE}/webhook-config`, body),
}
