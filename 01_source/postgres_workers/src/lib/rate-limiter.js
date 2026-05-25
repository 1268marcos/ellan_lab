export class RateLimiter {
  constructor(rps) {
    this.minIntervalMs = rps > 0 ? Math.ceil(1000 / rps) : 0
    this.nextAllowedAt = 0
  }

  async wait() {
    if (this.minIntervalMs <= 0) return
    const now = Date.now()
    const waitMs = this.nextAllowedAt - now
    if (waitMs > 0) {
      await new Promise((r) => setTimeout(r, waitMs))
    }
    this.nextAllowedAt = Date.now() + this.minIntervalMs
  }
}
