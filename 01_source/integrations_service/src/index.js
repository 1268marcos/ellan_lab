import cors from 'cors'
import express from 'express'
import { config } from './config.js'
import { pool } from './lib/db.js'
import { rateLimitMiddleware } from './middleware/rate-limit.js'
import partnersRouter from './routes/partners.js'
import capabilitiesRouter from './routes/capabilities.js'
import marketplacesRouter from './routes/marketplaces.js'
import carrierRatesRouter from './routes/carrier-rates.js'
import webhookRouter from './routes/webhook-test.js'
import { execSeed } from './seed/seed-on-start.js'

const app = express()

app.set('trust proxy', 1)
app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
  }),
)
app.use(express.json())
app.use(rateLimitMiddleware)

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'integrations-service' })
})

app.get('/api/v1/health', (_req, res) => {
  res.json({ status: 'ok', service: 'integrations-service', version: 'v1' })
})

app.use('/api/v1/partners/webhook', webhookRouter)
app.use('/api/v1/partners', partnersRouter)
app.use('/api/v1/partners/:id/capabilities', capabilitiesRouter)
app.use('/api/v1/marketplaces', marketplacesRouter)
app.use('/api/v1/carriers/rates', carrierRatesRouter)

app.use((err, _req, res, _next) => {
  console.error('[integrations-service]', err)
  res.status(500).json({ detail: 'internal_error', message: err.message })
})

async function start() {
  await pool.query('SELECT 1')
  if (config.seedOnStart) {
    await execSeed()
  }
  app.listen(config.port, () => {
    console.log(`integrations-service listening on :${config.port}`)
  })
}

start().catch((err) => {
  console.error(err)
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
