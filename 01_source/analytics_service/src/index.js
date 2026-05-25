import cors from 'cors'
import cron from 'node-cron'
import express from 'express'
import { config } from './config.js'
import { pool } from './lib/db.js'
import { attachDbClient } from './lib/rls.js'
import analyticsRouter from './api/routes/analytics.js'
import { monitorRefreshViews } from './db/monitor-refresh.js'

const app = express()

app.set('trust proxy', 1)
app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
  }),
)
app.use(express.json())

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'analytics-service' })
})

app.use(attachDbClient(pool))
app.use('/api/v1/analytics', analyticsRouter)

async function start() {
  await pool.query('SELECT 1')

  cron.schedule(config.monitorCron, () => {
    monitorRefreshViews().catch((err) => {
      console.error('[monitor-refresh]', err)
    })
  })

  app.listen(config.port, () => {
    console.log(`analytics-service listening on :${config.port}`)
  })
}

start().catch((err) => {
  console.error('[analytics-service]', err)
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
