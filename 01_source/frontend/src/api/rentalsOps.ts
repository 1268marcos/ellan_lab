import { api } from './client'

const BASE = '/api/op/v1/rentals-admin'

export type RentalPlan = {
  id: string
  name: string
  locker_id?: string | null
  slot_size?: string | null
  billing_cycle: string
  amount_cents: number
  currency: string
  active: boolean
}

export type RentalContract = {
  id: string
  locker_id: string
  slot_label: string
  renter_name?: string
  status: string
  billing_cycle: string
  amount_cents: number
  plan_id?: string
  tenant_id?: string
}

export type RentalEcosystemCatalog = {
  version: string
  networks_total: number
  priority_codes: string[]
  networks: Array<Record<string, unknown>>
  by_region: Record<string, unknown[]>
  by_type: Record<string, string[]>
  plans_catalog: number
  operators_catalog: number
}

export const rentalsOpsApi = {
  ecosystemCatalog: () =>
    api.get<{ ok: boolean; catalog: RentalEcosystemCatalog }>(`${BASE}/ecosystem/catalog`),

  seed: () => api.post<{ ok: boolean; seeded: Record<string, number> }>(`${BASE}/seed`),

  listPlans: (params?: { active_only?: boolean; locker_id?: string }) =>
    api.get<{ items: RentalPlan[]; total: number }>(`${BASE}/plans`, { params }),

  createPlan: (body: Record<string, unknown>) => api.post<RentalPlan>(`${BASE}/plans`, body),
  updatePlan: (planId: string, body: Record<string, unknown>) =>
    api.patch<RentalPlan>(`${BASE}/plans/${encodeURIComponent(planId)}`, body),
  deletePlan: (planId: string) => api.delete(`${BASE}/plans/${encodeURIComponent(planId)}`),

  listContracts: (params?: { status?: string; locker_id?: string; tenant_id?: string }) =>
    api.get<{ items: RentalContract[]; total: number }>(`${BASE}/contracts`, { params }),

  getContract: (contractId: string) =>
    api.get<{ contract: Record<string, unknown>; plan?: RentalPlan; slot?: Record<string, unknown> }>(
      `${BASE}/contracts/${encodeURIComponent(contractId)}`,
    ),

  createContract: (body: Record<string, unknown>) => api.post(`${BASE}/contracts`, body),
  updateContract: (contractId: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/contracts/${encodeURIComponent(contractId)}`, body),
  cancelContract: (contractId: string, body?: { cancel_reason?: string }) =>
    api.post(`${BASE}/contracts/${encodeURIComponent(contractId)}/cancel`, body ?? {}),

  listWebhooks: (tenantId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/webhooks`, { params: tenantId ? { tenant_id: tenantId } : {} }),

  upsertWebhook: (tenantId: string, body: Record<string, unknown>) =>
    api.put(`${BASE}/webhooks/${encodeURIComponent(tenantId)}`, body),

  listApiKeys: (tenantId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/api-keys`, { params: tenantId ? { tenant_id: tenantId } : {} }),

  rotateApiKey: (tenantId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(`${BASE}/api-keys/${encodeURIComponent(tenantId)}/rotate`),

  analyticsSummary: () => api.get<{ ok: boolean; summary: Record<string, number> }>(`${BASE}/analytics/summary`),

  listNetworks: (params?: { network_type?: string; active_only?: boolean }) =>
    api.get<{ items: unknown[] }>(`${BASE}/networks`, { params }),

  listCorridors: (networkId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/corridors`, { params: networkId ? { network_id: networkId } : {} }),

  listOperators: (params?: { tenant_id?: string; network_id?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/operators`, { params }),

  listInvoices: (params?: { contract_id?: string; status?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/billing/invoices`, { params }),

  listSlaPolicies: (networkId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/sla-policies`, { params: networkId ? { network_id: networkId } : {} }),

  listContractEvents: (contractId: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/contracts/${encodeURIComponent(contractId)}/events`),

  listWebhookDeliveries: (params?: { status?: string }) =>
    api.get<{ items: unknown[] }>(`${BASE}/webhook-deliveries`, { params }),

  premiumSummary: () =>
    api.get<{ ok: boolean; summary: Record<string, number> }>(`${BASE}/analytics/premium-summary`),

  listOnboarding: (status?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/onboarding`, { params: status ? { status } : {} }),

  listCapacity: (networkId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/capacity`, { params: networkId ? { network_id: networkId } : {} }),

  listSettlements: (status?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/settlements`, { params: status ? { status } : {} }),

  listSlaBreaches: (status?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/sla-breaches`, { params: status ? { status } : {} }),

  listDisputes: (status?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/disputes`, { params: status ? { status } : {} }),

  listRenewalOffers: (status?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/renewal-offers`, { params: status ? { status } : {} }),

  networkHealth: () => api.get<{ items: unknown[] }>(`${BASE}/analytics/network-health`),

  activateContract: (contractId: string) =>
    api.post(`${BASE}/contracts/${encodeURIComponent(contractId)}/activate`),

  listAccessPasses: (contractId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/access-passes`, {
      params: contractId ? { contract_id: contractId } : {},
    }),

  listDeposits: (contractId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/deposits`, {
      params: contractId ? { contract_id: contractId } : {},
    }),

  listSlotBlocks: (lockerId?: string) =>
    api.get<{ items: unknown[] }>(`${BASE}/slot-blocks`, {
      params: lockerId ? { locker_id: lockerId } : {},
    }),

  listPricingRules: () => api.get<{ items: unknown[] }>(`${BASE}/pricing-rules`),

  priceQuote: (body: Record<string, unknown>) =>
    api.post<{ ok: boolean; quoted: boolean; amount_cents?: number }>(`${BASE}/pricing/quote`, body),

  listDunning: () => api.get<{ items: unknown[] }>(`${BASE}/dunning`),

  scanDunning: () => api.post<{ ok: boolean; cases_created: number }>(`${BASE}/dunning/scan`),

  listTransfers: () => api.get<{ items: unknown[] }>(`${BASE}/transfers`),
}
