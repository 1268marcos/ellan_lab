export function nextRetryAt(retryCount) {
  const now = Date.now()
  const delaysSec = [15, 60, 300, 900, 900]
  const idx = Math.min(Math.max(retryCount - 1, 0), delaysSec.length - 1)
  return new Date(now + delaysSec[idx] * 1000)
}

export function backoffDelayMs(retryCount, baseMs = 1000) {
  const exp = Math.min(retryCount, 8)
  return Math.min(baseMs * 2 ** exp, 3_600_000)
}
