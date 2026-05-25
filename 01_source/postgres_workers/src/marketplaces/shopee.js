import { config } from '../config.js'

export async function syncStock(row) {
  const url = config.marketplace.SHOPEE.syncUrl
  if (!url) {
    return { ok: true, simulated: true, marketplace: 'SHOPEE' }
  }
  const body = {
    product_id: row.product_id,
    locker_id: row.locker_id,
    quantity_available: row.quantity_available,
    operation: row.operation,
  }
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Marketplace': 'SHOPEE' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`shopee_sync_${res.status}:${text.slice(0, 200)}`)
  }
  return { ok: true, http_status: res.status, marketplace: 'SHOPEE' }
}
