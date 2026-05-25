import { Router } from 'express'
import { query } from '../lib/db.js'
import { buildHmacSignature, hashSecret, verifyHmacSignature } from '../lib/crypto.js'
import { config } from '../config.js'
import { newId } from '../lib/id.js'

const router = Router()

router.post('/test', async (req, res, next) => {
  try {
    const {
      ecosystem_player_id,
      player_code,
      capability_code,
      url,
      secret,
      payload,
      verify_inbound_signature,
      signature_header,
    } = req.body || {}

    let webhook = null
    if (ecosystem_player_id || player_code) {
      const { rows } = await query(
        `SELECT w.* FROM partner_capability_webhooks w
         JOIN partner_ecosystem_players p ON p.id = w.ecosystem_player_id
         WHERE ($1::text IS NULL OR w.ecosystem_player_id = $1)
           AND ($2::text IS NULL OR p.code = $2)
           AND ($3::text IS NULL OR w.capability_code = $3)
           AND w.active = true
         ORDER BY w.updated_at DESC LIMIT 1`,
        [ecosystem_player_id || null, player_code || null, capability_code || null],
      )
      webhook = rows[0]
    }

    const targetUrl = url || webhook?.url
    if (!targetUrl) {
      res.status(400).json({ detail: 'url_or_webhook_required' })
      return
    }

    const secretVal = secret || webhook?.secret_key || `whsec_test_${Date.now()}`
    const bodyObj = payload || {
      event: 'webhook.test',
      player_code: player_code || webhook?.player_code,
      capability_code: capability_code || webhook?.capability_code,
      sent_at: new Date().toISOString(),
    }
    const body = JSON.stringify(bodyObj)
    const signature = buildHmacSignature(secretVal, Buffer.from(body, 'utf8'))

    if (verify_inbound_signature && signature_header) {
      const ok = verifyHmacSignature(secretVal, Buffer.from(body, 'utf8'), signature_header)
      if (!ok) {
        res.status(401).json({ detail: 'invalid_signature' })
        return
      }
    }

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), config.webhookTestTimeoutMs)
    let httpStatus = 0
    let responseText = ''
    try {
      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Ellan-Event': 'webhook.test',
          'X-Ellan-Signature': signature,
        },
        body,
        signal: controller.signal,
      })
      httpStatus = response.status
      responseText = (await response.text()).slice(0, 500)
    } catch (err) {
      httpStatus = 0
      responseText = String(err.message || err).slice(0, 500)
    } finally {
      clearTimeout(timer)
    }

    if (webhook) {
      const ok = httpStatus >= 200 && httpStatus < 300
      await query(
        `INSERT INTO partner_capability_webhook_deliveries (
          id, webhook_id, event_type, payload_json, http_status, success, response_snippet, created_at
        ) VALUES ($1,$2,'webhook.test',$3,$4,$5,$6,NOW())`,
        [newId(), webhook.id, body, httpStatus || null, ok, responseText],
      )
      await query(
        `UPDATE partner_capability_webhooks SET last_http_status = $2, last_delivered_at = NOW(), last_error = $3, updated_at = NOW()
         WHERE id = $1`,
        [webhook.id, httpStatus || null, httpStatus >= 200 && httpStatus < 300 ? null : responseText],
      )
    }

    const signatureValid = verifyHmacSignature(secretVal, Buffer.from(body, 'utf8'), signature)
    res.json({
      ok: httpStatus >= 200 && httpStatus < 300,
      http_status: httpStatus,
      signature,
      signature_valid: signatureValid,
      response_preview: responseText,
      webhook_id: webhook?.id || null,
    })
  } catch (err) {
    next(err)
  }
})

router.post('/verify-signature', (req, res) => {
  const { secret, payload, signature } = req.body || {}
  if (!secret || !payload || !signature) {
    res.status(400).json({ detail: 'secret_payload_signature_required' })
    return
  }
  const bytes = Buffer.from(typeof payload === 'string' ? payload : JSON.stringify(payload), 'utf8')
  const valid = verifyHmacSignature(secret, bytes, signature)
  res.json({ valid, expected: buildHmacSignature(secret, bytes) })
})

export { hashSecret }
export default router
