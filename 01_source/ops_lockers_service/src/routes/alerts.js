import { Router } from 'express'
import { query } from '../lib/db.js'

const router = Router()

router.get('/alerts', async (req, res, next) => {
  try {
    const limit = Math.min(500, Math.max(1, Number(req.query.limit) || 100))
    const alertType = req.query.alert_type
    const severity = req.query.severity

    const clauses = ['1=1']
    const params = []
    let n = 1

    if (alertType) {
      clauses.push(`alert_type = $${n++}`)
      params.push(alertType)
    }
    if (severity) {
      clauses.push(`severity::text ILIKE $${n++}`)
      params.push(severity)
    }

    params.push(limit)

    const { rows } = await query(
      `
      SELECT alert_type, alert_id, severity, breach_type,
             detected_at, expected_at, resolved_at,
             locker_display_name, reference_id, priority
      FROM vw_noc_alerts
      WHERE ${clauses.join(' AND ')}
      ORDER BY priority ASC, detected_at DESC
      LIMIT $${n}
      `,
      params,
    )
    res.json({ items: rows })
  } catch (err) {
    next(err)
  }
})

export default router
