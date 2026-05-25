import { pool } from '../lib/db.js'

const VIEW_CONFIG = [
  { viewName: 'mv_locker_monthly_profitability', intervalMinutes: 60, maxMissedCycles: 2 },
  { viewName: 'mv_realtime_kpis', intervalMinutes: 5, maxMissedCycles: 2 },
  { viewName: 'v_financial_dashboard', intervalMinutes: 60, maxMissedCycles: 2 },
]

async function getLastExecution(viewName) {
  const { rows } = await pool.query(
    `SELECT id, view_name, status, started_at, finished_at, duration_ms, error_message
     FROM mv_refresh_log
     WHERE view_name = $1
     ORDER BY started_at DESC
     LIMIT 1`,
    [viewName],
  )
  return rows[0] ?? null
}

async function countRecentFailures(viewName, sinceMinutes) {
  const { rows } = await pool.query(
    `SELECT COUNT(*)::int AS cnt
     FROM mv_refresh_log
     WHERE view_name = $1
       AND status = 'FAILED'
       AND started_at >= now() - ($2 || ' minutes')::interval`,
    [viewName, String(sinceMinutes)],
  )
  return rows[0]?.cnt ?? 0
}

async function logAlert(viewName, message, metadata = {}) {
  await pool.query(
    `INSERT INTO mv_refresh_log (view_name, status, triggered_by, error_message, metadata, finished_at, duration_ms)
     VALUES ($1, 'ALERT', 'monitor-refresh', $2, $3::jsonb, now(), 0)`,
    [viewName, message, JSON.stringify(metadata)],
  )
}

export async function monitorRefreshViews() {
  const results = []

  for (const cfg of VIEW_CONFIG) {
    const last = await getLastExecution(cfg.viewName)
    const thresholdMinutes = cfg.intervalMinutes * cfg.maxMissedCycles
    const stale =
      !last ||
      (last.status === 'SUCCESS' &&
        Date.now() - new Date(last.finished_at || last.started_at).getTime() >
          thresholdMinutes * 60_000)

    const recentFailures = await countRecentFailures(cfg.viewName, thresholdMinutes)
    const failedCycles = recentFailures + (last?.status === 'FAILED' ? 1 : 0)

    let alert = null
    if (stale) {
      alert = `Sem refresh bem-sucedido há mais de ${thresholdMinutes} minutos`
    } else if (failedCycles >= cfg.maxMissedCycles) {
      alert = `${failedCycles} falhas consecutivas (limite: ${cfg.maxMissedCycles} ciclos)`
    }

    if (alert) {
      await logAlert(cfg.viewName, alert, {
        last_status: last?.status ?? null,
        last_started_at: last?.started_at ?? null,
        failed_cycles: failedCycles,
        threshold_minutes: thresholdMinutes,
      })
    }

    results.push({
      view_name: cfg.viewName,
      last_execution: last,
      stale,
      failed_cycles: failedCycles,
      alert,
    })
  }

  return results
}

async function main() {
  try {
    const results = await monitorRefreshViews()
    const alerts = results.filter((r) => r.alert)
    console.log(JSON.stringify({ ok: alerts.length === 0, results }, null, 2))
    process.exit(alerts.length === 0 ? 0 : 1)
  } catch (err) {
    console.error('[monitor-refresh]', err)
    process.exit(1)
  } finally {
    await pool.end()
  }
}

const isDirectRun = process.argv[1]?.endsWith('monitor-refresh.js')
if (isDirectRun) {
  main()
}
