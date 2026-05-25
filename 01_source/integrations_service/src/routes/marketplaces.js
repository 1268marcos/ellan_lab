import { Router } from 'express'
import { query } from '../lib/db.js'
import { newId } from '../lib/id.js'
import { mapMarketplace } from '../lib/row-mapper.js'

const router = Router()

router.get('/connections', async (req, res, next) => {
  try {
    const { country, active } = req.query
    const clauses = []
    const params = []
    if (country) {
      params.push(String(country).toUpperCase())
      clauses.push(`country = $${params.length}`)
    }
    if (active === 'true') clauses.push('active = true')
    const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : ''
    const { rows } = await query(
      `SELECT * FROM marketplace_channel_partners ${where} ORDER BY sort_order, code`,
      params,
    )
    res.json({ items: rows.map(mapMarketplace), total: rows.length })
  } catch (err) {
    next(err)
  }
})

router.post('/connections', async (req, res, next) => {
  try {
    const id = req.body.id || `mcp-${String(req.body.code).toLowerCase()}`
    const { rows } = await query(
      `INSERT INTO marketplace_channel_partners (
        id, code, name, partner_role, country, website, integration_type,
        supports_marketplace, supports_lockers, active, sort_order, parent_group, integration_mode, regions_json, api_docs_url, created_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,NOW())
      RETURNING *`,
      [
        id,
        String(req.body.code).toUpperCase(),
        req.body.name,
        req.body.partner_role || 'MARKETPLACE',
        String(req.body.country || 'BR').toUpperCase(),
        req.body.website || null,
        req.body.integration_type || 'REST',
        req.body.supports_marketplace !== false,
        Boolean(req.body.supports_lockers),
        req.body.active !== false,
        Number(req.body.sort_order || 100),
        req.body.parent_group || 'MARKETPLACE',
        req.body.integration_mode || 'DIRECT_API',
        JSON.stringify(req.body.regions || [req.body.country || 'BR']),
        req.body.api_docs_url || null,
      ],
    )
    res.status(201).json(mapMarketplace(rows[0]))
  } catch (err) {
    if (err.code === '23505') {
      res.status(409).json({ detail: 'code_already_exists' })
      return
    }
    next(err)
  }
})

router.get('/connections/:connId', async (req, res, next) => {
  try {
    const { rows } = await query('SELECT * FROM marketplace_channel_partners WHERE id = $1 OR code = $1', [
      req.params.connId,
    ])
    if (!rows[0]) {
      res.status(404).json({ detail: 'connection_not_found' })
      return
    }
    res.json(mapMarketplace(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.put('/connections/:connId', async (req, res, next) => {
  try {
    const { rows: existing } = await query('SELECT id FROM marketplace_channel_partners WHERE id = $1 OR code = $1', [
      req.params.connId,
    ])
    if (!existing[0]) {
      res.status(404).json({ detail: 'connection_not_found' })
      return
    }
    const cid = existing[0].id
    const fields = []
    const params = [cid]
    for (const key of [
      'name',
      'partner_role',
      'country',
      'website',
      'integration_type',
      'supports_marketplace',
      'supports_lockers',
      'active',
      'sort_order',
      'integration_mode',
      'api_docs_url',
      'notes',
    ]) {
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
    const { rows } = await query(
      `UPDATE marketplace_channel_partners SET ${fields.join(', ')} WHERE id = $1 RETURNING *`,
      params,
    )
    res.json(mapMarketplace(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.delete('/connections/:connId', async (req, res, next) => {
  try {
    const { rowCount } = await query('DELETE FROM marketplace_channel_partners WHERE id = $1 OR code = $1', [
      req.params.connId,
    ])
    if (!rowCount) {
      res.status(404).json({ detail: 'connection_not_found' })
      return
    }
    res.status(204).end()
  } catch (err) {
    next(err)
  }
})

export default router
