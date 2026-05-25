const INTEGRATIONS_TARGET = process.env.INTEGRATIONS_SERVICE_PROXY ?? 'http://localhost:8128'

const TENANT_PARTNER_PATH =
  /^\/api\/v1\/partners\/[^/]+\/(apikey|eligible-lockers|check-compatibility|webhooks)(\/|$)/

export function integrationsProxyBypass(req) {
  const url = req.url || ''
  if (url.startsWith('/api/v1/partners/login')) return url
  if (TENANT_PARTNER_PATH.test(url)) return url
  if (req.method === 'POST' && (url === '/api/v1/partners' || url.startsWith('/api/v1/partners?'))) return url
  return null
}

export function integrationsViteProxies() {
  return {
    '/api/v1/marketplaces': { target: INTEGRATIONS_TARGET, changeOrigin: true },
    '/api/v1/carriers/rates': { target: INTEGRATIONS_TARGET, changeOrigin: true },
    '/api/v1/partners/webhook': { target: INTEGRATIONS_TARGET, changeOrigin: true },
    '/api/v1/partners': {
      target: INTEGRATIONS_TARGET,
      changeOrigin: true,
      bypass: integrationsProxyBypass,
    },
  }
}
