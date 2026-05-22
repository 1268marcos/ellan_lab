import { api } from './client'

const BASE = '/api/marketplace-admin/v1/marketplace-admin'

export type MarketplaceSeller = {
  id: string
  legal_name: string
  trade_name?: string
  tax_id: string
  email: string
  phone?: string
  website?: string
  status: string
  commission_pct: string | number
  monthly_fee_cents: number
  seller_rating?: string | number
  total_sales_cents: number
  total_orders: number
}

export type SellerProduct = {
  id: string
  seller_id: string
  locker_id: string
  product_id: string
  seller_sku?: string
  price_cents: number
  quantity: number
  status: string
}

export type MarketplaceCommission = {
  id: string
  seller_id: string
  order_id: string
  commission_amount_cents: number
  net_to_seller_cents: number
  status: string
}

export type SellerReview = {
  id: string
  seller_id: string
  order_id: string
  rating: number
  comment?: string
}

export const marketplaceAdminApi = {
  seed: () => api.post(`${BASE}/seed`),

  listSellers: (params?: { active_only?: boolean }) =>
    api.get<{ sellers: MarketplaceSeller[]; total: number }>(`${BASE}/sellers`, { params }),
  createSeller: (body: Record<string, unknown>) => api.post<MarketplaceSeller>(`${BASE}/sellers`, body),
  updateSeller: (id: string, body: Record<string, unknown>) =>
    api.patch<MarketplaceSeller>(`${BASE}/sellers/${encodeURIComponent(id)}`, body),
  deleteSeller: (id: string) => api.delete(`${BASE}/sellers/${encodeURIComponent(id)}`),

  listProducts: (params?: { seller_id?: string; locker_id?: string }) =>
    api.get<{ products: SellerProduct[]; total: number }>(`${BASE}/seller-products`, { params }),
  createProduct: (body: Record<string, unknown>) => api.post<SellerProduct>(`${BASE}/seller-products`, body),
  deleteProduct: (id: string) => api.delete(`${BASE}/seller-products/${encodeURIComponent(id)}`),

  listCommissions: (params?: { seller_id?: string; status?: string }) =>
    api.get<{ commissions: MarketplaceCommission[]; total: number }>(`${BASE}/commissions`, { params }),
  createCommission: (body: Record<string, unknown>) => api.post(`${BASE}/commissions`, body),
  updateCommission: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/commissions/${encodeURIComponent(id)}`, body),

  listReviews: (params?: { seller_id?: string }) =>
    api.get<{ reviews: SellerReview[]; total: number }>(`${BASE}/seller-reviews`, { params }),
  createReview: (body: Record<string, unknown>) => api.post(`${BASE}/seller-reviews`, body),

  configureWebhook: (sellerId: string, body: { url: string; secret?: string; events?: string[] }) =>
    api.put(`${BASE}/sellers/${encodeURIComponent(sellerId)}/webhook`, body),
  rotateApiKey: (sellerId: string) =>
    api.post<{ api_key: string; key_prefix: string }>(
      `${BASE}/sellers/${encodeURIComponent(sellerId)}/api-keys/rotate`,
    ),

  getDashboard: () => api.get<Record<string, number | null>>(`${BASE}/dashboard`),
  listCategories: () => api.get<{ categories: unknown[]; total: number }>(`${BASE}/categories`),
  createCategory: (body: Record<string, unknown>) => api.post(`${BASE}/categories`, body),
  listContacts: (seller_id?: string) =>
    api.get<{ contacts: unknown[]; total: number }>(`${BASE}/seller-contacts`, { params: { seller_id } }),
  createContact: (body: Record<string, unknown>) => api.post(`${BASE}/seller-contacts`, body),
  listPayoutAccounts: (seller_id?: string) =>
    api.get<{ accounts: unknown[]; total: number }>(`${BASE}/seller-payout-accounts`, { params: { seller_id } }),
  createPayoutAccount: (body: Record<string, unknown>) => api.post(`${BASE}/seller-payout-accounts`, body),
  listSettlementBatches: (seller_id?: string) =>
    api.get<{ batches: unknown[]; total: number }>(`${BASE}/seller-settlement-batches`, { params: { seller_id } }),
  createSettlementBatch: (body: Record<string, unknown>) => api.post(`${BASE}/seller-settlement-batches`, body),
  updateSettlementBatch: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-settlement-batches/${encodeURIComponent(id)}`, body),
  listKyc: (seller_id?: string) =>
    api.get<{ documents: unknown[]; total: number }>(`${BASE}/seller-kyc-documents`, { params: { seller_id } }),
  createKyc: (body: Record<string, unknown>) => api.post(`${BASE}/seller-kyc-documents`, body),
  updateKyc: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-kyc-documents/${encodeURIComponent(id)}`, body),
  listDisputes: (seller_id?: string) =>
    api.get<{ disputes: unknown[]; total: number }>(`${BASE}/seller-commission-disputes`, { params: { seller_id } }),
  createDispute: (body: Record<string, unknown>) => api.post(`${BASE}/seller-commission-disputes`, body),
  resolveDispute: (id: string, body: Record<string, unknown>) =>
    api.patch(`${BASE}/seller-commission-disputes/${encodeURIComponent(id)}`, body),

  listChannelPartners: (params?: { lockers_only?: boolean; active_only?: boolean }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/channel-partners`, { params }),
  seedChannelPlayers: () => api.post(`${BASE}/channel-partners/seed-players`),
  getChannelPartner: (id: string) => api.get(`${BASE}/channel-partners/${encodeURIComponent(id)}`),
  integrationMatrix: () => api.get(`${BASE}/integration-hub/summary`),

  listIntegrationReadiness: (params?: { band?: string; limit?: number }) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-readiness`, { params }),
  recomputeIntegrationReadiness: () => api.post(`${BASE}/integration-readiness/recompute`),
  integrationHubSummary: () => api.get<Record<string, unknown>>(`${BASE}/integration-hub/summary`),
  listReadinessAlerts: (open_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/readiness-alerts`, { params: { open_only } }),
  acknowledgeReadinessAlert: (alertId: string) =>
    api.post(`${BASE}/readiness-alerts/${encodeURIComponent(alertId)}/acknowledge`),
  listCapabilityWebhooks: (channel_partner_id?: string) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/capability-webhooks`, {
      params: channel_partner_id ? { channel_partner_id } : undefined,
    }),
  upsertCapabilityWebhook: (body: Record<string, unknown>) => api.put(`${BASE}/capability-webhooks`, body),
  testCapabilityWebhook: (webhookId: string) =>
    api.post(`${BASE}/capability-webhooks/${encodeURIComponent(webhookId)}/test`),
  simulateScoreDrop: (partner_code: string, new_score: number) =>
    api.post(`${BASE}/integration-readiness/simulate-drop`, { partner_code, new_score }),
  listIntegrationIncidents: (open_only = true) =>
    api.get<{ items: unknown[]; total: number }>(`${BASE}/integration-incidents`, { params: { open_only } }),
}
