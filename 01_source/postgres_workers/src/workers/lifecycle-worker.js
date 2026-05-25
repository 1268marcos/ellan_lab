import { config } from '../config.js'
import { pool, withTransaction } from '../lib/db.js'
import { insertDeadLetter } from '../lib/dlq.js'
import { logger } from '../lib/logger.js'
import { executeDeadline } from './lifecycle-handlers.js'

const WORKER = 'lifecycle_deadlines'
const STALE_MINUTES = 10

async function claimBatch(client) {
  const staleBefore = new Date(Date.now() - STALE_MINUTES * 60_000)
  const { rows } = await client.query(
    `SELECT id FROM lifecycle_deadlines
     WHERE (
       (status = 'PENDING' AND due_at <= NOW())
       OR (status = 'EXECUTING' AND locked_at IS NOT NULL AND locked_at <= $2)
     )
     ORDER BY due_at ASC
     LIMIT $1
     FOR UPDATE SKIP LOCKED`,
    [config.batchSize, staleBefore],
  )
  if (!rows.length) return []
  const ids = rows.map((r) => r.id)
  const claimed = await client.query(
    `UPDATE lifecycle_deadlines
     SET status = 'EXECUTING', locked_at = NOW(), updated_at = NOW()
     WHERE id = ANY($1::uuid[])
     RETURNING *`,
    [ids],
  )
  return claimed.rows
}

async function processDeadline(deadline) {
  const client = await pool.connect()
  try {
    await client.query('BEGIN')
    const fresh = await client.query(`SELECT * FROM lifecycle_deadlines WHERE id = $1 FOR UPDATE`, [
      deadline.id,
    ])
    const row = fresh.rows[0]
    if (!row || row.status !== 'EXECUTING') {
      await client.query('ROLLBACK')
      return
    }
    await executeDeadline(client, row)
    await client.query('COMMIT')
  } catch (err) {
    await client.query('ROLLBACK')
    const errClient = await pool.connect()
    try {
      await errClient.query('BEGIN')
      await insertDeadLetter(errClient, {
        workerName: WORKER,
        sourceTable: 'lifecycle_deadlines',
        sourceId: String(deadline.id),
        payload: deadline,
        errorMessage: String(err),
        attemptCount: Number(deadline.failure_count || 0) + 1,
      })
      await errClient.query(
        `UPDATE lifecycle_deadlines
         SET status = 'FAILED', failure_count = failure_count + 1, updated_at = NOW()
         WHERE id = $1`,
        [deadline.id],
      )
      await errClient.query('COMMIT')
    } catch (inner) {
      await errClient.query('ROLLBACK')
      logger.error('lifecycle_failure_persist_error', { error: String(inner) })
    } finally {
      errClient.release()
    }
    logger.error('lifecycle_deadline_failed', {
      worker: WORKER,
      deadline_id: deadline.id,
      deadline_type: deadline.deadline_type,
      error: String(err),
    })
  } finally {
    client.release()
  }
}

export async function runLifecycleWorkerCycle() {
  const rows = await withTransaction((client) => claimBatch(client))
  if (!rows.length) return { processed: 0 }
  for (const row of rows) {
    await processDeadline(row)
  }
  return { processed: rows.length }
}
