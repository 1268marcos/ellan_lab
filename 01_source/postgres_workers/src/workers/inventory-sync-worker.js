import { randomUUID } from 'crypto'
import { config } from '../config.js'
import { pool, withTransaction } from '../lib/db.js'
import { insertDeadLetter } from '../lib/dlq.js'
import { logger } from '../lib/logger.js'
import { nextRetryAt } from '../lib/retry.js'
import { RateLimiter } from '../lib/rate-limiter.js'
import { getMarketplaceAdapter } from '../marketplaces/index.js'

const WORKER = 'inventory_sync_queue'
const STALE_MINUTES = 5

const limiters = {
  SHOPEE: new RateLimiter(config.marketplace.SHOPEE.rps),
  MAGALU: new RateLimiter(config.marketplace.MAGALU.rps),
  MERCADO_LIVRE: new RateLimiter(config.marketplace.MERCADO_LIVRE.rps),
}

async function writeAuditLog(client, row, summary, payload) {
  await client.query(
    `INSERT INTO marketplace_sync_audit_log (
      id, event_type, entity_type, entity_id, actor_id, summary, payload_json, created_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())`,
    [
      randomUUID(),
      'INVENTORY_SYNC',
      'product',
      row.product_id,
      WORKER,
      summary.slice(0, 255),
      JSON.stringify(payload ?? {}),
    ],
  )
}

async function claimBatch(client) {
  const staleBefore = new Date(Date.now() - STALE_MINUTES * 60_000)
  const { rows } = await client.query(
    `SELECT id FROM inventory_sync_queue
     WHERE (
       status = 'PENDING'
       OR (status = 'FAILED' AND (next_retry_at IS NULL OR next_retry_at <= NOW()) AND retry_count < max_retries)
       OR (status = 'PROCESSING' AND processing_started_at IS NOT NULL AND processing_started_at <= $2)
     )
     ORDER BY created_at ASC
     LIMIT $1
     FOR UPDATE SKIP LOCKED`,
    [config.batchSize, staleBefore],
  )
  if (!rows.length) return []
  const ids = rows.map((r) => r.id)
  const claimed = await client.query(
    `UPDATE inventory_sync_queue
     SET status = 'PROCESSING', processing_started_at = NOW(), updated_at = NOW()
     WHERE id = ANY($1::varchar[])
     RETURNING *`,
    [ids],
  )
  return claimed.rows
}

async function markSynced(client, row, result) {
  await client.query(
    `UPDATE inventory_sync_queue
     SET status = 'SYNCED', synced_at = NOW(), last_error = NULL,
         processing_started_at = NULL, next_retry_at = NULL, updated_at = NOW()
     WHERE id = $1`,
    [row.id],
  )
  await writeAuditLog(client, row, `Synced ${row.marketplace} stock`, {
    queue_id: row.id,
    result,
    quantity_available: row.quantity_available,
  })
}

async function markFailed(client, row, errorMessage) {
  const retryCount = Number(row.retry_count || 0) + 1
  const maxRetries = Number(row.max_retries || 5)
  if (retryCount >= maxRetries) {
    await insertDeadLetter(client, {
      workerName: WORKER,
      sourceTable: 'inventory_sync_queue',
      sourceId: row.id,
      payload: row,
      errorMessage,
      attemptCount: retryCount,
    })
    await client.query(
      `UPDATE inventory_sync_queue
       SET status = 'DEAD_LETTER', retry_count = $2, last_error = $3,
           processing_started_at = NULL, next_retry_at = NULL, updated_at = NOW()
       WHERE id = $1`,
      [row.id, retryCount, (errorMessage || '').slice(0, 4000)],
    )
    await writeAuditLog(client, row, `Dead letter ${row.marketplace}`, { error: errorMessage })
    return
  }
  const retryAt = nextRetryAt(retryCount)
  await client.query(
    `UPDATE inventory_sync_queue
     SET status = 'FAILED', retry_count = $2, last_error = $3,
         next_retry_at = $4, processing_started_at = NULL, updated_at = NOW()
     WHERE id = $1`,
    [row.id, retryCount, (errorMessage || '').slice(0, 4000), retryAt],
  )
  await writeAuditLog(client, row, `Retry scheduled ${row.marketplace}`, {
    retry_count: retryCount,
    next_retry_at: retryAt.toISOString(),
    error: errorMessage,
  })
}

async function processRow(row) {
  const marketplace = String(row.marketplace || '').toUpperCase()
  const limiter = limiters[marketplace]
  if (limiter) await limiter.wait()

  const client = await pool.connect()
  try {
    const adapter = getMarketplaceAdapter(marketplace)
    const result = await adapter.syncStock(row)
    await markSynced(client, row, result)
    logger.info('inventory_sync_ok', {
      worker: WORKER,
      queue_id: row.id,
      marketplace,
      product_id: row.product_id,
    })
  } catch (err) {
    await markFailed(client, row, String(err))
    logger.error('inventory_sync_failed', {
      worker: WORKER,
      queue_id: row.id,
      marketplace,
      error: String(err),
    })
  } finally {
    client.release()
  }
}

export async function runInventorySyncWorkerCycle() {
  let rows = []
  try {
    rows = await withTransaction((client) => claimBatch(client))
  } catch (err) {
    if (String(err).includes('inventory_sync_queue')) {
      logger.warn('inventory_sync_queue_missing', { error: String(err) })
      return { processed: 0, skipped: true }
    }
    throw err
  }
  if (!rows.length) return { processed: 0 }
  for (const row of rows) {
    await processRow(row)
  }
  return { processed: rows.length }
}
