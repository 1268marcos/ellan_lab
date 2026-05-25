import { Router } from 'express'
import { query } from '../lib/db.js'
import { newId } from '../lib/id.js'
import { mapCapability } from '../lib/row-mapper.js'

const router = Router({ mergeParams: true })

async function resolvePlayerId(id) {
  const { rows } = await query('SELECT id FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [id])
  return rows[0]?.id || null
}

router.get('/', async (req, res, next) => {
  try {
    const playerId = await resolvePlayerId(req.params.id)
    if (!playerId) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    const { rows } = await query(
      `SELECT * FROM partner_player_capabilities WHERE ecosystem_player_id = $1 ORDER BY capability_code`,
      [playerId],
    )
    res.json({ items: rows.map(mapCapability), total: rows.length })
  } catch (err) {
    next(err)
  }
})

router.post('/', async (req, res, next) => {
  try {
    const playerId = await resolvePlayerId(req.params.id)
    if (!playerId) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    const { rows } = await query(
      `INSERT INTO partner_player_capabilities (
        id, ecosystem_player_id, capability_code, protocol, direction, enabled, sandbox_ready, production_ready, notes, created_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,NOW())
      RETURNING *`,
      [
        newId(),
        playerId,
        req.body.capability_code,
        req.body.protocol || 'REST',
        req.body.direction || 'OUTBOUND',
        req.body.enabled !== false,
        Boolean(req.body.sandbox_ready),
        Boolean(req.body.production_ready),
        req.body.notes || null,
      ],
    )
    res.status(201).json(mapCapability(rows[0]))
  } catch (err) {
    if (err.code === '23505') {
      res.status(409).json({ detail: 'capability_exists' })
      return
    }
    next(err)
  }
})

router.put('/:capId', async (req, res, next) => {
  try {
    const playerId = await resolvePlayerId(req.params.id)
    if (!playerId) {
      res.status(404).json({ detail: 'partner_not_found' })
      return
    }
    const fields = []
    const params = [req.params.capId, playerId]
    for (const key of ['protocol', 'direction', 'enabled', 'sandbox_ready', 'production_ready', 'notes']) {
      if (req.body[key] !== undefined) {
        params.push(req.body[key])
        fields.push(`${key} = $${params.length}`)
      }
    }
    if (!fields.length) {
      res.status(400).json({ detail: 'no_fields' })
      return
    }
    const { rows } = await query(
      `UPDATE partner_player_capabilities SET ${fields.join(', ')}
       WHERE id = $1 AND ecosystem_player_id = $2 RETURNING *`,
      params,
    )
    if (!rows[0]) {
      res.status(404).json({ detail: 'capability_not_found' })
      return
    }
    res.json(mapCapability(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.delete('/:capId', async (req, res, next) => {
  try {
    const playerId = await resolvePlayerId(req.params.id)
    const { rowCount } = await query(
      'DELETE FROM partner_player_capabilities WHERE id = $1 AND ecosystem_player_id = $2',
      [req.params.capId, playerId],
    )
    if (!rowCount) {
      res.status(404).json({ detail: 'capability_not_found' })
      return
    }
    res.status(204).end()
  } catch (err) {
    next(err)
  }
})

export default router
