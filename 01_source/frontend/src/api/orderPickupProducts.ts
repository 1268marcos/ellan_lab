import { api } from './client'

const BASE = '/api/op'

export type ProductCategory = {
  id: string
  name: string
  description?: string | null
  parent_category?: string | null
  is_active?: boolean
  metadata_json?: Record<string, unknown>
  requires_age_verification?: boolean
  requires_id?: boolean
  requires_signature?: boolean
  max_weight_g?: number | null
  max_width_mm?: number | null
  max_height_mm?: number | null
  max_depth_mm?: number | null
  created_at: string
  updated_at: string
}

export type ProductListItem = {
  id: string
  name: string
  amount_cents: number
  category_id?: string | null
  status: string
  is_active: boolean
  updated_at: string
}

export type ProductDetail = ProductListItem & {
  description?: string | null
  currency: string
  width_mm?: number | null
  height_mm?: number | null
  depth_mm?: number | null
  weight_g?: number | null
  requires_age_verification?: boolean
  requires_id_check?: boolean
  requires_signature?: boolean
  is_hazardous?: boolean
  is_fragile?: boolean
  is_virtual?: boolean
  metadata_json?: Record<string, unknown>
  created_at: string
}

export const orderPickupProductsApi = {
  listCategories: () => api.get<{ ok: boolean; items: ProductCategory[] }>(`${BASE}/product-categories`),
  getCategory: (id: string) => api.get<ProductCategory>(`${BASE}/product-categories/${encodeURIComponent(id)}`),
  createCategory: (body: Record<string, unknown>) => api.post<ProductCategory>(`${BASE}/product-categories`, body),
  updateCategory: (id: string, body: Record<string, unknown>) =>
    api.patch<ProductCategory>(`${BASE}/product-categories/${encodeURIComponent(id)}`, body),
  deleteCategory: (id: string) => api.delete(`${BASE}/product-categories/${encodeURIComponent(id)}`),

  listProducts: (params?: {
    status?: string
    category?: string
    updated_from?: string
    updated_to?: string
    limit?: number
    offset?: number
  }) => api.get<{ ok: boolean; total: number; items: ProductListItem[] }>(`${BASE}/products`, { params }),
  getProduct: (id: string) => api.get<ProductDetail>(`${BASE}/products/${encodeURIComponent(id)}`),
  createProduct: (body: Record<string, unknown>) => api.post<ProductDetail>(`${BASE}/products`, body),
  updateProduct: (id: string, body: Record<string, unknown>) =>
    api.patch<ProductDetail>(`${BASE}/products/${encodeURIComponent(id)}`, body),
  deactivateProduct: (id: string) => api.delete(`${BASE}/products/${encodeURIComponent(id)}`),
  patchPrice: (id: string, amount_cents: number) =>
    api.patch(`${BASE}/products/${encodeURIComponent(id)}/price`, { amount_cents }),
  patchStatus: (id: string, to_status: string, reason?: string) =>
    api.patch(`${BASE}/products/${encodeURIComponent(id)}/status`, { to_status, reason }),

  seedCatalogProfessional: () =>
    api.post<{
      ok: boolean
      taxonomy_rows: number
      channel_rows: number
      attribute_definitions: number
      locker_categories_created?: number
    }>(`${BASE}/catalog-professional/seed`),

  getPlayersReference: () =>
    api.get<{
      ok: boolean
      taxonomy_schemes: string[]
      channel_codes: string[]
      players: { code: string; name: string; player_type: string; country: string; supports_lockers: boolean }[]
    }>(`${BASE}/catalog-professional/players-reference`),

  getEcosystemOverview: () =>
    api.get<{
      ok: boolean
      source: string
      players_total: number
      players_locker_ready: number
      taxonomy_mappings: number
      channel_listings: number
      eligibility_rules: number
      integration_targets: number
      ecommerce_partner_links: number
      logistics_partner_links: number
    }>(`${BASE}/catalog-professional/ecosystem-overview`),

  listGlobalPlayers: (params?: {
    player_type?: string
    country?: string
    capability?: string
    supports_lockers?: boolean
    q?: string
    limit?: number
  }) => api.get<{ ok: boolean; total: number; items: GlobalPlayer[] }>(`${BASE}/catalog-professional/global-players`, { params }),

  seedGlobalPlayers: () =>
    api.post<{
      ok: boolean
      players: number
      operators_created: number
      ecommerce_links: number
      logistics_links: number
    }>(`${BASE}/catalog-professional/global-players/seed`),

  syncGlobalPlayersPartners: () =>
    api.post<Record<string, number>>(`${BASE}/catalog-professional/global-players/sync-partners`),

  listCategoryEligibility: (params?: { category_id?: string; player_code?: string }) =>
    api.get<{ ok: boolean; total: number; items: CategoryEligibility[] }>(
      `${BASE}/catalog-professional/category-eligibility`,
      { params },
    ),

  createCategoryEligibility: (body: {
    category_id: string
    player_code: string
    eligibility?: string
    notes?: string
  }) => api.post<CategoryEligibility>(`${BASE}/catalog-professional/category-eligibility`, body),

  listCategoryTaxonomy: (params?: { category_id?: string; taxonomy_scheme?: string }) =>
    api.get<{ ok: boolean; items: CategoryTaxonomy[] }>(`${BASE}/catalog-professional/category-taxonomy`, { params }),
  createCategoryTaxonomy: (body: Record<string, unknown>) =>
    api.post<CategoryTaxonomy>(`${BASE}/catalog-professional/category-taxonomy`, body),
  deleteCategoryTaxonomy: (id: string) =>
    api.delete(`${BASE}/catalog-professional/category-taxonomy/${encodeURIComponent(id)}`),

  listChannelListings: (params?: { product_id?: string; channel_code?: string; listing_status?: string }) =>
    api.get<{ ok: boolean; total: number; items: ProductChannelListing[] }>(
      `${BASE}/catalog-professional/channel-listings`,
      { params },
    ),
  createChannelListing: (body: Record<string, unknown>) =>
    api.post<ProductChannelListing>(`${BASE}/catalog-professional/channel-listings`, body),
  updateChannelListing: (id: string, body: Record<string, unknown>) =>
    api.patch<ProductChannelListing>(`${BASE}/catalog-professional/channel-listings/${encodeURIComponent(id)}`, body),
  deleteChannelListing: (id: string) =>
    api.delete(`${BASE}/catalog-professional/channel-listings/${encodeURIComponent(id)}`),

  listAttributeDefinitions: (params?: { category_id?: string }) =>
    api.get<{ ok: boolean; items: ProductAttributeDefinition[] }>(
      `${BASE}/catalog-professional/attribute-definitions`,
      { params },
    ),
  createAttributeDefinition: (body: Record<string, unknown>) =>
    api.post<ProductAttributeDefinition>(`${BASE}/catalog-professional/attribute-definitions`, body),
  listProductAttributes: (productId: string) =>
    api.get<{ ok: boolean; items: ProductAttributeValue[] }>(
      `${BASE}/catalog-professional/products/${encodeURIComponent(productId)}/attributes`,
    ),
  upsertProductAttribute: (productId: string, body: Record<string, unknown>) =>
    api.put<ProductAttributeValue>(
      `${BASE}/catalog-professional/products/${encodeURIComponent(productId)}/attributes`,
      body,
    ),

  listBundles: (params?: { limit?: number; offset?: number }) =>
    api.get<{ ok: boolean; total: number; items: ProductBundle[] }>(`${BASE}/products/bundles`, { params }),
  listProductInventory: (params?: Record<string, unknown>) =>
    api.get<{ ok: boolean; total: number; items: ProductInventoryRow[] }>(`${BASE}/ops/products/inventory`, {
      params,
    }),
  reservationHealth: (params?: Record<string, unknown>) =>
    api.get<{ ok: boolean; total: number; by_status: { status: string; count: number }[]; items: unknown[] }>(
      `${BASE}/ops/inventory/reservation-health`,
      { params },
    ),
  pricingFiscalOverview: (params?: Record<string, unknown>) =>
    api.get<Record<string, unknown>>(`${BASE}/ops/products/pricing-fiscal/overview`, { params }),
}

export type GlobalPlayer = {
  code: string
  name: string
  player_type: string
  country: string
  supports_lockers: boolean
  supports_pudo?: boolean
  supports_food_delivery?: boolean
  supports_marketplace?: boolean
  operator_id?: string | null
  capabilities?: string[]
  regions?: string[]
}

export type CategoryEligibility = {
  id: string
  category_id: string
  category_name?: string | null
  player_code: string
  player_name?: string | null
  eligibility: string
  notes?: string | null
  created_at: string
}

export type CategoryTaxonomy = {
  id: string
  category_id: string
  taxonomy_scheme: string
  external_code: string
  external_name?: string | null
  country_code?: string | null
  is_primary: boolean
}

export type ProductChannelListing = {
  id: string
  product_id: string
  channel_code: string
  external_sku?: string | null
  listing_status: string
  price_cents?: number | null
  sync_mode: string
}

export type ProductAttributeDefinition = {
  id: string
  category_id?: string | null
  attr_key: string
  attr_label: string
  data_type: string
  is_required: boolean
}

export type ProductAttributeValue = {
  id: string
  product_id: string
  definition_id: string
  attr_key?: string
  attr_label?: string
  value_text?: string | null
  value_number?: number | null
  value_bool?: boolean | null
}

export type ProductBundle = {
  id: string
  name: string
  code: string
  amount_cents: number
  is_active: boolean
}

export type ProductInventoryRow = {
  id: string
  product_id: string
  locker_id: string
  quantity_available: number
  reorder_point: number
}
