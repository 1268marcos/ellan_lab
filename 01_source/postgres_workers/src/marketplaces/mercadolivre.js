import { config } from '../config.js'

export async function syncStock(row) {
  const url = config.marketplace.MERCADO_LIVRE.syncUrl
  if (!url) {
    return { ok: true, simulated: true, marketplace: 'MERCADO_LIVRE' }
  }
  const body = {
    item_id: row.product_id,
    available_quantity: row.quantity_available,
    payload: JSON.parse(row.payload_json || '{}'),
  }
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Marketplace': 'MERCADO_LIVRE' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`mercado_livre_sync_${res.status}:${text.slice(0, 200)}`)
  }
  return { ok: true, http_status: res.status, marketplace: 'MERCADO_LIVRE' }
}
