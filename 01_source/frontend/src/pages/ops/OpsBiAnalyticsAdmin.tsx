import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  biAnalyticsAdminApi,
  type AnalyticsFact,
  type BiDashboard,
  type BiDataPartner,
  type BiLockerNetworkPlayer,
  type BiOpsIntelligence,
  type BiReadinessRow,
} from '../../api/biAnalyticsAdmin'

type Tab =
  | 'overview'
  | 'intelligence'
  | 'readiness'
  | 'facts'
  | 'marts'
  | 'refresh'
  | 'kpis'
  | 'alerts'
  | 'reports'
  | 'lineage'
  | 'exports'
  | 'partners'
  | 'players'
  | 'taxonomy'
  | 'webhooks'
  | 'audit'
  | 'integration'
  | 'efficiency'

const TAB_KEYS: Tab[] = [
  'overview',
  'intelligence',
  'readiness',
  'facts',
  'marts',
  'refresh',
  'kpis',
  'alerts',
  'reports',
  'lineage',
  'exports',
  'partners',
  'players',
  'taxonomy',
  'webhooks',
  'audit',
  'integration',
  'efficiency',
]

const cardCls = 'rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900'
const inputCls = 'ellan-field dark:border-slate-600 dark:bg-slate-800'

export default function OpsBiAnalyticsAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('overview')
  const [dash, setDash] = useState<BiDashboard | null>(null)
  const [facts, setFacts] = useState<AnalyticsFact[]>([])
  const [kpis, setKpis] = useState<unknown[]>([])
  const [reports, setReports] = useState<unknown[]>([])
  const [marts, setMarts] = useState<{ mrr: unknown[]; locker_pnl: unknown[]; partner_revenue: unknown[] } | null>(
    null,
  )
  const [partners, setPartners] = useState<BiDataPartner[]>([])
  const [players, setPlayers] = useState<BiLockerNetworkPlayer[]>([])
  const [relations, setRelations] = useState<unknown[]>([])
  const [webhooks, setWebhooks] = useState<unknown[]>([])
  const [integration, setIntegration] = useState<Record<string, unknown> | null>(null)
  const [opsIntel, setOpsIntel] = useState<BiOpsIntelligence | null>(null)
  const [readiness, setReadiness] = useState<BiReadinessRow[]>([])
  const [readinessBands, setReadinessBands] = useState<Record<string, number>>({})
  const [martJobs, setMartJobs] = useState<unknown[]>([])
  const [alertRules, setAlertRules] = useState<unknown[]>([])
  const [alertEvents, setAlertEvents] = useState<unknown[]>([])
  const [lineage, setLineage] = useState<unknown[]>([])
  const [exportJobs, setExportJobs] = useState<unknown[]>([])
  const [taxonomy, setTaxonomy] = useState<unknown[]>([])
  const [marketPresence, setMarketPresence] = useState<unknown[]>([])
  const [domainLinks, setDomainLinks] = useState<unknown[]>([])
  const [audit, setAudit] = useState<unknown[]>([])
  const [efficiency, setEfficiency] = useState<Record<string, unknown> | null>(null)
  const [dqChecks, setDqChecks] = useState<unknown[]>([])
  const [anomalies, setAnomalies] = useState<unknown[]>([])
  const [bookmarks, setBookmarks] = useState<unknown[]>([])
  const [pipelines, setPipelines] = useState<unknown[]>([])
  const [tier1Coverage, setTier1Coverage] = useState<{
    tier1_present: number
    tier1_required: number
    tier1_codes: string[]
    coverage_pct: number
  } | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [rotatedKey, setRotatedKey] = useState('')

  const [partnerForm, setPartnerForm] = useState({ name: '', code: '', partner_type: 'WAREHOUSE' })
  const [factForm, setFactForm] = useState({
    fact_key: '',
    fact_name: '',
    order_id: '',
    payload: '{"event":"demo"}',
  })
  const [webhookForm, setWebhookForm] = useState({
    network_player_code: 'INPOST',
    capability_code: 'MART_REFRESH',
    url: '',
    secret: '',
  })

  useEffect(() => {
    const t = searchParams.get('tab') as Tab | null
    if (t && TAB_KEYS.includes(t)) setTab(t)
  }, [searchParams])

  const switchTab = (next: Tab) => {
    setTab(next)
    setSearchParams({ tab: next }, { replace: true })
  }

  const loadEfficiency = useCallback(async () => {
    try {
      const [sc, dq, an, bm, pl] = await Promise.all([
        biAnalyticsAdminApi.efficiencyScorecard(),
        biAnalyticsAdminApi.listDqChecks(),
        biAnalyticsAdminApi.listAnomalySignals('OPEN'),
        biAnalyticsAdminApi.listBookmarks(),
        biAnalyticsAdminApi.listPipelineSync(),
      ])
      setEfficiency(sc.data)
      setDqChecks(dq.data.checks ?? [])
      setAnomalies(an.data.signals ?? [])
      setBookmarks(bm.data.bookmarks ?? [])
      setPipelines(Array.isArray(pl.data) ? pl.data : [])
    } catch {
      /* optional tab */
    }
  }, [])

  useEffect(() => {
    if (tab === 'efficiency') void loadEfficiency()
  }, [tab, loadEfficiency])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const failHint =
      'Verifique se analytics-bi-admin está ativo na porta 8026: cd 01_source/analytics_bi_admin_service && ./dev.sh'
    try {
      const results = await Promise.allSettled([
        biAnalyticsAdminApi.dashboard(),
        biAnalyticsAdminApi.listFacts({ limit: 50 }),
        biAnalyticsAdminApi.listKpis(),
        biAnalyticsAdminApi.listReports(),
        biAnalyticsAdminApi.listMarts(),
        biAnalyticsAdminApi.listPartners(),
        biAnalyticsAdminApi.listPlayers(),
        biAnalyticsAdminApi.listRelations(),
        biAnalyticsAdminApi.listCapabilityWebhooks(),
        biAnalyticsAdminApi.integrationLinks(),
        biAnalyticsAdminApi.opsIntelligence(),
        biAnalyticsAdminApi.listReadiness(),
        biAnalyticsAdminApi.listMartJobs(),
        biAnalyticsAdminApi.listAlertRules(),
        biAnalyticsAdminApi.listAlertEvents('OPEN'),
        biAnalyticsAdminApi.listLineage(),
        biAnalyticsAdminApi.listExportJobs(),
        biAnalyticsAdminApi.listTaxonomy(),
        biAnalyticsAdminApi.listMarketPresence(),
        biAnalyticsAdminApi.listDomainLinks(),
        biAnalyticsAdminApi.listAudit(),
        biAnalyticsAdminApi.tier1Coverage(),
      ])
      const firstReject = results.find((r) => r.status === 'rejected') as PromiseRejectedResult | undefined
      if (firstReject) {
        const err = firstReject.reason as { response?: { status?: number }; message?: string }
        const status = err?.response?.status
        if (status === 404) {
          setError(`API BI admin não encontrada (404). ${failHint}`)
        } else {
          setError(err?.message ?? 'Falha ao carregar BI/Analytics admin')
        }
      }
      if (results[0].status === 'fulfilled') setDash(results[0].value.data)
      if (results[1].status === 'fulfilled') setFacts(results[1].value.data.items)
      if (results[2].status === 'fulfilled') setKpis(results[2].value.data.items)
      if (results[3].status === 'fulfilled') setReports(results[3].value.data.items)
      if (results[4].status === 'fulfilled') setMarts(results[4].value.data)
      if (results[5].status === 'fulfilled') setPartners(results[5].value.data.partners)
      if (results[6].status === 'fulfilled') setPlayers(results[6].value.data.players)
      if (results[7].status === 'fulfilled') setRelations(results[7].value.data.relations)
      if (results[8].status === 'fulfilled') setWebhooks(results[8].value.data.webhooks)
      if (results[9].status === 'fulfilled') setIntegration(results[9].value.data)
      if (results[10].status === 'fulfilled') setOpsIntel(results[10].value.data)
      if (results[11].status === 'fulfilled') {
        setReadiness(results[11].value.data.rows)
        setReadinessBands(results[11].value.data.bands)
      }
      if (results[12].status === 'fulfilled') setMartJobs(results[12].value.data.jobs)
      if (results[13].status === 'fulfilled') setAlertRules(results[13].value.data.rules)
      if (results[14].status === 'fulfilled') setAlertEvents(results[14].value.data.events)
      if (results[15].status === 'fulfilled') setLineage(results[15].value.data.edges)
      if (results[16].status === 'fulfilled') setExportJobs(results[16].value.data.jobs)
      if (results[17].status === 'fulfilled') setTaxonomy(results[17].value.data.segments)
      if (results[18].status === 'fulfilled') setMarketPresence(results[18].value.data.presence)
      if (results[19].status === 'fulfilled') setDomainLinks(results[19].value.data.links)
      if (results[20].status === 'fulfilled') setAudit(results[20].value.data.events)
      if (results[21].status === 'fulfilled') setTier1Coverage(results[21].value.data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar BI/Analytics admin')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    await biAnalyticsAdminApi.seed()
    await biAnalyticsAdminApi.seedProfessional()
    await load()
  }

  const onRecomputeReadiness = async () => {
    await biAnalyticsAdminApi.recomputeReadiness()
    await load()
  }

  const onRefreshMart = async () => {
    await biAnalyticsAdminApi.triggerMartRefresh({ mart_name: 'locker_pnl', triggered_by: 'ops-ui' })
    await load()
  }

  const onExport = async () => {
    await biAnalyticsAdminApi.createExportJob({ dataset_code: 'PARTNER_REVENUE_MONTHLY' })
    await load()
  }

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    await biAnalyticsAdminApi.createPartner(partnerForm)
    setPartnerForm({ name: '', code: '', partner_type: 'WAREHOUSE' })
    await load()
  }

  const onRotateKey = async (partnerId: string) => {
    const r = await biAnalyticsAdminApi.rotateApiKey(partnerId)
    setRotatedKey(r.data.api_key)
    await load()
  }

  const onCreateFact = async (e: FormEvent) => {
    e.preventDefault()
    await biAnalyticsAdminApi.createFact({
      ...factForm,
      payload: JSON.parse(factForm.payload),
      occurred_at: new Date().toISOString(),
    })
    await load()
  }

  const onSeedPlayers = async () => {
    await biAnalyticsAdminApi.seedPlayers()
    await load()
  }

  const onCreateWebhook = async (e: FormEvent) => {
    e.preventDefault()
    await biAnalyticsAdminApi.createCapabilityWebhook(webhookForm)
    await load()
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4 text-slate-100 md:p-6" data-testid="ops-bi-analytics-admin">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">BI · Analytics · Machine Learning</h1>
          <p className="text-sm text-slate-400">
            Facts, marts financeiros, KPIs, catálogo de relatórios e ecossistema locker mundial
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="ellan-btn-secondary" onClick={() => void onSeed()}>
            Seed
          </button>
          <button type="button" className="ellan-btn-secondary" onClick={() => void load()}>
            Atualizar
          </button>
          <Link to="/ops/ml/admin" className="ellan-btn-secondary">
            ML OPS →
          </Link>
          <Link to="/ops/analytics/financial" className="ellan-btn-secondary">
            Analytics financeiro →
          </Link>
        </div>
      </header>

      {error && <p className="mb-3 text-red-400">{error}</p>}
      {loading && <p className="mb-3 text-slate-400">Carregando…</p>}

      <nav className="mb-4 flex flex-wrap gap-1 border-b border-slate-700 pb-2">
        {TAB_KEYS.map((k) => (
          <button
            key={k}
            type="button"
            className={`rounded px-3 py-1 text-sm ${tab === k ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            onClick={() => switchTab(k)}
          >
            {k}
          </button>
        ))}
      </nav>

      {tab === 'overview' && dash && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ['Facts', dash.facts_count],
            ['Facts 24h', dash.facts_24h],
            ['Parceiros BI', dash.partners],
            ['KPIs', dash.kpi_definitions],
            ['Relatórios', dash.report_catalog],
            ['Players', dash.network_players],
            ['MRR rows', dash.mrr_rows],
            ['Webhooks', dash.capability_webhooks],
            ['Readiness GO_LIVE', dash.readiness_go_live ?? 0],
            ['Score médio', dash.readiness_avg_score ?? 0],
            ['Alertas KPI', dash.open_kpi_alerts ?? 0],
            ['Lineage', dash.lineage_edges ?? 0],
            ['Presença mercado', dash.market_presence_rows ?? 0],
          ].map(([label, val]) => (
            <div key={String(label)} className={cardCls}>
              <p className="text-xs text-slate-400">{label}</p>
              <p className="text-2xl font-semibold">{val}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'intelligence' && opsIntel && (
        <div className={`${cardCls} grid gap-3 sm:grid-cols-2 lg:grid-cols-4`}>
          {Object.entries(opsIntel).map(([k, v]) => (
            <div key={k}>
              <p className="text-xs text-slate-400">{k}</p>
              <p className="text-xl font-semibold">{String(v)}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'readiness' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button type="button" className="ellan-btn-secondary" onClick={() => void onRecomputeReadiness()}>
              Recomputar readiness
            </button>
          </div>
          <div className={cardCls}>
            <p className="mb-2 text-sm text-slate-400">Bands: {JSON.stringify(readinessBands)}</p>
            <pre className="max-h-96 overflow-auto text-xs">{JSON.stringify(readiness, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'facts' && (
        <div className="space-y-4">
          <form onSubmit={(e) => void onCreateFact(e)} className={`${cardCls} grid gap-2 md:grid-cols-4`}>
            <input className={inputCls} placeholder="fact_key" value={factForm.fact_key} onChange={(e) => setFactForm({ ...factForm, fact_key: e.target.value })} required />
            <input className={inputCls} placeholder="fact_name" value={factForm.fact_name} onChange={(e) => setFactForm({ ...factForm, fact_name: e.target.value })} required />
            <input className={inputCls} placeholder="order_id" value={factForm.order_id} onChange={(e) => setFactForm({ ...factForm, order_id: e.target.value })} required />
            <button type="submit" className="ellan-btn-primary">Inserir fact</button>
          </form>
          <div className={cardCls}>
            <pre className="max-h-96 overflow-auto text-xs">{JSON.stringify(facts, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'marts' && marts && (
        <div className={`${cardCls} space-y-4`}>
          <section>
            <h2 className="font-medium text-indigo-300">company_mrr_trend</h2>
            <pre className="text-xs">{JSON.stringify(marts.mrr, null, 2)}</pre>
          </section>
          <section>
            <h2 className="font-medium text-indigo-300">locker_pnl</h2>
            <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(marts.locker_pnl, null, 2)}</pre>
          </section>
          <section>
            <h2 className="font-medium text-indigo-300">partner_revenue_monthly</h2>
            <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(marts.partner_revenue, null, 2)}</pre>
          </section>
        </div>
      )}

      {tab === 'refresh' && (
        <div className="space-y-4">
          <button type="button" className="ellan-btn-primary" onClick={() => void onRefreshMart()}>
            Disparar refresh locker_pnl
          </button>
          <div className={cardCls}>
            <pre className="text-xs">{JSON.stringify(martJobs, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'kpis' && (
        <div className={cardCls}>
          <pre className="text-xs">{JSON.stringify(kpis, null, 2)}</pre>
        </div>
      )}

      {tab === 'alerts' && (
        <div className={`${cardCls} space-y-4`}>
          <section>
            <h2 className="font-medium text-amber-300">Regras</h2>
            <pre className="text-xs">{JSON.stringify(alertRules, null, 2)}</pre>
          </section>
          <section>
            <h2 className="font-medium text-red-300">Eventos abertos</h2>
            <pre className="text-xs">{JSON.stringify(alertEvents, null, 2)}</pre>
          </section>
        </div>
      )}

      {tab === 'reports' && (
        <div className={cardCls}>
          <pre className="text-xs">{JSON.stringify(reports, null, 2)}</pre>
        </div>
      )}

      {tab === 'lineage' && (
        <div className={cardCls}>
          <pre className="text-xs">{JSON.stringify(lineage, null, 2)}</pre>
        </div>
      )}

      {tab === 'exports' && (
        <div className="space-y-4">
          <button type="button" className="ellan-btn-primary" onClick={() => void onExport()}>
            Novo export PARTNER_REVENUE_MONTHLY
          </button>
          <div className={cardCls}>
            <pre className="text-xs">{JSON.stringify(exportJobs, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'partners' && (
        <div className="space-y-4">
          <form onSubmit={(e) => void onCreatePartner(e)} className={`${cardCls} flex flex-wrap gap-2`}>
            <input className={inputCls} placeholder="Nome" value={partnerForm.name} onChange={(e) => setPartnerForm({ ...partnerForm, name: e.target.value })} required />
            <input className={inputCls} placeholder="Código" value={partnerForm.code} onChange={(e) => setPartnerForm({ ...partnerForm, code: e.target.value })} required />
            <button type="submit" className="ellan-btn-primary">Criar parceiro</button>
          </form>
          {rotatedKey && <p className="text-amber-300 text-sm">Nova API key: {rotatedKey}</p>}
          <ul className={`${cardCls} space-y-2`}>
            {partners.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700 pb-2">
                <span>
                  {p.code} — {p.name}
                </span>
                <button type="button" className="ellan-btn-secondary text-xs" onClick={() => void onRotateKey(p.id)}>
                  Rotacionar API key
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === 'players' && (
        <div className="space-y-4">
          {tier1Coverage && (
            <div className={cardCls}>
              <p className="text-sm text-emerald-300">
                Tier-1 mundial: {tier1Coverage.tier1_present}/{tier1Coverage.tier1_required} (
                {tier1Coverage.coverage_pct}%)
              </p>
              <p className="mt-1 text-xs text-slate-400">
                {tier1Coverage.tier1_codes.join(' · ')}
              </p>
            </div>
          )}
          <button type="button" className="ellan-btn-secondary" onClick={() => void onSeedPlayers()}>
            Seed catálogo global (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT, Worten, ECI…)
          </button>
          <div className={cardCls}>
            <pre className="max-h-64 overflow-auto text-xs">{JSON.stringify(players, null, 2)}</pre>
          </div>
          <div className={cardCls}>
            <h2 className="mb-2 font-medium">Relações</h2>
            <pre className="text-xs">{JSON.stringify(relations, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'taxonomy' && (
        <div className={`${cardCls} space-y-4`}>
          <section>
            <h2 className="font-medium">Segmentos</h2>
            <pre className="text-xs">{JSON.stringify(taxonomy, null, 2)}</pre>
          </section>
          <section>
            <h2 className="font-medium">Presença de mercado</h2>
            <pre className="max-h-64 overflow-auto text-xs">{JSON.stringify(marketPresence, null, 2)}</pre>
          </section>
        </div>
      )}

      {tab === 'webhooks' && (
        <div className="space-y-4">
          <form onSubmit={(e) => void onCreateWebhook(e)} className={`${cardCls} grid gap-2 md:grid-cols-4`}>
            <input className={inputCls} value={webhookForm.network_player_code} onChange={(e) => setWebhookForm({ ...webhookForm, network_player_code: e.target.value })} />
            <input className={inputCls} value={webhookForm.capability_code} onChange={(e) => setWebhookForm({ ...webhookForm, capability_code: e.target.value })} />
            <input className={inputCls} placeholder="URL" value={webhookForm.url} onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })} required />
            <button type="submit" className="ellan-btn-primary">Registrar webhook</button>
          </form>
          <div className={cardCls}>
            <pre className="text-xs">{JSON.stringify(webhooks, null, 2)}</pre>
          </div>
        </div>
      )}

      {tab === 'audit' && (
        <div className={cardCls}>
          <pre className="text-xs">{JSON.stringify(audit, null, 2)}</pre>
        </div>
      )}

      {tab === 'integration' && (
        <div className={cardCls}>
          <pre className="mb-4 text-xs">{JSON.stringify(integration, null, 2)}</pre>
          <h2 className="mb-2 font-medium">Domínios unificados BI · ML · Finance</h2>
          <pre className="text-xs">{JSON.stringify(domainLinks, null, 2)}</pre>
          <p className="mt-3 text-sm text-slate-400">
            analytics-service (8127) · ml-admin (8021) · analytics-bi-admin (8026)
          </p>
        </div>
      )}

      {tab === 'efficiency' && (
        <div className="space-y-4">
          <div className={`${cardCls} flex flex-wrap items-center gap-3`}>
            <span className="text-2xl font-bold text-indigo-300">
              {String(efficiency?.efficiency_score ?? '—')}
            </span>
            <span className="text-sm text-slate-400">efficiency score</span>
            <button
              type="button"
              className="ellan-btn-secondary"
              onClick={() => {
                void biAnalyticsAdminApi.runDqChecks().then(() => loadEfficiency())
              }}
            >
              Run DQ
            </button>
            <button
              type="button"
              className="ellan-btn-secondary"
              onClick={() => {
                void biAnalyticsAdminApi.scanAnomalies().then(() => loadEfficiency())
              }}
            >
              Scan anomalies
            </button>
            <button
              type="button"
              className="ellan-btn-secondary"
              onClick={() => {
                void biAnalyticsAdminApi.tickScheduledExports().then(() => loadEfficiency())
              }}
            >
              Tick exports
            </button>
            <button type="button" className="ellan-btn-secondary" onClick={() => void loadEfficiency()}>
              Atualizar
            </button>
          </div>
          <div className={cardCls}>
            <h2 className="mb-2 font-medium">Scorecard</h2>
            <pre className="text-xs">{JSON.stringify(efficiency, null, 2)}</pre>
          </div>
          <div className={`${cardCls} grid gap-4 md:grid-cols-2`}>
            <section>
              <h2 className="mb-2 font-medium">Data quality ({dqChecks.length})</h2>
              <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(dqChecks, null, 2)}</pre>
            </section>
            <section>
              <h2 className="mb-2 font-medium">Anomalies ({anomalies.length})</h2>
              <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(anomalies, null, 2)}</pre>
            </section>
            <section>
              <h2 className="mb-2 font-medium">Bookmarks</h2>
              <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(bookmarks, null, 2)}</pre>
            </section>
            <section>
              <h2 className="mb-2 font-medium">Pipeline sync</h2>
              <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(pipelines, null, 2)}</pre>
            </section>
          </div>
        </div>
      )}
    </div>
  )
}
