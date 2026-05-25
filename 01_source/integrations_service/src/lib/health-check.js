import { query } from './db.js'
import { config } from '../config.js'

export async function runHealthCheck(partnerIdOrCode, endpointUrl) {
  const { rows: players } = await query('SELECT * FROM partner_ecosystem_players WHERE id = $1 OR code = $1', [
    partnerIdOrCode,
  ])
  const player = players[0]
  if (!player) return null

  const url =
    endpointUrl ||
    player.api_docs_url ||
    player.website_url ||
    `https://health.ellan.lab/ping/${player.code}`

  const started = Date.now()
  let status = 'UP'
  let httpStatus = null
  let errorMessage = null

  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), config.healthTimeoutMs)
    const res = await fetch(url, { method: 'HEAD', signal: controller.signal })
    clearTimeout(timer)
    httpStatus = res.status
    if (res.status >= 500) {
      status = 'DEGRADED'
      errorMessage = `http_${res.status}`
    }
  } catch (err) {
    status = 'DOWN'
    errorMessage = String(err.message || err).slice(0, 500)
  }

  const latencyMs = Date.now() - started
  const { rows } = await query(
    `INSERT INTO partner_integration_health (
      partner_id, partner_type, endpoint_url, status, latency_ms, http_status, error_message, checked_at
    ) VALUES ($1,'ECOSYSTEM',$2,$3,$4,$5,$6,NOW())
    RETURNING *`,
    [player.id, url, status, latencyMs, httpStatus, errorMessage],
  )
  return {
    partner_id: player.id,
    partner_code: player.code,
    endpoint_url: url,
    status,
    latency_ms: latencyMs,
    http_status: httpStatus,
    error_message: errorMessage,
    checked_at: rows[0].checked_at,
  }
}
