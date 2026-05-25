import { WebSocketServer } from 'ws'
import { query } from '../lib/db.js'
import { config } from '../config.js'

function safeSend(ws, payload) {
  if (ws.readyState === ws.OPEN) {
    ws.send(JSON.stringify(payload))
  }
}

async function fetchLatestTelemetry(lockerIds) {
  if (!lockerIds?.length) {
    const { rows } = await query(`
      SELECT DISTINCT ON (locker_id)
        locker_id, event_type, temperature_celsius, battery_pct, signal_rssi,
        humidity_pct, occurred_at
      FROM locker_telemetry
      WHERE occurred_at >= NOW() - INTERVAL '15 minutes'
      ORDER BY locker_id, occurred_at DESC
      LIMIT 200
    `)
    return rows
  }
  const { rows } = await query(
    `
    SELECT DISTINCT ON (locker_id)
      locker_id, event_type, temperature_celsius, battery_pct, signal_rssi,
      humidity_pct, occurred_at
    FROM locker_telemetry
    WHERE locker_id = ANY($1::text[])
      AND occurred_at >= NOW() - INTERVAL '2 hours'
    ORDER BY locker_id, occurred_at DESC
    `,
    [lockerIds],
  )
  return rows
}

async function fetchCriticalAlerts() {
  const { rows } = await query(`
    SELECT alert_type, alert_id, severity, breach_type,
           detected_at, locker_display_name, reference_id, priority
    FROM vw_noc_alerts
    WHERE priority = 1
    ORDER BY detected_at DESC
    LIMIT 50
  `)
  return rows
}

export function attachWebSockets(server) {
  const telemetryWss = new WebSocketServer({ noServer: true, path: '/ws/ops/realtime' })
  const alertsWss = new WebSocketServer({ noServer: true, path: '/ws/ops/alerts' })

  const telemetrySubs = new Map()

  telemetryWss.on('connection', (ws) => {
    const sub = { lockerIds: [] }
    telemetrySubs.set(ws, sub)

    ws.on('message', (raw) => {
      try {
        const msg = JSON.parse(String(raw))
        if (msg.type === 'subscribe' && Array.isArray(msg.locker_ids)) {
          sub.lockerIds = msg.locker_ids.map(String).slice(0, 100)
        }
      } catch {
        /* ignore */
      }
    })

    ws.on('close', () => telemetrySubs.delete(ws))
    safeSend(ws, { type: 'connected', channel: 'telemetry' })
  })

  alertsWss.on('connection', (ws) => {
    safeSend(ws, { type: 'connected', channel: 'alerts' })
  })

  setInterval(async () => {
    try {
      const allIds = [...telemetrySubs.values()].flatMap((s) => s.lockerIds)
      const unique = [...new Set(allIds)]
      const rows = await fetchLatestTelemetry(unique.length ? unique : null)
      const payload = { type: 'telemetry_batch', at: new Date().toISOString(), items: rows }
      for (const [ws, sub] of telemetrySubs) {
        if (!sub.lockerIds.length) {
          safeSend(ws, payload)
        } else {
          const filtered = rows.filter((r) => sub.lockerIds.includes(r.locker_id))
          safeSend(ws, { ...payload, items: filtered })
        }
      }
    } catch (err) {
      console.error('[ws/telemetry]', err.message)
    }
  }, config.telemetryPollMs)

  let lastAlertHash = ''
  setInterval(async () => {
    try {
      const items = await fetchCriticalAlerts()
      const hash = JSON.stringify(items.map((a) => a.alert_id))
      if (hash === lastAlertHash) return
      lastAlertHash = hash
      const payload = { type: 'alerts_critical', at: new Date().toISOString(), items }
      alertsWss.clients.forEach((ws) => safeSend(ws, payload))
    } catch (err) {
      console.error('[ws/alerts]', err.message)
    }
  }, config.alertsPollMs)

  server.on('upgrade', (request, socket, head) => {
    const { pathname } = new URL(request.url, 'http://localhost')
    if (pathname === '/ws/ops/realtime') {
      telemetryWss.handleUpgrade(request, socket, head, (ws) => {
        telemetryWss.emit('connection', ws, request)
      })
      return
    }
    if (pathname === '/ws/ops/alerts') {
      alertsWss.handleUpgrade(request, socket, head, (ws) => {
        alertsWss.emit('connection', ws, request)
      })
      return
    }
    socket.destroy()
  })

  return { telemetryWss, alertsWss }
}
