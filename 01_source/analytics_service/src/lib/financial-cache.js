import { cacheGet, cacheSet } from './redis.js'

export const FINANCIAL_CACHE_TTL_SEC = 300

export async function cachedQuery(key, fetcher, ttlSec = FINANCIAL_CACHE_TTL_SEC) {
  const hit = await cacheGet(key)
  if (hit !== null && hit !== undefined) {
    return { data: hit, cache: 'hit' }
  }
  const data = await fetcher()
  await cacheSet(key, data, ttlSec)
  return { data, cache: 'miss' }
}

export function cacheKey(prefix, parts = {}) {
  const tail = Object.entries(parts)
    .filter(([, v]) => v != null && v !== '')
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join('&')
  return tail ? `fin:${prefix}:${tail}` : `fin:${prefix}`
}
