import { createClient } from 'redis'
import { config } from '../config.js'

let client = null
let connectPromise = null

export async function getRedis() {
  if (!config.redisEnabled) return null
  if (client?.isOpen) return client
  if (!connectPromise) {
    client = createClient({ url: config.redisUrl })
    client.on('error', (err) => console.error('[redis]', err.message))
    connectPromise = client.connect().catch((err) => {
      console.warn('[redis] unavailable:', err.message)
      client = null
      connectPromise = null
      return null
    })
  }
  await connectPromise
  return client?.isOpen ? client : null
}

export async function cacheGet(key) {
  const r = await getRedis()
  if (!r) return null
  try {
    const raw = await r.get(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export async function cacheSet(key, value, ttlSeconds) {
  const r = await getRedis()
  if (!r) return
  try {
    await r.setEx(key, ttlSeconds, JSON.stringify(value))
  } catch {
    /* ignore */
  }
}
