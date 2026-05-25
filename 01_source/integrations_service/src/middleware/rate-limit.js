import { config } from '../config.js'
import { checkRateLimit, getRateLimit } from '../lib/rate-limit-store.js'
import { isEcosystemPartnerId } from '../lib/id.js'

function partnerIdFromPath(path) {
  const m = path.match(/^\/api\/v1\/partners\/([^/]+)/)
  return m ? m[1] : null
}

export function rateLimitMiddleware(req, res, next) {
  const path = req.originalUrl || req.url || ''
  if (path.startsWith('/health') || path.endsWith('/health')) {
    next()
    return
  }
  const partnerId = partnerIdFromPath(path) || req.headers['x-partner-id']
  const key = partnerId && (isEcosystemPartnerId(partnerId) || path.includes('/capabilities')) ? partnerId : 'global'
  const limit = getRateLimit(key, config.defaultRateLimitPerMinute)
  const result = checkRateLimit(key, limit)
  res.setHeader('X-RateLimit-Limit', String(limit))
  if (!result.allowed) {
    res.setHeader('Retry-After', String(result.retryAfterSec))
    res.status(429).json({ detail: 'rate_limit_exceeded', retry_after_sec: result.retryAfterSec })
    return
  }
  res.setHeader('X-RateLimit-Remaining', String(result.remaining))
  next()
}
