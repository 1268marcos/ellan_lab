import { Router } from 'express'
import { query } from '../lib/db.js'
import { newId, isEcosystemPartnerId, isUuid } from '../lib/id.js'
import { mapPlayer } from '../lib/row-mapper.js'
import { getRateLimit, setRateLimit } from '../lib/rate-limit-store.js'
import { config } from '../config.js'
import { runHealthCheck } from '../lib/health-check.js'

const router = Router()

function isEcosystemBody(body) {
  return Boolean(body?.code || body?.player_role || body?.parent_group)
}

router.get('/', async (req, res, next) => {
  try {
    const { parent_group, country, active, q } = req.query
    const clauses = []
    const params = []
    if (parent_group) {
      params.push(parent_group)
      clauses.push(`parent_group = $${params.length}`)
    }
    if (country) {
      params.push(String(country).toUpperCase())
      clauses.push(`country = $${params.length}`)
    }
    if (active === 'true') clauses.push('active = true')
    if (q) {
      params.push(`%${q}%`)
      clauses.push(`(name ILIKE $${params.length} OR code ILIKE $${params.length})`)
    }
    const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : ''
    const { rows } = await query(
      `SELECT * FROM partner_ecosystem_players ${where} ORDER BY sort_order, code`,
      params,
    )
    res.json({ items: rows.map(mapPlayer), total: rows.length })
  } catch (err) {
    next(err)
  }
})

router.post('/', async (req, res, next) => {
  try {
    if (!isEcosystemBody(req.body)) {
      res.status(400).json({ detail: 'ecosystem_player_body_required' })
      return
    }
    const id = req.body.id || `eco-${String(req.body.code).toLowerCase().replace(/[^a-z0-9]+/g, '-')}`
    const regions = JSON.stringify(req.body.regions || [req.body.country || 'BR'])
    const { rows } = await query(
      `INSERT INTO partner_ecosystem_players (
        id, code, name, player_role, parent_group, country, regions_json,
        supports_lockers, supports_marketplace, integration_mode,
        marketplace_channel_id, marketplace_channel_code, global_tier, sort_order, active,
        integration_status, website_url, api_docs_url, data_source, created_at, updated_at
      ) VALUES (
        $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,NOW(),NOW()
      ) RETURNING *`,
      [
        id,
        String(req.body.code).toUpperCase(),
        req.body.name,
        req.body.player_role,
        req.body.parent_group,
        String(req.body.country || 'BR').toUpperCase(),
        regions,
        Boolean(req.body.supports_lockers),
        Boolean(req.body.supports_marketplace),
        req.body.integration_mode || 'DIRECT_API',
        req.body.marketplace_channel_id || null,
        req.body.marketplace_channel_code || null,
        req.body.global_tier || 'REGIONAL',
        Number(req.body.sort_order || 100),
        req.body.active !== false,
        req.body.integration_status || 'PLANNED',
        req.body.website_url || null,
        req.body.api_docs_url || null,
        req.body.data_source || 'MANUAL',
      ],
    )
    res.status(201).json(mapPlayer(rows[0]))
  } catch (err) {
    if (err.code === '23505') {
      res.status(409).json({ detail: 'code_already_exists' })
      return
    }
    next(err)
  }
})

router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params
    if (!isEcosystemPartnerId(id) && isUuid(id)) {
      res.status(404).json({ detail: 'use_partner_service_for_tenant_partners' })
      return
    }
    const { rows } = await query('SELECT * FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [id])
    if (!rows[0]) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    res.json(mapPlayer(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.put('/:id', async (req, res, next) => {
  try {
    const { rows: existing } = await query('SELECT id FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [
      req.params.id,
    ])
    if (!existing[0]) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    const pid = existing[0].id
    const fields = []
    const params = [pid]
    const allowed = [
      'name',
      'player_role',
      'parent_group',
      'country',
      'supports_lockers',
      'supports_marketplace',
      'integration_mode',
      'global_tier',
      'sort_order',
      'active',
      'integration_status',
      'website_url',
      'api_docs_url',
      'notes',
    ]
    for (const key of allowed) {
      if (req.body[key] !== undefined) {
        params.push(req.body[key])
        fields.push(`${key} = $${params.length}`)
      }
    }
    if (req.body.regions) {
      params.push(JSON.stringify(req.body.regions))
      fields.push(`regions_json = $${params.length}`)
    }
    if (!fields.length) {
      res.status(400).json({ detail: 'no_fields' })
      return
    }
    fields.push('updated_at = NOW()')
    const { rows } = await query(
      `UPDATE partner_ecosystem_players SET ${fields.join(', ')} WHERE id = $1 RETURNING *`,
      params,
    )
    res.json(mapPlayer(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.delete('/:id', async (req, res, next) => {
  try {
    const { rowCount } = await query('DELETE FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [
      req.params.id,
    ])
    if (!rowCount) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    res.status(204).end()
  } catch (err) {
    next(err)
  }
})

router.get('/:id/rate-limit', (req, res) => {
  const limit = getRateLimit(req.params.id, config.defaultRateLimitPerMinute)
  res.json({ partner_id: req.params.id, limit_per_minute: limit })
})

router.put('/:id/rate-limit', (req, res) => {
  setRateLimit(req.params.id, req.body.limit_per_minute)
  res.json({ partner_id: req.params.id, limit_per_minute: getRateLimit(req.params.id, config.defaultRateLimitPerMinute) })
})

router.get('/:id/health', async (req, res, next) => {
  try {
    const { rows: p } = await query('SELECT id FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [
      req.params.id,
    ])
    if (!p[0]) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    const { rows } = await query(
      `SELECT * FROM partner_integration_health
       WHERE partner_id = $1 AND partner_type = 'ECOSYSTEM'
       ORDER BY checked_at DESC LIMIT 20`,
      [p[0].id],
    )
    res.json({ items: rows.map((r) => ({
      id: r.id,
      partner_id: r.partner_id,
      status: r.status,
      latency_ms: r.latency_ms,
      http_status: r.http_status,
      checked_at: r.checked_at,
      endpoint_url: r.endpoint_url,
      error_message: r.error_message,
    })), total: rows.length })
  } catch (err) {
    next(err)
  }
})

router.post('/:id/health/check', async (req, res, next) => {
  try {
    const result = await runHealthCheck(req.params.id, req.body?.endpoint_url)
    if (!result) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    res.json(result)
  } catch (err) {
    next(err)
  }
})

export default router
