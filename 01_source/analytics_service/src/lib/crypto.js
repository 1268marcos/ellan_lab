import { createHash } from 'crypto'
import { config } from '../config.js'

export function hashSessionToken(raw) {
  return createHash('sha256').update(String(raw), 'utf8').digest('hex')
}

export function hashApiKey(raw) {
  return createHash('sha256').update(`${config.apiKeyPepper}:${raw}`, 'utf8').digest('hex')
}
