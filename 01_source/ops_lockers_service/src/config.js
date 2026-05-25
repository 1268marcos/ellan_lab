const corsOrigins = (process.env.CORS_ORIGINS || 'http://localhost:5173,http://localhost:5174,http://localhost:3000')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

export const config = {
  port: Number(process.env.PORT || 8129),
  databaseUrl: process.env.DATABASE_URL || 'postgresql://admin:admin123@127.0.0.1:5435/locker_central',
  corsOrigins,
  telemetryPollMs: Number(process.env.TELEMETRY_POLL_MS || 3000),
  alertsPollMs: Number(process.env.ALERTS_POLL_MS || 5000),
}
