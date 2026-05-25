import { cacheGet, cacheSet } from '../lib/redis.js'
import { config } from '../config.js'
import { hasPermission, loadUserPermissions } from '../lib/permissions.js'
import { writeSecurityAudit } from '../lib/audit.js'

const ADMIN_ROLES = new Set([
  'admin_operacao',
  'admin.financeiro',
  'admin.operacao',
  'admin_operacao_global',
  'super_admin',
])

async function deny(req, res, permission, status = 403) {
  if (req.db) {
    try {
      await writeSecurityAudit(req.db, {
        actorId: req.auth?.userId || null,
        actorRole: req.auth?.role || null,
        action: 'ACCESS_DENIED',
        targetType: 'Permission',
        targetId: permission,
        ipAddress: req.ip || req.headers['x-forwarded-for'] || null,
        userAgent: req.headers['user-agent'] || null,
        newState: { path: req.path, method: req.method, roles: req.auth?.roles },
      })
    } catch {
      /* ignore */
    }
  }
  return res.status(status).json({ error: 'forbidden', detail: `missing_permission:${permission}` })
}

async function getGrantedPermissions(req) {
  if (!req.auth?.userId) return []
  if (req.auth.scopes?.includes?.('*') || req.auth.scopes?.length) {
    const scopes = req.auth.scopes
    if (scopes.includes('*')) return ['*']
    return scopes
  }

  const cacheKey = `rbac:perms:${req.auth.userId}`
  const cached = await cacheGet(cacheKey)
  if (cached) return cached

  const perms = await loadUserPermissions(req.db, req.auth.userId)
  await cacheSet(cacheKey, perms, config.permissionCacheTtlSec)
  return perms
}

export function requirePermission(permission) {
  return async function rbacMiddleware(req, res, next) {
    if (!req.auth?.userId) {
      return res.status(401).json({ error: 'unauthorized', detail: 'auth_required' })
    }

    const roles = req.auth.roles || [req.auth.role].filter(Boolean)
    if (roles.some((r) => ADMIN_ROLES.has(r))) return next()

    const granted = await getGrantedPermissions(req)
    if (hasPermission(granted, permission)) return next()

    return deny(req, res, permission)
  }
}

export function requireAnyPermission(...permissions) {
  return async function rbacAnyMiddleware(req, res, next) {
    if (!req.auth?.userId) {
      return res.status(401).json({ error: 'unauthorized', detail: 'auth_required' })
    }

    const roles = req.auth.roles || [req.auth.role].filter(Boolean)
    if (roles.some((r) => ADMIN_ROLES.has(r))) return next()

    const granted = await getGrantedPermissions(req)
    if (permissions.some((p) => hasPermission(granted, p))) return next()

    return deny(req, res, permissions.join('|'))
  }
}
