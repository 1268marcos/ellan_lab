import { config } from '../config.js'
import { logger } from './logger.js'

export async function releaseLockerSlot({ regionCode, lockerId, slot, allocationId }) {
  const headers = { 'Content-Type': 'application/json' }
  if (config.lifecycleRuntimeToken) {
    headers.Authorization = `Bearer ${config.lifecycleRuntimeToken}`
    headers['X-Internal-Token'] = config.lifecycleRuntimeToken
  }
  const base = config.lifecycleRuntimeUrl
  const results = { release_ok: false, set_state_ok: false }

  if (slot != null && regionCode && lockerId) {
    try {
      const url = `${base}/api/v1/runtime/${encodeURIComponent(regionCode)}/lockers/${encodeURIComponent(lockerId)}/slots/${slot}/state`
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ state: 'AVAILABLE' }),
      })
      results.set_state_ok = res.ok
      if (!res.ok) {
        logger.warn('runtime_set_state_failed', { status: res.status, url })
      }
    } catch (err) {
      logger.warn('runtime_set_state_error', { error: String(err) })
    }
  }

  if (allocationId && regionCode) {
    try {
      const url = `${base}/api/v1/runtime/${encodeURIComponent(regionCode)}/allocations/${encodeURIComponent(allocationId)}/release`
      const res = await fetch(url, { method: 'POST', headers })
      results.release_ok = res.ok
      if (!res.ok) {
        logger.warn('runtime_release_failed', { status: res.status, url })
      }
    } catch (err) {
      logger.warn('runtime_release_error', { error: String(err) })
    }
  }

  return results
}
