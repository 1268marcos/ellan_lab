import { hashApiKey } from '../lib/crypto.js'
import { buildRLSContext } from '../lib/rls.js'
import { resolvePrimaryRole, resolveTenantId, resolveUserRoles } from '../lib/permissions.js'
import { writeSecurityAudit } from '../lib/audit.js'

function parseScopes(scopesJson) {
  try {
    const parsed = JSON.parse(scopesJson || '[]')
    return Array.isArray(parsed) ? parsed.map((s) => String(s)) : []
  } catch {
    return []
  }
}

function scopeAllows(scopes, required) {
  if (!required) return true
  return scopes.includes('*') || scopes.includes(required)
}

async function deny(req, res, detail, status = 401) {
  if (req.db) {
    try {
      await writeSecurityAudit(req.db, {
        actorId: req.auth?.userId || null,
        actorRole: req.auth?.role || null,
        action: 'ACCESS_DENIED',
        targetType: 'ApiKey',
        targetId: detail,
        ipAddress: req.ip || req.headers['x-forwarded-for'] || null,
        userAgent: req.headers['user-agent'] || null,
        newState: { status, path: req.path },
      })
    } catch {
      /* ignore */
    }
  }
  return res.status(status).json({ error: status === 403 ? 'forbidden' : 'unauthorized', detail })
}

export function requireApiKey(requiredScope = null) {
  return async function apiKeyMiddleware(req, res, next) {
    if (!req.db) return res.status(500).json({ error: 'db_client_missing' })

    const rawKey = String(req.headers['x-api-key'] || '').trim()
    if (!rawKey) return deny(req, res, 'missing_api_key')

    const keyHash = hashApiKey(rawKey)
    const prefix = rawKey.slice(0, 16)

    const { rows } = await req.db.query(
      `SELECT id, user_id, scopes_json, expires_at, revoked_at
       FROM security_api_keys
       WHERE key_hash = $1
         AND key_prefix = $2
         AND revoked_at IS NULL
       LIMIT 1`,
      [keyHash, prefix],
    )

    if (!rows.length) return deny(req, res, 'invalid_api_key')

    const row = rows[0]
    if (row.expires_at && new Date(row.expires_at).getTime() <= Date.now()) {
      return deny(req, res, 'api_key_expired')
    }

    const scopes = parseScopes(row.scopes_json)
    if (!scopeAllows(scopes, requiredScope)) {
      return deny(req, res, 'insufficient_api_key_scope', 403)
    }

    const userId = String(row.user_id)
    const roles = await resolveUserRoles(req.db, userId)
    const primaryRole = roles[0] || (await resolvePrimaryRole(req.db, userId))
    const tenantId = await resolveTenantId(req.db, userId, req.headers['x-tenant-id'])

    req.auth = {
      userId,
      tenantId,
      roles: roles.length ? roles : [primaryRole],
      role: primaryRole,
      authMethod: 'API_KEY',
      apiKeyId: row.id,
      scopes,
    }

    await buildRLSContext(req.db, { userId, tenantId, role: primaryRole })

    req.db
      .query(`UPDATE security_api_keys SET last_used_at = NOW() WHERE id = $1`, [row.id])
      .catch(() => {})

    return next()
  }
}

export function requireApiKeyOrJwt(requiredScope = null) {
  return async function combinedAuth(req, res, next) {
    if (String(req.headers['x-api-key'] || '').trim()) {
      return requireApiKey(requiredScope)(req, res, next)
    }
    const { requireJwtAuth } = await import('./auth.js')
    return requireJwtAuth(req, res, next)
  }
}
