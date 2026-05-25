import fs from 'fs'

function resolveDatabaseUrl() {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL
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
  port: Number(process.env.PORT || 8127),
  databaseUrl: resolveDatabaseUrl(),
  adminApiKey: process.env.ADMIN_API_KEY || 'dev-analytics-admin-key',
  monitorCron: process.env.MONITOR_CRON || '*/5 * * * *',
  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:5173,http://localhost:5174')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  jwtSecret:
    process.env.JWT_SECRET ||
    process.env.PARTNER_JWT_SECRET ||
    'partner-service-dev-secret',
  allowOpsActorAuth: process.env.ALLOW_OPS_ACTOR_AUTH !== '0',
  jwtAlg: process.env.JWT_ALG || 'HS256',
  apiKeyPepper: process.env.PARTNER_ADMIN_API_KEY_PEPPER || 'dev-partner-admin-pepper',
  redisUrl: process.env.REDIS_URL || 'redis://127.0.0.1:6379/0',
  redisEnabled: process.env.REDIS_ENABLED !== '0',
  sessionCacheTtlSec: Number(process.env.SESSION_CACHE_TTL_SEC || 300),
  permissionCacheTtlSec: Number(process.env.PERMISSION_CACHE_TTL_SEC || 300),
}
