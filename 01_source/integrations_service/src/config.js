const corsOrigins = (process.env.CORS_ORIGINS || 'http://localhost:5173,http://localhost:5174,http://localhost:3000')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

export const config = {
  port: Number(process.env.PORT || 8128),
  databaseUrl: process.env.DATABASE_URL || 'postgresql://admin:admin123@127.0.0.1:5435/locker_central',
  corsOrigins,
  seedOnStart: process.env.SEED_ON_START === 'true',
  defaultRateLimitPerMinute: Number(process.env.RATE_LIMIT_PER_MINUTE || 120),
  healthTimeoutMs: Number(process.env.HEALTH_TIMEOUT_MS || 8000),
  webhookTestTimeoutMs: Number(process.env.WEBHOOK_TEST_TIMEOUT_MS || 10000),
  partnerServiceUrl: (process.env.PARTNER_SERVICE_URL || 'http://localhost:8402').replace(/\/$/, ''),
}
