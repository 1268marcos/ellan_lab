import cron from 'node-cron'
import { config } from './config.js'
import { pool } from './lib/db.js'
import { logger } from './lib/logger.js'
import { runDomainEventWorkerCycle } from './workers/domain-event-worker.js'
import { runLifecycleWorkerCycle } from './workers/lifecycle-worker.js'
import { runInventorySyncWorkerCycle } from './workers/inventory-sync-worker.js'

let running = false

async function runAllWorkers() {
  if (running) {
    logger.warn('worker_cycle_skipped', { reason: 'previous_cycle_in_progress' })
    return
  }
  running = true
  const started = Date.now()
  try {
    const [domain, lifecycle, inventory] = await Promise.all([
      runDomainEventWorkerCycle().catch((err) => {
        logger.error('domain_worker_cycle_error', { error: String(err) })
        return { processed: 0, error: String(err) }
      }),
      runLifecycleWorkerCycle().catch((err) => {
        logger.error('lifecycle_worker_cycle_error', { error: String(err) })
        return { processed: 0, error: String(err) }
      }),
      runInventorySyncWorkerCycle().catch((err) => {
        logger.error('inventory_worker_cycle_error', { error: String(err) })
        return { processed: 0, error: String(err) }
      }),
    ])
    logger.info('worker_cycle_complete', {
      duration_ms: Date.now() - started,
      domain_processed: domain.processed,
      lifecycle_processed: lifecycle.processed,
      inventory_processed: inventory.processed,
    })
  } finally {
    running = false
  }
}

async function main() {
  await pool.query('SELECT 1')
  logger.info('postgres_workers_started', { cron: config.cronExpr })
  await runAllWorkers()
  cron.schedule(config.cronExpr, () => {
    runAllWorkers().catch((err) => logger.error('worker_scheduler_error', { error: String(err) }))
  })
}

main().catch((err) => {
  logger.error('postgres_workers_fatal', { error: String(err) })
  process.exit(1)
})

process.on('SIGINT', async () => {
  await pool.end()
  process.exit(0)
})
process.on('SIGTERM', async () => {
  await pool.end()
  process.exit(0)
})
