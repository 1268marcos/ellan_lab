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
import {
  criticalTableSecurityApi,
  type CriticalAccessLogRow,
  type CriticalTablePolicy,
  type CriticalTableRegistry,
  type PublicAuditLogRow,
} from '../../api/criticalTableSecurity'
import CriticalAppLayerBanner from '../../components/ops/CriticalAppLayerBanner'

const TABS = [
  'overview',
  'intelligence',
  'access-review',
  'break-glass',
  'access-requests',
  'jit-access',
  'delegations',
  'entitlements',
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
  'critical-tables',
  'critical-policies',
  'critical-access-log',
  'critical-audit-public',
  'cross-domain',
] as const
type Tab = (typeof TABS)[number]

const CRITICAL_TABS: Tab[] = [
  'critical-tables',
  'critical-policies',
  'critical-access-log',
  'critical-audit-public',
]
const MAIN_TABS = TABS.filter((t) => !CRITICAL_TABS.includes(t))

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Visão geral',
  intelligence: 'Inteligência OPS',
  'access-review': 'Revisão de acesso',
  'break-glass': 'Break-glass',
  'access-requests': 'Pedidos de acesso',
  'jit-access': 'Acesso JIT',
  delegations: 'Delegação act-as',
  entitlements: 'Entitlements remotos',
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
  'critical-tables': 'Tabelas críticas',
  'critical-policies': 'Políticas app',
  'critical-access-log': 'Log de acesso',
  'critical-audit-public': 'audit_logs público',
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
  const [criticalRegistry, setCriticalRegistry] = useState<CriticalTableRegistry[]>([])
  const [criticalPolicies, setCriticalPolicies] = useState<CriticalTablePolicy[]>([])
  const [criticalAccessLog, setCriticalAccessLog] = useState<CriticalAccessLogRow[]>([])
  const [publicAudit, setPublicAudit] = useState<PublicAuditLogRow[]>([])
  const [links, setLinks] = useState<DomainLink[]>([])
  const [lockerPlayers, setLockerPlayers] = useState<LockerPlayer[]>([])
  const [userPlayerAccess, setUserPlayerAccess] = useState<UserPlayerAccess[]>([])
  const [intel, setIntel] = useState<Awaited<ReturnType<typeof securityAdminApi.intelligence>>['data'] | null>(null)
  const [alerts, setAlerts] = useState<Array<{ id: string; title: string; severity: string }>>([])
  const [templates, setTemplates] = useState<Array<{ code: string; name: string }>>([])
  const [campaigns, setCampaigns] = useState<Array<{ id: string; name: string; status: string; pending_items: number }>>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState('')
  const [reviewItems, setReviewItems] = useState<
    Array<{
      id: string
      user_id: string
      subject_type: string
      subject_label?: string
      decision?: string | null
    }>
  >([])
  const [breakGlassEvents, setBreakGlassEvents] = useState<
    Array<{ id: string; user_id: string; reason: string; status: string; expires_at: string; granted_roles: string[] }>
  >([])
  const [bgForm, setBgForm] = useState({ user_id: 'usr-suporte', reason: '', duration_hours: 4, role: 'admin_operacao' })
  const [accessRequests, setAccessRequests] = useState<Array<{ id: string; user_id: string; domain_code: string; status: string; permission_key: string }>>([])
  const [jitGrants, setJitGrants] = useState<Array<{ id: string; user_id: string; domain_code: string; expires_at: string }>>([])
  const [delegations, setDelegations] = useState<Array<{ id: string; delegate_user_id: string; target_domain: string; target_entity_id: string }>>([])
  const [entitlements, setEntitlements] = useState<{ items: unknown[]; domains_synced: number } | null>(null)
  const REVIEWER_ID = 'usr-admin-ops'
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
        const [c, u] = await Promise.all([securityAdminApi.listAccessReviews(), partnerAdminApi.listUsers()])
        const items = c.data.items ?? []
        setCampaigns(items)
        setUsers(u.data.users ?? [])
        const campId = selectedCampaignId || items[0]?.id || ''
        if (campId) {
          setSelectedCampaignId(campId)
          const ri = await securityAdminApi.listAccessReviewItems(campId, true)
          setReviewItems(ri.data.items ?? [])
        } else {
          setReviewItems([])
        }
      } else if (tab === 'access-requests') {
        const ar = await securityAdminApi.listAccessRequests('PENDING')
        setAccessRequests(ar.data.items ?? [])
      } else if (tab === 'jit-access') {
        const j = await securityAdminApi.listJitGrants()
        setJitGrants(j.data.items ?? [])
      } else if (tab === 'delegations') {
        const d = await securityAdminApi.listDelegations()
        setDelegations(d.data.items ?? [])
      } else if (tab === 'entitlements') {
        const e = await securityAdminApi.listEntitlements()
        setEntitlements(e.data)
      } else if (tab === 'break-glass') {
        const [bg, u] = await Promise.all([
          securityAdminApi.listBreakGlass(true),
          partnerAdminApi.listUsers(),
        ])
        setBreakGlassEvents(bg.data.items ?? [])
        setUsers(u.data.users ?? [])
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
      } else if (tab === 'critical-tables') {
        const r = await criticalTableSecurityApi.listRegistry()
        setCriticalRegistry(r.data.items ?? [])
      } else if (tab === 'critical-policies') {
        const p = await criticalTableSecurityApi.listPolicies()
        setCriticalPolicies(p.data.items ?? [])
      } else if (tab === 'critical-access-log') {
        const l = await criticalTableSecurityApi.listAccessLog({ limit: 120 })
        setCriticalAccessLog(l.data.items ?? [])
      } else if (tab === 'critical-audit-public') {
        const a = await criticalTableSecurityApi.listPublicAuditLogs(120)
        setPublicAudit(a.data.items ?? [])
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
  }, [tab, selectedCampaignId])

  useEffect(() => {
    void load()
  }, [load])

  const onSelectCampaign = async (campId: string) => {
    setSelectedCampaignId(campId)
    setLoading(true)
    try {
      const ri = await securityAdminApi.listAccessReviewItems(campId, true)
      setReviewItems(ri.data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar itens')
    } finally {
      setLoading(false)
    }
  }

  const onDecideReview = async (itemId: string, decision: 'APPROVE' | 'REVOKE') => {
    setLoading(true)
    setError(null)
    try {
      await securityAdminApi.decideAccessReviewItem(itemId, {
        decision,
        reviewer_id: REVIEWER_ID,
        notes: decision === 'REVOKE' ? 'Revogado na certificação OPS' : undefined,
      })
      setMessage(decision === 'REVOKE' ? 'Acesso revogado' : 'Acesso certificado')
      if (selectedCampaignId) await onSelectCampaign(selectedCampaignId)
      const c = await securityAdminApi.listAccessReviews()
      setCampaigns(c.data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha na decisão')
    } finally {
      setLoading(false)
    }
  }

  const onOpenBreakGlass = async (e: FormEvent) => {
    e.preventDefault()
    if (!bgForm.reason.trim()) return
    setLoading(true)
    setError(null)
    try {
      await securityAdminApi.openBreakGlass({
        user_id: bgForm.user_id,
        reason: bgForm.reason,
        granted_roles: [bgForm.role],
        approved_by: REVIEWER_ID,
        duration_hours: bgForm.duration_hours,
      })
      setMessage('Break-glass aberto')
      setBgForm((f) => ({ ...f, reason: '' }))
      const bg = await securityAdminApi.listBreakGlass(true)
      setBreakGlassEvents(bg.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao abrir break-glass')
    } finally {
      setLoading(false)
    }
  }

  const onRevokeBreakGlass = async (eventId: string) => {
    setLoading(true)
    setError(null)
    try {
      await securityAdminApi.revokeBreakGlass(eventId, { revoked_by: REVIEWER_ID, reason: 'Encerrado pelo OPS' })
      setMessage('Break-glass revogado')
      const bg = await securityAdminApi.listBreakGlass(true)
      setBreakGlassEvents(bg.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao revogar')
    } finally {
      setLoading(false)
    }
  }

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
          CRUD usuários, papéis, permissões, webhooks e auditoria. Tabelas{' '}
          <span className="font-mono text-amber-300/90">users</span>,{' '}
          <span className="font-mono text-amber-300/90">privacy_consents</span> e{' '}
          <span className="font-mono text-amber-300/90">audit_logs</span> sem RLS — enforcement na camada de
          aplicação.
        </p>
      </div>

      {CRITICAL_TABS.includes(tab) ? <CriticalAppLayerBanner /> : null}

      <div className="flex flex-wrap gap-1">
        {MAIN_TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1.5 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300'}`}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-1 border-t border-slate-700/80 pt-2">
        <span className="mr-1 text-[10px] font-bold uppercase tracking-wide text-amber-400/90">App</span>
        {CRITICAL_TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1.5 text-sm ${tab === t ? 'bg-amber-600 text-white' : 'bg-slate-800 text-amber-200/80'}`}
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

      {tab === 'access-review' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {campaigns.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => void onSelectCampaign(c.id)}
                className={`rounded px-3 py-1 text-sm ${
                  selectedCampaignId === c.id ? 'bg-emerald-700 text-white' : 'bg-slate-800 text-slate-300'
                }`}
              >
                {c.name} ({c.pending_items} pend.)
              </button>
            ))}
          </div>
          <div className="overflow-x-auto rounded-xl border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/80 text-slate-400">
                <tr>
                  <th className="p-2">Utilizador</th>
                  <th className="p-2">Tipo</th>
                  <th className="p-2">Sujeito</th>
                  <th className="p-2">Ações</th>
                </tr>
              </thead>
              <tbody>
                {reviewItems.map((item) => (
                  <tr key={item.id} className="border-t border-slate-800">
                    <td className="p-2 font-mono text-xs">{item.user_id}</td>
                    <td className="p-2">{item.subject_type}</td>
                    <td className="p-2">{item.subject_label ?? item.subject_id}</td>
                    <td className="p-2 space-x-2">
                      <button
                        type="button"
                        className="rounded bg-emerald-700 px-2 py-1 text-xs text-white"
                        onClick={() => void onDecideReview(item.id, 'APPROVE')}
                        disabled={loading}
                      >
                        Aprovar
                      </button>
                      <button
                        type="button"
                        className="rounded bg-red-700 px-2 py-1 text-xs text-white"
                        onClick={() => void onDecideReview(item.id, 'REVOKE')}
                        disabled={loading}
                        title="Revoga UserRole ou CrossDomainGrant"
                      >
                        Revogar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!reviewItems.length && <p className="p-4 text-sm text-slate-500">Nenhum item pendente nesta campanha.</p>}
          </div>
        </div>
      )}

      {tab === 'access-requests' &&
        accessRequests.map((r) => (
          <div key={r.id} className="flex gap-2 border-b border-slate-800 py-2 text-sm">
            <span>
              {r.user_id} · {r.domain_code} · {r.permission_key}
            </span>
            <button type="button" className="rounded bg-emerald-700 px-2 py-1 text-xs text-white" onClick={() => void securityAdminApi.decideAccessRequest(r.id, { decision: 'APPROVE', reviewer_id: REVIEWER_ID }).then(() => load())}>
              Aprovar
            </button>
            <button type="button" className="rounded bg-red-800 px-2 py-1 text-xs text-white" onClick={() => void securityAdminApi.decideAccessRequest(r.id, { decision: 'DENY', reviewer_id: REVIEWER_ID }).then(() => load())}>
              Negar
            </button>
          </div>
        ))}

      {tab === 'jit-access' &&
        jitGrants.map((j) => (
          <div key={j.id} className="border-b border-slate-800 py-2 text-sm font-mono">
            {j.user_id} · {j.domain_code} · expira {new Date(j.expires_at).toLocaleString()}
          </div>
        ))}

      {tab === 'delegations' &&
        delegations.map((d) => (
          <div key={d.id} className="border-b border-slate-800 py-2 text-sm">
            {d.delegate_user_id} → {d.target_domain}/{d.target_entity_id}
          </div>
        ))}

      {tab === 'entitlements' && entitlements && (
        <p className="text-sm text-slate-400">
          {entitlements.items.length} entitlements · {entitlements.domains_synced} domínios
          <button type="button" className="ml-3 rounded bg-slate-700 px-2 py-1 text-xs" onClick={() => void securityAdminApi.syncEntitlements().then(() => load())}>
            Sincronizar
          </button>
        </p>
      )}

      {tab === 'break-glass' && (
        <div className="space-y-4">
          <form onSubmit={onOpenBreakGlass} className="flex flex-wrap gap-2 rounded-xl border border-amber-800/60 bg-amber-950/30 p-4">
            <select
              className="ellan-field"
              value={bgForm.user_id}
              onChange={(e) => setBgForm({ ...bgForm, user_id: e.target.value })}
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.id})
                </option>
              ))}
            </select>
            <select
              className="ellan-field"
              value={bgForm.role}
              onChange={(e) => setBgForm({ ...bgForm, role: e.target.value })}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
            <input
              className="ellan-field min-w-[200px] flex-1"
              placeholder="Motivo do incidente (obrigatório)"
              value={bgForm.reason}
              onChange={(e) => setBgForm({ ...bgForm, reason: e.target.value })}
              required
            />
            <input
              type="number"
              min={1}
              max={24}
              className="ellan-field w-20"
              value={bgForm.duration_hours}
              onChange={(e) => setBgForm({ ...bgForm, duration_hours: Number(e.target.value) })}
            />
            <button type="submit" className="rounded bg-amber-600 px-4 py-2 text-sm text-white" disabled={loading}>
              Abrir break-glass
            </button>
          </form>
          {breakGlassEvents.map((ev) => (
            <div key={ev.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 py-2 text-sm">
              <span>
                <strong className="font-mono">{ev.user_id}</strong> · {ev.reason} · expira {new Date(ev.expires_at).toLocaleString()}
                <br />
                <span className="text-slate-500">roles: {(ev.granted_roles || []).join(', ')}</span>
              </span>
              <button
                type="button"
                className="rounded bg-slate-700 px-3 py-1 text-xs text-white"
                onClick={() => void onRevokeBreakGlass(ev.id)}
                disabled={loading}
              >
                Revogar agora
              </button>
            </div>
          ))}
          {!breakGlassEvents.length && <p className="text-sm text-slate-500">Nenhuma sessão break-glass ativa.</p>}
        </div>
      )}

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

      {tab === 'critical-tables' && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Tabela</th>
              <th className="px-3 py-2">RLS</th>
              <th className="px-3 py-2">Enforcement</th>
              <th className="px-3 py-2">Descrição</th>
            </tr>
          </thead>
          <tbody>
            {criticalRegistry.map((r) => (
              <tr key={r.table_name} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono">{r.table_name}</td>
                <td className="px-3 py-2">{r.rls_enabled ? 'sim' : 'não'}</td>
                <td className="px-3 py-2">{r.enforcement_layer}</td>
                <td className="px-3 py-2 text-slate-400">{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'critical-policies' && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Tabela</th>
              <th className="px-3 py-2">Op</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Escopo</th>
              <th className="px-3 py-2">Permite</th>
            </tr>
          </thead>
          <tbody>
            {criticalPolicies.map((p) => (
              <tr key={p.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono">{p.table_name}</td>
                <td className="px-3 py-2">{p.operation}</td>
                <td className="px-3 py-2">{p.role}</td>
                <td className="px-3 py-2">{p.scope_type}</td>
                <td className="px-3 py-2">{p.allowed ? '✓' : '✗'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'critical-access-log' &&
        criticalAccessLog.map((row) => (
          <div key={row.id} className="border-b border-slate-800 py-1 text-xs font-mono">
            {row.occurred_at} {row.decision} {row.table_name}/{row.operation} · {row.reason}
          </div>
        ))}

      {tab === 'critical-audit-public' &&
        publicAudit.map((a) => (
          <div key={a.id} className="border-b border-slate-800 py-1 text-xs font-mono">
            {String(a.occurred_at)} {a.action} {a.target_type}/{a.target_id}{' '}
            {a.source_service ? `· ${a.source_service}` : ''}
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
