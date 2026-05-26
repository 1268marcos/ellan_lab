import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { Link, useSearchParams } from 'react-router-dom'
import {
  capabilityAdminApi,
  type CapabilityDashboard,
  type CapabilityProfile,
  type MatrixResponse,
} from '../../api/capabilityAdmin'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'

const TABS = [
  'overview',
  'matrix',
  'channels',
  'regions',
  'profiles',
  'composition',
  'ecosystem',
  'catalogs',
  'geo',
  'webhooks',
  'deliveries',
  'audit',
  'intelligence',
  'tools',
] as const

type Tab = (typeof TABS)[number]

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Visão geral',
  matrix: 'Matriz cobertura',
  channels: 'Canais & contextos',
  regions: 'Regiões',
  profiles: 'Perfis capability',
  composition: 'Ações · métodos · constraints',
  ecosystem: 'Players mundiais',
  catalogs: 'Catálogos pagamento',
  geo: 'País · província · locker',
  webhooks: 'Webhook & API keys',
  deliveries: 'Entregas · DLQ',
  audit: 'Auditoria',
  intelligence: 'Inteligência OPS',
  tools: 'Ferramentas OPS',
}

export default function OpsCapabilityAdmin() {
  const { tab, setTab } = useOpsTabFromUrl<Tab>('/ops/capability/admin', TABS, 'overview')
  const [dash, setDash] = useState<CapabilityDashboard | null>(null)
  const [channels, setChannels] = useState<unknown[]>([])
  const [contexts, setContexts] = useState<unknown[]>([])
  const [regions, setRegions] = useState<unknown[]>([])
  const [profiles, setProfiles] = useState<CapabilityProfile[]>([])
  const [methods, setMethods] = useState<unknown[]>([])
  const [interfaces, setInterfaces] = useState<unknown[]>([])
  const [wallets, setWallets] = useState<unknown[]>([])
  const [countries, setCountries] = useState<unknown[]>([])
  const [provinces, setProvinces] = useState<unknown[]>([])
  const [locations, setLocations] = useState<unknown[]>([])
  const [webhooks, setWebhooks] = useState<unknown[]>([])
  const [matrix, setMatrix] = useState<MatrixResponse | null>(null)
  const [segments, setSegments] = useState<unknown[]>([])
  const [ecoPlayers, setEcoPlayers] = useState<unknown[]>([])
  const [bindings, setBindings] = useState<unknown[]>([])
  const [profileActions, setProfileActions] = useState<unknown[]>([])
  const [profileMethods, setProfileMethods] = useState<unknown[]>([])
  const [profileConstraints, setProfileConstraints] = useState<unknown[]>([])
  const [deliveries, setDeliveries] = useState<unknown[]>([])
  const [auditLog, setAuditLog] = useState<unknown[]>([])
  const [lockerPresence, setLockerPresence] = useState<unknown[]>([])
  const [worldReport, setWorldReport] = useState<Record<string, unknown> | null>(null)
  const [readiness, setReadiness] = useState<unknown[]>([])
  const [insights, setInsights] = useState<unknown[]>([])
  const [recommendations, setRecommendations] = useState<unknown[]>([])
  const [corridors, setCorridors] = useState<unknown[]>([])
  const [featureFlags, setFeatureFlags] = useState<unknown[]>([])
  const [resolved, setResolved] = useState<Record<string, unknown> | null>(null)
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null)
  const [templates, setTemplates] = useState<unknown[]>([])
  const [opsJobs, setOpsJobs] = useState<unknown[]>([])
  const [searchParams] = useSearchParams()
  const intelligenceView = searchParams.get('view') || 'world'
  const ecoView = searchParams.get('view')
  const [selectedProfile, setSelectedProfile] = useState<number | null>(null)
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.example.com/capability')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const profilesRef = useRef<CapabilityProfile[]>([])

  const formatLoadError = (err: unknown): string => {
    if (axios.isAxiosError(err)) {
      if (!err.response) {
        return 'Serviço capability-admin indisponível na porta 8028. Execute: cd 01_source/capability_admin_service && ./dev.sh'
      }
      if (err.response.status === 429) {
        return 'Muitas requisições (429). Aguarde alguns segundos e clique em Recarregar.'
      }
      if (err.response.status === 404) {
        return 'API capability-admin não encontrada (404). Suba o serviço: cd 01_source/capability_admin_service && ./dev.sh'
      }
      const detail = (err.response.data as { detail?: string })?.detail
      return detail || `Erro HTTP ${err.response.status}`
    }
    return err instanceof Error ? err.message : 'Falha ao carregar capability-admin'
  }

  const loadCore = useCallback(async () => {
    const [d, ch, ctx, reg, prof, pm] = await Promise.all([
      capabilityAdminApi.dashboard(),
      capabilityAdminApi.listChannels(),
      capabilityAdminApi.listContexts(),
      capabilityAdminApi.listRegions(),
      capabilityAdminApi.listProfiles(),
      capabilityAdminApi.listPaymentMethods(),
    ])
    setDash(d.data)
    setChannels(ch.data.items ?? [])
    setContexts(ctx.data.items ?? [])
    setRegions(reg.data.items ?? [])
    const profItems = prof.data.items ?? []
    setProfiles(profItems)
    profilesRef.current = profItems
    setMethods(pm.data.items ?? [])
    setSelectedProfile((prev) => prev ?? profItems[0]?.id ?? null)
  }, [])

  const loadTabData = useCallback(async (activeTab: Tab) => {
    const pid = selectedProfile ?? profilesRef.current[0]?.id
    switch (activeTab) {
      case 'catalogs': {
        const [pm, iface, wallets] = await Promise.all([
          capabilityAdminApi.listPaymentMethods(),
          capabilityAdminApi.listInterfaces(),
          capabilityAdminApi.listWallets(),
        ])
        setMethods(pm.data.items ?? [])
        setInterfaces(iface.data.items ?? [])
        setWallets(wallets.data.items ?? [])
        break
      }
      case 'geo': {
        const [co, pr, loc] = await Promise.all([
          capabilityAdminApi.listCountries(),
          capabilityAdminApi.listProvinces(),
          capabilityAdminApi.listLockerLocations(),
        ])
        setCountries(co.data.items ?? [])
        setProvinces(pr.data.items ?? [])
        setLocations(loc.data.items ?? [])
        break
      }
      case 'webhooks': {
        const wh = await capabilityAdminApi.listWebhooks()
        setWebhooks(wh.data.items ?? [])
        break
      }
      case 'matrix': {
        const m = await capabilityAdminApi.matrix()
        setMatrix(m.data)
        break
      }
      case 'ecosystem': {
        const [s, p, b] = await Promise.all([
          capabilityAdminApi.listSegments(),
          capabilityAdminApi.listEcosystemPlayers(),
          capabilityAdminApi.listBindings(),
        ])
        setSegments(s.data.items ?? [])
        setEcoPlayers(p.data.items ?? [])
        setBindings(b.data.items ?? [])
        if (ecoView === 'locker') {
          const lp = await capabilityAdminApi.listLockerPresence()
          setLockerPresence(lp.data.items ?? [])
        } else {
          setLockerPresence([])
        }
        break
      }
      case 'tools': {
        const [tpl, jobs] = await Promise.all([capabilityAdminApi.listTemplates(), capabilityAdminApi.listOpsJobs()])
        setTemplates(tpl.data.items ?? [])
        setOpsJobs(jobs.data.items ?? [])
        if (pid) {
          const sim = await capabilityAdminApi.simulateFlow(pid, 'pay')
          setSimResult(sim.data)
        }
        break
      }
      case 'intelligence': {
        const view = new URLSearchParams(window.location.search).get('view') || 'world'
        if (view === 'readiness') {
          const r = await capabilityAdminApi.listReadiness()
          setReadiness(r.data.items ?? [])
        } else if (view === 'insights') {
          const i = await capabilityAdminApi.listInsights()
          setInsights(i.data.items ?? [])
        } else if (view === 'recommendations') {
          const rec = await capabilityAdminApi.listRecommendations()
          setRecommendations(rec.data.items ?? [])
        } else if (view === 'corridors') {
          const c = await capabilityAdminApi.listCorridors()
          setCorridors(c.data.items ?? [])
        } else if (view === 'flags') {
          const f = await capabilityAdminApi.listFeatureFlags()
          setFeatureFlags(f.data.items ?? [])
        } else {
          const w = await capabilityAdminApi.worldReport()
          setWorldReport(w.data)
        }
        break
      }
      case 'composition':
        if (pid) {
          const [a, m, c] = await Promise.all([
            capabilityAdminApi.listProfileActions(pid),
            capabilityAdminApi.listProfileMethods(pid),
            capabilityAdminApi.listProfileConstraints(pid),
          ])
          setProfileActions(a.data.items ?? [])
          setProfileMethods(m.data.items ?? [])
          setProfileConstraints(c.data.items ?? [])
        }
        break
      case 'deliveries': {
        const d = await capabilityAdminApi.listWebhookDeliveries({ dead_letter_only: false })
        setDeliveries(d.data.items ?? [])
        break
      }
      case 'audit': {
        const a = await capabilityAdminApi.listAuditLog(pid ?? undefined)
        setAuditLog(a.data.items ?? [])
        break
      }
      default:
        break
    }
  }, [selectedProfile, ecoView])

  const refresh = useCallback(
    async (activeTab: Tab) => {
      setLoading(true)
      setError(null)
      try {
        const needsCore = ['overview', 'channels', 'regions', 'profiles', 'composition', 'webhooks', 'ecosystem'].includes(
          activeTab,
        )
        if (needsCore) await loadCore()
        if (activeTab !== 'overview') await loadTabData(activeTab)
      } catch (err: unknown) {
        setError(formatLoadError(err))
      } finally {
        setLoading(false)
      }
    },
    [loadCore, loadTabData],
  )

  useEffect(() => {
    void refresh(tab)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- apenas ao mudar aba
  }, [tab, intelligenceView, ecoView])

  const load = useCallback(() => refresh(tab), [refresh, tab])

  const onRecomputeIntelligence = async () => {
    setLoading(true)
    try {
      await capabilityAdminApi.recomputeIntelligence()
      setMessage('Inteligência recalculada')
      await refresh('intelligence')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao recalcular')
    } finally {
      setLoading(false)
    }
  }

  const onSeed = async () => {
    setLoading(true)
    try {
      const r = await capabilityAdminApi.seed()
      setMessage(`Seed: ${JSON.stringify(r.data)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedProfile) return
    setLoading(true)
    try {
      const r = await capabilityAdminApi.rotateApiKey(selectedProfile)
      setLastApiKey(r.data.api_key)
      setMessage(`API key rotacionada (${r.data.key_prefix})`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar API key')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async (e: FormEvent) => {
    e.preventDefault()
    if (!selectedProfile) return
    setLoading(true)
    try {
      await capabilityAdminApi.upsertWebhook({
        profile_id: selectedProfile,
        url: webhookUrl,
        secret: webhookSecret || undefined,
      })
      setMessage('Webhook configurado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const tabBtn = (active: boolean) =>
    active
      ? 'rounded px-3 py-1 text-sm bg-indigo-600 text-white'
      : 'rounded px-3 py-1 text-sm border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'

  const cardCls = 'rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900'

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Capability</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Perfis region×canal×contexto, catálogos, ecossistema mundial, webhooks · capability-admin :8028
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="ellan-btn-outline">
            Seed
          </button>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Atualizar
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500 dark:text-slate-400">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
          API key: {lastApiKey}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t} type="button" onClick={() => setTab(t)} className={tabBtn(tab === t)}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <section className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {dash ? (
            Object.entries(dash).map(([k, v]) => (
              <div key={k} className={cardCls}>
                <p className="text-xs text-gray-500 uppercase">{k.replace(/_/g, ' ')}</p>
                <p className="text-2xl font-semibold">{v}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500 col-span-full">
              Clique Recarregar ou abra outra aba. Ative{' '}
              <code className="text-xs">cd 01_source/capability_admin_service && ./dev.sh</code>
            </p>
          )}
          <div className="col-span-full flex flex-wrap gap-3 text-sm">
            <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
              Payment Gateway
            </Link>
            <Link to="/ops/partners/admin?tab=capability_webhooks" className="text-indigo-600 hover:underline">
              Partner webhooks
            </Link>
            <Link to="/integrations/partners" className="text-indigo-600 hover:underline">
              Integrations hub
            </Link>
          </div>
        </section>
      )}

      {tab === 'matrix' && matrix && (
        <section className="space-y-3">
          <p className="text-sm text-gray-600">
            Cobertura matriz região×canal×contexto: <strong>{matrix.coverage_pct}%</strong> ({matrix.cells.filter((c) => c.has_profile).length}/
            {matrix.cells.length} células)
          </p>
          <div className={`overflow-x-auto max-h-96 ${cardCls}`}>
            <table className="min-w-full text-xs">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-2 py-1 text-left">Região</th>
                  <th className="px-2 py-1 text-left">Canal</th>
                  <th className="px-2 py-1 text-left">Contexto</th>
                  <th className="px-2 py-1 text-left">Perfil</th>
                </tr>
              </thead>
              <tbody>
                {matrix.cells.map((c, i) => (
                  <tr key={i} className={c.has_profile ? 'bg-green-50' : 'bg-red-50/40'}>
                    <td className="px-2 py-1">{c.region_code}</td>
                    <td className="px-2 py-1">{c.channel_code}</td>
                    <td className="px-2 py-1">{c.context_code}</td>
                    <td className="px-2 py-1">{c.profile_code ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === 'channels' && (
        <div className="grid md:grid-cols-2 gap-4">
          <Table title="Canais" rows={channels} cols={['code', 'name', 'is_active']} />
          <Table title="Contextos" rows={contexts} cols={['channel_id', 'code', 'name', 'is_active']} />
        </div>
      )}

      {tab === 'regions' && <Table title="Regiões operacionais" rows={regions} cols={['code', 'name', 'default_currency', 'country_code', 'is_active']} />}

      {tab === 'profiles' && (
        <div className="space-y-3">
          <Table
            title="Perfis (region × channel × context)"
            rows={profiles}
            cols={['profile_code', 'name', 'currency', 'priority', 'is_active']}
          />
          {selectedProfile && (
            <button
              type="button"
              className="text-sm text-indigo-600 underline"
              onClick={() =>
                void capabilityAdminApi.snapshotProfile(selectedProfile, 'ops-ui').then(() => setMessage('Snapshot criado.'))
              }
            >
              Criar snapshot do perfil #{selectedProfile}
            </button>
          )}
        </div>
      )}

      {tab === 'composition' && (
        <div className="grid md:grid-cols-3 gap-4">
          <label className="text-sm block md:col-span-3">
            Perfil
            <select
              className="mt-1 border rounded px-2 py-1"
              value={selectedProfile ?? ''}
              onChange={(e) => {
                setSelectedProfile(Number(e.target.value))
                void refresh('composition')
              }}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.profile_code}
                </option>
              ))}
            </select>
          </label>
          <Table title="Ações" rows={profileActions} cols={['action_code', 'label', 'is_active']} />
          <Table title="Métodos" rows={profileMethods} cols={['payment_method_id', 'is_default', 'sort_order']} />
          <Table title="Constraints" rows={profileConstraints} cols={['code']} />
        </div>
      )}

      {tab === 'ecosystem' && (
        <div className="space-y-4">
          {ecoView === 'locker' ? (
            <Table
              title="Locker world (presença global)"
              rows={lockerPresence}
              cols={['player_code', 'locker_role', 'program_name', 'region_scope', 'supports_returns']}
            />
          ) : (
            <div className="grid md:grid-cols-3 gap-4">
              <Table title="Segmentos" rows={segments} cols={['code', 'name']} />
              <Table title="Players" rows={ecoPlayers} cols={['code', 'name', 'segment_code', 'country_codes']} />
              <Table title="Bindings perfil↔player" rows={bindings} cols={['profile_code', 'player_code', 'binding_role']} />
            </div>
          )}
        </div>
      )}

      {tab === 'tools' && (
        <section className={`space-y-4 ${cardCls}`}>
          <h2 className="font-medium text-slate-200">Resolver perfil (runtime)</h2>
          <div className="flex flex-wrap gap-2 text-sm">
            <button
              type="button"
              className="ellan-btn-outline"
              onClick={async () => {
                try {
                  const r = await capabilityAdminApi.resolveProfile({
                    region_code: 'SP',
                    channel_code: 'kiosk',
                    context_code: 'purchase',
                  })
                  setResolved(r.data)
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'resolve failed')
                }
              }}
            >
              Resolver SP:kiosk:purchase
            </button>
          </div>
          {resolved && <pre className="text-xs overflow-auto">{JSON.stringify(resolved, null, 2)}</pre>}
          {simResult && (
            <>
              <h3 className="text-sm font-medium text-slate-300">Simulação pay (perfil selecionado)</h3>
              <pre className="text-xs overflow-auto">{JSON.stringify(simResult, null, 2)}</pre>
            </>
          )}
          <Table title="Templates" rows={templates} cols={['code', 'name', 'region_code', 'channel_code']} />
          <Table title="Jobs OPS recentes" rows={opsJobs} cols={['job_type', 'status', 'created_at']} />
        </section>
      )}

      {tab === 'intelligence' && (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void onRecomputeIntelligence()} className="ellan-btn-outline text-sm">
              Recalcular inteligência
            </button>
          </div>
          {intelligenceView === 'readiness' && (
            <Table title="Readiness por perfil" rows={readiness} cols={['profile_code', 'score', 'grade', 'gaps']} />
          )}
          {intelligenceView === 'insights' && (
            <Table title="Insights abertos" rows={insights} cols={['severity', 'category', 'title', 'recommendation']} />
          )}
          {intelligenceView === 'recommendations' && (
            <Table title="Recomendações" rows={recommendations} cols={['priority', 'profile_code', 'action', 'message']} />
          )}
          {intelligenceView === 'corridors' && (
            <Table
              title="Corredores regionais"
              rows={corridors}
              cols={['code', 'from_region_code', 'to_region_code', 'channel_code', 'default_currency']}
            />
          )}
          {intelligenceView === 'flags' && (
            <Table title="Feature flags" rows={featureFlags} cols={['code', 'name', 'scope', 'is_enabled']} />
          )}
          {intelligenceView === 'world' && worldReport && (
            <pre className={`text-xs overflow-auto max-h-96 ${cardCls}`}>{JSON.stringify(worldReport, null, 2)}</pre>
          )}
        </section>
      )}

      {tab === 'catalogs' && (
        <div className="grid md:grid-cols-3 gap-4">
          <Table title="Métodos de pagamento" rows={methods} cols={['code', 'name', 'family', 'is_active']} />
          <Table title="Interfaces" rows={interfaces} cols={['code', 'name', 'interface_type', 'is_active']} />
          <Table title="Wallet providers" rows={wallets} cols={['code', 'name', 'is_active']} />
        </div>
      )}

      {tab === 'geo' && (
        <div className="grid md:grid-cols-3 gap-4">
          <Table title="Países" rows={countries} cols={['code', 'name', 'default_currency']} />
          <Table title="Províncias" rows={provinces} cols={['code', 'name', 'country_code']} />
          <Table title="Locker locations" rows={locations} cols={['external_id', 'city_name', 'province_code', 'is_active']} />
        </div>
      )}

      {tab === 'webhooks' && (
        <div className="grid md:grid-cols-2 gap-4">
          <form onSubmit={onWebhook} className={`space-y-3 ${cardCls}`}>
            <h2 className="font-medium">Webhook por perfil</h2>
            <label className="block text-sm">
              Perfil
              <select
                className="ellan-field mt-1 w-full dark:bg-slate-900"
                value={selectedProfile ?? ''}
                onChange={(e) => setSelectedProfile(Number(e.target.value))}
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.profile_code}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              URL
              <input className="ellan-field mt-1 w-full dark:bg-slate-900" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
            </label>
            <label className="block text-sm">
              Secret (opcional)
              <input
                className="ellan-field mt-1 w-full dark:bg-slate-900"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
              />
            </label>
            <button type="submit" className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white">
              Salvar webhook
            </button>
            <button type="button" onClick={() => void onRotateKey()} className="ellan-btn-outline ml-2 text-sm">
              Rotacionar API key
            </button>
          </form>
          <Table title="Webhooks configurados" rows={webhooks} cols={['profile_code', 'url', 'active', 'last_http_status']} />
        </div>
      )}

      {tab === 'deliveries' && (
        <Table
          title="Entregas webhook (incl. DLQ)"
          rows={deliveries}
          cols={['event_type', 'http_status', 'success', 'status', 'dead_lettered_at']}
        />
      )}

      {tab === 'audit' && (
        <Table title="Audit log" rows={auditLog} cols={['entity_type', 'action', 'actor', 'created_at']} />
      )}

    </div>
  )
}

function Table({ title, rows, cols }: { title: string; rows: unknown[]; cols: string[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-600/70 bg-slate-900/90 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="border-b border-slate-600/70 px-3 py-2 text-sm font-medium text-slate-200">{title}</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-slate-800/80 text-left text-slate-300">
              {cols.map((c) => (
                <th key={c} className="px-3 py-2 font-medium">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={cols.length} className="px-3 py-4 text-slate-500">
                  Sem dados — clique em Seed
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr key={i} className="border-t border-slate-700/60">
                  {cols.map((c) => (
                    <td key={c} className="px-3 py-2 text-slate-200">
                      {String((row as Record<string, unknown>)[c] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
