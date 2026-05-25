import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'
import { partnerAdminApi, type UserRole, type UserSummary } from '../../api/partnerAdmin'
import {
  securityAdminApi,
  type AuditLogRow,
  type DomainLink,
  type PermissionGroup,
  type SecurityApiKeyMeta,
  type SecuritySummary,
  type SecurityWebhook,
  type LockerPlayer,
  type UserPlayerAccess,
} from '../../api/securityAdmin'

const TABS = [
  'overview',
  'intelligence',
  'access-review',
  'alerts',
  'compliance',
  'templates',
  'matrix',
  'domains',
  'ecosystem',
  'locker-players',
  'users',
  'user-360',
  'roles',
  'role-catalog',
  'permissions',
  'grants',
  'webhooks',
  'deliveries',
  'api-keys',
  'sessions',
  'identity',
  'policy',
  'audit',
  'cross-domain',
] as const
type Tab = (typeof TABS)[number]

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Visão geral',
  intelligence: 'Inteligência OPS',
  'access-review': 'Revisão de acesso',
  alerts: 'Alertas',
  compliance: 'Compliance',
  templates: 'Templates onboarding',
  matrix: 'Matriz acesso',
  domains: 'Domínios OPS',
  ecosystem: 'Ecossistema',
  'locker-players': 'Players locker mundial',
  users: 'Usuários',
  'user-360': 'Usuário 360°',
  roles: 'Papéis',
  'role-catalog': 'Catálogo roles',
  permissions: 'Permissões',
  grants: 'Grants',
  webhooks: 'Webhooks',
  deliveries: 'Entregas WH',
  'api-keys': 'API keys',
  sessions: 'Sessões',
  identity: 'Identity / SSO',
  policy: 'Policy',
  audit: 'Auditoria',
  'cross-domain': 'Links legado',
}

const ROLES = ['admin_operacao', 'suporte', 'auditoria', 'usuario_comum']

export default function OpsUsersSecurityAdmin() {
  const { tab, setTab } = useOpsTabFromUrl<Tab>('/ops/access/security-admin', TABS, 'overview')
  const [summary, setSummary] = useState<SecuritySummary | null>(null)
  const [users, setUsers] = useState<UserSummary[]>([])
  const [roles, setRoles] = useState<UserRole[]>([])
  const [groups, setGroups] = useState<PermissionGroup[]>([])
  const [webhooks, setWebhooks] = useState<SecurityWebhook[]>([])
  const [apiKeys, setApiKeys] = useState<SecurityApiKeyMeta[]>([])
  const [audit, setAudit] = useState<AuditLogRow[]>([])
  const [links, setLinks] = useState<DomainLink[]>([])
  const [lockerPlayers, setLockerPlayers] = useState<LockerPlayer[]>([])
  const [userPlayerAccess, setUserPlayerAccess] = useState<UserPlayerAccess[]>([])
  const [intel, setIntel] = useState<Awaited<ReturnType<typeof securityAdminApi.intelligence>>['data'] | null>(null)
  const [alerts, setAlerts] = useState<Array<{ id: string; title: string; severity: string }>>([])
  const [templates, setTemplates] = useState<Array<{ code: string; name: string }>>([])
  const [campaigns, setCampaigns] = useState<Array<{ id: string; name: string; status: string; pending_items: number }>>([])
  const [compliance, setCompliance] = useState<{ items: unknown[]; coverage_pct: number } | null>(null)
  const [matrix, setMatrix] = useState<{ users: string[]; domains: string[]; cells: unknown[] } | null>(null)
  const [userForm, setUserForm] = useState({ full_name: '', email: '' })
  const [roleUserId, setRoleUserId] = useState('')
  const [roleName, setRoleName] = useState('suporte')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (tab === 'intelligence') {
        const i = await securityAdminApi.intelligence()
        setIntel(i.data)
      } else if (tab === 'alerts') {
        const a = await securityAdminApi.listAlerts()
        setAlerts(a.data.items ?? [])
      } else if (tab === 'templates') {
        const t = await securityAdminApi.listRoleTemplates()
        setTemplates(t.data.items ?? [])
      } else if (tab === 'access-review') {
        const c = await securityAdminApi.listAccessReviews()
        setCampaigns(c.data.items ?? [])
      } else if (tab === 'compliance') {
        const c = await securityAdminApi.listCompliance()
        setCompliance(c.data)
      } else if (tab === 'matrix') {
        const m = await securityAdminApi.accessMatrix()
        setMatrix(m.data)
      } else if (tab === 'overview') {
        const [s, u, r] = await Promise.all([
          securityAdminApi.summary(),
          partnerAdminApi.listUsers(),
          partnerAdminApi.listUserRoles({ active_only: false }),
        ])
        setSummary(s.data)
        setUsers(u.data.users ?? [])
        setRoles(r.data.roles ?? [])
      } else if (tab === 'users' || tab === 'roles') {
        const [u, r] = await Promise.all([
          partnerAdminApi.listUsers(),
          partnerAdminApi.listUserRoles({ active_only: false }),
        ])
        setUsers(u.data.users ?? [])
        setRoles(r.data.roles ?? [])
      } else if (tab === 'permissions') {
        const g = await securityAdminApi.listPermissionGroups()
        setGroups(g.data.items ?? [])
      } else if (tab === 'webhooks') {
        const w = await securityAdminApi.listWebhooks()
        setWebhooks(w.data.items ?? [])
      } else if (tab === 'api-keys') {
        const [k, u] = await Promise.all([
          securityAdminApi.listApiKeys(),
          partnerAdminApi.listUsers(),
        ])
        setApiKeys(k.data.items ?? [])
        setUsers(u.data.users ?? [])
      } else if (tab === 'audit') {
        const a = await securityAdminApi.listAudit()
        setAudit(a.data.items ?? [])
      } else if (tab === 'cross-domain') {
        const l = await securityAdminApi.listDomainLinks()
        setLinks(l.data.items ?? [])
      } else if (tab === 'locker-players') {
        const [lp, upa] = await Promise.all([
          securityAdminApi.listLockerPlayers(true),
          securityAdminApi.listUserPlayerAccess(),
        ])
        setLockerPlayers(lp.data.items ?? [])
        setUserPlayerAccess(upa.data.items ?? [])
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [tab])

  useEffect(() => {
    void load()
  }, [load])

  const onCreateUser = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await securityAdminApi.createUser({ ...userForm, is_active: true })
      setMessage('Usuário criado.')
      setUserForm({ full_name: '', email: '' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha')
    } finally {
      setLoading(false)
    }
  }

  const onGrantRole = async (e: FormEvent) => {
    e.preventDefault()
    if (!roleUserId) return
    await partnerAdminApi.createUserRole({ user_id: roleUserId, role: roleName, scope_type: 'GLOBAL' })
    setMessage('Role concedida.')
    await load()
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap gap-2 text-xs">
        <Link to="/ops/access/user-roles" className="text-indigo-400 hover:underline">
          user_roles (legado)
        </Link>
        <Link to="/ops/partners/admin" className="text-indigo-400 hover:underline">
          Parceiros
        </Link>
        <Link to="/ops/marketplace/admin" className="text-indigo-400 hover:underline">
          Marketplace
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">
          OPS · Users &amp; Roles &amp; Security
        </h1>
        <p className="text-sm text-gray-500 dark:text-slate-400">
          CRUD usuários, papéis, permissões, webhooks, rotação de API keys e auditoria cross-domain.
        </p>
      </div>

      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1.5 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300'}`}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
        <button
          type="button"
          onClick={() => void load()}
          className="ml-auto rounded bg-slate-700 px-3 py-1.5 text-sm text-white"
        >
          Atualizar
        </button>
        <button
          type="button"
          onClick={() => void securityAdminApi.seed().then(() => load())}
          className="rounded bg-emerald-600 px-3 py-1.5 text-sm text-white"
        >
          Seed
        </button>
      </div>

      {loading && <p className="text-sm text-gray-500">Carregando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded bg-amber-900/40 p-2 font-mono text-xs text-amber-200">API key: {lastApiKey}</p>
      )}

      {tab === 'intelligence' && intel && (
        <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
          <p className="text-lg font-medium">Postura: {intel.overall_posture}</p>
          <p className="text-sm text-slate-400">
            Risco médio {intel.average_user_risk} · {intel.open_alerts} alertas · {intel.pending_reviews} revisões
          </p>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-300">
            {intel.recommendations.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {tab === 'alerts' &&
        alerts.map((a) => (
          <div key={a.id} className="border-b border-slate-800 py-2 text-sm">
            [{a.severity}] {a.title}
          </div>
        ))}

      {tab === 'templates' &&
        templates.map((t) => (
          <div key={t.code} className="text-sm">
            {t.code} — {t.name}
          </div>
        ))}

      {tab === 'access-review' &&
        campaigns.map((c) => (
          <div key={c.id} className="border-b border-slate-800 py-2 text-sm">
            {c.name} · {c.status} · {c.pending_items} pendentes
          </div>
        ))}

      {tab === 'compliance' && compliance && (
        <div className="text-sm text-slate-300">
          Cobertura {compliance.coverage_pct}% · {(compliance.items as unknown[]).length} controlos
        </div>
      )}

      {tab === 'matrix' && matrix && (
        <p className="text-sm text-slate-400">
          {matrix.users.length} utilizadores × {matrix.domains.length} domínios · {matrix.cells.length} células
        </p>
      )}

      {tab === 'overview' && summary && (
        <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4 text-sm">
          {summary.users} usuários · {summary.active_roles} roles · {summary.permission_groups} grupos ·{' '}
          {summary.webhook_endpoints} webhooks · {summary.active_api_keys} API keys · {summary.audit_logs} audit
        </div>
      )}

      {tab === 'users' && (
        <form onSubmit={onCreateUser} className="flex flex-wrap gap-2 rounded-xl border border-slate-700 p-4">
          <input
            className="ellan-field"
            placeholder="Nome"
            value={userForm.full_name}
            onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
            required
          />
          <input
            className="ellan-field"
            placeholder="E-mail"
            value={userForm.email}
            onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
            required
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar usuário
          </button>
        </form>
      )}

      {tab === 'roles' && (
        <form onSubmit={onGrantRole} className="mb-4 flex flex-wrap gap-2">
          <select className="ellan-field" value={roleUserId} onChange={(e) => setRoleUserId(e.target.value)} required>
            <option value="">Usuário</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.email}
              </option>
            ))}
          </select>
          <select className="ellan-field" value={roleName} onChange={(e) => setRoleName(e.target.value)}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Conceder
          </button>
        </form>
      )}

      {(tab === 'users' || tab === 'overview') && users.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">E-mail</th>
              <th className="px-3 py-2">Ativo</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{u.id}</td>
                <td className="px-3 py-2">{u.full_name}</td>
                <td className="px-3 py-2">{u.email}</td>
                <td className="px-3 py-2">{u.is_active ? 'sim' : 'não'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'roles' && (
        <table className="w-full text-left text-sm">
          <tbody>
            {roles.map((r) => (
              <tr key={r.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{r.user_id}</td>
                <td className="px-3 py-2">{r.role}</td>
                <td className="px-3 py-2">{r.scope_type}</td>
                <td className="px-3 py-2">
                  {r.is_active && !r.revoked_at && (
                    <button
                      type="button"
                      className="text-xs text-red-500"
                      onClick={() =>
                        void partnerAdminApi.revokeUserRole(r.id).then(() => {
                          setMessage('Revogada')
                          void load()
                        })
                      }
                    >
                      Revogar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'permissions' &&
        groups.map((g) => (
          <div key={g.id} className="rounded border border-slate-700 px-3 py-2 text-sm">
            {g.name} {g.is_system ? '(sistema)' : ''}
          </div>
        ))}

      {tab === 'webhooks' && (
        <ul className="space-y-2 text-sm">
          {webhooks.map((w) => (
            <li key={w.id} className="flex flex-wrap items-center gap-2 rounded border border-slate-700 p-2">
              <span>{w.url}</span>
              <button
                type="button"
                className="text-xs text-indigo-400"
                onClick={() =>
                  void securityAdminApi.rotateWebhook(w.id).then((r) => {
                    setMessage(`Secret: ${r.data.webhook_secret}`)
                  })
                }
              >
                Rotate secret
              </button>
            </li>
          ))}
        </ul>
      )}

      {tab === 'api-keys' && (
        <>
          <select
            className="ellan-field mb-2"
            onChange={(e) => {
              const uid = e.target.value
              if (uid)
                void securityAdminApi.rotateApiKey(uid).then((r) => {
                  setLastApiKey(r.data.api_key)
                  setMessage('API key rotacionada')
                })
            }}
            defaultValue=""
          >
            <option value="">Rotacionar para usuário…</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.email}
              </option>
            ))}
          </select>
          {apiKeys.map((k) => (
            <div key={k.id} className="font-mono text-xs text-slate-400">
              {k.key_prefix} · {k.user_id}
            </div>
          ))}
        </>
      )}

      {tab === 'audit' &&
        audit.map((a) => (
          <div key={a.id} className="border-b border-slate-800 py-1 text-xs font-mono">
            {a.occurred_at} {a.action} {a.target_type}/{a.target_id}
          </div>
        ))}

      {tab === 'cross-domain' &&
        links.map((l) => (
          <div key={l.id} className="text-sm">
            {l.user_id} → {l.domain} {l.entity_type}/{l.entity_id} ({l.relation})
          </div>
        ))}

      {tab === 'locker-players' && (
        <>
          <p className="text-sm text-slate-400">
            InPost, DHL, DPD, Magalu, Mercado Livre, Amazon, Correios, CTT, Worten, El Corte Inglés e rede mundial.
          </p>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Player</th>
                <th className="px-3 py-2">Segmento</th>
                <th className="px-3 py-2">Domínio</th>
                <th className="px-3 py-2">Tier</th>
              </tr>
            </thead>
            <tbody>
              {lockerPlayers.map((p) => (
                <tr key={p.player_code} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{p.name}</td>
                  <td className="px-3 py-2">{p.segment}</td>
                  <td className="px-3 py-2">{p.primary_domain}</td>
                  <td className="px-3 py-2">{p.global_tier}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {userPlayerAccess.length > 0 && (
            <div className="mt-4 text-xs text-slate-400">
              {userPlayerAccess.length} vínculos usuário ↔ player (NETWORK_ADMIN / SUPPORT / AUDITOR)
            </div>
          )}
        </>
      )}
    </div>
  )
}
