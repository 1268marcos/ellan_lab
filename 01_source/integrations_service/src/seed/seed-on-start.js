import { pool } from '../lib/db.js'
import { newId } from '../lib/id.js'
import {
  CAPABILITY_CATALOG,
  ECOSYSTEM_PLAYERS,
  MARKETPLACE_CONNECTIONS,
  defaultCapabilitiesForPlayer,
} from './ecosystem-seed.js'
import { hashSecret } from '../lib/crypto.js'

export async function execSeed() {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    for (const cap of CAPABILITY_CATALOG) {
      await client.query(
        `INSERT INTO partner_integration_capability_catalog (code, name, category, default_protocol, sort_order)
         VALUES ($1, $2, $3, $4, $5) ON CONFLICT (code) DO NOTHING`,
        [cap.code, cap.name, cap.category, cap.default_protocol, cap.sort_order],
      )
    }
    for (const p of ECOSYSTEM_PLAYERS) {
      const { rows: inserted } = await client.query(
        `INSERT INTO partner_ecosystem_players (
          id, code, name, player_role, parent_group, country, regions_json,
          supports_lockers, supports_marketplace, integration_mode,
          marketplace_channel_id, marketplace_channel_code, global_tier, sort_order, active,
          integration_status, data_source, created_at, updated_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,NOW(),NOW())
        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW()
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
      const playerId = inserted[0]?.id || (
        await client.query('SELECT id FROM partner_ecosystem_players WHERE code = $1', [p.code])
      ).rows[0]?.id
      if (!playerId) continue
      for (const c of defaultCapabilitiesForPlayer(p)) {
        await client.query(
          `INSERT INTO partner_player_capabilities (
            id, ecosystem_player_id, capability_code, protocol, direction, enabled, created_at
          ) VALUES ($1,$2,$3,$4,$5,true,NOW())
          ON CONFLICT (ecosystem_player_id, capability_code) DO NOTHING`,
          [newId(), playerId, c.capability_code, c.protocol, c.direction],
        )
      }
    }
    for (const m of MARKETPLACE_CONNECTIONS) {
      await client.query(
        `INSERT INTO marketplace_channel_partners (
          id, code, name, partner_role, country, parent_group, integration_type,
          supports_marketplace, supports_lockers, active, sort_order, integration_mode, regions_json, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,'REST',$7,$8,$9,$10,$11,$12,NOW())
        ON CONFLICT (code) DO NOTHING`,
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
    }
    await client.query('COMMIT')
    console.log('[integrations-service] seed applied')
  } catch (err) {
    await client.query('ROLLBACK')
    console.warn('[integrations-service] seed skipped:', err.message)
  } finally {
    client.release()
  }
}
