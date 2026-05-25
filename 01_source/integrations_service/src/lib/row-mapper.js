export function mapPlayer(row) {
  if (!row) return null
  let regions = []
  try {
    regions = JSON.parse(row.regions_json || '[]')
  } catch {
    regions = []
  }
  return {
    id: row.id,
    code: row.code,
    name: row.name,
    player_role: row.player_role,
    parent_group: row.parent_group,
    country: row.country,
    regions,
    supports_lockers: row.supports_lockers,
    supports_marketplace: row.supports_marketplace,
    integration_mode: row.integration_mode,
    marketplace_channel_id: row.marketplace_channel_id,
    marketplace_channel_code: row.marketplace_channel_code,
    locker_operator_ref: row.locker_operator_ref,
    ecommerce_partner_code: row.ecommerce_partner_code,
    api_docs_url: row.api_docs_url,
    website_url: row.website_url,
    global_tier: row.global_tier,
    integration_status: row.integration_status,
    estimated_locker_count: row.estimated_locker_count,
    data_source: row.data_source,
    sort_order: row.sort_order,
    active: row.active,
    created_at: row.created_at,
    updated_at: row.updated_at,
  }
}

export function mapCapability(row) {
  if (!row) return null
  return {
    id: row.id,
    ecosystem_player_id: row.ecosystem_player_id,
    capability_code: row.capability_code,
    protocol: row.protocol,
    direction: row.direction,
    enabled: row.enabled,
    sandbox_ready: row.sandbox_ready,
    production_ready: row.production_ready,
    notes: row.notes,
    created_at: row.created_at,
  }
}

export function mapMarketplace(row) {
  if (!row) return null
  let regions = []
  try {
    regions = JSON.parse(row.regions_json || '[]')
  } catch {
    regions = []
  }
  return {
    id: row.id,
    code: row.code,
    name: row.name,
    partner_role: row.partner_role,
    country: row.country,
    website: row.website,
    integration_type: row.integration_type,
    supports_marketplace: row.supports_marketplace,
    supports_lockers: row.supports_lockers,
    active: row.active,
    sort_order: row.sort_order,
    parent_group: row.parent_group,
    integration_mode: row.integration_mode,
    regions,
    api_docs_url: row.api_docs_url,
    created_at: row.created_at,
  }
}

export function mapHealth(row) {
  if (!row) return null
  return {
    id: row.id,
    partner_id: row.partner_id,
    partner_type: row.partner_type,
    endpoint_url: row.endpoint_url,
    checked_at: row.checked_at,
    status: row.status,
    latency_ms: row.latency_ms,
    http_status: row.http_status,
    error_message: row.error_message,
  }
}
