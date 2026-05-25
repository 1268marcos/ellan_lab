import { randomUUID } from 'crypto'

export async function enqueueUserNotification(
  client,
  { userId, orderId, templateKey, dedupeKey, payload },
) {
  if (!userId && !orderId) return null
  const key = dedupeKey || `${templateKey}:${orderId || userId}:${randomUUID()}`
  const existing = await client.query(
    `SELECT id FROM notification_logs WHERE dedupe_key = $1 LIMIT 1`,
    [key],
  )
  if (existing.rowCount > 0) return existing.rows[0].id

  const now = new Date()
  const res = await client.query(
    `INSERT INTO notification_logs (
      user_id, order_id, channel, template_key, destination_masked,
      dedupe_key, status, attempt_count, payload_json, created_at, next_attempt_at
    ) VALUES ($1, $2, 'EMAIL', $3, $4, $5, 'QUEUED', 0, $6::json, $7, $7)
    RETURNING id`,
    [
      userId || null,
      orderId || null,
      templateKey,
      'masked@ellan.local',
      key,
      JSON.stringify(payload ?? {}),
      now,
    ],
  )
  return res.rows[0]?.id
}
