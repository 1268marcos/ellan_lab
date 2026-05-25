import { config } from '../config.js'
import { pool, withTransaction } from '../lib/db.js'
import { insertDeadLetter } from '../lib/dlq.js'
import { logger } from '../lib/logger.js'
import { nextRetryAt } from '../lib/retry.js'
import { endpointAcceptsEvent, postPartnerWebhook } from '../lib/webhook.js'

const WORKER = 'domain_event_outbox'
const STALE_MINUTES = 5

function resolvePartnerHints(payload) {
  const p = payload && typeof payload === 'object' ? payload : {}
  return {
    partnerId:
      p.ecommerce_partner_id ||
      p.partner_id ||
      p.logistics_partner_id ||
      p.aggregate_partner_id ||
      null,
    partnerType: (p.partner_type || p.partnerType || 'ECOMMERCE').toUpperCase(),
  }
}

async function claimBatch(client) {
  const staleBefore = new Date(Date.now() - STALE_MINUTES * 60_000)
  const { rows } = await client.query(
    `SELECT id FROM domain_event_outbox
     WHERE (
       status = 'PENDING'
       OR (status = 'FAILED' AND (next_retry_at IS NULL OR next_retry_at <= NOW()) AND retry_count < $2)
       OR (status = 'PROCESSING' AND processing_started_at IS NOT NULL AND processing_started_at <= $3)
     )
     ORDER BY created_at ASC
     LIMIT $1
     FOR UPDATE SKIP LOCKED`,
    [config.batchSize, config.domainEventMaxRetries, staleBefore],
  )
  if (!rows.length) return []

  const ids = rows.map((r) => r.id)
  const claimed = await client.query(
    `UPDATE domain_event_outbox
     SET status = 'PROCESSING', processing_started_at = NOW(), updated_at = NOW()
     WHERE id = ANY($1::varchar[])
     RETURNING *`,
    [ids],
  )
  return claimed.rows
}

async function loadEndpoints(client, partnerId, partnerType) {
  if (!partnerId) return []
  const { rows } = await client.query(
    `SELECT * FROM partner_webhook_endpoints
     WHERE partner_id = $1 AND partner_type = $2 AND active = true`,
    [partnerId, partnerType],
  )
  return rows
}

async function markPublished(client, id) {
  await client.query(
    `UPDATE domain_event_outbox
     SET status = 'PUBLISHED', published_at = NOW(), last_error = NULL,
         processing_started_at = NULL, next_retry_at = NULL, updated_at = NOW()
     WHERE id = $1`,
    [id],
  )
}

async function markFailed(client, row, errorMessage) {
  const retryCount = Number(row.retry_count || 0) + 1
  if (retryCount >= config.domainEventMaxRetries) {
    await insertDeadLetter(client, {
      workerName: WORKER,
      sourceTable: 'domain_event_outbox',
      sourceId: row.id,
      payload: row,
      errorMessage,
      attemptCount: retryCount,
    })
    await client.query(
      `UPDATE domain_event_outbox
       SET status = 'FAILED', retry_count = $2, last_error = $3,
           processing_started_at = NULL, next_retry_at = NULL, updated_at = NOW()
       WHERE id = $1`,
      [row.id, retryCount, (errorMessage || '').slice(0, 4000)],
    )
    return
  }
  const retryAt = nextRetryAt(retryCount)
  await client.query(
    `UPDATE domain_event_outbox
     SET status = 'FAILED', retry_count = $2, last_error = $3,
         next_retry_at = $4, processing_started_at = NULL, updated_at = NOW()
     WHERE id = $1`,
    [row.id, retryCount, (errorMessage || '').slice(0, 4000), retryAt],
  )
}

async function resolvePartnerFromOrder(client, aggregateId) {
  if (!aggregateId) return null
  const { rows } = await client.query(
    `SELECT ecommerce_partner_id FROM orders WHERE id = $1 LIMIT 1`,
    [aggregateId],
  )
  return rows[0]?.ecommerce_partner_id || null
}

async function processRow(row) {
  const payload = JSON.parse(row.payload_json || '{}')
  const hints = resolvePartnerHints(payload)
  const client = await pool.connect()
  try {
    if (!hints.partnerId && row.aggregate_type === 'Order') {
      hints.partnerId = await resolvePartnerFromOrder(client, row.aggregate_id)
      hints.partnerType = 'ECOMMERCE'
    }
    const endpoints = await loadEndpoints(client, hints.partnerId, hints.partnerType)
    const matching = endpoints.filter((ep) =>
      endpointAcceptsEvent(ep.events_json, row.event_name),
    )
    if (!matching.length) {
      throw new Error(
        hints.partnerId
          ? 'NO_ACTIVE_WEBHOOK_ENDPOINT_FOR_EVENT'
          : 'PARTNER_ID_MISSING_IN_PAYLOAD',
      )
    }
    for (const ep of matching) {
      await postPartnerWebhook(ep, row)
    }
    await markPublished(client, row.id)
    logger.info('domain_event_published', {
      worker: WORKER,
      event_id: row.id,
      event_name: row.event_name,
      aggregate_id: row.aggregate_id,
      endpoints: matching.length,
    })
  } catch (err) {
    await markFailed(client, row, String(err))
    logger.error('domain_event_publish_failed', {
      worker: WORKER,
      event_id: row.id,
      event_name: row.event_name,
      error: String(err),
    })
  } finally {
    client.release()
  }
}

export async function runDomainEventWorkerCycle() {
  const rows = await withTransaction((client) => claimBatch(client))
  if (!rows.length) return { processed: 0 }
  for (const row of rows) {
    await processRow(row)
  }
  return { processed: rows.length }
}
