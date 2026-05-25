import { config } from '../../config.js'

const ADMIN_ROLES = new Set([
  'admin_operacao',
  'admin.financeiro',
  'admin.operacao',
  'admin_operacao_global',
  'super_admin',
])

export function requireAdmin(req, res, next) {
  const rolesHeader = String(req.headers['x-actor-roles'] || '')
  const roles = rolesHeader
    .split(',')
    .map((r) => r.trim())
    .filter(Boolean)

  if (roles.some((r) => ADMIN_ROLES.has(r))) {
    return next()
  }

  const apiKey = String(req.headers['x-api-key'] || '')
  const bearer = String(req.headers.authorization || '').replace(/^Bearer\s+/i, '')
  if (apiKey && apiKey === config.adminApiKey) return next()
  if (bearer && bearer === config.adminApiKey) return next()

  return res.status(403).json({
    error: 'forbidden',
    detail: 'Admin role or valid API key required',
  })
}

export function requireAuthenticated(req, res, next) {
  const rolesHeader = String(req.headers['x-actor-roles'] || '')
  const apiKey = String(req.headers['x-api-key'] || '')
  const bearer = String(req.headers.authorization || '').replace(/^Bearer\s+/i, '')

  if (rolesHeader || apiKey || bearer) {
    return next()
  }

  return res.status(401).json({
    error: 'unauthorized',
    detail: 'Authentication headers required',
  })
}
