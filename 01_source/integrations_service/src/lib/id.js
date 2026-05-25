import crypto from 'crypto'

export function newId() {
  return crypto.randomUUID()
}

export function isUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(String(value || ''))
}

export function isEcosystemPartnerId(id) {
  if (!id) return false
  if (isUuid(id)) return false
  return id.startsWith('eco-') || id.startsWith('mcp-') || id.startsWith('net-')
}
