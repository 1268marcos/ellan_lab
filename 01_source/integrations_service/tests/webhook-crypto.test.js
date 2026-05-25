import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { buildHmacSignature, verifyHmacSignature } from '../src/lib/crypto.js'

describe('HMAC-SHA256 webhook', () => {
  it('builds and verifies signature', () => {
    const secret = 'whsec_test'
    const body = Buffer.from(JSON.stringify({ event: 'webhook.test' }), 'utf8')
    const sig = buildHmacSignature(secret, body)
    assert.ok(sig.startsWith('sha256='))
    assert.equal(verifyHmacSignature(secret, body, sig), true)
    assert.equal(verifyHmacSignature(secret, body, 'sha256=dead'), false)
  })
})
