import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { orderPickupAdminApi } from '../../api/orderPickupAdmin'
import {
  workersAdminApi,
  type InventorySyncRow,
  type LifecycleDeadlineRow,
  type WorkerDlqRow,
  type WorkerQueueStats,
} from '../../api/workersAdmin'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'
import { useAuth } from '../../contexts/AuthContext'

const PAGE_VERSION = 'ops/workers/admin v1.0'
const API_BASE = '/api/order-pickup-admin/v1/order-pickup-admin'

const TABS = ['overview', 'domain', 'lifecycle', 'inventory', 'dlq'] as const
type Tab = (typeof TABS)[number]

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Visão geral',
  domain: 'Domain outbox',
  lifecycle: 'Lifecycle',
  inventory: 'Inventory sync',
  dlq: 'Dead letter',
}

const inp =
  'ellan-field w-full rounded-lg border border-slate-600/70 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 dark:border-slate-600 dark:bg-slate-800'

type DomainOutboxRow = {
  id: string
  event_key: string
  event_name?: string | null
  aggregate_id?: string | null
  status: string
  retry_count: number
}

const WORKER_STATUS_CLASS: Record<string, string> = {
  PENDING: 'bg-amber-500/20 text-amber-200 ring-amber-500/40',
  PROCESSING: 'bg-sky-500/20 text-sky-200 ring-sky-500/40',
  PUBLISHED: 'bg-emerald-500/20 text-emerald-200 ring-emerald-500/40',
  SYNCED: 'bg-emerald-500/20 text-emerald-200 ring-emerald-500/40',
  EXECUTED: 'bg-emerald-500/20 text-emerald-200 ring-emerald-500/40',
  FAILED: 'bg-red-500/20 text-red-200 ring-red-500/40',
  DEAD_LETTER: 'bg-orange-500/20 text-orange-200 ring-orange-500/40',
  EXECUTING: 'bg-violet-500/20 text-violet-200 ring-violet-500/40',
  CANCELLED: 'bg-slate-500/20 text-slate-300 ring-slate-500/40',
}

function statusPill(status: string) {
  const key = String(status || '').toUpperCase()
  const cls = WORKER_STATUS_CLASS[key] ?? 'bg-slate-500/15 text-slate-300 ring-slate-500/30'
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${cls}`}>
      {status || '—'}
    </span>
  )
}

function sumCounts(counts?: Record<string, number>) {
  return Object.values(counts ?? {}).reduce((n, v) => n + Number(v || 0), 0)
}

function OverviewKpis({ stats }: { stats: WorkerQueueStats | null }) {
  if (!stats) {
    return (
      <p className="text-xs text-slate-400">Use Listar para carregar o resumo das filas.</p>
    )
  }
  const blocks: {
    title: string
    counts: Record<string, number>
    tab: Tab
    hint: string
  }[] = [
    {
      title: 'Domain event outbox',
      counts: stats.domain_event_outbox,
      tab: 'domain',
      hint: 'Webhooks parceiros · retry máx. 5',
    },
    {
      title: 'Lifecycle deadlines',
      counts: stats.lifecycle_deadlines,
      tab: 'lifecycle',
      hint: 'PREPAYMENT · POSTPAYMENT · PICKUP',
    },
    {
      title: 'Inventory sync',
      counts: stats.inventory_sync_queue,
      tab: 'inventory',
      hint: 'Shopee · Magalu · Mercado Livre',
    },
    {
      title: 'Dead letter',
      counts: stats.worker_dead_letter_queue,
      tab: 'dlq',
      hint: 'Falhas permanentes por worker',
    },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {blocks.map((b) => {
        const total = sumCounts(b.counts)
        const pending = Number(b.counts?.PENDING ?? 0)
        const failed =
          Number(b.counts?.FAILED ?? 0) + Number(b.counts?.DEAD_LETTER ?? 0)
        return (
          <div
            key={b.title}
            className="rounded-xl border border-slate-600/60 bg-slate-950/80 p-4 dark:border-slate-700"
          >
            <p className="text-xs font-medium text-slate-400">{b.title}</p>
            <p className="mt-1 text-2xl font-bold text-slate-50">{total}</p>
            <p className="mt-2 text-xs text-slate-500">{b.hint}</p>
            <ul className="mt-3 space-y-1 text-xs text-slate-400">
              {Object.entries(b.counts).map(([k, v]) => (
                <li key={k} className="flex items-center justify-between gap-2">
                  {statusPill(k)}
                  <span className="font-mono text-slate-300">{v}</span>
                </li>
              ))}
              {!Object.keys(b.counts).length ? (
                <li className="text-slate-500">Sem registros</li>
              ) : null}
            </ul>
            <p className="mt-3 text-xs text-slate-500">
              PENDING: {pending} · falhas/DLQ: {failed}
            </p>
            <Link
              to={`/ops/workers/admin?tab=${b.tab}`}
              className="mt-3 inline-block text-xs font-semibold text-indigo-400 hover:text-indigo-300"
            >
              Abrir fila →
            </Link>
          </div>
        )
      })}
    </div>
  )
}

export default function OpsWorkersAdmin() {
  const { tab, setTab } = useOpsTabFromUrl<Tab>('/ops/workers/admin', TABS, 'overview')
  const { isAuthenticated, profile } = useAuth()
  const canReplay = profile === 'admin' || profile === 'ops'

  const [stats, setStats] = useState<WorkerQueueStats | null>(null)
  const [domainOutbox, setDomainOutbox] = useState<DomainOutboxRow[]>([])
  const [lifecycle, setLifecycle] = useState<LifecycleDeadlineRow[]>([])
  const [inventory, setInventory] = useState<InventorySyncRow[]>([])
  const [dlq, setDlq] = useState<WorkerDlqRow[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [marketplaceFilter, setMarketplaceFilter] = useState('')
  const [dlqWorkerFilter, setDlqWorkerFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const statusParam = statusFilter || undefined
      const [st, dom, life, inv, dl] = await Promise.all([
        workersAdminApi.stats(),
        orderPickupAdminApi.listDomainOutbox({ status: statusParam }),
        workersAdminApi.listLifecycle({
          status: statusParam,
          deadline_type: undefined,
        }),
        workersAdminApi.listInventory({
          status: statusParam,
          marketplace: marketplaceFilter || undefined,
        }),
        workersAdminApi.listDlq({
          worker_name: dlqWorkerFilter || undefined,
        }),
      ])
      setStats(st.data)
      setDomainOutbox((dom.data.items ?? []) as DomainOutboxRow[])
      setLifecycle(life.data.items ?? [])
      setInventory(inv.data.items ?? [])
      setDlq(dl.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar workers')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, marketplaceFilter, dlqWorkerFilter])

  useEffect(() => {
    if (isAuthenticated) void load()
    // Listar reaplica filtros; carga inicial ao montar
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  const setTabAndUrl = (next: Tab) => {
    setTab(next)
    setStatusFilter('')
    setMarketplaceFilter('')
    setDlqWorkerFilter('')
  }

  const onReplayDomain = async (id: string) => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      await orderPickupAdminApi.replayDomainOutbox(id)
      setMessage(`Domain outbox ${id} reenfileirado (PENDING).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Replay falhou')
    } finally {
      setLoading(false)
    }
  }

  const onReplayInventory = async (id: string) => {
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      await workersAdminApi.replayInventory(id)
      setMessage(`Inventory sync ${id} reenfileirado (PENDING).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Replay falhou')
    } finally {
      setLoading(false)
    }
  }

  const listCount = useMemo(() => {
    if (tab === 'domain') return domainOutbox.length
    if (tab === 'lifecycle') return lifecycle.length
    if (tab === 'inventory') return inventory.length
    if (tab === 'dlq') return dlq.length
    return 0
  }, [tab, domainOutbox, lifecycle, inventory, dlq])

  const listTitle =
    tab === 'domain'
      ? `Domain event outbox (${listCount})`
      : tab === 'lifecycle'
        ? `Lifecycle deadlines (${listCount})`
        : tab === 'inventory'
          ? `Inventory sync queue (${listCount})`
          : tab === 'dlq'
            ? `Dead letter queue (${listCount})`
            : ''

  const tableWrap = 'overflow-x-auto rounded-lg border border-slate-700/80'
  const th =
    'px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-400'
  const td = 'px-3 py-2 text-sm text-slate-200 align-top border-t border-slate-800'

  return (
    <div className="space-y-4 p-4" data-testid="ops-workers-admin-page">
      <div className="flex flex-wrap justify-end gap-2">
        <Link
          to="/ops/orders/admin?tab=overview"
          className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20"
        >
          Pedidos OPS
        </Link>
        <Link
          to="/ops/marketplace/admin"
          className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20"
        >
          Marketplace
        </Link>
        <Link
          to="/ops/partners/admin"
          className="rounded-lg border border-indigo-500/50 bg-indigo-500/10 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/20"
        >
          Parceiros
        </Link>
      </div>

      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold text-slate-50">OPS — Workers PostgreSQL (Node)</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Filas <code className="text-slate-300">domain_event_outbox</code>,{' '}
            <code className="text-slate-300">lifecycle_deadlines</code>,{' '}
            <code className="text-slate-300">inventory_sync_queue</code> — cron 10s · SKIP LOCKED
          </p>
          <p className="mt-1 font-mono text-xs text-slate-500">
            {PAGE_VERSION} · {API_BASE}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading || !isAuthenticated}
          className="ellan-btn-outline"
        >
          {loading ? 'Atualizando…' : 'Listar'}
        </button>
      </header>

      {message ? (
        <p className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950 dark:text-red-200">
          {error}
        </p>
      ) : null}
      {!isAuthenticated ? (
        <p className="text-xs text-slate-400">Faça login com perfil OPS para listar as filas.</p>
      ) : null}
      {isAuthenticated && !canReplay ? (
        <p className="text-xs text-slate-400">Replay disponível para perfis admin ou ops.</p>
      ) : null}

      <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-medium text-slate-200">Filas e monitoramento</h2>
          <div className="flex flex-wrap gap-1 border-b border-slate-700/80 dark:border-slate-700">
            {(TABS as readonly Tab[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setTabAndUrl(key)}
                className={`rounded-t px-3 py-2 text-sm ${
                  tab === key
                    ? 'border-b-2 border-indigo-500 font-medium text-indigo-300'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {TAB_LABELS[key]}
              </button>
            ))}
          </div>
        </div>

        {tab === 'overview' ? (
          <p className="mb-3 text-xs text-slate-400">
            KPIs por fila. Nas outras abas, filtre por status e use Replay para reenfileirar itens com falha.
          </p>
        ) : null}
        {tab === 'domain' ? (
          <p className="mb-3 text-xs text-slate-400">
            Publicação via <code className="text-slate-300">partner_webhook_endpoints</code> (backoff
            exponencial, máx. 5 tentativas).
          </p>
        ) : null}
        {tab === 'lifecycle' ? (
          <p className="mb-3 text-xs text-slate-400">
            PREPAYMENT_TIMEOUT, POSTPAYMENT_EXPIRY, PICKUP_TIMEOUT — cancelar pedido, liberar slot,
            notificar.
          </p>
        ) : null}
        {tab === 'inventory' ? (
          <p className="mb-3 text-xs text-slate-400">
            Rate limit por marketplace. Auditoria em{' '}
            <code className="text-slate-300">marketplace_sync_audit_log</code>.
          </p>
        ) : null}
        {tab === 'dlq' ? (
          <p className="mb-3 text-xs text-slate-400">
            Registros em <code className="text-slate-300">worker_dead_letter_queue</code> após
            esgotar tentativas.
          </p>
        ) : null}

        {tab !== 'overview' ? (
          <div className="mb-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {tab !== 'dlq' ? (
              <label className="grid gap-1 text-xs text-slate-400">
                status
                <select
                  className={inp}
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">— todos —</option>
                  <option value="PENDING">PENDING</option>
                  <option value="PROCESSING">PROCESSING</option>
                  <option value="FAILED">FAILED</option>
                  {tab === 'domain' ? <option value="PUBLISHED">PUBLISHED</option> : null}
                  {tab === 'lifecycle' ? (
                    <>
                      <option value="EXECUTING">EXECUTING</option>
                      <option value="EXECUTED">EXECUTED</option>
                      <option value="CANCELLED">CANCELLED</option>
                    </>
                  ) : null}
                  {tab === 'inventory' ? (
                    <>
                      <option value="SYNCED">SYNCED</option>
                      <option value="DEAD_LETTER">DEAD_LETTER</option>
                    </>
                  ) : null}
                </select>
              </label>
            ) : (
              <label className="grid gap-1 text-xs text-slate-400">
                worker_name
                <select
                  className={inp}
                  value={dlqWorkerFilter}
                  onChange={(e) => setDlqWorkerFilter(e.target.value)}
                >
                  <option value="">— todos —</option>
                  <option value="domain_event_outbox">domain_event_outbox</option>
                  <option value="lifecycle_deadlines">lifecycle_deadlines</option>
                  <option value="inventory_sync_queue">inventory_sync_queue</option>
                </select>
              </label>
            )}
            {tab === 'inventory' ? (
              <label className="grid gap-1 text-xs text-slate-400">
                marketplace
                <select
                  className={inp}
                  value={marketplaceFilter}
                  onChange={(e) => setMarketplaceFilter(e.target.value)}
                >
                  <option value="">— todos —</option>
                  <option value="SHOPEE">SHOPEE</option>
                  <option value="MAGALU">MAGALU</option>
                  <option value="MERCADO_LIVRE">MERCADO_LIVRE</option>
                </select>
              </label>
            ) : null}
          </div>
        ) : null}
      </section>

      {tab === 'overview' ? (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-3 text-sm font-medium text-slate-200">Resumo das filas</h2>
          <OverviewKpis stats={stats} />
        </section>
      ) : null}

      {tab !== 'overview' && listCount > 0 ? (
        <section className="rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-3 text-sm font-medium text-slate-200">{listTitle}</h2>
          <div className={tableWrap}>
            {tab === 'domain' ? (
              <table className="w-full min-w-[520px] border-collapse text-sm">
                <thead className="bg-slate-950/60">
                  <tr>
                    {['evento', 'aggregate', 'status', 'retries', 'ação'].map((h) => (
                      <th key={h} className={th}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {domainOutbox.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-800/40">
                      <td className={td}>
                        <div>{row.event_name || '—'}</div>
                        <code className="text-xs text-slate-500">{row.event_key}</code>
                      </td>
                      <td className={td}>
                        <code className="text-xs">{row.aggregate_id || '—'}</code>
                      </td>
                      <td className={td}>{statusPill(row.status)}</td>
                      <td className={td}>{row.retry_count ?? 0}</td>
                      <td className={td}>
                        {row.status !== 'PUBLISHED' && canReplay ? (
                          <button
                            type="button"
                            className="ellan-btn-outline text-xs"
                            onClick={() => void onReplayDomain(row.id)}
                            disabled={loading}
                          >
                            Replay
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}

            {tab === 'lifecycle' ? (
              <table className="w-full min-w-[520px] border-collapse text-sm">
                <thead className="bg-slate-950/60">
                  <tr>
                    {['tipo', 'pedido', 'status', 'due_at', 'falhas'].map((h) => (
                      <th key={h} className={th}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lifecycle.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-800/40">
                      <td className={td}>{statusPill(row.deadline_type)}</td>
                      <td className={td}>
                        <code className="text-xs">{row.order_id}</code>
                      </td>
                      <td className={td}>{statusPill(row.status)}</td>
                      <td className={td}>
                        {row.due_at ? new Date(row.due_at).toLocaleString('pt-BR') : '—'}
                      </td>
                      <td className={td}>{row.failure_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}

            {tab === 'inventory' ? (
              <table className="w-full min-w-[520px] border-collapse text-sm">
                <thead className="bg-slate-950/60">
                  <tr>
                    {['marketplace', 'produto', 'qtd', 'status', 'retries', 'ação'].map((h) => (
                      <th key={h} className={th}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-800/40">
                      <td className={td}>{statusPill(row.marketplace)}</td>
                      <td className={td}>
                        <code className="text-xs">{row.product_id}</code>
                      </td>
                      <td className={td}>{row.quantity_available}</td>
                      <td className={td}>{statusPill(row.status)}</td>
                      <td className={td}>{row.retry_count ?? 0}</td>
                      <td className={td}>
                        {row.status !== 'SYNCED' && canReplay ? (
                          <button
                            type="button"
                            className="ellan-btn-outline text-xs"
                            onClick={() => void onReplayInventory(row.id)}
                            disabled={loading}
                          >
                            Replay
                          </button>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}

            {tab === 'dlq' ? (
              <table className="w-full min-w-[520px] border-collapse text-sm">
                <thead className="bg-slate-950/60">
                  <tr>
                    {['worker', 'origem', 'tentativas', 'erro', 'quando'].map((h) => (
                      <th key={h} className={th}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dlq.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-800/40">
                      <td className={td}>
                        <code className="text-xs">{row.worker_name}</code>
                      </td>
                      <td className={td}>
                        <code className="text-xs">{row.source_table}</code>
                        <span className="text-slate-500"> / </span>
                        <code className="text-xs">{row.source_id}</code>
                      </td>
                      <td className={td}>{row.attempt_count}</td>
                      <td className={td} title={row.error_message ?? ''}>
                        <span className="block max-w-xs truncate">{row.error_message || '—'}</span>
                      </td>
                      <td className={td}>
                        {row.dead_lettered_at
                          ? new Date(row.dead_lettered_at).toLocaleString('pt-BR')
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </div>
        </section>
      ) : null}

      {tab !== 'overview' && isAuthenticated && !loading && listCount === 0 ? (
        <p className="text-xs text-slate-400">
          Nenhum registro para os filtros atuais. Ajuste status ou use Listar.
        </p>
      ) : null}
    </div>
  )
}
