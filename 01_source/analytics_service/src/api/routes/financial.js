import { Router } from 'express'
import { requireApiKeyOrJwt } from '../../middleware/api-key.js'
import { requirePermission } from '../../middleware/rbac.js'
import { cachedQuery, cacheKey } from '../../lib/financial-cache.js'
import { buildMinimalPdf, rowsToCsv } from '../../lib/export.js'

const router = Router()
const READ = requirePermission('analytics.read')

router.use(requireApiKeyOrJwt())

function sendCached(res, payload, cache) {
  res.setHeader('X-Cache', cache)
  res.json(payload)
}

router.get('/kpis', READ, async (req, res) => {
  try {
    const { data, cache } = await cachedQuery(cacheKey('kpis'), async () => {
      const { rows } = await req.db.query(`SELECT * FROM v_financial_dashboard LIMIT 1`)
      return rows[0] ?? {}
    })
    sendCached(res, data, cache)
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/locker-roi', READ, async (req, res) => {
  try {
    const city = req.query.city ? String(req.query.city) : ''
    const viability = req.query.viability ? String(req.query.viability) : ''
    const { data, cache } = await cachedQuery(cacheKey('locker-roi', { city, viability }), async () => {
      const conditions = []
      const params = []
      if (city) {
        params.push(city)
        conditions.push(`city ILIKE $${params.length}`)
      }
      if (viability) {
        params.push(viability)
        conditions.push(`viability_classification = $${params.length}`)
      }
      const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
      const { rows } = await req.db.query(
        `SELECT locker_id, external_id, display_name, city, region, installation_date,
                total_investment_brl, expected_life_months, salvage_value_brl,
                avg_monthly_profit_brl, profit_volatility_brl, first_profit_month,
                months_to_profitability, lifetime_revenue_brl, lifetime_costs_brl,
                lifetime_profit_brl, avg_margin_pct, payback_months, annual_roi_pct,
                viability_classification, recommendation, alert_status, computed_at
         FROM v_locker_roi_analysis
         ${where}
         ORDER BY annual_roi_pct DESC NULLS LAST, locker_id
         LIMIT 1000`,
        params,
      )
      return { items: rows, total: rows.length }
    })
    sendCached(res, data, cache)
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/locker-pnl', READ, async (req, res) => {
  try {
    const lockerId = req.query.locker_id ? String(req.query.locker_id) : ''
    const monthFrom = req.query.month_from ? String(req.query.month_from) : ''
    const monthTo = req.query.month_to ? String(req.query.month_to) : ''
    const sort = ['month_ref', 'locker_id', 'revenue_cents', 'net_profit_cents', 'margin_pct'].includes(
      String(req.query.sort || 'month_ref'),
    )
      ? String(req.query.sort)
      : 'month_ref'
    const order = String(req.query.order || 'desc').toLowerCase() === 'asc' ? 'ASC' : 'DESC'

    const { data, cache } = await cachedQuery(
      cacheKey('locker-pnl', { lockerId, monthFrom, monthTo, sort, order }),
      async () => {
        const conditions = []
        const params = []
        if (lockerId) {
          params.push(lockerId)
          conditions.push(`locker_id = $${params.length}`)
        }
        if (monthFrom) {
          params.push(monthFrom)
          conditions.push(`month_ref >= $${params.length}::date`)
        }
        if (monthTo) {
          params.push(monthTo)
          conditions.push(`month_ref <= $${params.length}::date`)
        }
        const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
        const { rows } = await req.db.query(
          `SELECT month_ref, locker_id, revenue_cents, opex_cents, depreciation_cents,
                  total_cost_cents, net_profit_cents, margin_pct
           FROM mv_locker_monthly_pnl
           ${where}
           ORDER BY ${sort} ${order}, locker_id
           LIMIT 2000`,
          params,
        )
        return { items: rows, total: rows.length }
      },
    )
    sendCached(res, data, cache)
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/partner-revenue', READ, async (req, res) => {
  try {
    const partnerId = req.query.partner_id ? String(req.query.partner_id) : ''
    const { data, cache } = await cachedQuery(cacheKey('partner-revenue', { partnerId }), async () => {
      const revParams = []
      const revWhere = partnerId
        ? (revParams.push(partnerId), `WHERE pr.partner_id = $1`)
        : ''

      const { rows: revenue } = await req.db.query(
        `SELECT pr.month_ref, pr.partner_id,
                COALESCE(ep.name, lp.name, pr.partner_id) AS partner_name,
                pr.locker_id, pr.currency, pr.country_code,
                pr.revenue_recognized_cents, pr.deferred_amount_cents, pr.updated_at
         FROM analytics_analytics.partner_revenue_monthly pr
         LEFT JOIN ecommerce_partners ep ON ep.id::text = pr.partner_id::text
         LEFT JOIN logistics_partners lp ON lp.id::text = pr.partner_id::text
         ${revWhere}
         ORDER BY pr.month_ref DESC, pr.partner_id
         LIMIT 500`,
        revParams,
      )

      const settleParams = []
      const settleWhere = partnerId
        ? (settleParams.push(partnerId), `WHERE psb.partner_id = $1`)
        : ''

      const { rows: settlements } = await req.db.query(
        `SELECT psb.id, psb.partner_id,
                COALESCE(ep.name, lp.name, psb.partner_id) AS partner_name,
                psb.partner_type, psb.period_start, psb.period_end, psb.currency,
                psb.total_orders, psb.gross_revenue_cents, psb.revenue_share_pct,
                psb.revenue_share_cents, psb.fees_cents, psb.net_amount_cents,
                psb.status, psb.settled_at, psb.settlement_ref, psb.created_at
         FROM partner_settlement_batches psb
         LEFT JOIN ecommerce_partners ep ON ep.id = psb.partner_id
         LEFT JOIN logistics_partners lp ON lp.id = psb.partner_id
         ${settleWhere}
         ORDER BY psb.period_end DESC
         LIMIT 200`,
        settleParams,
      )

      return { revenue, settlements, total_revenue_rows: revenue.length, total_settlement_rows: settlements.length }
    })
    sendCached(res, data, cache)
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.get('/revenue-trend', READ, async (req, res) => {
  try {
    const months = Math.min(36, Math.max(3, Number(req.query.months) || 12))
    const { data, cache } = await cachedQuery(cacheKey('revenue-trend', { months }), async () => {
      const { rows } = await req.db.query(
        `SELECT month_ref::text AS month,
                ROUND(COALESCE(SUM(revenue_cents), 0) / 100.0, 2) AS revenue_brl,
                ROUND(COALESCE(SUM(net_profit_cents), 0) / 100.0, 2) AS profit_brl,
                ROUND(AVG(margin_pct), 2) AS avg_margin_pct
         FROM mv_locker_monthly_pnl
         WHERE month_ref >= (date_trunc('month', CURRENT_DATE) - make_interval(months => $1::int))::date
         GROUP BY month_ref
         ORDER BY month_ref`,
        [months],
      )
      return { items: rows }
    })
    sendCached(res, data, cache)
  } catch (err) {
    res.status(500).json({ error: 'query_failed', detail: String(err.message || err) })
  }
})

router.post('/simulate-expansion', READ, async (req, res) => {
  try {
    const b = req.body || {}
    const targetCity = String(b.target_city || b.p_target_city || '').trim()
    if (!targetCity) {
      return res.status(400).json({ error: 'invalid_body', detail: 'target_city required' })
    }
    const lockersCount = Number(b.lockers_count ?? b.p_lockers_count ?? 1)
    const revenuePerLocker = Number(
      b.estimated_monthly_revenue_per_locker_cents ?? b.p_estimated_monthly_revenue_per_locker_cents ?? 0,
    )
    const opexPerLocker = Number(
      b.estimated_monthly_opex_per_locker_cents ?? b.p_estimated_monthly_opex_per_locker_cents ?? 0,
    )
    const installPerLocker = Number(
      b.installation_cost_per_locker_cents ?? b.p_installation_cost_per_locker_cents ?? 0,
    )
    const hardwarePerLocker = Number(
      b.hardware_cost_per_locker_cents ?? b.p_hardware_cost_per_locker_cents ?? 0,
    )
    const usefulLife = Number(b.useful_life_months ?? b.p_useful_life_months ?? 60)
    const occupancy = Number(b.expected_occupancy_rate_pct ?? b.p_expected_occupancy_rate_pct ?? 70)

    const { rows } = await req.db.query(
      `SELECT scenario_metric, value, description
       FROM simulate_expansion_scenario_v2(
         $1::varchar, $2::int, $3::int, $4::int, $5::int, $6::int, $7::int, $8::numeric
       )`,
      [
        targetCity,
        lockersCount,
        revenuePerLocker,
        opexPerLocker,
        installPerLocker,
        hardwarePerLocker,
        usefulLife,
        occupancy,
      ],
    )
    res.json({ items: rows, target_city: targetCity })
  } catch (err) {
    res.status(500).json({ error: 'simulation_failed', detail: String(err.message || err) })
  }
})

async function loadExportDataset(req, dataset) {
  switch (dataset) {
    case 'kpis': {
      const { rows } = await req.db.query(`SELECT * FROM v_financial_dashboard LIMIT 1`)
      return rows
    }
    case 'locker-roi': {
      const { rows } = await req.db.query(
        `SELECT * FROM v_locker_roi_analysis ORDER BY locker_id LIMIT 5000`,
      )
      return rows
    }
    case 'locker-pnl': {
      const { rows } = await req.db.query(
        `SELECT * FROM mv_locker_monthly_pnl ORDER BY month_ref DESC, locker_id LIMIT 5000`,
      )
      return rows
    }
    case 'partner-revenue': {
      const { rows } = await req.db.query(
        `SELECT pr.month_ref, pr.partner_id,
                COALESCE(ep.name, lp.name, pr.partner_id) AS partner_name,
                pr.revenue_recognized_cents, pr.deferred_amount_cents
         FROM analytics_analytics.partner_revenue_monthly pr
         LEFT JOIN ecommerce_partners ep ON ep.id::text = pr.partner_id::text
         LEFT JOIN logistics_partners lp ON lp.id::text = pr.partner_id::text
         ORDER BY pr.month_ref DESC
         LIMIT 5000`,
      )
      return rows
    }
    default:
      return null
  }
}

router.get('/export/csv', READ, async (req, res) => {
  try {
    const dataset = String(req.query.dataset || 'kpis')
    const rows = await loadExportDataset(req, dataset)
    if (rows === null) {
      return res.status(400).json({
        error: 'invalid_dataset',
        detail: 'dataset=kpis|locker-roi|locker-pnl|partner-revenue',
      })
    }
    const csv = rowsToCsv(rows)
    res.setHeader('Content-Type', 'text/csv; charset=utf-8')
    res.setHeader('Content-Disposition', `attachment; filename="ellan-financial-${dataset}.csv"`)
    res.send(csv)
  } catch (err) {
    res.status(500).json({ error: 'export_failed', detail: String(err.message || err) })
  }
})

router.get('/export/pdf', READ, async (req, res) => {
  try {
    const dataset = String(req.query.dataset || 'kpis')
    const rows = await loadExportDataset(req, dataset)
    if (rows === null) {
      return res.status(400).json({
        error: 'invalid_dataset',
        detail: 'dataset=kpis|locker-roi|locker-pnl|partner-revenue',
      })
    }
    const title = `Ellan Financial — ${dataset}`
    const preview = rows.slice(0, 28).map((row, idx) => {
      const keys = Object.keys(row).slice(0, 4)
      const vals = keys.map((k) => `${k}=${row[k]}`).join(' | ')
      return `${idx + 1}. ${vals}`
    })
    const pdf = buildMinimalPdf(title, [`rows: ${rows.length}`, ...preview])
    res.setHeader('Content-Type', 'application/pdf')
    res.setHeader('Content-Disposition', `attachment; filename="ellan-financial-${dataset}.pdf"`)
    res.send(pdf)
  } catch (err) {
    res.status(500).json({ error: 'export_failed', detail: String(err.message || err) })
  }
})

export default router
