import { randomUUID } from 'crypto'
import { logger } from './logger.js'

export async function insertDeadLetter(
  client,
  { workerName, sourceTable, sourceId, payload, errorMessage, attemptCount },
) {
  const id = randomUUID()
  await client.query(
    `INSERT INTO worker_dead_letter_queue (
      id, worker_name, source_table, source_id, payload_json, error_message, attempt_count
    ) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
    [
      id,
      workerName,
      sourceTable,
      sourceId,
      JSON.stringify(payload ?? {}),
      (errorMessage || '').slice(0, 4000),
      attemptCount ?? 0,
    ],
  )
  logger.warn('dead_letter_inserted', {
    worker: workerName,
    source_table: sourceTable,
    source_id: sourceId,
    dlq_id: id,
  })
  return id
}
