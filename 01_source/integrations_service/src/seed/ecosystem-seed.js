export const CAPABILITY_CATALOG = [
  { code: 'LOCKER_INVENTORY', name: 'Inventário lockers/PUDO', category: 'LOCKER', default_protocol: 'REST', sort_order: 10 },
  { code: 'LABEL_API', name: 'Emissão de etiqueta', category: 'LOGISTICS', default_protocol: 'REST', sort_order: 20 },
  { code: 'TRACKING_PUSH', name: 'Rastreio push/webhook', category: 'LOGISTICS', default_protocol: 'WEBHOOK', sort_order: 30 },
  { code: 'ORDERS_WEBHOOK', name: 'Pedidos webhook', category: 'COMMERCE', default_protocol: 'WEBHOOK', sort_order: 40 },
  { code: 'ORDERS_POLL', name: 'Pedidos polling', category: 'COMMERCE', default_protocol: 'REST', sort_order: 41 },
  { code: 'SELLER_OAUTH', name: 'OAuth vendedor', category: 'COMMERCE', default_protocol: 'OAUTH2', sort_order: 50 },
  { code: 'SETTLEMENT_FEED', name: 'Liquidação/repasse', category: 'PAYMENTS', default_protocol: 'REST', sort_order: 60 },
  { code: 'PICKUP_POINT_LIST', name: 'Lista pontos coleta', category: 'PUDO', default_protocol: 'REST', sort_order: 95 },
]

const hardware = [
  ['eco-swipbox', 'SWIPBOX', 'SwipBox', 'LOCKER_OPERATOR', 'LOCKER_NETWORK', 'DK', true, false, 15],
  ['eco-cleveron', 'CLEVERON', 'Cleveron', 'LOCKER_OPERATOR', 'LOCKER_NETWORK', 'EE', true, false, 20],
  ['eco-pickup-pl', 'PICKUP_PL', 'Pickup.pl', 'LOCKER_OPERATOR', 'LOCKER_NETWORK', 'PL', true, false, 25],
  ['eco-bloqit', 'BLOQIT', 'Bloq.it', 'LOCKER_OPERATOR', 'LOCKER_NETWORK', 'IT', true, false, 30],
  ['eco-quadient', 'QUADIENT', 'Quadient', 'HARDWARE_VENDOR', 'LOCKER_NETWORK', 'UK', true, false, 35],
  ['eco-packeta', 'PACKETA', 'Packeta', 'PUDO_OPERATOR', 'LOCKER_NETWORK', 'CZ', true, false, 40],
  ['eco-vinted-go', 'VINTED_GO', 'Vinted Go', 'LOCKER_OPERATOR', 'LOCKER_NETWORK', 'FR', true, false, 45],
]

const carriers = [
  ['eco-inpost', 'INPOST', 'InPost', 'LOCKER_OPERATOR', 'CARRIER_LAST_MILE', 'PL', true, false, 5],
  ['eco-dpd', 'DPD', 'DPD', 'CARRIER', 'CARRIER_LAST_MILE', 'DE', true, false, 10],
  ['eco-dhl', 'DHL', 'DHL', 'CARRIER', 'CARRIER_LAST_MILE', 'DE', true, false, 12],
  ['eco-usps', 'USPS', 'USPS', 'CARRIER', 'CARRIER_LAST_MILE', 'US', false, false, 50],
  ['eco-royalmail', 'ROYALMAIL', 'Royal Mail', 'CARRIER', 'CARRIER_LAST_MILE', 'UK', true, false, 55],
  ['eco-laposte', 'LAPOSTE', 'La Poste', 'CARRIER', 'CARRIER_LAST_MILE', 'FR', true, false, 60],
  ['eco-colissimo', 'COLISSIMO', 'Colissimo', 'CARRIER', 'CARRIER_LAST_MILE', 'FR', true, false, 65],
  ['eco-hermes-de', 'HERMES_DE', 'Hermes DE', 'CARRIER', 'CARRIER_LAST_MILE', 'DE', true, false, 70],
  ['eco-yodel', 'YODEL', 'Yodel', 'CARRIER', 'CARRIER_LAST_MILE', 'UK', true, false, 75],
  ['eco-swisspost', 'SWISSPOST', 'Swiss Post', 'CARRIER', 'CARRIER_LAST_MILE', 'CH', true, false, 80],
  ['eco-auspost', 'AU_POST', 'Australia Post', 'CARRIER', 'CARRIER_LAST_MILE', 'AU', true, false, 85],
  ['eco-bluedart', 'BLUEDART', 'Blue Dart', 'CARRIER', 'CARRIER_LAST_MILE', 'IN', false, false, 90],
  ['eco-bring', 'BRING', 'Bring', 'CARRIER', 'CARRIER_LAST_MILE', 'NO', true, false, 95],
  ['eco-postnord', 'POSTNORD', 'PostNord', 'CARRIER', 'CARRIER_LAST_MILE', 'SE', true, false, 100],
]

const marketplaces = [
  ['mcp-magalu', 'MAGALU', 'Magalu', 'MARKETPLACE', 'MARKETPLACE', 'BR', false, true, 10],
  ['mcp-meli', 'MERCADOLIVRE', 'Mercado Livre', 'MARKETPLACE', 'MARKETPLACE', 'BR', false, true, 15],
  ['mcp-worten', 'WORTEN', 'Worten', 'MARKETPLACE', 'MARKETPLACE', 'PT', true, true, 20],
  ['mcp-eci', 'EL_CORTE_INGLES', 'El Corte Inglés', 'MARKETPLACE', 'MARKETPLACE', 'ES', true, true, 25],
  ['mcp-amazon-br', 'AMAZON_BR', 'Amazon BR', 'MARKETPLACE', 'MARKETPLACE', 'BR', false, true, 30],
  ['mcp-walmart', 'WALMART', 'Walmart', 'MARKETPLACE', 'MARKETPLACE', 'US', false, true, 35],
  ['mcp-rakuten', 'RAKUTEN', 'Rakuten', 'MARKETPLACE', 'MARKETPLACE', 'JP', false, true, 40],
  ['mcp-cdiscount', 'CDISCOUNT', 'Cdiscount', 'MARKETPLACE', 'MARKETPLACE', 'FR', false, true, 45],
  ['mcp-otto', 'OTTO', 'OTTO', 'MARKETPLACE', 'MARKETPLACE', 'DE', false, true, 50],
  ['mcp-flipkart', 'FLIPKART', 'Flipkart', 'MARKETPLACE', 'MARKETPLACE', 'IN', false, true, 55],
  ['mcp-shopee', 'SHOPEE', 'Shopee', 'MARKETPLACE', 'MARKETPLACE', 'SG', false, true, 60],
  ['mcp-shein', 'SHEIN', 'Shein', 'MARKETPLACE', 'MARKETPLACE', 'CN', false, true, 65],
  ['mcp-temu', 'TEMU', 'Temu', 'MARKETPLACE', 'MARKETPLACE', 'CN', false, true, 70],
  ['mcp-tiktok', 'TIKTOK_SHOP', 'TikTok Shop', 'MARKETPLACE', 'MARKETPLACE', 'US', false, true, 75],
]

const aggregators = [
  ['eco-easypost', 'EASYPOST', 'EasyPost', 'AGGREGATOR', 'AGGREGATOR', 'US', false, false, 110],
  ['eco-shippo', 'SHIPPO', 'Shippo', 'AGGREGATOR', 'AGGREGATOR', 'US', false, false, 115],
  ['eco-intelipost', 'INTELIPOST', 'Intelipost', 'AGGREGATOR', 'AGGREGATOR', 'BR', false, false, 120],
  ['eco-melhor-envio', 'MELHOR_ENVIO', 'Melhor Envio', 'AGGREGATOR', 'AGGREGATOR', 'BR', false, false, 125],
]

export const ECOSYSTEM_PLAYERS = [...hardware, ...carriers, ...marketplaces, ...aggregators].map(
  ([id, code, name, player_role, parent_group, country, supports_lockers, supports_marketplace, sort_order]) => ({
    id,
    code,
    name,
    player_role,
    parent_group,
    country,
    regions_json: JSON.stringify([country]),
    supports_lockers,
    supports_marketplace,
    integration_mode: parent_group === 'MARKETPLACE' ? 'MARKETPLACE_API' : 'DIRECT_API',
    marketplace_channel_id: id.startsWith('mcp-') ? id : null,
    marketplace_channel_code: id.startsWith('mcp-') ? code : null,
    global_tier: ['INPOST', 'DPD', 'DHL', 'MAGALU', 'MERCADOLIVRE', 'AMAZON_BR'].includes(code) ? 'PRIORITY' : 'REGIONAL',
    sort_order,
    active: true,
    integration_status: 'PLANNED',
    data_source: 'INTEGRATIONS_SEED',
  }),
)

export const MARKETPLACE_CONNECTIONS = marketplaces.map(
  ([id, code, name, partner_role, parent_group, country], idx) => ({
    id,
    code,
    name,
    partner_role,
    country,
    parent_group,
    integration_type: 'REST',
    supports_marketplace: true,
    supports_lockers: ['WORTEN', 'EL_CORTE_INGLES'].includes(code),
    active: true,
    sort_order: (idx + 1) * 10,
    integration_mode: 'DIRECT_API',
    regions_json: JSON.stringify([country]),
  }),
)

export function defaultCapabilitiesForPlayer(player) {
  const caps = []
  if (player.supports_lockers) {
    caps.push({ capability_code: 'LOCKER_INVENTORY', protocol: 'REST', direction: 'OUTBOUND' })
    caps.push({ capability_code: 'PICKUP_POINT_LIST', protocol: 'REST', direction: 'OUTBOUND' })
  }
  if (player.supports_marketplace) {
    caps.push({ capability_code: 'ORDERS_WEBHOOK', protocol: 'WEBHOOK', direction: 'INBOUND' })
    caps.push({ capability_code: 'SELLER_OAUTH', protocol: 'OAUTH2', direction: 'INBOUND' })
  }
  if (player.parent_group === 'CARRIER_LAST_MILE' || player.player_role === 'CARRIER') {
    caps.push({ capability_code: 'LABEL_API', protocol: 'REST', direction: 'OUTBOUND' })
    caps.push({ capability_code: 'TRACKING_PUSH', protocol: 'WEBHOOK', direction: 'INBOUND' })
  }
  if (player.parent_group === 'AGGREGATOR') {
    caps.push({ capability_code: 'LABEL_API', protocol: 'REST', direction: 'OUTBOUND' })
    caps.push({ capability_code: 'SETTLEMENT_FEED', protocol: 'REST', direction: 'OUTBOUND' })
  }
  if (!caps.length) {
    caps.push({ capability_code: 'ORDERS_POLL', protocol: 'REST', direction: 'OUTBOUND' })
  }
  return caps
}
