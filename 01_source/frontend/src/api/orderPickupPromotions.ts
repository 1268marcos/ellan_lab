import { api } from './client'

const BASE = '/api/op'

export type Promotion = {
  id: string
  code: string | null
  name: string
  type: string
  discount_pct: number | null
  discount_cents: number | null
  min_order_cents: number
  max_discount_cents: number | null
  max_uses: number | null
  uses_count: number
  per_user_limit: number | null
  conditions_json: Record<string, unknown>
  is_active: boolean
  valid_from: string
  valid_until: string | null
  created_by: string | null
  created_at: string
}

export type PromotionExclusion = {
  promotion_id: string
  product_id: string
}

export const orderPickupPromotionsApi = {
  list: (params?: {
    code?: string
    is_active?: boolean
    from_date?: string
    to_date?: string
    limit?: number
    offset?: number
  }) =>
    api.get<{ ok: boolean; total: number; limit: number; offset: number; items: Promotion[] }>(
      `${BASE}/promotions`,
      { params },
    ),

  get: (id: string) => api.get<Promotion>(`${BASE}/promotions/${encodeURIComponent(id)}`),

  create: (body: Record<string, unknown>) => api.post<Promotion>(`${BASE}/promotions`, body),

  patchStatus: (id: string, body: { is_active: boolean; reason?: string }) =>
    api.patch<{ ok: boolean; promotion_id: string; is_active: boolean }>(
      `${BASE}/promotions/${encodeURIComponent(id)}/status`,
      body,
    ),

  seed: () =>
    api.post<{ ok: boolean; inserted: number; skipped: number; total_catalog: number }>(
      `${BASE}/promotions/seed`,
    ),

  listExclusions: (promotionId: string, limit = 200) =>
    api.get<{ ok: boolean; total: number; items: PromotionExclusion[] }>(
      `${BASE}/promotions/${encodeURIComponent(promotionId)}/product-exclusions`,
      { params: { limit } },
    ),

  addExclusion: (promotionId: string, product_id: string) =>
    api.post<PromotionExclusion>(
      `${BASE}/promotions/${encodeURIComponent(promotionId)}/product-exclusions`,
      { product_id },
    ),

  removeExclusion: (promotionId: string, productId: string) =>
    api.delete<{ ok: boolean }>(
      `${BASE}/promotions/${encodeURIComponent(promotionId)}/product-exclusions/${encodeURIComponent(productId)}`,
    ),

  overview: () => api.get<PromotionOverview>(`${BASE}/promotions/overview`),

  seedWorld: () =>
    api.post<{
      ok: boolean
      campaigns_inserted: number
      promotions_inserted: number
      scopes_inserted: number
    }>(`${BASE}/promotions/seed-world`),

  listCampaigns: (params?: { limit?: number; offset?: number }) =>
    api.get<{ ok: boolean; total: number; items: PromotionCampaign[] }>(`${BASE}/promotion-campaigns`, {
      params,
    }),

  createCampaign: (body: Record<string, unknown>) =>
    api.post<PromotionCampaign>(`${BASE}/promotion-campaigns`, body),

  listScopes: (promotionId: string) =>
    api.get<{ ok: boolean; total: number; items: PromotionScope[] }>(
      `${BASE}/promotions/${encodeURIComponent(promotionId)}/scopes`,
    ),

  addScope: (promotionId: string, body: { scope_type: string; scope_value: string; mode?: string }) =>
    api.post<PromotionScope>(`${BASE}/promotions/${encodeURIComponent(promotionId)}/scopes`, body),

  removeScope: (promotionId: string, scopeId: string) =>
    api.delete(`${BASE}/promotions/${encodeURIComponent(promotionId)}/scopes/${encodeURIComponent(scopeId)}`),

  listRedemptions: (params?: { promotion_id?: string; limit?: number }) =>
    api.get<{ ok: boolean; total: number; items: PromotionRedemption[] }>(`${BASE}/promotion-redemptions`, {
      params,
    }),

  lockerPlayersCatalog: (params?: { segment?: string }) =>
    api.get<LockerPlayerCatalog>(`${BASE}/promotions/locker-players-catalog`, { params }),

  simulate: (body: Record<string, unknown>) =>
    api.post<PromotionSimulateOut>(`${BASE}/promotions/simulate`, body),

  match: (body: Record<string, unknown>) =>
    api.post<{ ok: boolean; total: number; items: PromotionMatchItem[] }>(`${BASE}/promotions/match`, body),

  conflicts: () => api.get<{ ok: boolean; total: number; items: PromotionConflict[] }>(`${BASE}/promotions/conflicts`),

  playerMatrix: () => api.get<{ ok: boolean; items: { player_code: string; active_promotions: number }[] }>(
    `${BASE}/promotions/player-matrix`,
  ),

  clone: (promotionId: string, body: { new_code: string; new_name?: string }) =>
    api.post<{ ok: boolean; promotion_id: string; promotion_code: string }>(
      `${BASE}/promotions/${encodeURIComponent(promotionId)}/clone`,
      body,
    ),
}

export type PromotionSimulateOut = {
  ok: boolean
  valid: boolean
  reason?: string | null
  discount_cents: number
  net_amount_cents?: number
  promotion_code?: string
}

export type PromotionMatchItem = {
  promotion_id: string
  promotion_code: string
  promotion_name: string
  eligible: boolean
  reason?: string | null
  estimated_discount_cents: number
}

export type PromotionConflict = {
  scope_type: string
  scope_value: string
  promotions_count: number
  promotions: { id: string; code: string; name: string }[]
  hint: string
}

export type PromotionOverview = {
  ok: boolean
  promotions_total: number
  promotions_active: number
  campaigns_total: number
  campaigns_active: number
  redemptions_24h: number
  redemptions_total: number
  top_promotion_codes: { code: string; redemptions: number }[]
  top_player_scopes: { player_code: string; scopes: number }[]
  locker_players_catalog_size?: number
  featured_locker_players?: string[]
  player_segments?: { segment: string; count: number }[]
  player_promotion_matrix?: { player_code: string; active_promotions: number }[]
}

export type LockerPlayerRef = {
  code: string
  display_name: string
  segment: string
  countries: string[]
  aliases: string[]
  notes?: string | null
}

export type LockerPlayerCatalog = {
  ok: boolean
  total: number
  items: LockerPlayerRef[]
  featured_codes: string[]
}

export type PromotionCampaign = {
  id: string
  code: string
  name: string
  channel_family: string
  primary_country: string | null
  promotions_count: number
  is_active: boolean
}

export type PromotionScope = {
  id: string
  promotion_id: string
  scope_type: string
  scope_value: string
  mode: string
}

export type PromotionRedemption = {
  id: string
  order_id: string
  player_code: string | null
  country_code: string | null
  discount_cents: number
  redeemed_at: string
}
