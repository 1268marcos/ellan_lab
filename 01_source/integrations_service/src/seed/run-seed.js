import { pool } from '../lib/db.js'
import { newId } from '../lib/id.js'
import {
  CAPABILITY_CATALOG,
  ECOSYSTEM_PLAYERS,
  MARKETPLACE_CONNECTIONS,
  defaultCapabilitiesForPlayer,
} from './ecosystem-seed.js'
import { hashSecret } from '../lib/crypto.js'

async function upsertCatalog(client) {
  for (const cap of CAPABILITY_CATALOG) {
    await client.query(
      `INSERT INTO partner_integration_capability_catalog (code, name, category, default_protocol, sort_order)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category`,
      [cap.code, cap.name, cap.category, cap.default_protocol, cap.sort_order],
    )
  }
}

async function upsertPlayers(client) {
  let players = 0
  for (const p of ECOSYSTEM_PLAYERS) {
    const { rows: upserted } = await client.query(
      `INSERT INTO partner_ecosystem_players (
        id, code, name, player_role, parent_group, country, regions_json,
        supports_lockers, supports_marketplace, integration_mode,
        marketplace_channel_id, marketplace_channel_code, global_tier, sort_order, active,
        integration_status, data_source, created_at, updated_at
      ) VALUES (
        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,NOW(),NOW()
      )
      ON CONFLICT (code) DO UPDATE SET
        name = EXCLUDED.name,
        player_role = EXCLUDED.player_role,
        parent_group = EXCLUDED.parent_group,
        supports_lockers = EXCLUDED.supports_lockers,
        supports_marketplace = EXCLUDED.supports_marketplace,
        updated_at = NOW()
      RETURNING id`,
      [
        p.id,
        p.code,
        p.name,
        p.player_role,
        p.parent_group,
        p.country,
        p.regions_json,
        p.supports_lockers,
        p.supports_marketplace,
        p.integration_mode,
        p.marketplace_channel_id,
        p.marketplace_channel_code,
        p.global_tier,
        p.sort_order,
        p.active,
        p.integration_status,
        p.data_source,
      ],
    )
    const playerId =
      upserted[0]?.id ||
      (await client.query('SELECT id FROM partner_ecosystem_players WHERE code = $1', [p.code])).rows[0]?.id
    if (!playerId) continue
    players += 1
    const caps = defaultCapabilitiesForPlayer(p)
    for (const c of caps) {
      await client.query(
        `INSERT INTO partner_player_capabilities (
          id, ecosystem_player_id, capability_code, protocol, direction, enabled, sandbox_ready, production_ready, created_at
        ) VALUES ($1,$2,$3,$4,$5,true,false,false,NOW())
        ON CONFLICT (ecosystem_player_id, capability_code) DO UPDATE SET protocol = EXCLUDED.protocol`,
        [newId(), playerId, c.capability_code, c.protocol, c.direction],
      )
    }
  }
  return players
}

async function upsertMarketplaces(client) {
  let rows = 0
  for (const m of MARKETPLACE_CONNECTIONS) {
    await client.query(
      `INSERT INTO marketplace_channel_partners (
        id, code, name, partner_role, country, parent_group, integration_type,
        supports_marketplace, supports_lockers, active, sort_order, integration_mode, regions_json, created_at
      ) VALUES ($1,$2,$3,$4,$5,$6,'REST',$7,$8,$9,$10,$11,$12,NOW())
      ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, active = EXCLUDED.active`,
      [
        m.id,
        m.code,
        m.name,
        m.partner_role,
        m.country,
        m.parent_group,
        m.supports_marketplace,
        m.supports_lockers,
        m.active,
        m.sort_order,
        m.integration_mode,
        m.regions_json,
      ],
    )
    rows += 1
  }
  return rows
}

async function seedCarrierRates(client) {
  const carriers = ECOSYSTEM_PLAYERS.filter((p) => p.parent_group === 'CARRIER_LAST_MILE')
  let n = 0
  for (const c of carriers.slice(0, 8)) {
    const exists = await client.query(
      `SELECT 1 FROM logistics_carrier_rates WHERE carrier_code = $1 AND origin_zone = 'BR-SP' LIMIT 1`,
      [c.code.slice(0, 20)],
    )
    if (!exists.rows[0]) {
      await client.query(
        `INSERT INTO logistics_carrier_rates (
          id, carrier_code, origin_zone, destination_zone, weight_tier_g, amount_cents, currency, valid_from, is_active, created_at
        ) VALUES ($1,$2,'BR-SP','BR-RJ',1000,1290,'BRL',CURRENT_DATE,true,NOW())`,
        [newId(), c.code.slice(0, 20)],
      )
    }
    n += 1
  }
  return n
}

async function seedWebhooks(client) {
  const { rows } = await client.query(
    `SELECT p.id, p.code, c.capability_code
     FROM partner_ecosystem_players p
     JOIN partner_player_capabilities c ON c.ecosystem_player_id = p.id
     WHERE c.protocol = 'WEBHOOK' OR c.capability_code IN ('TRACKING_PUSH','ORDERS_WEBHOOK')
     LIMIT 40`,
  )
  let n = 0
  for (const r of rows) {
    const secret = `whsec_${r.code.toLowerCase()}_${r.capability_code.toLowerCase()}`
    const playerId = r.id
    await client.query(
      `INSERT INTO partner_capability_webhooks (
        id, ecosystem_player_id, player_code, capability_code, url, secret_hash, secret_key,
        event_types_json, source, active, created_at, updated_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'SEED',true,NOW(),NOW())
      ON CONFLICT (ecosystem_player_id, capability_code) DO NOTHING`,
      [
        newId(),
        playerId,
        r.code,
        r.capability_code,
        `https://hooks.ellan.lab/ingress/${r.code}/${r.capability_code}`,
        hashSecret(secret),
        secret,
        JSON.stringify(['webhook.test', 'capability.health']),
      ],
    )
    n += 1
  }
  return n
}

async function main() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const catalog = CAPABILITY_CATALOG.length
    await upsertCatalog(client)
    const players = await upsertPlayers(client)
    const marketplaces = await upsertMarketplaces(client)
    const rates = await seedCarrierRates(client)
    const webhooks = await seedWebhooks(client)
    await client.query('COMMIT')
    console.log(JSON.stringify({ catalog, players, marketplaces, rates, webhooks }))
  } catch (err) {
    await client.query('ROLLBACK')
    console.error(err)
    process.exit(1)
  } finally {
    client.release()
    await pool.end()
  }
}

main()
