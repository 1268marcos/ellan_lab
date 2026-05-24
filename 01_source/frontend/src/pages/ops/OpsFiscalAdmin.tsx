import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fiscalAdminApi, type FiscalIssuer, type GapWorkbenchResponse, type UnifiedGap } from '../../api/fiscalAdmin'

const TABS = [
  'global',
  'intelligence',
  'issuers',
  'documents',
  'gaps',
  'corridors',
  'readiness',
  'certifications',
  'classification',
  'slo',
  'webhooks',
  'config',
  'governance',
] as const
type Tab = (typeof TABS)[number]

export default function OpsFiscalAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') || 'global'
  const tab: Tab = TABS.includes(tabParam as Tab) ? (tabParam as Tab) : 'global'
  const setTab = (t: Tab) => setSearchParams({ tab: t }, { replace: true })
  const [issuers, setIssuers] = useState<FiscalIssuer[]>([])
  const [documents, setDocuments] = useState<unknown[]>([])
  const [gapWorkbench, setGapWorkbench] = useState<GapWorkbenchResponse | null>(null)
  const [gapStatusFilter, setGapStatusFilter] = useState('OPEN')
  const [gapRefreshBilling, setGapRefreshBilling] = useState(false)
  const [gapIncludeSnapshot, setGapIncludeSnapshot] = useState(false)
  const [tenants, setTenants] = useState<unknown[]>([])
  const [products, setProducts] = useState<unknown[]>([])
  const [health, setHealth] = useState<unknown[]>([])
  const [approvals, setApprovals] = useState<unknown[]>([])
  const [callbacks, setCallbacks] = useState<unknown[]>([])
  const [summary, setSummary] = useState<Record<string, number> | null>(null)
  const [corridors, setCorridors] = useState<unknown[]>([])
  const [readiness, setReadiness] = useState<unknown[]>([])
  const [certifications, setCertifications] = useState<unknown[]>([])
  const [classRules, setClassRules] = useState<unknown[]>([])
  const [classLogs, setClassLogs] = useState<unknown[]>([])
  const [slos, setSlos] = useState<unknown[]>([])
  const [webhookDlq, setWebhookDlq] = useState<unknown[]>([])
  const [jurisdictions, setJurisdictions] = useState<unknown[]>([])
  const [intelDash, setIntelDash] = useState<Record<string, number> | null>(null)
  const [insights, setInsights] = useState<unknown[]>([])
  const [contingencies, setContingencies] = useState<unknown[]>([])
  const [corridorDetail, setCorridorDetail] = useState<Record<string, unknown> | null>(null)
  const [classifySku, setClassifySku] = useState('SKU-LOCKER-RENT-01')
  const [classifyResult, setClassifyResult] = useState<Record<string, unknown> | null>(null)
  const [contingencyForm, setContingencyForm] = useState({
    country: 'BR',
    region_code: 'SP',
    authority: 'SEFAZ-SP',
    contingency_mode: 'SVC-AN',
    reason: '',
    issuer_code: 'SEFAZ-BR-SP',
  })
  const [issuerForm, setIssuerForm] = useState({ name: '', code: '', issuer_type: 'SEFAZ', country: 'BR' })
  const [selectedIssuer, setSelectedIssuer] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [sm, i, d, wb, t, p, h, a, c, cor, rd, cert, cr, cl, slo, wh, jur, idash, ins, cont] = await Promise.all([
        fiscalAdminApi.globalSummary(),
        fiscalAdminApi.listIssuers(),
        fiscalAdminApi.listDocuments(),
        fiscalAdminApi.listGapsWorkbench({
          status: gapStatusFilter || undefined,
          refresh_billing: gapRefreshBilling,
          include_snapshot: gapIncludeSnapshot,
        }),
        fiscalAdminApi.listTenants(),
        fiscalAdminApi.listProducts(),
        fiscalAdminApi.listProviderHealth(),
        fiscalAdminApi.listApprovals(),
        fiscalAdminApi.listCallbacks(),
        fiscalAdminApi.listCorridors(),
        fiscalAdminApi.listReadiness(),
        fiscalAdminApi.listCertifications(undefined, true),
        fiscalAdminApi.listClassRules(),
        fiscalAdminApi.listClassificationLogs(),
        fiscalAdminApi.listSloPolicies(),
        fiscalAdminApi.listWebhookDlq(),
        fiscalAdminApi.listJurisdictions(),
        fiscalAdminApi.intelligenceDashboard(),
        fiscalAdminApi.listIntelligenceInsights(),
        fiscalAdminApi.listContingencies(false),
      ])
      setSummary(sm.data)
      setIssuers(i.data.issuers ?? [])
      setDocuments(d.data.items ?? [])
      setGapWorkbench(wb.data)
      setTenants(t.data.items ?? [])
      setProducts(p.data.items ?? [])
      setHealth(h.data.items ?? [])
      setApprovals(a.data.items ?? [])
      setCallbacks(c.data.items ?? [])
      setCorridors(cor.data.items ?? [])
      setReadiness(rd.data.items ?? [])
      setCertifications(cert.data.items ?? [])
      setClassRules(cr.data.items ?? [])
      setClassLogs(cl.data.items ?? [])
      setSlos(slo.data.items ?? [])
      setWebhookDlq(wh.data.items ?? [])
      setJurisdictions(jur.data.items ?? [])
      setIntelDash(idash.data)
      setInsights(ins.data.items ?? [])
      setContingencies(cont.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [gapStatusFilter, gapRefreshBilling, gapIncludeSnapshot])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      await fiscalAdminApi.seed()
      setMessage('Seed fiscal aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateIssuer = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.createIssuer(issuerForm)
      setMessage(`Emissor ${data.code} criado.`)
      setSelectedIssuer(data.id)
      setIssuerForm({ name: '', code: '', issuer_type: 'SEFAZ', country: 'BR' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar emissor')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedIssuer || !webhookUrl) return
    setLoading(true)
    try {
      await fiscalAdminApi.configureWebhook(selectedIssuer, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['fiscal.document.authorized', 'fiscal.callback.received'],
      })
      setMessage('Webhook fiscal configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedIssuer) return
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.rotateApiKey(selectedIssuer)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onResolveGap = async (gapId: string, source: 'admin' | 'billing') => {
    setLoading(true)
    try {
      await fiscalAdminApi.patchGapWorkbench(gapId, source, { status: 'RESOLVED' })
      setMessage(`Gap ${gapId} (${source}) resolvido.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao resolver gap')
    } finally {
      setLoading(false)
    }
  }

  const onReloadGaps = async () => {
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.listGapsWorkbench({
        status: gapStatusFilter || undefined,
        refresh_billing: gapRefreshBilling,
        include_snapshot: gapIncludeSnapshot,
      })
      setGapWorkbench(data)
      setMessage(`Workbench: ${data.total} gap(s) — admin ${data.summary.admin_count}, billing ${data.summary.billing_count}.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar workbench')
    } finally {
      setLoading(false)
    }
  }

  const onRecomputeReadiness = async () => {
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.recomputeReadiness()
      setMessage(`Readiness recalculado (${data.updated ?? 0} emissores).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao recalcular readiness')
    } finally {
      setLoading(false)
    }
  }

  const onAnalyzeIntelligence = async () => {
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.analyzeIntelligence()
      setMessage(`Scan fiscal: ${data.insights_created ?? 0} insight(s) novos, ${data.insights_open ?? 0} abertos.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no scan de inteligência')
    } finally {
      setLoading(false)
    }
  }

  const onRetryWebhook = async (deliveryId: string) => {
    setLoading(true)
    try {
      await fiscalAdminApi.retryWebhook(deliveryId)
      setMessage(`Webhook ${deliveryId} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no retry webhook')
    } finally {
      setLoading(false)
    }
  }

  const onOpenCorridor = async (code: string) => {
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.getCorridor(code)
      setCorridorDetail(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar corredor')
    } finally {
      setLoading(false)
    }
  }

  const onClassifySku = async () => {
    setLoading(true)
    try {
      const { data } = await fiscalAdminApi.testClassifySku(classifySku)
      setClassifyResult(data)
      setMessage(data.matched ? `NCM ${String(data.ncm_code)} aplicado.` : 'SKU sem regra.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na classificação')
    } finally {
      setLoading(false)
    }
  }

  const onRegisterContingency = async () => {
    setLoading(true)
    try {
      await fiscalAdminApi.registerContingency(contingencyForm)
      setMessage('Contingência registrada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao registrar contingência')
    } finally {
      setLoading(false)
    }
  }

  const onCloseContingency = async (eventId: string) => {
    setLoading(true)
    try {
      await fiscalAdminApi.closeContingency(eventId)
      setMessage(`Contingência ${eventId} encerrada.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao encerrar contingência')
    } finally {
      setLoading(false)
    }
  }

  const tabLabels: Record<Tab, string> = {
    global: 'Global',
    intelligence: 'Inteligência',
    issuers: 'Emissores',
    documents: 'Documentos',
    gaps: 'Gaps',
    corridors: 'Corredores',
    readiness: 'Readiness',
    certifications: 'Certs',
    classification: 'NCM/CFOP',
    slo: 'SLA',
    webhooks: 'DLQ',
    config: 'Config',
    governance: 'Gov',
  }

  const rows = useMemo(() => {
    if (tab === 'global' && summary) {
      return [
        ...Object.entries(summary).map(([k, v]) => ({ id: k, detail: String(v) })),
        ...(jurisdictions as { country?: string; name?: string; currency?: string; authority_name?: string }[]).map((j) => ({
          id: j.country ?? '—',
          detail: `${j.name} · ${j.currency} · ${j.authority_name ?? '—'}`,
        })),
      ]
    }
    if (tab === 'intelligence' && intelDash) {
      return [
        ...Object.entries(intelDash).map(([k, v]) => ({ id: k, detail: String(v) })),
        ...(insights as { severity?: string; title?: string; entity_ref?: string; suggested_action?: string }[]).map((x) => ({
          id: `${x.severity ?? '—'} · ${x.entity_ref ?? ''}`,
          detail: `${x.title ?? ''}${x.suggested_action ? ` → ${x.suggested_action}` : ''}`,
        })),
      ]
    }
    if (tab === 'corridors') {
      return (corridors as { corridor_code?: string; origin_country?: string; dest_country?: string; primary_issuer_code?: string }[]).map(
        (x) => ({
          id: x.corridor_code ?? '—',
          detail: `${x.origin_country}→${x.dest_country} · ${x.primary_issuer_code}`,
          corridorCode: x.corridor_code,
        }),
      )
    }
    if (tab === 'readiness') {
      return (readiness as { issuer_code?: string; readiness_band?: string; score_total?: number }[]).map((x) => ({
        id: x.issuer_code ?? '—',
        detail: `band ${x.readiness_band} · score ${x.score_total}`,
      }))
    }
    if (tab === 'certifications') {
      return (certifications as { certification_type?: string; issuer_code?: string; status?: string; expiry_severity?: string; days_until_expiry?: number }[]).map((x) => ({
        id: x.certification_type ?? '—',
        detail: `${x.issuer_code} · ${x.status} · ${x.expiry_severity ?? '—'}${x.days_until_expiry != null ? ` (${x.days_until_expiry}d)` : ''}`,
      }))
    }
    if (tab === 'classification') {
      return [
        ...(classRules as { sku_pattern?: string; ncm_code?: string }[]).map((x) => ({
          id: x.sku_pattern ?? '—',
          detail: `regra NCM ${x.ncm_code}`,
        })),
        ...(classLogs as { order_id?: string; sku_id?: string; ncm_applied?: string }[]).map((x) => ({
          id: x.order_id ?? '—',
          detail: `log ${x.sku_id} · ${x.ncm_applied}`,
        })),
      ]
    }
    if (tab === 'slo') {
      return (slos as { corridor_code?: string; metric_name?: string; target_p99_ms?: number }[]).map((x) => ({
        id: x.corridor_code ?? '—',
        detail: `${x.metric_name} · p99 ${x.target_p99_ms}ms`,
      }))
    }
    if (tab === 'webhooks') {
      return (webhookDlq as { id?: string; event_type?: string; delivery_status?: string; error_message?: string }[]).map((x) => ({
        id: x.event_type ?? '—',
        detail: `${x.delivery_status} · ${x.error_message ?? ''}`,
        whId: x.id,
      }))
    }
    if (tab === 'issuers') {
      return issuers.map((x) => ({ id: x.code, detail: `${x.name} · ${x.issuer_type} · ${x.country}` }))
    }
    if (tab === 'documents') {
      return (documents as { id?: string; order_id?: string; receipt_code?: string; send_status?: string }[]).map(
        (x) => ({ id: x.id ?? '—', detail: `${x.order_id} · ${x.receipt_code} · ${x.send_status ?? '—'}` }),
      )
    }
    if (tab === 'gaps') {
      return (gapWorkbench?.items ?? []).map((x: UnifiedGap) => ({
        id: x.id,
        detail: `[${x.source}] ${x.gap_type} · ${x.severity} · ${x.status}${x.order_id ? ` · order ${x.order_id}` : ''}${x.invoice_id ? ` · inv ${x.invoice_id}` : ''}`,
        gapId: x.id,
        gapSource: x.source,
      }))
    }
    if (tab === 'config') {
      return [
        ...(tenants as { tenant_id?: string; razao_social?: string }[]).map((x) => ({
          id: x.tenant_id ?? '—',
          detail: `tenant · ${x.razao_social}`,
        })),
        ...(products as { sku_id?: string; ncm_code?: string }[]).map((x) => ({
          id: x.sku_id ?? '—',
          detail: `sku · NCM ${x.ncm_code ?? '—'}`,
        })),
        ...(health as { country?: string; provider_name?: string; last_status?: string }[]).map((x) => ({
          id: x.country ?? '—',
          detail: `${x.provider_name} · ${x.last_status}`,
        })),
      ]
    }
    if (tab === 'governance') {
      return [
        ...(approvals as { id?: string; owner?: string; status?: string }[]).map((x) => ({
          id: x.id ?? '—',
          detail: `approval · ${x.owner} · ${x.status}`,
        })),
        ...(callbacks as { id?: string; authority?: string; event_type?: string }[]).map((x) => ({
          id: x.id ?? '—',
          detail: `${x.authority} · ${x.event_type}`,
        })),
      ]
    }
    return []
  }, [
    tab,
    summary,
    issuers,
    documents,
    gapWorkbench,
    tenants,
    products,
    health,
    approvals,
    callbacks,
    corridors,
    readiness,
    certifications,
    classRules,
    classLogs,
    slos,
    webhookDlq,
    jurisdictions,
    intelDash,
    insights,
  ])

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4" data-testid="ops-fiscal-admin-page">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Fiscal</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Emissores (SEFAZ, AT-PT), documentos NFC-e, gaps de reconciliação, tenant/product config, aprovações e callbacks.
          </p>
          <p className="mt-1 text-xs text-gray-400">
            <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
              Payment Gateway
            </Link>
            {' · '}
            <Link to="/ops/finance/admin" className="text-indigo-600 hover:underline">
              Finance
            </Link>
            {' · '}
            <Link to="/fiscal/global" className="text-indigo-600 hover:underline">
              Fiscal Global
            </Link>
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="rounded-lg border px-3 py-2 text-sm">
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

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {tabLabels[t]}
          </button>
        ))}
      </div>

      {tab === 'intelligence' && (
        <section className="space-y-4 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => void onAnalyzeIntelligence()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Scan inteligência fiscal
            </button>
            <button type="button" onClick={() => void onRecomputeReadiness()} className="rounded border px-3 py-1 text-sm">
              Recalcular readiness
            </button>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-medium">Registrar contingência SEFAZ</h3>
              <div className="flex flex-wrap gap-2">
                <input className="rounded border px-2 py-1 text-sm" value={contingencyForm.country} onChange={(e) => setContingencyForm((f) => ({ ...f, country: e.target.value }))} placeholder="País" />
                <input className="rounded border px-2 py-1 text-sm" value={contingencyForm.contingency_mode} onChange={(e) => setContingencyForm((f) => ({ ...f, contingency_mode: e.target.value }))} placeholder="Modo (SVC-AN/EPEC)" />
                <input className="min-w-[12rem] flex-1 rounded border px-2 py-1 text-sm" value={contingencyForm.reason} onChange={(e) => setContingencyForm((f) => ({ ...f, reason: e.target.value }))} placeholder="Motivo" />
                <button type="button" onClick={() => void onRegisterContingency()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
                  Registrar
                </button>
              </div>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium">Contingências (histórico)</h3>
              <ul className="space-y-1 text-xs">
                {(contingencies as { id?: string; contingency_mode?: string; authority?: string; active?: boolean }[]).slice(0, 5).map((c) => (
                  <li key={c.id} className="flex items-center justify-between gap-2">
                    <span>{c.contingency_mode} · {c.authority} · {c.active ? 'ATIVA' : 'encerrada'}</span>
                    {c.active && c.id ? (
                      <button type="button" className="text-indigo-600" onClick={() => void onCloseContingency(c.id!)}>
                        Encerrar
                      </button>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {tab === 'gaps' && (
        <section className="space-y-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-gray-600 dark:text-slate-400">
            Workbench unificado: gaps do catálogo fiscal (admin) + emissão real (
            <code className="text-xs">billing_fiscal_service</code>).
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-xs text-gray-500">
              Status
              <select
                className="ml-1 rounded border px-2 py-1 text-sm"
                value={gapStatusFilter}
                onChange={(e) => setGapStatusFilter(e.target.value)}
              >
                <option value="OPEN">OPEN</option>
                <option value="RESOLVED">RESOLVED</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-500">
              <input type="checkbox" checked={gapRefreshBilling} onChange={(e) => setGapRefreshBilling(e.target.checked)} />
              Re-scan billing (refresh)
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-500">
              <input type="checkbox" checked={gapIncludeSnapshot} onChange={(e) => setGapIncludeSnapshot(e.target.checked)} />
              Snapshot conciliação
            </label>
            <button type="button" onClick={() => void onReloadGaps()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Carregar workbench
            </button>
          </div>
          {gapWorkbench ? (
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">
                Admin: {gapWorkbench.summary.admin_count}
              </span>
              <span className="rounded bg-slate-100 px-2 py-1 dark:bg-slate-800">
                Billing: {gapWorkbench.summary.billing_count}
              </span>
              <span
                className={`rounded px-2 py-1 ${gapWorkbench.billing_available ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900'}`}
              >
                {gapWorkbench.billing_available ? 'Billing conectado' : `Billing: ${gapWorkbench.billing_error ?? 'indisponível'}`}
              </span>
            </div>
          ) : null}
          {gapWorkbench?.snapshot && typeof gapWorkbench.snapshot === 'object' && 'open_total' in gapWorkbench.snapshot ? (
            <p className="text-xs text-gray-500">
              Snapshot OPEN total: {String((gapWorkbench.snapshot as { open_total?: number }).open_total ?? '—')}
            </p>
          ) : null}
        </section>
      )}

      {tab === 'readiness' && (
        <div className="mb-2">
          <button type="button" onClick={() => void onRecomputeReadiness()} className="rounded border px-3 py-1 text-sm">
            Recalcular readiness (A–D)
          </button>
        </div>
      )}

      {tab === 'classification' && (
        <section className="mb-4 flex flex-wrap items-end gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <input className="rounded border px-2 py-1 text-sm" value={classifySku} onChange={(e) => setClassifySku(e.target.value)} placeholder="SKU para classificar" />
          <button type="button" onClick={() => void onClassifySku()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
            Testar NCM/CFOP
          </button>
          {classifyResult ? (
            <span className="text-xs text-gray-600">
              {classifyResult.matched ? `NCM ${String(classifyResult.ncm_code)} · CFOP ${String(classifyResult.cfop ?? '—')}` : 'Sem match'}
            </span>
          ) : null}
        </section>
      )}

      {corridorDetail ? (
        <section className="rounded-xl border border-indigo-200 bg-indigo-50 p-4 text-sm dark:border-indigo-900 dark:bg-indigo-950">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="font-medium">Corredor {String(corridorDetail.corridor_code)}</h2>
            <button type="button" className="text-xs" onClick={() => setCorridorDetail(null)}>
              Fechar
            </button>
          </div>
          <p>{String(corridorDetail.name)}</p>
          <p className="text-xs text-gray-600">
            {String(corridorDetail.origin_country)}→{String(corridorDetail.dest_country)} · {String(corridorDetail.document_type_code)}
          </p>
          <ul className="mt-2 space-y-1 font-mono text-xs">
            {((corridorDetail.tax_rules as { tax_code?: string; rate_pct?: number; cfop?: string }[]) ?? []).map((r, i) => (
              <li key={i}>{r.tax_code} {r.rate_pct != null ? `${r.rate_pct}%` : ''} CFOP {r.cfop ?? '—'}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {tab === 'issuers' && (
        <>
          <form
            onSubmit={onCreateIssuer}
            className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4"
          >
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome emissor"
              required
              value={issuerForm.name}
              onChange={(e) => setIssuerForm((f) => ({ ...f, name: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Código"
              required
              value={issuerForm.code}
              onChange={(e) => setIssuerForm((f) => ({ ...f, code: e.target.value }))}
            />
            <select
              className="rounded border px-2 py-1 text-sm"
              value={issuerForm.issuer_type}
              onChange={(e) => setIssuerForm((f) => ({ ...f, issuer_type: e.target.value }))}
            >
              <option value="SEFAZ">SEFAZ</option>
              <option value="AT_PT">AT_PT</option>
              <option value="STUB">STUB</option>
            </select>
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar emissor
            </button>
          </form>
          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
            <div className="flex flex-wrap gap-2">
              <select
                className="rounded border px-2 py-1 text-sm"
                value={selectedIssuer}
                onChange={(e) => setSelectedIssuer(e.target.value)}
              >
                <option value="">Emissor</option>
                {issuers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <input
                className="min-w-[14rem] flex-1 rounded border px-2 py-1 text-sm"
                placeholder="Webhook URL"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
              <input
                className="rounded border px-2 py-1 text-sm"
                placeholder="Secret"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
              />
              <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
                Webhook
              </button>
              <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
                Rotacionar API key
              </button>
            </div>
          </section>
        </>
      )}

      <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-700 dark:bg-slate-900">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Detalhe</th>
              {(tab === 'gaps' || tab === 'corridors' || tab === 'webhooks') && <th className="px-3 py-2">Ação</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-gray-100 dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{r.id}</td>
                <td className="px-3 py-2">{r.detail}</td>
                {tab === 'gaps' && 'gapId' in r && r.gapId && 'gapSource' in r ? (
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      className="text-indigo-600 text-xs"
                      onClick={() => void onResolveGap(String(r.gapId), r.gapSource as 'admin' | 'billing')}
                    >
                      Resolver
                    </button>
                  </td>
                ) : tab === 'corridors' && 'corridorCode' in r && r.corridorCode ? (
                  <td className="px-3 py-2">
                    <button type="button" className="text-indigo-600 text-xs" onClick={() => void onOpenCorridor(String(r.corridorCode))}>
                      Regras fiscais
                    </button>
                  </td>
                ) : tab === 'webhooks' && 'whId' in r && r.whId ? (
                  <td className="px-3 py-2">
                    <button type="button" className="text-indigo-600 text-xs" onClick={() => void onRetryWebhook(String(r.whId))}>
                      Retry
                    </button>
                  </td>
                ) : tab === 'gaps' || tab === 'corridors' || tab === 'webhooks' ? (
                  <td />
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <p className="p-4 text-gray-500">Nenhum registro. Execute Seed.</p>}
      </div>
    </div>
  )
}
