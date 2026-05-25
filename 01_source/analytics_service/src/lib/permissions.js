export function permissionMatches(granted, required) {
  const g = String(granted || '').trim()
  const r = String(required || '').trim()
  if (!g || !r) return false
  if (g === '*' || g === r) return true
  if (g.endsWith('.*')) {
    const prefix = g.slice(0, -2)
    return r === prefix || r.startsWith(`${prefix}.`)
  }
  return false
}

export function hasPermission(grantedList, required) {
  const list = Array.isArray(grantedList) ? grantedList : []
  return list.some((g) => permissionMatches(g, required))
}

export async function loadUserPermissions(db, userId) {
  const { rows } = await db.query(
    `SELECT DISTINCT sp.object_key
     FROM security_permissions sp
     INNER JOIN security_permission_memberships spm ON spm.group_id = sp.group_id
     WHERE spm.user_id = $1`,
    [userId],
  )
  return rows.map((r) => r.object_key)
}

export async function resolvePrimaryRole(db, userId) {
  const { rows } = await db.query(
    `SELECT role
     FROM user_roles
     WHERE user_id = $1
       AND COALESCE(is_active, true) = true
       AND revoked_at IS NULL
     ORDER BY granted_at DESC NULLS LAST, id DESC
     LIMIT 1`,
    [userId],
  )
  return rows[0]?.role || 'usuario_comum'
}

export async function resolveUserRoles(db, userId) {
  const { rows } = await db.query(
    `SELECT role
     FROM user_roles
     WHERE user_id = $1
       AND COALESCE(is_active, true) = true
       AND revoked_at IS NULL`,
    [userId],
  )
  return rows.map((r) => r.role).filter(Boolean)
}

export async function resolveTenantId(db, userId, hint) {
  if (hint) return String(hint)
  const link = await db.query(
    `SELECT entity_id
     FROM user_domain_links
     WHERE user_id = $1 AND is_primary = true
     ORDER BY created_at DESC
     LIMIT 1`,
    [userId],
  )
  if (link.rows[0]?.entity_id) return String(link.rows[0].entity_id)
  const roleScope = await db.query(
    `SELECT scope_id
     FROM user_roles
     WHERE user_id = $1
       AND scope_type ILIKE 'tenant'
       AND scope_id IS NOT NULL
       AND COALESCE(is_active, true) = true
       AND revoked_at IS NULL
     LIMIT 1`,
    [userId],
  )
  return roleScope.rows[0]?.scope_id ? String(roleScope.rows[0].scope_id) : null
}
