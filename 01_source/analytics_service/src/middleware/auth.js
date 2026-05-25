import { jwtVerify } from 'jose'
import { config } from '../config.js'
import { hashSessionToken } from '../lib/crypto.js'
import { cacheGet, cacheSet } from '../lib/redis.js'
import { buildRLSContext } from '../lib/rls.js'
import { resolvePrimaryRole, resolveTenantId, resolveUserRoles } from '../lib/permissions.js'
import { writeSecurityAudit } from '../lib/audit.js'

const JWT_SECRET = new TextEncoder().encode(config.jwtSecret)

function parseBearer(req) {
  const header = String(req.headers.authorization || '')
  const match = header.match(/^Bearer\s+(.+)$/i)
  return match ? match[1].trim() : null
}

async function verifyJwtToken(token) {
  const { payload } = await jwtVerify(token, JWT_SECRET, { algorithms: [config.jwtAlg] })
  const userId = payload.sub || payload.user_id || payload.userId
  if (!userId) throw new Error('jwt_missing_sub')
  const roles = normalizeRoles(payload.roles ?? payload.role)
  return {
    userId: String(userId),
    tenantId: payload.tenant_id ? String(payload.tenant_id) : null,
    roles,
    primaryRole: roles[0] || null,
    authMethod: 'JWT',
  }
}

function normalizeRoles(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw.map((r) => String(r).trim()).filter(Boolean)
  return [String(raw).trim()].filter(Boolean)
}

async function verifySessionToken(db, token) {
  const tokenHash = hashSessionToken(token)
  const { rows } = await db.query(
    `SELECT s.user_id::text AS user_id
     FROM auth_sessions s
     INNER JOIN users u ON u.id::text = s.user_id::text
     WHERE s.session_token_hash = $1
       AND s.revoked_at IS NULL
       AND s.expires_at > NOW()
       AND u.is_active = true
       AND u.deleted_at IS NULL
       AND u.anonymized_at IS NULL
     LIMIT 1`,
    [tokenHash],
  )
  if (!rows.length) throw new Error('session_invalid')
  const userId = rows[0].user_id
  const roles = await resolveUserRoles(db, userId)
  const primaryRole = roles[0] || (await resolvePrimaryRole(db, userId))
  const tenantId = await resolveTenantId(db, userId, null)
  return { userId, tenantId, roles: roles.length ? roles : [primaryRole], primaryRole, authMethod: 'SESSION' }
}

async function hydrateContext(db, base, req) {
  const tenantHint = req.headers['x-tenant-id'] || base.tenantId
  const tenantId = await resolveTenantId(db, base.userId, tenantHint)
  let roles = base.roles?.length ? base.roles : []
  if (!roles.length) roles = await resolveUserRoles(db, base.userId)
  const primaryRole = base.primaryRole || roles[0] || (await resolvePrimaryRole(db, base.userId))
  if (!roles.length) roles = [primaryRole]
  return { ...base, tenantId, roles, primaryRole }
}

async function applyAuthContext(req, ctx) {
  req.auth = {
    userId: ctx.userId,
    tenantId: ctx.tenantId,
    roles: ctx.roles,
    role: ctx.primaryRole,
    authMethod: ctx.authMethod,
  }
  if (req.db) {
    await buildRLSContext(req.db, {
      userId: ctx.userId,
      tenantId: ctx.tenantId,
      role: ctx.primaryRole,
    })
  }
}

async function deny(req, res, detail, status = 401) {
  if (req.db) {
    try {
      await writeSecurityAudit(req.db, {
        actorId: req.auth?.userId || null,
        actorRole: req.auth?.role || null,
        action: 'ACCESS_DENIED',
        targetType: 'Auth',
        targetId: detail,
        ipAddress: req.ip || req.headers['x-forwarded-for'] || null,
        userAgent: req.headers['user-agent'] || null,
        newState: { status, path: req.path, method: req.method },
      })
    } catch {
      /* ignore */
    }
  }
  return res.status(status).json({ error: status === 403 ? 'forbidden' : 'unauthorized', detail })
}

export async function requireJwtAuth(req, res, next) {
  if (!req.db) return res.status(500).json({ error: 'db_client_missing' })

  const token = parseBearer(req)
  if (!token) return deny(req, res, 'missing_bearer_token')

  const cacheKey = `auth:ctx:${hashSessionToken(token).slice(0, 32)}`
  const cached = await cacheGet(cacheKey)
  if (cached) {
    await applyAuthContext(req, cached)
    return next()
  }

  try {
    let ctx
    if (token.split('.').length === 3) {
      try {
        ctx = await verifyJwtToken(token)
      } catch {
        ctx = await verifySessionToken(req.db, token)
      }
    } else {
      ctx = await verifySessionToken(req.db, token)
    }
    ctx = await hydrateContext(req.db, ctx, req)
    await cacheSet(cacheKey, ctx, config.sessionCacheTtlSec)
    await applyAuthContext(req, ctx)
    return next()
  } catch (err) {
    return deny(req, res, String(err.message || 'invalid_token'))
  }
}

export async function optionalJwtAuth(req, res, next) {
  const token = parseBearer(req)
  if (!token) return next()
  return requireJwtAuth(req, res, next)
}
