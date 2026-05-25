import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'
import {
  paymentsAdminApi,
  type EcosystemGraphPayload,
  type GlobalReadiness,
  type IntegrationMilestone,
  type PaymentIntelligenceSummary,
  type RoutingRule,
  type RoutingSuggestion,
} from '../../api/paymentsAdmin'
const EcosystemGraphFlow = lazy(() => import('../../components/payments/EcosystemGraphFlow'))
import CrossDomainPanel from '../../components/payments/CrossDomainPanel'
import MilestoneCrudPanel from '../../components/payments/MilestoneCrudPanel'
import RoutingRuleCrudPanel from '../../components/payments/RoutingRuleCrudPanel'

const TAB_KEYS = [
  'intelligence',
  'cross-domain',
  'graph',
  'ecosystem',
  'segments',
  'integrations',
  'coverage',
  'milestones',
  'corridors',
  'compliance',
  'routing',
  'incidents',
  'relations',
  'order-context',
  'transactions',
  'instructions',
  'splits',
  'payments',
  'batches',
  'webhooks',
  'deliveries',
  'holds',
  'vault',
  'events',
] as const

type Tab = (typeof TAB_KEYS)[number]

const TAB_LABELS: Record<Tab, string> = {
  intelligence: 'Inteligência',
  'cross-domain': 'Hub cross-domain',
  graph: 'Grafo ecossistema',
  ecosystem: 'Ecossistema mundial',
  segments: 'Segmentos',
  integrations: 'Integrações',
  coverage: 'Cobertura país',
  milestones: 'Roadmap',
  corridors: 'Corredores FX',
  compliance: 'Compliance',
  routing: 'Roteamento',
  incidents: 'Incidentes',
  relations: 'Relações players',
  'order-context': 'Contexto pedido',
  transactions: 'Transações',
  instructions: 'Instruções',
  splits: 'Splits',
  payments: 'Ledger',
  batches: 'Lotes conciliação',
  webhooks: 'Webhooks',
  deliveries: 'Entregas webhook',
  holds: 'Holds parceiro',
  vault: 'Cartões salvos',
  events: 'Gateway events',
}

function formatCents(cents: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

const PAYMENTS_PATH = '/ops/payments/admin'

export default function OpsPaymentsAdmin() {
  const { tab, setTab } = useOpsTabFromUrl(PAYMENTS_PATH, TAB_KEYS, 'intelligence')

  const [orderFilter, setOrderFilter] = useState('ORD-DEMO-INPOST-001')
  const [summary, setSummary] = useState<PaymentIntelligenceSummary | null>(null)
  const [globalReady, setGlobalReady] = useState<GlobalReadiness | null>(null)
  const [routingHint, setRoutingHint] = useState<RoutingSuggestion | null>(null)
  const [ecosystemGraph, setEcosystemGraph] = useState<EcosystemGraphPayload | null>(null)
  const [orderGraph, setOrderGraph] = useState<unknown>(null)
  const [routeCountry, setRouteCountry] = useState('BR')
  const [routeMethod, setRouteMethod] = useState('PIX')
  const [rows, setRows] = useState<unknown[]>([])
  const [selectedWebhook, setSelectedWebhook] = useState('')
  const [lastSecret, setLastSecret] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    const orderParams = orderFilter.trim() ? { order_id: orderFilter.trim() } : undefined
    try {
      if (tab === 'intelligence' || tab === 'graph') {
        if (tab === 'intelligence') {
          const [sumRes, gr, graph] = await Promise.all([
            paymentsAdminApi.intelligenceSummary(),
            paymentsAdminApi.globalReadiness(),
            paymentsAdminApi.ecosystemGraph(),
          ])
          setSummary(sumRes.data)
          setGlobalReady(gr.data)
          setEcosystemGraph(graph.data)
          try {
            const rg = await paymentsAdminApi.routingSuggest({
              country_code: routeCountry,
              payment_method: routeMethod,
              sales_channel: 'MARKETPLACE',
            })
            setRoutingHint(rg.data)
          } catch {
            setRoutingHint(null)
          }
          if (orderFilter.trim()) {
            const g = await paymentsAdminApi.orderGraph(orderFilter.trim())
            setOrderGraph(g.data)
          } else {
            setOrderGraph(null)
          }
        } else {
          setSummary(null)
          setGlobalReady(null)
          setRoutingHint(null)
          setOrderGraph(null)
          const graph = await paymentsAdminApi.ecosystemGraph()
          setEcosystemGraph(graph.data)
        }
        setRows([])
        return
      }
      setSummary(null)
      setGlobalReady(null)
      setRoutingHint(null)
      setEcosystemGraph(null)
      setOrderGraph(null)
      let res: { data: { items: unknown[] } }
      switch (tab) {
        case 'ecosystem':
          res = await paymentsAdminApi.listEcosystemPlayers({ active_only: false })
          break
        case 'segments':
          res = await paymentsAdminApi.listEcosystemSegments()
          break
        case 'integrations':
          res = await paymentsAdminApi.listPlayerIntegrations({ min_readiness: 0 })
          break
        case 'coverage':
          res = await paymentsAdminApi.listPlayerCountryCoverage()
          break
        case 'milestones':
          res = await paymentsAdminApi.listIntegrationMilestones()
          break
        case 'corridors':
          res = await paymentsAdminApi.listSettlementCorridors()
          break
        case 'compliance':
          res = await paymentsAdminApi.listPlayerCompliance()
          break
        case 'routing':
          res = await paymentsAdminApi.listRoutingRules({ active_only: false })
          break
        case 'incidents':
          res = await paymentsAdminApi.listIntegrationIncidents()
          break
        case 'relations':
          res = await paymentsAdminApi.listPlayerRelations()
          break
        case 'order-context':
          res = await paymentsAdminApi.listOrderContext()
          break
        case 'transactions':
          res = await paymentsAdminApi.listTransactions(orderParams)
          break
        case 'instructions':
          res = await paymentsAdminApi.listInstructions(orderParams)
          break
        case 'splits':
          res = await paymentsAdminApi.listSplits(orderParams)
          break
        case 'payments':
          res = await paymentsAdminApi.listPayments(orderParams)
          break
        case 'batches':
          res = await paymentsAdminApi.listReconciliationBatches()
          break
        case 'webhooks':
          res = await paymentsAdminApi.listWebhooks()
          break
        case 'deliveries':
          res = await paymentsAdminApi.listWebhookDeliveries()
          break
        case 'holds':
          res = await paymentsAdminApi.listPartnerHolds()
          break
        case 'vault':
          res = await paymentsAdminApi.listSavedMethods()
          break
        case 'events':
          res = await paymentsAdminApi.listGatewayEvents(orderParams)
          break
        case 'cross-domain':
          setRows([])
          setLoading(false)
          return
        default:
          res = { data: { items: [] } }
      }
      setRows(res.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [tab, orderFilter, routeCountry, routeMethod])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      await paymentsAdminApi.seed()
      setMessage('Seed mundial aplicado (players, contexto, lotes, holds).')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onRotateSecret = async () => {
    if (!selectedWebhook) return
    setLoading(true)
    try {
      const { data } = await paymentsAdminApi.rotateWebhookSecret(selectedWebhook)
      setLastSecret(data.secret)
      setMessage('Secret rotacionado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar')
    } finally {
      setLoading(false)
    }
  }

  const onRetryDelivery = async (id: string) => {
    setLoading(true)
    try {
      await paymentsAdminApi.retryWebhookDelivery(id)
      setMessage(`Retry enfileirado: ${id}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no retry')
    } finally {
      setLoading(false)
    }
  }

  const tableDetail = useMemo(() => {
    return (row: Record<string, unknown>) => {
      if (tab === 'ecosystem') {
        const meta = row.metadata_json as Record<string, unknown> | undefined
        const pri = meta?.payment_priority ? ' ★' : ''
        return `${row.segment} · ${JSON.stringify(row.countries_json)} · ${row.integration_status}${pri}`
      }
      if (tab === 'segments') {
        return `${row.name} · ${row.default_protocol}`
      }
      if (tab === 'integrations') {
        return `score ${row.readiness_score} · ${row.integration_protocol} · ${row.payment_capture_mode} · prod=${row.production_ready ? 'Y' : 'N'}`
      }
      if (tab === 'coverage') {
        return `${row.country_code} · ${row.coverage_role} · ${row.locker_density}${row.is_primary_market ? ' · primary' : ''}`
      }
      if (tab === 'milestones') {
        return `${row.player_code} · ${row.phase} · ${row.status} · ${row.title}`
      }
      if (tab === 'corridors') {
        return `${row.origin_country}→${row.destination_country} · ${row.source_player_code}→${row.settlement_player_code} · ${row.fee_basis_points}bps`
      }
      if (tab === 'compliance') {
        return `${row.country_code} · ${row.regulatory_framework} · ${row.audit_status} · risk ${row.risk_tier}`
      }
      if (tab === 'routing') {
        return `${row.country_code} · ${row.payment_method} · ${row.primary_player_code} → ${row.fallback_player_code ?? '—'}`
      }
      if (tab === 'incidents') {
        return `${row.severity} · ${row.incident_type} · ${row.status} · ${row.title}`
      }
      if (tab === 'relations') {
        return `${row.from_player_code} → ${row.to_player_code} · ${row.relation_type}`
      }
      if (tab === 'order-context') {
        return `${row.order_id} · ${row.locker_network_code} · ${row.status} · ${row.total_amount_cents}c`
      }
      if (tab === 'batches') {
        return `${row.batch_code} · ${row.gateway} · ${row.status} · matched ${row.matched_count}/${row.expected_count}`
      }
      if (tab === 'deliveries') {
        return `${row.event_name} · ${row.status} · attempts ${row.attempt_count}`
      }
      if (tab === 'holds') {
        return `${row.partner_id} · ${row.hold_amount_cents}c · ${row.status}`
      }
      if (tab === 'vault') {
        return `${row.user_id} · ${row.method_code} · ****${row.last4}`
      }
      return JSON.stringify(row)
    }
  }, [tab])

  return (
    <div className={`mx-auto space-y-6 ${tab === 'graph' ? 'max-w-[96rem]' : 'max-w-6xl'}`}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Payments</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Domínio PAYMENT com relação a pedidos, lockers, marketplaces, carriers e financeiro.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="ellan-btn-outline">
            Seed mundial
          </button>
          <button type="button" onClick={() => void load()} className="ellan-btn-outline">
            {loading ? '…' : 'Atualizar'}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        <Link to="/ops/payment-gateway/admin" className="text-blue-600 underline">
          Payment Gateway
        </Link>
        <Link to="/ops/money-cambio/admin" className="text-blue-600 underline">
          Money &amp; Câmbio
        </Link>
        <Link to="/ops/finance/admin?tab=treasury" className="text-blue-600 underline">
          Finance (holds)
        </Link>
        <Link to="/ops/marketplace/admin" className="text-blue-600 underline">
          Marketplace
        </Link>
      </div>

      {loading ? (
        <p className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm text-indigo-800 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200">
          Carregando aba «{TAB_LABELS[tab]}»…
        </p>
      ) : null}
      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30">
          {error} — verifique payments-admin na porta 8126.
        </p>
      ) : null}
      {tab === 'intelligence' && !loading && !error && !summary ? (
        <p className="text-sm text-amber-700">
          Sem KPIs ainda. Inicie o backend, clique em «Seed mundial» ou «Atualizar».
        </p>
      ) : null}

      <div className="flex flex-wrap gap-1">
        {TAB_KEYS.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setTab(k)}
            className={`rounded-lg border px-2 py-1 text-xs ${tab === k ? 'bg-slate-800 text-white' : ''}`}
          >
            {TAB_LABELS[k]}
          </button>
        ))}
      </div>

      {tab === 'cross-domain' ? (
        <CrossDomainPanel
          orderFilter={orderFilter}
          onMessage={setMessage}
          onError={setError}
        />
      ) : null}

      {tab === 'graph' ? (
        <Suspense fallback={<p className="text-sm text-gray-500">Carregando grafo…</p>}>
          <EcosystemGraphFlow graph={ecosystemGraph} loading={loading} error={error} height={640} />
        </Suspense>
      ) : null}

      {tab === 'intelligence' && ecosystemGraph ? (
        <Suspense fallback={<p className="text-sm text-gray-500">Carregando grafo…</p>}>
          <EcosystemGraphFlow graph={ecosystemGraph} height={380} />
        </Suspense>
      ) : null}

      {tab === 'milestones' ? (
        <MilestoneCrudPanel
          rows={rows as IntegrationMilestone[]}
          onSaved={() => void load()}
          onMessage={setMessage}
          onError={setError}
        />
      ) : null}

      {tab === 'routing' ? (
        <RoutingRuleCrudPanel
          rows={rows as RoutingRule[]}
          onSaved={() => void load()}
          onMessage={setMessage}
          onError={setError}
        />
      ) : null}

      {![
        'ecosystem',
        'segments',
        'integrations',
        'coverage',
        'milestones',
        'corridors',
        'compliance',
        'routing',
        'incidents',
        'cross-domain',
        'graph',
      ].includes(tab) ? (
        <label className="block text-sm">
          order_id (grafo / filtros)
          <input
            value={orderFilter}
            onChange={(e) => setOrderFilter(e.target.value)}
            className="mt-1 w-full max-w-md ellan-field"
          />
        </label>
      ) : null}

      {tab === 'intelligence' && summary ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ['Transações', `${summary.transactions_approved}/${summary.transactions_total}`],
            ['Conciliação pendente', String(summary.reconciliation_pending)],
            ['Lotes abertos', String(summary.open_batches)],
            ['Webhooks pendentes', String(summary.webhook_pending)],
            ['Holds ativos', formatCents(summary.holds_active_cents)],
            ['Players LIVE', `${summary.ecosystem_players_live}/${summary.ecosystem_players_total}`],
            ['Prioritários LIVE', String(summary.priority_players_live)],
            ['Relações', String(summary.player_relations_total)],
            ['Pedidos c/ contexto', String(summary.orders_with_context)],
            ['Segmentos taxonomia', String(summary.ecosystem_segments_defined)],
            ['Cobertura país', String(summary.country_coverage_rows)],
            ['Integrações prod', String(summary.integrations_production_ready)],
            ['Readiness médio', String(summary.integrations_avg_readiness)],
            ['Incidentes abertos', String(summary.open_integration_incidents)],
            ['Corredores FX', String(summary.active_settlement_corridors)],
            ['Regras roteamento', String(summary.routing_rules_active)],
            ['Marcos em curso', String(summary.milestones_in_progress)],
            ['Vínculos externos', String(summary.external_references_total)],
            ['Obrigações pendentes', String(summary.pending_domain_obligations)],
            ['Bloqueantes', String(summary.blocking_domain_obligations)],
            ['Gaps cross-domain', String(summary.cross_domain_gaps_detected)],
            ['Eventos pendentes', String(summary.cross_domain_events_pending)],
          ].map(([label, val]) => (
            <div key={label} className="rounded-lg border p-3 text-sm">
              <div className="text-gray-500">{label}</div>
              <div className="text-lg font-semibold">{val}</div>
            </div>
          ))}
          <div className="rounded-lg border p-3 text-sm sm:col-span-2">
            <div className="text-gray-500">Segmentos ecossistema</div>
            <pre className="mt-1 text-xs">{JSON.stringify(summary.segments, null, 2)}</pre>
          </div>
        </div>
      ) : null}

      {tab === 'intelligence' && globalReady ? (
        <div className="rounded-lg border p-4 text-sm">
          <div className="font-medium text-gray-700 dark:text-slate-300">Prontidão global</div>
          <p className="mt-1 text-xs text-gray-600">
            Produção: {globalReady.production_integrations}/{globalReady.players_total} · readiness{' '}
            {globalReady.avg_readiness} · corredores {globalReady.active_corridors} · compliance aprovado{' '}
            {globalReady.compliance_approved}
          </p>
          {globalReady.top_risk_players.length ? (
            <p className="mt-1 text-xs text-amber-700">
              Risco alto: {globalReady.top_risk_players.join(', ')}
            </p>
          ) : null}
        </div>
      ) : null}

      {tab === 'intelligence' ? (
        <div className="flex flex-wrap items-end gap-2 rounded-lg border p-3 text-sm">
          <label>
            país
            <input
              value={routeCountry}
              onChange={(e) => setRouteCountry(e.target.value.toUpperCase())}
              className="ml-1 w-12 rounded border px-1 dark:bg-slate-900"
            />
          </label>
          <label>
            método
            <input
              value={routeMethod}
              onChange={(e) => setRouteMethod(e.target.value.toUpperCase())}
              className="ml-1 w-28 rounded border px-1 dark:bg-slate-900"
            />
          </label>
          <button type="button" onClick={() => void load()} className="rounded border px-2 py-1 text-xs">
            Simular roteamento
          </button>
          {routingHint ? (
            <span className="text-xs text-green-700">
              → {routingHint.primary_player_code}
              {routingHint.fallback_player_code ? ` / ${routingHint.fallback_player_code}` : ''} (
              {routingHint.rule_code})
            </span>
          ) : null}
        </div>
      ) : null}

      {tab === 'intelligence' && orderGraph ? (
        <pre className="max-h-96 overflow-auto rounded-lg border bg-slate-50 p-3 text-xs dark:bg-slate-900">
          {JSON.stringify(orderGraph, null, 2)}
        </pre>
      ) : null}

      {tab === 'webhooks' ? (
        <div className="flex flex-wrap items-end gap-2 rounded-lg border p-4">
          <select
            value={selectedWebhook}
            onChange={(e) => setSelectedWebhook(e.target.value)}
            className="ellan-field dark:bg-slate-900"
          >
            <option value="">endpoint —</option>
            {(rows as { id: string; partner_type: string }[]).map((w) => (
              <option key={w.id} value={w.id}>
                {w.id}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => void onRotateSecret()} className="ellan-btn-outline">
            Rotacionar secret
          </button>
          {lastSecret ? <code className="text-xs">{lastSecret}</code> : null}
        </div>
      ) : null}

      {tab !== 'intelligence' && tab !== 'graph' ? (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-100 dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">id / code</th>
                <th className="px-3 py-2">detalhe</th>
                {tab === 'deliveries' ? <th className="px-3 py-2">ação</th> : null}
              </tr>
            </thead>
            <tbody>
              {(rows as Record<string, unknown>[]).map((row, i) => (
                <tr key={String(row.id ?? row.code ?? i)} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs">
                    {String(row.id ?? row.code ?? row.player_code ?? row.rule_code ?? row.corridor_code ?? '—')}
                  </td>
                  <td className="px-3 py-2 text-xs">{tableDetail(row)}</td>
                  {tab === 'deliveries' ? (
                    <td className="px-3 py-2">
                      {row.status === 'PENDING' ? (
                        <button
                          type="button"
                          className="text-xs text-blue-600 underline"
                          onClick={() => void onRetryDelivery(String(row.id))}
                        >
                          retry
                        </button>
                      ) : null}
                    </td>
                  ) : null}
                </tr>
              ))}
              {!rows.length ? (
                <tr>
                  <td colSpan={3} className="px-3 py-4 text-gray-500">
                    Nenhum registro.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
