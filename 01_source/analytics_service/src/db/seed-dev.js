/**
 * Seed local para analytics/financial (API keys, permissões, refresh MVs).
 *
 *   DATABASE_URL=postgresql://admin:admin123@127.0.0.1:5435/locker_central npm run db:seed-dev
 */
import { createHash, randomUUID } from 'crypto'
import pg from 'pg'

const DATABASE_URL =
  process.env.DATABASE_URL || 'postgresql://admin:admin123@127.0.0.1:5435/locker_central'
const PEPPER = process.env.PARTNER_ADMIN_API_KEY_PEPPER || 'dev-partner-admin-pepper'
const ADMIN_USER_ID = process.env.ANALYTICS_SEED_USER_ID || '0e92a909-9ac5-4694-b5f6-a3447e6a1544'
const GROUP_ID = 'grp-analytics-ops'

const DEV_API_KEYS = [
  { raw: 'dev-analytics-admin-key', label: 'Analytics admin (default)' },
  { raw: 'ellan_dev_analytics_2026', label: 'Analytics dev v1/v0 financial' },
]

function hashApiKey(raw) {
  return createHash('sha256').update(`${PEPPER}:${raw}`, 'utf8').digest('hex')
}

async function main() {
  const pool = new pg.Pool({ connectionString: DATABASE_URL })
  const client = await pool.connect()

  try {
    await client.query('BEGIN')

    const user = await client.query(`SELECT id, email FROM users WHERE id = $1`, [ADMIN_USER_ID])
    if (!user.rows.length) {
      throw new Error(`User ${ADMIN_USER_ID} not found — rode POST /api/v1/seed no partner-admin`)
    }

    await client.query(
      `INSERT INTO security_permission_groups (id, name, description, is_system, created_at, updated_at)
       VALUES ($1, 'Analytics OPS', 'Leitura e refresh analytics/financial', true, NOW(), NOW())
       ON CONFLICT (id) DO NOTHING`,
      [GROUP_ID],
    )

    for (const obj of ['analytics.read', 'analytics.refresh', 'analytics.*']) {
      await client.query(
        `INSERT INTO security_permissions (id, group_id, object_key, created_at)
         VALUES ($1, $2, $3, NOW())
         ON CONFLICT (group_id, object_key) DO NOTHING`,
        [randomUUID(), GROUP_ID, obj],
      )
    }

    await client.query(
      `INSERT INTO security_permission_memberships (id, user_id, group_id, is_group_manager, created_at)
       VALUES ($1, $2, $3, true, NOW())
       ON CONFLICT (user_id, group_id) DO NOTHING`,
      [randomUUID(), ADMIN_USER_ID, GROUP_ID],
    )

    const roleExists = await client.query(
      `SELECT 1 FROM user_roles WHERE user_id = $1::varchar AND role = 'admin_operacao' AND revoked_at IS NULL LIMIT 1`,
      [ADMIN_USER_ID],
    )
    if (!roleExists.rows.length) {
      await client.query(
        `INSERT INTO user_roles (id, user_id, role, scope_type, scope_id, is_active, granted_at)
         VALUES ($1::varchar, $2::varchar, 'admin_operacao', 'GLOBAL', 'ellanlab', true, NOW())`,
        [randomUUID(), ADMIN_USER_ID],
      )
    }

    for (const { raw, label } of DEV_API_KEYS) {
      const prefix = raw.slice(0, 16)
      const keyHash = hashApiKey(raw)
      const exists = await client.query(
        `SELECT id FROM security_api_keys WHERE key_hash = $1 AND key_prefix = $2 AND revoked_at IS NULL`,
        [keyHash, prefix],
      )
      if (!exists.rows.length) {
        await client.query(
          `INSERT INTO security_api_keys (
             id, user_id, key_prefix, key_hash, label, scopes_json, created_by, created_at
           ) VALUES ($1, $2, $3, $4, $5, $6, $2, NOW())`,
          [randomUUID(), ADMIN_USER_ID, prefix, keyHash, label, JSON.stringify(['*'])],
        )
      }
    }

    await client.query('COMMIT')

    console.log('✅ Analytics seed OK')
    console.log(`   user: ${user.rows[0].email}`)
    console.log('   X-API-Key (testes diretos / Postman):')
    DEV_API_KEYS.forEach(({ raw }) => console.log(`     - ${raw}`))
    console.log('   Login v1 (Bearer JWT — use no /v1/financial):')
    console.log('     ellan-ceo-dev-hub-000000000 / pk_local_dev_key_ceo_01')
    console.log('     11111111-1111-1111-1111-111111111111 / pk_test_frontend_v1_20260505')
    console.log('   (partner seed: partner_service SEED_DEV_PARTNERS=true)')

    for (const fn of [
      'fn_refresh_mv_locker_monthly_profitability',
      'fn_refresh_mv_locker_monthly_pnl',
      'fn_refresh_mv_realtime_kpis',
      'fn_refresh_financial_dashboard',
    ]) {
      try {
        await client.query(`SELECT public.${fn}($1)`, ['seed-dev'])
        console.log(`   refreshed: ${fn}`)
      } catch (err) {
        console.warn(`   skip ${fn}:`, err.message)
      }
    }
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {})
    console.error('❌ seed failed:', err.message)
    process.exitCode = 1
  } finally {
    client.release()
    await pool.end()
  }
}

main()
