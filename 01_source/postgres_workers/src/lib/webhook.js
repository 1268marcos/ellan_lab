import crypto from 'crypto'
import { config } from '../config.js'

export function buildSignature(secretKey, payloadBytes) {
  const digest = crypto.createHmac('sha256', secretKey).update(payloadBytes).digest('hex')
  return `sha256=${digest}`
}

export function endpointAcceptsEvent(eventsJson, eventName) {
  try {
    const events = JSON.parse(eventsJson || '["*"]')
    if (!Array.isArray(events)) return true
    if (events.includes('*')) return true
    return events.includes(eventName)
  } catch {
    return true
  }
}

export async function postPartnerWebhook(endpoint, eventRow) {
  const envelope = {
    event_key: eventRow.event_key,
    aggregate_type: eventRow.aggregate_type,
    aggregate_id: eventRow.aggregate_id,
    event_name: eventRow.event_name,
    event_version: eventRow.event_version,
    occurred_at: eventRow.occurred_at,
    payload: JSON.parse(eventRow.payload_json || '{}'),
  }
  const body = JSON.stringify(envelope)
  const headers = {
    'Content-Type': 'application/json',
    'X-Ellan-Event': String(eventRow.event_name || 'unknown'),
    'X-Ellan-Event-Id': String(eventRow.id),
    'X-Ellan-Api-Version': String(endpoint.api_version || 'v1'),
  }
  const secret = String(endpoint.secret_key || '').trim()
  if (secret) {
    headers['X-Ellan-Signature'] = buildSignature(secret, Buffer.from(body, 'utf8'))
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), config.domainEventHttpTimeoutMs)
  try {
    const res = await fetch(endpoint.url, {
      method: 'POST',
      headers,
      body,
      signal: controller.signal,
    })
    if (res.status < 200 || res.status >= 300) {
      const text = await res.text().catch(() => '')
      throw new Error(`webhook_http_${res.status}:${text.slice(0, 200)}`)
    }
    return res.status
  } finally {
    clearTimeout(timer)
  }
}
