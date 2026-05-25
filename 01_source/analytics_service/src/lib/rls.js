export async function buildRLSContext(db, { userId, tenantId, role }) {
  await db.query(`SELECT set_config('app.current_tenant_id', $1, false)`, [
    tenantId ? String(tenantId) : '',
  ])
  await db.query(`SELECT set_config('app.current_user_id', $1, false)`, [userId ? String(userId) : ''])
  await db.query(`SELECT set_config('app.user_role', $1, false)`, [role ? String(role) : ''])
}

export async function clearRLSContext(db) {
  await db.query(`RESET app.current_tenant_id`)
  await db.query(`RESET app.current_user_id`)
  await db.query(`RESET app.user_role`)
}

export function attachDbClient(pool) {
  return async function dbClientMiddleware(req, res, next) {
    let client
    try {
      client = await pool.connect()
      req.db = client
      const release = () => {
        if (!client) return
        const c = client
        client = null
        clearRLSContext(c)
          .catch(() => {})
          .finally(() => c.release())
      }
      res.on('finish', release)
      res.on('close', release)
      next()
    } catch (err) {
      if (client) client.release()
      next(err)
    }
  }
}
