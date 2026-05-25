import { Router } from 'express'
import { query } from '../lib/db.js'

const router = Router()

function mapLockerRow(row) {
  const healthScore = row.health_score != null ? Number(row.health_score) : null
  let opsStatus = 'unknown'
  if (row.active === false) opsStatus = 'offline'
  else if (row.health_status === 'CRITICO') opsStatus = 'critical'
  else if (row.health_status === 'ATENCAO') opsStatus = 'warning'
  else if (row.health_status === 'SAUDAVEL') opsStatus = 'healthy'
  else if (row.active === true) opsStatus = 'healthy'

  return {
    id: row.id,
    external_id: row.external_id,
    display_name: row.display_name,
    region: row.region,
    city: row.city,
    address_line: row.address_line,
    latitude: row.latitude,
    longitude: row.longitude,
    active: row.active,
    slots_count: row.slots_count,
    slots_available: row.slots_available,
    occupancy_pct: row.occupancy_pct != null ? Number(row.occupancy_pct) : null,
    occupancy_level: row.occupancy_level,
    has_urgent_pickup: row.has_urgent_pickup,
    health_score: healthScore,
    health_status: row.health_status,
    last_telemetry_at: row.last_telemetry_at,
    ops_status: opsStatus,
  }
}

router.get('/lockers', async (req, res, next) => {
  try {
    const {
      region,
      city,
      active,
      status,
      q,
      limit = '200',
      offset = '0',
    } = req.query

    const clauses = ['l.deleted_at IS NULL']
    const params = []
    let n = 1

    if (region) {
      clauses.push(`l.region = $${n++}`)
      params.push(region)
    }
    if (city) {
      clauses.push(`l.city ILIKE $${n++}`)
      params.push(`%${city}%`)
    }
    if (active === 'true' || active === 'false') {
      clauses.push(`l.active = $${n++}`)
      params.push(active === 'true')
    }
    if (q) {
      clauses.push(
        `(l.id ILIKE $${n} OR l.external_id ILIKE $${n} OR l.display_name ILIKE $${n} OR l.address_line ILIKE $${n})`,
      )
      params.push(`%${q}%`)
      n += 1
    }

    const lim = Math.min(500, Math.max(1, Number(limit) || 200))
    const off = Math.max(0, Number(offset) || 0)

    const sql = `
      SELECT l.id, l.external_id, l.display_name, l.region, l.city, l.address_line,
             l.latitude, l.longitude, l.active, l.slots_count, l.slots_available,
             occ.occupancy_pct, occ.occupancy_level, occ.has_urgent_pickup,
             h.health_score, h.status AS health_status, h.last_telemetry_at
      FROM lockers l
      LEFT JOIN vw_ceo_occupancy occ ON occ.locker_id = l.id
      LEFT JOIN LATERAL (
        SELECT * FROM fn_locker_health(l.id)
      ) h ON TRUE
      WHERE ${clauses.join(' AND ')}
      ORDER BY l.display_name NULLS LAST, l.id
      LIMIT $${n++} OFFSET $${n++}
    `
    params.push(lim, off)

    const { rows } = await query(sql, params)
    let items = rows.map(mapLockerRow)

    if (status) {
      const want = String(status).toLowerCase()
      items = items.filter((it) => it.ops_status === want)
    }

    res.json({ items, total: items.length, limit: lim, offset: off })
  } catch (err) {
    next(err)
  }
})

router.get('/lockers/occupancy', async (_req, res, next) => {
  try {
    const { rows } = await query(`
      SELECT locker_id, external_id, region, city, address_line,
             total_slots, occupied_slots, maintenance_slots,
             occupancy_pct, occupancy_level, has_urgent_pickup
      FROM vw_ceo_occupancy
      ORDER BY occupancy_pct DESC NULLS LAST
    `)
    res.json({ items: rows })
  } catch (err) {
    next(err)
  }
})

router.get('/lockers/:id', async (req, res, next) => {
  try {
    const { rows } = await query(
      `
      SELECT l.*, occ.occupancy_pct, occ.occupancy_level, occ.has_urgent_pickup,
             occ.total_slots, occ.occupied_slots, occ.maintenance_slots,
             h.health_score, h.status AS health_status, h.last_telemetry_at
      FROM lockers l
      LEFT JOIN vw_ceo_occupancy occ ON occ.locker_id = l.id
      LEFT JOIN LATERAL (SELECT * FROM fn_locker_health(l.id)) h ON TRUE
      WHERE l.id = $1 AND l.deleted_at IS NULL
      LIMIT 1
      `,
      [req.params.id],
    )
    if (!rows.length) {
      res.status(404).json({ detail: 'locker_not_found' })
      return
    }
    res.json(mapLockerRow(rows[0]))
  } catch (err) {
    next(err)
  }
})

router.get('/lockers/:id/telemetry', async (req, res, next) => {
  try {
    const hours = Math.min(168, Math.max(1, Number(req.query.hours) || 24))
    const { rows } = await query(
      `
      SELECT id, locker_id, event_type, slot_label,
             temperature_celsius, humidity_pct, battery_pct,
             voltage_mv, signal_rssi, firmware_version, occurred_at
      FROM locker_telemetry
      WHERE locker_id = $1
        AND occurred_at >= NOW() - ($2::text || ' hours')::interval
      ORDER BY occurred_at ASC
      LIMIT 5000
      `,
      [req.params.id, String(hours)],
    )
    res.json({ items: rows, locker_id: req.params.id, hours })
  } catch (err) {
    next(err)
  }
})

router.get('/lockers/:id/maintenance', async (req, res, next) => {
  try {
    const { rows } = await query(
      `
      SELECT id, locker_id, title, description, status, priority,
             assigned_to, created_by, created_at, updated_at, resolved_at
      FROM locker_maintenance_tickets
      WHERE locker_id = $1
      ORDER BY
        CASE status
          WHEN 'OPEN' THEN 1
          WHEN 'IN_PROGRESS' THEN 2
          WHEN 'WAITING_PARTS' THEN 3
          WHEN 'RESOLVED' THEN 4
          ELSE 5
        END,
        updated_at DESC
      `,
      [req.params.id],
    )
    res.json({ items: rows })
  } catch (err) {
    next(err)
  }
})

router.post('/lockers/:id/maintenance', async (req, res, next) => {
  try {
    const { title, description, priority = 'MEDIUM', assigned_to, created_by } = req.body ?? {}
    if (!title || typeof title !== 'string') {
      res.status(400).json({ detail: 'title_required' })
      return
    }
    const pri = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].includes(priority) ? priority : 'MEDIUM'
    const { rows } = await query(
      `
      INSERT INTO locker_maintenance_tickets
        (locker_id, title, description, priority, assigned_to, created_by, status)
      VALUES ($1, $2, $3, $4, $5, $6, 'OPEN')
      RETURNING *
      `,
      [req.params.id, title.trim(), description ?? null, pri, assigned_to ?? null, created_by ?? null],
    )
    res.status(201).json(rows[0])
  } catch (err) {
    next(err)
  }
})

router.get('/lockers/:id/pickups', async (req, res, next) => {
  try {
    const { rows } = await query(
      `
      SELECT o.id AS order_id, o.status, o.pickup_deadline_at, o.amount_cents,
             o.created_at, a.state AS allocation_state, ls.slot_label
      FROM allocations a
      JOIN orders o ON o.id = a.order_id
      LEFT JOIN locker_slots ls
        ON ls.locker_id = a.locker_id AND ls.slot_label = a.slot::text
      WHERE a.locker_id = $1
        AND o.picked_up_at IS NULL
        AND o.deleted_at IS NULL
        AND o.status IN ('PAID_PENDING_PICKUP', 'PAYMENT_PENDING')
      ORDER BY o.pickup_deadline_at ASC NULLS LAST
      LIMIT 100
      `,
      [req.params.id],
    )
    res.json({ items: rows })
  } catch (err) {
    next(err)
  }
})

export default router
