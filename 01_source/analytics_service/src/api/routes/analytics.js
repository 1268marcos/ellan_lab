import { Router } from 'express'
import { pool } from '../../lib/db.js'
import { requireAdmin, requireAuthenticated } from '../middleware/auth.js'

const router = Router()

router.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'analytics-service' })
})

router.get('/locker-profitability', requireAuthenticated, async (req, res) => {
  try {
    const { locker_id: lockerId, month } = req.query
    const conditions = []
    const params = []

    if (lockerId) {
      params.push(String(lockerId))
      conditions.push(`locker_id = $${params.length}`)
    }
    if (month) {
      params.push(String(month))
      conditions.push(`month = $${params.length}::date`)
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
    const { rows } = await pool.query(
      `SELECT locker_id, month, sales_revenue_cents, rental_revenue_cents,
              marketplace_commission_cents, total_revenue_cents, total_opex_cents,
              depreciation_cents, total_costs_cents, net_profit_cents, net_margin_pct,
              total_pickups, active_rentals, avg_revenue_per_pickup_cents, computed_at
       FROM mv_locker_monthly_profitability
       ${where}
       ORDER BY month DESC, locker_id
       LIMIT 500`,
      params,
    )

    res.json({ items: rows, total: rows.length })
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/financial-dashboard', requireAuthenticated, async (_req, res) => {
  try {
    const { rows } = await pool.query(`SELECT * FROM v_financial_dashboard LIMIT 1`)
    res.json(rows[0] ?? {})
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/realtime-kpis', requireAuthenticated, async (_req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT snapshot_time, orders_last_hour, revenue_last_hour, orders_last_24h,
              unique_customers_24h, revenue_last_24h, avg_pickup_minutes, offline_lockers,
              active_sellers, pending_payment, expired_pickup, critical_alerts, high_alerts
       FROM mv_realtime_kpis
       ORDER BY snapshot_time DESC
       LIMIT 1`,
    )
    res.json(rows[0] ?? {})
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/refresh-status', requireAuthenticated, async (_req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT DISTINCT ON (view_name)
              view_name, status, started_at, finished_at, duration_ms, error_message, triggered_by
       FROM mv_refresh_log
       ORDER BY view_name, started_at DESC`,
    )
    res.json({ items: rows })
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.post('/refresh', requireAdmin, async (req, res) => {
  const target = String(req.body?.view || 'all')
  const triggeredBy = String(req.headers['x-actor-id'] || 'api_admin')

  const targets =
    target === 'all'
      ? [
          'fn_refresh_mv_locker_monthly_profitability',
          'fn_refresh_mv_realtime_kpis',
          'fn_refresh_financial_dashboard',
        ]
      : {
          'mv_locker_monthly_profitability': ['fn_refresh_mv_locker_monthly_profitability'],
          mv_realtime_kpis: ['fn_refresh_mv_realtime_kpis'],
          v_financial_dashboard: ['fn_refresh_financial_dashboard'],
        }[target]

  if (!targets) {
    return res.status(400).json({
      error: 'invalid_view',
      detail: 'Use view=all|mv_locker_monthly_profitability|mv_realtime_kpis|v_financial_dashboard',
    })
  }

  const results = []
  try {
    for (const fn of targets) {
      await pool.query(`SELECT public.${fn}($1)`, [triggeredBy])
      results.push({ function: fn, status: 'SUCCESS' })
    }
    res.json({ ok: true, refreshed: results })
  } catch (err) {
    res.status(500).json({
      error: 'refresh_failed',
      detail: String(err.message || err),
      refreshed: results,
    })
  }
})

export default router
