import { loadAuth } from './auth'

/** Headers para APIs com enforcement de tabelas críticas (sem RLS nativo). */
export function opsActorHeaders(): Record<string, string> {
  const auth = loadAuth()
  const profile = auth?.profile ?? 'ops'
  const role =
    profile === 'admin' || profile === 'ops' ? 'admin_operacao' : 'usuario_comum'
  const headers: Record<string, string> = {
    'X-Actor-Roles': role,
    'X-Service-Name': 'frontend_v1_ops',
  }
  if (auth?.partnerId) {
    headers['X-Actor-Id'] = auth.partnerId
  }
  return headers
}

export function needsOpsActorHeaders(url: string): boolean {
  return (
    url.includes('/partner-admin/') ||
    url.includes('/privacy-compliance-admin/')
  )
}
