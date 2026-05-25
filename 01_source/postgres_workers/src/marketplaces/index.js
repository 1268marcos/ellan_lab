import * as shopee from './shopee.js'
import * as magalu from './magalu.js'
import * as mercadolivre from './mercadolivre.js'

const adapters = {
  SHOPEE: shopee,
  MAGALU: magalu,
  MERCADO_LIVRE: mercadolivre,
}

export function getMarketplaceAdapter(code) {
  const key = String(code || '').toUpperCase()
  const adapter = adapters[key]
  if (!adapter) throw new Error(`UNSUPPORTED_MARKETPLACE:${code}`)
  return adapter
}
