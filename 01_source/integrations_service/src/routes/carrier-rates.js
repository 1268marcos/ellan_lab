import { Router } from 'express'
import { query } from '../lib/db.js'
import { newId } from '../lib/id.js'

const router = Router()

router.get('/', async (req, res, next) => {
  try {
    const { carrier_code, active } = req.query
    const clauses = []
    const params = []
    if (carrier_code) {
      params.push(String(carrier_code).toUpperCase())
      clauses.push(`carrier_code = $${params.length}`)
    }
    if (active === 'true') clauses.push('is_active = true')
    const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : ''
    const { rows } = await query(
      `SELECT * FROM logistics_carrier_rates ${where} ORDER BY carrier_code, valid_from DESC`,
      params,
    )
    res.json({ items: rows, total: rows.length })
  } catch (err) {
    next(err)
  }
})

router.post('/', async (req, res, next) => {
  try {
    const { rows } = await query(
      `INSERT INTO logistics_carrier_rates (
        id, carrier_code, origin_zone, destination_zone, weight_tier_g, size_tier,
        amount_cents, currency, valid_from, valid_until, is_active, created_at
      ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,NOW())
      RETURNING *`,
      [
        newId(),
        String(req.body.carrier_code).toUpperCase(),
        req.body.origin_zone,
        req.body.destination_zone,
        Number(req.body.weight_tier_g || 1000),
        req.body.size_tier || null,
        Number(req.body.amount_cents),
        req.body.currency || 'BRL',
        req.body.valid_from || new Date().toISOString().slice(0, 10),
        req.body.valid_until || null,
        req.body.is_active !== false,
      ],
    )
    res.status(201).json(rows[0])
  } catch (err) {
    next(err)
  }
})

router.put('/:rateId', async (req, res, next) => {
  try {
    const fields = []
    const params = [req.params.rateId]
    for (const key of ['amount_cents', 'valid_until', 'is_active', 'size_tier']) {
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
      `UPDATE logistics_carrier_rates SET ${fields.join(', ')} WHERE id = $1 RETURNING *`,
      params,
    )
    if (!rows[0]) {
      res.status(404).json({ detail: 'rate_not_found' })
      return
    }
    res.json(rows[0])
  } catch (err) {
    next(err)
  }
})

router.delete('/:rateId', async (req, res, next) => {
  try {
    const { rowCount } = await query('DELETE FROM logistics_carrier_rates WHERE id = $1', [req.params.rateId])
    if (!rowCount) {
      res.status(404).json({ detail: 'rate_not_found' })
      return
    }
    res.status(204).end()
  } catch (err) {
    next(err)
  }
})

export default router
