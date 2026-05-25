const perPartner = new Map()

export function getRateLimit(partnerId, defaultPerMinute) {
  const row = perPartner.get(partnerId)
  return row?.limitPerMinute ?? defaultPerMinute
}

export function setRateLimit(partnerId, limitPerMinute) {
  perPartner.set(partnerId, {
    limitPerMinute: Math.max(1, Math.min(10000, Number(limitPerMinute) || 60)),
    updatedAt: new Date().toISOString(),
  })
}

export function listRateLimits() {
  return Object.fromEntries(perPartner.entries())
}

const buckets = new Map()

export function checkRateLimit(partnerId, limitPerMinute) {
  const now = Date.now()
  const windowMs = 60_000
  let bucket = buckets.get(partnerId)
  if (!bucket || now - bucket.windowStart >= windowMs) {
    bucket = { windowStart: now, count: 0 }
    buckets.set(partnerId, bucket)
  }
  bucket.count += 1
  if (bucket.count > limitPerMinute) {
    const retryAfter = Math.ceil((bucket.windowStart + windowMs - now) / 1000)
    return { allowed: false, retryAfterSec: Math.max(1, retryAfter) }
  }
  return { allowed: true, remaining: limitPerMinute - bucket.count }
}
