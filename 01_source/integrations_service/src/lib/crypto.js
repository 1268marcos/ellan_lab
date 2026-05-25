import crypto from 'crypto'

export function hashSecret(secret) {
  return crypto.createHash('sha256').update(String(secret)).digest('hex')
}

export function buildHmacSignature(secret, payloadBytes) {
  const digest = crypto.createHmac('sha256', secret).update(payloadBytes).digest('hex')
  return `sha256=${digest}`
}

export function verifyHmacSignature(secret, payloadBytes, signatureHeader) {
  if (!secret || !signatureHeader) return false
  const expected = buildHmacSignature(secret, payloadBytes)
  const received = String(signatureHeader).trim()
  try {
    return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(received))
  } catch {
    return false
  }
}
