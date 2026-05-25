import http from 'node:http'
import cors from 'cors'
import express from 'express'
import { config } from './config.js'
import { pool } from './lib/db.js'
import { ensureSchema } from './db/migrate.js'
import lockersRouter from './routes/lockers.js'
import alertsRouter from './routes/alerts.js'
import { attachWebSockets } from './ws/realtime.js'

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
  res.json({ status: 'ok', service: 'ops-lockers-service' })
})

app.get('/api/v1/ops/health', (_req, res) => {
  res.json({ status: 'ok', service: 'ops-lockers-service', version: 'v1' })
})

app.use('/api/v1/ops', lockersRouter)
app.use('/api/v1/ops', alertsRouter)

app.use((err, _req, res, _next) => {
  console.error('[ops-lockers-service]', err)
  res.status(500).json({ detail: 'internal_error', message: err.message })
})

async function start() {
  await pool.query('SELECT 1')
  await ensureSchema()

  const server = http.createServer(app)
  attachWebSockets(server)

  server.listen(config.port, () => {
    console.log(`ops-lockers-service listening on :${config.port}`)
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
