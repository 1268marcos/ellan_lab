import { api } from './client'

const BASE = '/api/partner-admin/v1/partner-admin'

export type Tenant = {
  tenant_id: string
  cnpj: string
  razao_social: string
  regime: string
  crt: string
  is_active: boolean
}

export type CustomDomain = {
  id: string
  tenant_id: string
  domain: string
  verified: boolean | null
}

export type TenantPartnerLink = {
  id: string
  tenant_id: string
  partner_id: string
  partner_type: string
  is_default: boolean
}

export const tenantAdminApi = {
  seed: () => api.post(`${BASE}/seed`),
  listTenants: () => api.get<{ tenants: Tenant[]; total: number }>(`${BASE}/tenants`),
  createTenant: (body: Record<string, unknown>) => api.post<Tenant>(`${BASE}/tenants`, body),
  listDomains: (tenantId: string) =>
    api.get<{ domains: CustomDomain[]; total: number }>(
      `${BASE}/tenants/${encodeURIComponent(tenantId)}/domains`,
    ),
  addDomain: (tenantId: string, body: { domain: string; verified?: boolean }) =>
    api.post(`${BASE}/tenants/${encodeURIComponent(tenantId)}/domains`, body),
  listPartnerLinks: (tenantId: string) =>
    api.get<{ links: TenantPartnerLink[]; total: number }>(
      `${BASE}/tenants/${encodeURIComponent(tenantId)}/partner-links`,
    ),
  addPartnerLink: (
    tenantId: string,
    body: { partner_id: string; partner_type: string; is_default?: boolean },
  ) => api.post(`${BASE}/tenants/${encodeURIComponent(tenantId)}/partner-links`, body),
}
