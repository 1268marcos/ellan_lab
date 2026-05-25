import { randomUUID } from 'crypto'

export async function writeSecurityAudit(
  db,
  {
    actorId = null,
    actorRole = null,
    action,
    targetType,
    targetId,
    oldState = null,
    newState = null,
    ipAddress = null,
    userAgent = null,
  },
) {
  await db.query(
    `INSERT INTO security_audit_logs (
       id, actor_id, actor_role, action, target_type, target_id,
       old_state_json, new_state_json, ip_address, user_agent, occurred_at
     ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())`,
    [
      randomUUID(),
      actorId,
      actorRole,
      action,
      targetType,
      targetId,
      oldState ? JSON.stringify(oldState) : null,
      newState ? JSON.stringify(newState) : null,
      ipAddress,
      userAgent,
    ],
  )
}
