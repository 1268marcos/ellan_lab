import fs from 'fs'

/** Host: porta 5435 no laptop (compose); postgres_central:5432 dentro da rede Docker. */
function resolveDatabaseUrl() {
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL
  }
  const inDocker =
    process.env.DOCKER === '1' ||
    fs.existsSync('/.dockerenv') ||
    String(process.env.PGHOST || '').includes('postgres_central')
  if (inDocker) {
    return 'postgresql://admin:admin123@postgres_central:5432/locker_central'
  }
  return 'postgresql://admin:admin123@127.0.0.1:5435/locker_central'
}

export const config = {
  databaseUrl: resolveDatabaseUrl(),
  cronExpr: process.env.WORKER_CRON || '*/10 * * * * *',
  batchSize: Number(process.env.WORKER_BATCH_SIZE || 50),
  domainEventMaxRetries: Number(process.env.DOMAIN_EVENT_MAX_RETRIES || 5),
  domainEventHttpTimeoutMs: Number(process.env.DOMAIN_EVENT_HTTP_TIMEOUT_MS || 8000),
  lifecycleRuntimeUrl: (process.env.LIFECYCLE_RUNTIME_URL || 'http://runtime_service:8000').replace(
    /\/$/,
    '',
  ),
  lifecycleRuntimeToken: process.env.LIFECYCLE_RUNTIME_TOKEN || process.env.INTERNAL_TOKEN || '',
  notificationDefaultDestination:
    process.env.NOTIFICATION_DEFAULT_DESTINATION || 'ops@ellan.local',
  marketplace: {
    SHOPEE: {
      syncUrl: process.env.MARKETPLACE_SHOPEE_SYNC_URL || '',
      rps: Number(process.env.MARKETPLACE_SHOPEE_RPS || 2),
    },
    MAGALU: {
      syncUrl: process.env.MARKETPLACE_MAGALU_SYNC_URL || '',
      rps: Number(process.env.MARKETPLACE_MAGALU_RPS || 1),
    },
    MERCADO_LIVRE: {
      syncUrl: process.env.MARKETPLACE_MERCADO_LIVRE_SYNC_URL || '',
      rps: Number(process.env.MARKETPLACE_MERCADO_LIVRE_RPS || 3),
    },
  },
}
