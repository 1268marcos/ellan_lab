import { config } from '../config.js'

export async function syncStock(row) {
  const url = config.marketplace.MAGALU.syncUrl
  if (!url) {
    return { ok: true, simulated: true, marketplace: 'MAGALU' }
  }
  const body = {
    sku: row.product_id,
    available_quantity: row.quantity_available,
    locker_id: row.locker_id,
  }
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'X-Marketplace': 'MAGALU' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`magalu_sync_${res.status}:${text.slice(0, 200)}`)
  }
  return { ok: true, http_status: res.status, marketplace: 'MAGALU' }
}
