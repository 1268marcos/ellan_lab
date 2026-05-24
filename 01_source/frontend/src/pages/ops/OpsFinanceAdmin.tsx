import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { financeAdminApi, type FinancePartner, type LockerNetworkPlayer } from '../../api/financeAdmin'

type Tab =
  | 'intelligence'
  | 'networks'
  | 'ecosystem'
  | 'readiness'
  | 'roadmap'
  | 'contracts'
  | 'slas'
  | 'partners'
  | 'billing'
  | 'invoices'
  | 'settlements'
  | 'treasury'
  | 'wallet'
  | 'pnl'
  | 'reconciliation'
  | 'webhooks'
  | 'ops'
  | 'dunning'
  | 'tiers'
  | 'fx'
  | 'tax'
  | 'audit'
  | 'documents'
  | 'revrec'
  | 'jobs'

const TABS: { key: Tab; label: string }[] = [
  { key: 'networks', label: 'Redes mundiais' },
  { key: 'intelligence', label: 'Inteligência' },
  { key: 'ecosystem', label: 'Ecossistema' },
  { key: 'readiness', label: 'Readiness' },
  { key: 'roadmap', label: 'Roadmap integração' },
  { key: 'contracts', label: 'Contratos' },
  { key: 'slas', label: 'SLAs' },
  { key: 'partners', label: 'Parceiros' },
  { key: 'billing', label: 'Billing + line items' },
  { key: 'invoices', label: 'NF B2B' },
  { key: 'settlements', label: 'Settlements' },
  { key: 'treasury', label: 'Créditos / holds / comissão' },
  { key: 'wallet', label: 'Wallet' },
  { key: 'pnl', label: 'PnL locker (cost center)' },
  { key: 'reconciliation', label: 'Gaps fiscais' },
  { key: 'webhooks', label: 'Webhook DLQ' },
  { key: 'ops', label: 'NF ops + eventos' },
  { key: 'dunning', label: 'Cobrança' },
  { key: 'tiers', label: 'Níveis comerciais' },
  { key: 'fx', label: 'Câmbio (FX)' },
  { key: 'tax', label: 'Corredores fiscais' },
  { key: 'documents', label: 'Docs NF' },
  { key: 'audit', label: 'Auditoria' },
  { key: 'revrec', label: 'Rev. receita' },
  { key: 'jobs', label: 'Jobs agendados' },
]

type Row = { key: string; col1: string; col2: string; col3: string }

export default function OpsFinanceAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = (searchParams.get('tab') as Tab) || 'networks'
  const setTab = (t: Tab) => setSearchParams({ tab: t }, { replace: true })

  const [networkCatalog, setNetworkCatalog] = useState<LockerNetworkPlayer[]>([])
  const [networkStats, setNetworkStats] = useState<Record<string, number>>({})
  const [worldPriorityIndex, setWorldPriorityIndex] = useState<
    { code: string; segment: string; countries: string[] }[]
  >([])
  const [ecosystemMatrix, setEcosystemMatrix] = useState<{
    total_players: number
    total_relations: number
    total_aliases: number
  } | null>(null)
  const [networkFilter, setNetworkFilter] = useState('')
  const [selectedNetworkCode, setSelectedNetworkCode] = useState('')
  const [integrationGuide, setIntegrationGuide] = useState<Awaited<
    ReturnType<typeof financeAdminApi.playerIntegrationGuide>
  >['data'] | null>(null)
  const [intelDashboard, setIntelDashboard] = useState<Record<string, unknown> | null>(null)
  const [intelInsights, setIntelInsights] = useState<unknown[]>([])
  const [intelBenchmarks, setIntelBenchmarks] = useState<unknown[]>([])
  const [partners, setPartners] = useState<FinancePartner[]>([])
  const [plans, setPlans] = useState<unknown[]>([])
  const [cycles, setCycles] = useState<unknown[]>([])
  const [lineItems, setLineItems] = useState<unknown[]>([])
  const [b2b, setB2b] = useState<unknown[]>([])
  const [settlements, setSettlements] = useState<unknown[]>([])
  const [credits, setCredits] = useState<unknown[]>([])
  const [holds, setHolds] = useState<unknown[]>([])
  const [commissions, setCommissions] = useState<unknown[]>([])
  const [costCenters, setCostCenters] = useState<unknown[]>([])
  const [ccMonthly, setCcMonthly] = useState<unknown[]>([])
  const [gaps, setGaps] = useState<unknown[]>([])
  const [deliveries, setDeliveries] = useState<unknown[]>([])
  const [walletProviders, setWalletProviders] = useState<unknown[]>([])
  const [walletTx, setWalletTx] = useState<unknown[]>([])
  const [opsInvoices, setOpsInvoices] = useState<unknown[]>([])
  const [billingEvents, setBillingEvents] = useState<unknown[]>([])
  const [ecosystemSummary, setEcosystemSummary] = useState<Record<string, unknown> | null>(null)
  const [playerRelations, setPlayerRelations] = useState<unknown[]>([])
  const [readiness, setReadiness] = useState<unknown[]>([])
  const [milestones, setMilestones] = useState<unknown[]>([])
  const [contracts, setContracts] = useState<unknown[]>([])
  const [slaDefs, setSlaDefs] = useState<unknown[]>([])
  const [slaBreaches, setSlaBreaches] = useState<unknown[]>([])
  const [paymentTerms, setPaymentTerms] = useState<unknown[]>([])
  const [fxRates, setFxRates] = useState<unknown[]>([])
  const [commercialTiers, setCommercialTiers] = useState<unknown[]>([])
  const [tierAssignments, setTierAssignments] = useState<unknown[]>([])
  const [dunningCases, setDunningCases] = useState<unknown[]>([])
  const [taxCorridors, setTaxCorridors] = useState<unknown[]>([])
  const [invoiceDocuments, setInvoiceDocuments] = useState<unknown[]>([])
  const [auditLog, setAuditLog] = useState<unknown[]>([])
  const [revenueSchedules, setRevenueSchedules] = useState<unknown[]>([])
  const [revenueEntries, setRevenueEntries] = useState<unknown[]>([])
  const [jobRuns, setJobRuns] = useState<unknown[]>([])

  const [selectedPartner, setSelectedPartner] = useState('')
  const [partnerForm, setPartnerForm] = useState({ code: '', name: '', partner_type: 'ECOMMERCE' })
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMessage(null)
    const safe = async <T,>(fn: () => Promise<{ data: T }>, fallback: T): Promise<T> => {
      try {
        const r = await fn()
        return r.data
      } catch {
        return fallback
      }
    }
    const emptyList = { items: [] as unknown[], total: 0 }
    const emptyCatalog = { items: [], total: 0, by_parent_group: {} as Record<string, number> }
    try {
      const [
        nc,
        p,
        pl,
        cy,
        li,
        inv,
        st,
        cr,
        ho,
        co,
        cc,
        ccm,
        gp,
        wd,
        wp,
        wt,
        oi,
        be,
        eco,
        rel,
        rd,
        ms,
        ct,
        sla,
        br,
        pt,
        fx,
        tr,
        ta,
        dc,
        tx,
        doc,
        aud,
        rs,
        re,
        jr,
        wpi,
        matrix,
      ] = await Promise.all([
        safe(
          () =>
            financeAdminApi.listLockerNetworkCatalog(
              networkFilter ? { segment_code: networkFilter } : undefined,
            ),
          emptyCatalog,
        ),
        safe(() => financeAdminApi.listPartners(), emptyList),
        safe(() => financeAdminApi.listPlans(), emptyList),
        safe(() => financeAdminApi.listCycles(), emptyList),
        safe(() => financeAdminApi.listLineItems(), emptyList),
        safe(() => financeAdminApi.listB2bInvoices(), emptyList),
        safe(() => financeAdminApi.listSettlements(), emptyList),
        safe(() => financeAdminApi.listCreditNotes(), emptyList),
        safe(() => financeAdminApi.listPaymentHolds(), emptyList),
        safe(() => financeAdminApi.listCommissions(), emptyList),
        safe(() => financeAdminApi.listCostCenters(), emptyList),
        safe(() => financeAdminApi.listCostCenterMonthly(), emptyList),
        safe(() => financeAdminApi.listFiscalGaps(), emptyList),
        safe(
          () => financeAdminApi.listWebhookDeliveries({ failed_only: tab === 'webhooks' }),
          emptyList,
        ),
        safe(() => financeAdminApi.listWalletProviders(), emptyList),
        safe(() => financeAdminApi.listWalletTransactions(), emptyList),
        safe(() => financeAdminApi.listOpsInvoices(), emptyList),
        safe(() => financeAdminApi.listBillingEvents(), emptyList),
        safe(() => financeAdminApi.ecosystemSummary(), {} as Record<string, unknown>),
        safe(() => financeAdminApi.listPlayerRelations(), emptyList),
        safe(() => financeAdminApi.listPartnerReadiness(), { items: [], total: 0, average_score: 0 }),
        safe(() => financeAdminApi.listIntegrationMilestones(), emptyList),
        safe(() => financeAdminApi.listCommercialContracts(), emptyList),
        safe(() => financeAdminApi.listSlaDefinitions(), emptyList),
        safe(() => financeAdminApi.listSlaBreaches(), emptyList),
        safe(() => financeAdminApi.listPaymentTerms(), emptyList),
        safe(() => financeAdminApi.listFxRates(), emptyList),
        safe(() => financeAdminApi.listCommercialTiers(), emptyList),
        safe(() => financeAdminApi.listTierAssignments(), emptyList),
        safe(() => financeAdminApi.listDunningCases(), emptyList),
        safe(() => financeAdminApi.listTaxCorridors(), emptyList),
        safe(() => financeAdminApi.listInvoiceDocuments(), emptyList),
        safe(() => financeAdminApi.listAuditLog(), emptyList),
        safe(() => financeAdminApi.listRevenueSchedules(), emptyList),
        safe(() => financeAdminApi.listRevenueEntries(), emptyList),
        safe(() => financeAdminApi.listJobRuns(), emptyList),
        safe(() => financeAdminApi.worldPriorityIndex(), { items: [], total: 0 }),
        safe(() => financeAdminApi.ecosystemMatrix(), {
          segments: [],
          matrix: {},
          total_players: 0,
          total_relations: 0,
          total_aliases: 0,
        }),
      ])
      setNetworkCatalog(nc.items ?? [])
      setNetworkStats(nc.by_parent_group ?? {})
      setWorldPriorityIndex(wpi.items ?? [])
      setEcosystemMatrix({
        total_players: matrix.total_players ?? 0,
        total_relations: matrix.total_relations ?? 0,
        total_aliases: matrix.total_aliases ?? 0,
      })
      setPartners(p.items ?? [])
      setPlans(pl.items ?? [])
      setCycles(cy.items ?? [])
      setLineItems(li.items ?? [])
      setB2b(inv.items ?? [])
      setSettlements(st.items ?? [])
      setCredits(cr.items ?? [])
      setHolds(ho.items ?? [])
      setCommissions(co.items ?? [])
      setCostCenters(cc.items ?? [])
      setCcMonthly(ccm.items ?? [])
      setGaps(gp.items ?? [])
      setDeliveries(wd.items ?? [])
      setWalletProviders(wp.items ?? [])
      setWalletTx(wt.items ?? [])
      setOpsInvoices(oi.items ?? [])
      setBillingEvents(be.items ?? [])
      setEcosystemSummary(eco && 'total_players' in eco ? eco : null)
      setPlayerRelations(rel.items ?? [])
      setReadiness(rd.items ?? [])
      setMilestones(ms.items ?? [])
      setContracts(ct.items ?? [])
      setSlaDefs(sla.items ?? [])
      setSlaBreaches(br.items ?? [])
      setPaymentTerms(pt.items ?? [])
      setFxRates(fx.items ?? [])
      setCommercialTiers(tr.items ?? [])
      setTierAssignments(ta.items ?? [])
      setDunningCases(dc.items ?? [])
      setTaxCorridors(tx.items ?? [])
      setInvoiceDocuments(doc.items ?? [])
      setAuditLog(aud.items ?? [])
      setRevenueSchedules(rs.items ?? [])
      setRevenueEntries(re.items ?? [])
      setJobRuns(jr.items ?? [])

      const hasCore = (p.items?.length ?? 0) > 0 || (pl.items?.length ?? 0) > 0
      const hasCatalog = (nc.items?.length ?? 0) > 0
      if (!hasCore && !hasCatalog) {
        setError(
          'Nenhum dado finance-admin. Inicie o serviço na porta 8123 e clique Seed (ou Sync catálogo).',
        )
      } else if (!hasCatalog || (li.items?.length ?? 0) === 0 && (st.items?.length ?? 0) === 0) {
        setMessage(
          'Alguns módulos podem estar indisponíveis (404). Reinicie finance-admin com a versão atual e execute Seed.',
        )
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar finance-admin')
    } finally {
      setLoading(false)
    }
  }, [tab, networkFilter])

  useEffect(() => {
    void load()
  }, [load])

  const loadIntelligence = useCallback(async () => {
    try {
      const [dash, ins, bench] = await Promise.all([
        financeAdminApi.intelligenceDashboard(),
        financeAdminApi.listEcosystemInsights(),
        financeAdminApi.listPlayerBenchmarks(),
      ])
      setIntelDashboard(dash.data as Record<string, unknown>)
      setIntelInsights(ins.data.items ?? [])
      setIntelBenchmarks(bench.data.items ?? [])
    } catch {
      setIntelDashboard(null)
      setIntelInsights([])
      setIntelBenchmarks([])
    }
  }, [])

  useEffect(() => {
    if (tab === 'intelligence') void loadIntelligence()
  }, [tab, loadIntelligence])

  const onAnalyzeIntelligence = async () => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.analyzeEcosystem()
      setMessage(
        `Scan: ${data.insights_created} insights · ${data.benchmarks_computed} benchmarks · ${data.health_checks_run} health checks`,
      )
      await loadIntelligence()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no scan de inteligência')
    } finally {
      setLoading(false)
    }
  }

  const onResolveInsight = async (insightId: string) => {
    setLoading(true)
    try {
      await financeAdminApi.resolveInsight(insightId)
      setMessage(`Insight ${insightId} resolvido.`)
      await loadIntelligence()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao resolver insight')
    } finally {
      setLoading(false)
    }
  }

  const onSyncCatalog = async () => {
    setLoading(true)
    try {
      await financeAdminApi.syncLockerNetworkCatalog()
      setMessage('Catálogo mundial sincronizado (InPost, DHL, Magalu, ML, Amazon, DPD, Correios, CTT…).')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao sincronizar catálogo')
    } finally {
      setLoading(false)
    }
  }

  const onSeed = async () => {
    setLoading(true)
    try {
      await financeAdminApi.seed()
      setMessage('Seed financeiro aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    if (!partnerForm.code || !partnerForm.name) return
    setLoading(true)
    try {
      const { data } = await financeAdminApi.createPartner(partnerForm)
      setMessage(`Parceiro ${data.code} criado.`)
      setSelectedPartner(data.id)
      setPartnerForm({ code: '', name: '', partner_type: 'ECOMMERCE' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar parceiro')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedPartner || !webhookUrl) return
    setLoading(true)
    try {
      await financeAdminApi.configureWebhook(selectedPartner, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
      })
      setMessage('Webhook configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedPartner) return
    setLoading(true)
    try {
      const { data } = await financeAdminApi.rotateApiKey(selectedPartner)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…).`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na rotação')
    } finally {
      setLoading(false)
    }
  }

  const onRecomputeReadiness = async () => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.recomputeReadiness()
      setMessage(`Readiness por blueprint: ${data.recomputed} players · média ${data.average_score}`)
      await load()
      if (selectedNetworkCode) {
        const { data: guide } = await financeAdminApi.playerIntegrationGuide(selectedNetworkCode)
        setIntegrationGuide(guide)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha readiness')
    } finally {
      setLoading(false)
    }
  }

  const loadIntegrationGuide = async (catalogCode: string) => {
    setSelectedNetworkCode(catalogCode)
    setLoading(true)
    setError(null)
    try {
      const { data } = await financeAdminApi.playerIntegrationGuide(catalogCode)
      setIntegrationGuide(data)
    } catch (err: unknown) {
      setIntegrationGuide(null)
      setError(err instanceof Error ? err.message : 'Falha ao carregar guia de integração')
    } finally {
      setLoading(false)
    }
  }

  const onReplayWebhook = async (deliveryId: string) => {
    setLoading(true)
    try {
      await financeAdminApi.replayWebhookDelivery(deliveryId)
      setMessage(`Webhook ${deliveryId} reenviado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha replay')
    } finally {
      setLoading(false)
    }
  }

  const onRunRevRec = async () => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.runRevenueRecognition(false)
      setMessage(`RevRec: +${data.entries_created} entradas · ${data.schedules_updated} schedules`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha revrec')
    } finally {
      setLoading(false)
    }
  }

  const onRunJob = async (code: string) => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.runJob(code)
      setMessage(`Job ${code}: ${data.status}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha job')
    } finally {
      setLoading(false)
    }
  }

  const onEmitFiscal = async (invoiceId: string) => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.emitB2bFiscal(invoiceId)
      setMessage(`NF fiscal ${data.mode ?? 'OK'} · ${data.access_key ?? '—'}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha emissão fiscal')
    } finally {
      setLoading(false)
    }
  }

  const onScanDunning = async () => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.scanDunning()
      setMessage(`Dunning: ${data.cases_opened} casos · ${data.invoices_scanned} faturas`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha dunning scan')
    } finally {
      setLoading(false)
    }
  }

  const onReconcileSettlement = async (batchId: string) => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.reconcileSettlement(batchId)
      setMessage(`Reconciliação: ${data.run.matched_count} matches · var ${data.run.variance_cents}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha reconciliação')
    } finally {
      setLoading(false)
    }
  }

  const onCloseCycle = async (cycleId: string) => {
    setLoading(true)
    try {
      const { data } = await financeAdminApi.closeBillingCycle(cycleId)
      setMessage(`Ciclo fechado · NF ${data.invoice_id ?? '—'} · ${data.total_amount_cents} centavos`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha fechar ciclo')
    } finally {
      setLoading(false)
    }
  }

  const resolveGap = async (gapId: string) => {
    setLoading(true)
    try {
      await financeAdminApi.patchFiscalGap(gapId, { status: 'RESOLVED' })
      setMessage(`Gap ${gapId} resolvido.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao resolver gap')
    } finally {
      setLoading(false)
    }
  }

  const tableRows: Row[] = useMemo(() => {
    switch (tab) {
      case 'intelligence':
        return [
          ...(intelDashboard
            ? [
                {
                  key: 'intel-dash',
                  col1: 'KPI',
                  col2: `${intelDashboard.open_insights} insights abertos · ${intelDashboard.critical_insights} críticos`,
                  col3: `readiness médio ${intelDashboard.avg_readiness} · composite ${intelDashboard.avg_composite_score}`,
                },
              ]
            : []),
          ...intelInsights.map(
            (i: { id?: string; catalog_code?: string; insight_type?: string; severity?: string; title?: string; suggested_action?: string }) => ({
              key: i.id ?? '',
              col1: i.catalog_code ?? '',
              col2: `${i.severity} · ${i.insight_type} · ${i.title}`,
              col3: i.suggested_action ?? '',
            }),
          ),
          ...intelBenchmarks.slice(0, 15).map(
            (b: { catalog_code?: string; composite_score?: number; readiness_rank?: number; segment_code?: string }) => ({
              key: `bm-${b.catalog_code}`,
              col1: b.catalog_code ?? '',
              col2: `benchmark #${b.readiness_rank} · ${b.segment_code}`,
              col3: `composite ${b.composite_score}`,
            }),
          ),
        ]
      case 'ecosystem':
        return [
          ...(ecosystemSummary
            ? [
                {
                  key: 'eco-sum',
                  col1: 'KPI',
                  col2: `${ecosystemSummary.total_players} players · ${ecosystemSummary.live_count} LIVE`,
                  col3: `readiness médio ${ecosystemSummary.readiness_average} · ${ecosystemSummary.total_relations} relações`,
                },
              ]
            : []),
          ...playerRelations.map((r: { id?: string; from_catalog_code?: string; to_catalog_code?: string; relation_type?: string }) => ({
            key: r.id ?? `${r.from_catalog_code}-${r.to_catalog_code}`,
            col1: r.relation_type ?? 'REL',
            col2: `${r.from_catalog_code} → ${r.to_catalog_code}`,
            col3: '',
          })),
        ]
      case 'readiness':
        return readiness.map((r: { catalog_code?: string; readiness_score?: number; grade?: string; blockers_json?: string }) => ({
          key: r.catalog_code ?? '',
          col1: r.catalog_code ?? '',
          col2: `score ${r.readiness_score} · grade ${r.grade}`,
          col3: r.blockers_json ?? '[]',
        }))
      case 'roadmap':
        return milestones.map((m: { id?: string; catalog_code?: string; phase?: string; title?: string; status?: string; target_date?: string }) => ({
          key: m.id ?? '',
          col1: m.catalog_code ?? '',
          col2: `${m.phase} · ${m.title}`,
          col3: `${m.status} · ${m.target_date ?? '—'}`,
        }))
      case 'contracts':
        return contracts.map((c: { id?: string; title?: string; contract_type?: string; status?: string; catalog_code?: string }) => ({
          key: c.id ?? '',
          col1: c.catalog_code ?? '—',
          col2: c.title ?? '',
          col3: `${c.contract_type} · ${c.status}`,
        }))
      case 'dunning':
        return dunningCases.map((d: { id?: string; invoice_id?: string; stage?: number; amount_due_cents?: number; status?: string }) => ({
          key: d.id ?? '',
          col1: `stage ${d.stage}`,
          col2: d.invoice_id?.slice(0, 12) ?? '',
          col3: `${d.status} · ${d.amount_due_cents} centavos`,
        }))
      case 'tiers':
        return [
          ...commercialTiers.map((t: { tier_code?: string; name?: string; default_revenue_share_pct?: string }) => ({
            key: t.tier_code ?? '',
            col1: t.tier_code ?? '',
            col2: t.name ?? '',
            col3: String(t.default_revenue_share_pct ?? '—'),
          })),
          ...tierAssignments.map((a: { id?: string; partner_id?: string; tier_code?: string }) => ({
            key: a.id ?? '',
            col1: 'assign',
            col2: a.partner_id?.slice(0, 8) ?? '',
            col3: a.tier_code ?? '',
          })),
        ]
      case 'fx':
        return fxRates.map((f: { id?: string; base_currency?: string; quote_currency?: string; rate?: string; rate_date?: string }) => ({
          key: f.id ?? '',
          col1: `${f.base_currency}/${f.quote_currency}`,
          col2: String(f.rate),
          col3: f.rate_date ?? '',
        }))
      case 'tax':
        return taxCorridors.map((t: { id?: string; partner_id?: string; tax_regime?: string; origin_country?: string; destination_country?: string }) => ({
          key: t.id ?? '',
          col1: t.tax_regime ?? '',
          col2: `${t.origin_country}→${t.destination_country}`,
          col3: t.partner_id?.slice(0, 8) ?? '',
        }))
      case 'documents':
        return invoiceDocuments.map((d: { id?: string; invoice_id?: string; document_kind?: string; access_key?: string }) => ({
          key: d.id ?? '',
          col1: d.document_kind ?? '',
          col2: d.invoice_id?.slice(0, 12) ?? '',
          col3: d.access_key?.slice(0, 16) ?? '—',
        }))
      case 'revrec':
        return [
          ...revenueSchedules.map((s: { id?: string; source_id?: string; total_cents?: number; deferred_cents?: number; status?: string }) => ({
            key: s.id ?? '',
            col1: 'schedule',
            col2: s.source_id ?? '',
            col3: `total ${s.total_cents} · def ${s.deferred_cents} · ${s.status}`,
          })),
          ...revenueEntries.map((e: { id?: string; recognition_date?: string; amount_cents?: number; fiscal_synced?: boolean }) => ({
            key: e.id ?? '',
            col1: 'entry',
            col2: e.recognition_date ?? '',
            col3: `${e.amount_cents} · fiscal:${e.fiscal_synced ? 'ok' : 'pend'}`,
          })),
        ]
      case 'jobs':
        return jobRuns.map((j: { id?: string; job_code?: string; status?: string; started_at?: string; error_message?: string | null }) => ({
          key: j.id ?? '',
          col1: j.job_code ?? '',
          col2: j.status ?? '',
          col3: j.error_message || j.started_at || '',
        }))
      case 'audit':
        return auditLog.map((a: { id?: string; action?: string; entity_type?: string; entity_id?: string; created_at?: string }) => ({
          key: a.id ?? '',
          col1: a.action ?? '',
          col2: `${a.entity_type}:${a.entity_id?.slice(0, 12)}`,
          col3: a.created_at ?? '',
        }))
      case 'slas':
        return [
          ...slaDefs.map((s: { id?: string; metric_code?: string; metric_name?: string; target_value?: string; partner_id?: string }) => ({
            key: `sla-${s.id}`,
            col1: 'def',
            col2: s.metric_name ?? s.metric_code ?? '',
            col3: `meta ${s.target_value} · ${s.partner_id?.slice(0, 8)}`,
          })),
          ...slaBreaches.map((b: { id?: string; sla_id?: string; status?: string; observed_value?: string }) => ({
            key: `br-${b.id}`,
            col1: 'breach',
            col2: b.sla_id?.slice(0, 8) ?? '',
            col3: `${b.status} · obs ${b.observed_value}`,
          })),
        ]
      case 'networks':
        return networkCatalog.map((n) => ({
          key: n.id,
          col1: n.code,
          col2: `${n.name} · ${n.parent_group} · ${n.country_code}`,
          col3: `${n.integration_status} · ${n.finance_partner_code ? `fin:${n.finance_partner_code}` : 'sem conta'} · ${n.estimated_locker_count ?? '—'} lockers`,
        }))
      case 'partners':
        return partners.map((p) => ({
          key: p.id,
          col1: p.code,
          col2: `${p.name} · ${p.partner_type}`,
          col3: p.active ? 'ativo' : 'inativo',
        }))
      case 'billing':
        return [
          ...plans.map((pl: { id?: string; plan_name?: string; billing_model?: string }) => ({
            key: `pl-${pl.id}`,
            col1: 'plano',
            col2: pl.plan_name ?? '',
            col3: pl.billing_model ?? '',
          })),
          ...cycles.map((c: { id?: string; status?: string; total_amount_cents?: number }) => ({
            key: `cy-${c.id}`,
            col1: 'ciclo',
            col2: c.status ?? '',
            col3: String(c.total_amount_cents ?? 0),
          })),
          ...lineItems.map((li: { id?: number; line_type?: string; description?: string; total_cents?: number }) => ({
            key: `li-${li.id}`,
            col1: li.line_type ?? 'line',
            col2: li.description ?? '',
            col3: String(li.total_cents ?? 0),
          })),
        ]
      case 'invoices':
        return b2b.map((i: { id?: string; invoice_number?: string; status?: string; amount_cents?: number; fiscal_status?: string }) => ({
          key: i.id ?? '',
          col1: i.invoice_number ?? i.id?.slice(0, 8) ?? '',
          col2: `${i.status} · fiscal ${i.fiscal_status ?? 'PENDING'}`,
          col3: `R$ ${((i.amount_cents ?? 0) / 100).toFixed(2)}`,
        }))
      case 'settlements':
        return settlements.map((s: { id?: string; status?: string; net_amount_cents?: number; partner_id?: string }) => ({
          key: s.id ?? '',
          col1: s.id?.slice(0, 8) ?? '',
          col2: s.partner_id?.slice(0, 8) ?? '',
          col3: `${s.status} · net ${s.net_amount_cents}`,
        }))
      case 'treasury':
        return [
          ...credits.map((c: { id?: string; reason_code?: string; amount_cents?: number; status?: string }) => ({
            key: `cr-${c.id}`,
            col1: 'crédito',
            col2: c.reason_code ?? '',
            col3: `${c.status} · ${c.amount_cents}`,
          })),
          ...holds.map((h: { id?: string; status?: string; hold_amount_cents?: number }) => ({
            key: `ho-${h.id}`,
            col1: 'hold',
            col2: h.status ?? '',
            col3: String(h.hold_amount_cents),
          })),
          ...commissions.map((c: { id?: string; commission_percentage?: string | number; partner_id?: string }) => ({
            key: `cm-${c.id}`,
            col1: 'comissão',
            col2: String(c.commission_percentage),
            col3: c.partner_id?.slice(0, 8) ?? '',
          })),
        ]
      case 'wallet':
        return [
          ...walletProviders.map((w: { code?: string; name?: string }) => ({
            key: `wp-${w.code}`,
            col1: 'provider',
            col2: w.code ?? '',
            col3: w.name ?? '',
          })),
          ...walletTx.map((t: { id?: string; type?: string; amount_cents?: number }) => ({
            key: `wt-${t.id}`,
            col1: 'tx',
            col2: t.type ?? '',
            col3: String(t.amount_cents),
          })),
        ]
      case 'pnl':
        return [
          ...costCenters.map((c: { locker_id?: string; network_code?: string }) => ({
            key: `cc-${c.locker_id}`,
            col1: 'locker',
            col2: c.locker_id ?? '',
            col3: c.network_code ?? '',
          })),
          ...ccMonthly.map((m: { locker_id?: string; month?: string; total_costs_cents?: number }) => ({
            key: `ccm-${m.locker_id}-${m.month}`,
            col1: 'mensal',
            col2: `${m.locker_id} · ${m.month}`,
            col3: `opex+depr ${m.total_costs_cents}`,
          })),
        ]
      case 'reconciliation':
        return gaps.map((g: { id?: string; gap_type?: string; severity?: string; status?: string; order_id?: string }) => ({
          key: g.id ?? '',
          col1: g.gap_type ?? '',
          col2: `${g.severity} · ${g.order_id ?? '—'}`,
          col3: g.status ?? '',
        }))
      case 'webhooks':
        return deliveries.map((d: { id?: string; event_type?: string; status?: string; http_status?: number }) => ({
          key: d.id ?? '',
          col1: d.event_type ?? '',
          col2: String(d.http_status ?? '—'),
          col3: d.status ?? '',
        }))
      default:
        return [
          ...opsInvoices.map((o: { order_id?: string; status?: string }) => ({
            key: `oi-${o.order_id}`,
            col1: 'invoice',
            col2: o.order_id ?? '',
            col3: o.status ?? '',
          })),
          ...billingEvents.map((e: { event_type?: string; event_id?: string }) => ({
            key: `ev-${e.event_id}`,
            col1: 'event',
            col2: e.event_type ?? '',
            col3: e.event_id ?? '',
          })),
        ]
    }
  }, [
    tab,
    networkCatalog,
    partners,
    plans,
    cycles,
    lineItems,
    b2b,
    settlements,
    credits,
    holds,
    commissions,
    costCenters,
    ccMonthly,
    gaps,
    deliveries,
    walletProviders,
    walletTx,
    opsInvoices,
    billingEvents,
    intelDashboard,
    intelInsights,
    intelBenchmarks,
    ecosystemSummary,
    playerRelations,
    readiness,
    milestones,
    contracts,
    slaDefs,
    slaBreaches,
    paymentTerms,
    fxRates,
    commercialTiers,
    tierAssignments,
    dunningCases,
    taxCorridors,
    invoiceDocuments,
    auditLog,
    revenueSchedules,
    revenueEntries,
    jobRuns,
  ])

  return (
    <div className="space-y-4 p-4" data-testid="ops-finance-admin-page">
      <div className="flex flex-wrap gap-2 text-sm">
        <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
          Payment Gateway
        </Link>
        <Link to="/ops/partners/admin?tab=settlements" className="text-indigo-600 hover:underline">
          Partners settlements
        </Link>
        <Link to="/ops/billing/reconciliation-gaps" className="text-indigo-600 hover:underline">
          Billing fiscal (8020)
        </Link>
      </div>

      <header>
        <h1 className="text-xl font-semibold">OPS — Finance Admin (global)</h1>
        <p className="text-sm text-gray-600">
          Billing B2B, settlements, treasury, PnL por locker, gaps fiscais e monitoramento de webhooks — porta 8123.
        </p>
      </header>

      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`rounded px-2 py-1 text-xs ${tab === t.key ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
        <button type="button" className="rounded bg-sky-600 px-2 py-1 text-xs text-white" onClick={() => void onSyncCatalog()}>
          Sync catálogo
        </button>
        <button type="button" className="rounded bg-emerald-600 px-2 py-1 text-xs text-white" onClick={() => void onSeed()}>
          Seed
        </button>
        <button type="button" className="rounded bg-gray-700 px-2 py-1 text-xs text-white" onClick={() => void load()}>
          Recarregar
        </button>
        {tab === 'intelligence' ? (
          <button type="button" className="rounded bg-purple-600 px-2 py-1 text-xs text-white" onClick={() => void onAnalyzeIntelligence()}>
            Scan inteligência
          </button>
        ) : null}
        {tab === 'readiness' ? (
          <button type="button" className="rounded bg-violet-600 px-2 py-1 text-xs text-white" onClick={() => void onRecomputeReadiness()}>
            Recompute readiness
          </button>
        ) : null}
        {tab === 'dunning' ? (
          <button type="button" className="rounded bg-amber-600 px-2 py-1 text-xs text-white" onClick={() => void onScanDunning()}>
            Scan inadimplência
          </button>
        ) : null}
        {tab === 'revrec' ? (
          <button type="button" className="rounded bg-teal-600 px-2 py-1 text-xs text-white" onClick={() => void onRunRevRec()}>
            Run revrec
          </button>
        ) : null}
        {tab === 'jobs' ? (
          <>
            {['DUNNING_SCAN', 'SETTLEMENT_RECONCILE', 'REVENUE_RECOGNITION', 'FISCAL_GAP_SYNC', 'READINESS_RECOMPUTE', 'ECOSYSTEM_INTELLIGENCE_SCAN'].map((c) => (
              <button key={c} type="button" className="rounded bg-slate-600 px-2 py-1 text-xs text-white" onClick={() => void onRunJob(c)}>
                {c}
              </button>
            ))}
          </>
        ) : null}
      </div>

      {tab === 'networks' ? (
        <div className="space-y-2">
          <div className="rounded border border-indigo-200 bg-indigo-50/80 px-3 py-2 text-sm dark:border-indigo-800 dark:bg-indigo-950/40">
            <div className="mb-1 font-medium text-indigo-900 dark:text-indigo-200">
              Players prioritários (world-priority-index)
            </div>
            <div className="flex flex-wrap gap-1.5">
              {worldPriorityIndex.length === 0 ? (
                <span className="text-xs text-gray-500">Execute Sync catálogo para carregar o índice.</span>
              ) : (
                worldPriorityIndex.map((p) => {
                  const inCatalog = networkCatalog.some((n) => n.code === p.code)
                  return (
                    <button
                      key={p.code}
                      type="button"
                      title={`${p.segment} · ${p.countries.join(', ')}`}
                      className={`rounded px-2 py-0.5 text-xs ${
                        selectedNetworkCode === p.code
                          ? 'ring-2 ring-white'
                          : ''
                      } ${
                        inCatalog ? 'bg-indigo-600 text-white' : 'bg-amber-100 text-amber-900'
                      }`}
                      onClick={() => void loadIntegrationGuide(p.code)}
                    >
                      {p.code}
                      <span className="opacity-80"> · {p.countries.join('/')}</span>
                    </button>
                  )
                })
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 items-center text-sm">
            <span className="text-gray-600">Grupo:</span>
            {[
              '',
              'LOCKER_NETWORK',
              'LOCKER_NETWORK_OPERATOR',
              'CARRIER_LAST_MILE',
              'MARKETPLACE',
              'COLLECTION_POINT',
              'LOGISTICS_PLATFORM',
              'FOOD_DELIVERY',
              'PAYMENTS_FISCAL',
            ].map((g) => (
              <button
                key={g || 'all'}
                type="button"
                className={`rounded px-2 py-0.5 text-xs ${networkFilter === g ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
                onClick={() => setNetworkFilter(g)}
              >
                {g || 'Todos'} {g && networkStats[g] != null ? `(${networkStats[g]})` : ''}
              </button>
            ))}
            <span className="text-xs text-gray-500 ml-2">
              {ecosystemMatrix
                ? `${ecosystemMatrix.total_players} players · ${ecosystemMatrix.total_relations} relações · ${ecosystemMatrix.total_aliases} aliases`
                : '90+ players mundiais'}
              {' · '}6 blueprints de integração (LOCKER_API, Marketplace OAuth, Carrier, Agregador, Food, Cross-border)
            </span>
          </div>
        </div>
      ) : null}

      {tab === 'networks' && integrationGuide ? (
        <div className="rounded border border-slate-300 bg-white p-4 text-sm shadow-sm dark:border-slate-600 dark:bg-slate-900">
          <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
            <div>
              <h3 className="font-semibold text-base">
                Como integrar · {integrationGuide.name}{' '}
                <span className="font-mono text-indigo-600 text-sm">({integrationGuide.catalog_code})</span>
              </h3>
              <p className="text-xs text-gray-500">
                {integrationGuide.segment_code} · status {integrationGuide.integration_status}
                {integrationGuide.finance_partner_code ? ` · fin:${integrationGuide.finance_partner_code}` : ''}
              </p>
            </div>
            <button
              type="button"
              className="text-xs text-gray-500 hover:text-gray-800"
              onClick={() => {
                setIntegrationGuide(null)
                setSelectedNetworkCode('')
              }}
            >
              Fechar
            </button>
          </div>

          {integrationGuide.blueprint ? (
            <div className="mb-3 rounded bg-indigo-50 p-3 dark:bg-indigo-950/30">
              <div className="font-medium text-indigo-900 dark:text-indigo-200">
                Blueprint: {integrationGuide.blueprint.name} ({integrationGuide.blueprint.code})
              </div>
              <p className="text-xs mt-1">
                Auth {integrationGuide.blueprint.auth_type} · capability{' '}
                <code>{integrationGuide.blueprint.primary_capability}</code>
              </p>
              {integrationGuide.blueprint.docs_hint ? (
                <p className="text-xs text-gray-600 mt-1">{integrationGuide.blueprint.docs_hint}</p>
              ) : null}
            </div>
          ) : null}

          {integrationGuide.integration_steps?.length ? (
            <ol className="list-decimal list-inside text-xs space-y-1 mb-3 text-gray-700 dark:text-slate-300">
              {integrationGuide.integration_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          ) : null}

          <div className="grid gap-3 md:grid-cols-3 text-xs">
            <div>
              <div className="font-medium mb-1">Capabilities ({integrationGuide.capabilities.length})</div>
              <ul className="space-y-0.5 max-h-32 overflow-y-auto">
                {integrationGuide.capabilities.map((c) => (
                  <li key={`${c.capability_code}-${c.direction}`}>
                    {c.capability_code} · {c.protocol} · {c.direction}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-medium mb-1">Relações ({integrationGuide.relations.length})</div>
              <ul className="space-y-0.5 max-h-32 overflow-y-auto">
                {integrationGuide.relations.map((r) => (
                  <li key={`${r.from_catalog_code}-${r.to_catalog_code}-${r.relation_type}`}>
                    {r.from_catalog_code} → {r.to_catalog_code} ({r.relation_type})
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-medium mb-1">Cobertura ({integrationGuide.country_coverage.length})</div>
              <ul className="space-y-0.5 max-h-32 overflow-y-auto">
                {integrationGuide.country_coverage.map((c) => (
                  <li key={c.country_code}>
                    {c.country_code}:{' '}
                    {[c.locker_service && 'locker', c.pudo_service && 'PUDO', c.marketplace_channel && 'mkt', c.food_pickup && 'food']
                      .filter(Boolean)
                      .join(', ') || '—'}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {integrationGuide.readiness ? (
            <p className="text-xs mt-3 text-gray-600">
              Readiness {integrationGuide.readiness.readiness_score} ({integrationGuide.readiness.grade}) · blueprint{' '}
              {integrationGuide.readiness.integration_blueprint_code ?? '—'} · score {integrationGuide.readiness.blueprint_score}
            </p>
          ) : (
            <p className="text-xs mt-3 text-amber-700">Readiness não calculado — Recompute ou job READINESS_RECOMPUTE.</p>
          )}

          <p className="text-xs mt-2 text-gray-400 font-mono break-all">
            {integrationGuide.cross_refs?.partner_admin_path} · {integrationGuide.cross_refs?.ml_admin_path}
          </p>
        </div>
      ) : null}

      {tab === 'partners' ? (
        <>
          <form className="flex flex-wrap gap-2" onSubmit={onCreatePartner}>
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="code"
              value={partnerForm.code}
              onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="nome"
              value={partnerForm.name}
              onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
            />
            <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Criar
            </button>
          </form>
          <div className="flex flex-wrap gap-2 items-center text-sm">
            <select className="rounded border px-2 py-1" value={selectedPartner} onChange={(e) => setSelectedPartner(e.target.value)}>
              <option value="">Parceiro webhook/key</option>
              {partners.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input className="rounded border px-2 py-1" placeholder="webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
            <button type="button" className="rounded bg-slate-600 px-2 py-1 text-white" onClick={() => void onWebhook()}>
              Webhook
            </button>
            <button type="button" className="rounded bg-amber-600 px-2 py-1 text-white" onClick={() => void onRotateKey()}>
              API key
            </button>
          </div>
        </>
      ) : null}

      {tab === 'reconciliation' ? (
        <p className="text-xs text-gray-500">Clique num gap OPEN na tabela para resolver (demo).</p>
      ) : null}

      {lastApiKey ? <pre className="rounded bg-amber-50 p-2 text-xs break-all border">{lastApiKey}</pre> : null}
      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {loading ? <p className="text-sm text-gray-500">Carregando…</p> : null}

      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-1">Tipo / ID</th>
            <th className="py-1">Detalhe</th>
            <th className="py-1">Status / valor</th>
            {tab === 'intelligence' || tab === 'reconciliation' || tab === 'webhooks' || tab === 'billing' || tab === 'settlements' || tab === 'invoices' ? (
              <th className="py-1">Ação</th>
            ) : tab === 'networks' ? (
              <th className="py-1">Integrar</th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {tableRows.map((r) => (
            <tr key={r.key} className="border-b border-gray-100">
              <td className="py-1 font-mono text-xs">{r.col1}</td>
              <td className="py-1">{r.col2}</td>
              <td className="py-1 text-gray-600">{r.col3}</td>
              {tab === 'networks' ? (
                <td className="py-1">
                  <button
                    type="button"
                    className="text-indigo-600 text-xs"
                    onClick={() => void loadIntegrationGuide(r.col1)}
                  >
                    Como integrar
                  </button>
                </td>
              ) : null}
              {tab === 'intelligence' && r.key && !r.key.startsWith('bm-') && r.key !== 'intel-dash' ? (
                <td className="py-1">
                  <button type="button" className="text-indigo-600 text-xs" onClick={() => void onResolveInsight(r.key)}>
                    Resolver
                  </button>
                </td>
              ) : tab === 'intelligence' ? (
                <td className="py-1">—</td>
              ) : null}
              {tab === 'reconciliation' ? (
                <td className="py-1">
                  {r.col3 === 'OPEN' ? (
                    <button type="button" className="text-indigo-600 text-xs" onClick={() => void resolveGap(r.key)}>
                      Resolver
                    </button>
                  ) : (
                    '—'
                  )}
                </td>
              ) : null}
              {tab === 'webhooks' ? (
                <td className="py-1">
                  {r.col3 === 'FAILED' ? (
                    <button type="button" className="text-indigo-600 text-xs" onClick={() => void onReplayWebhook(r.key)}>
                      Replay
                    </button>
                  ) : (
                    '—'
                  )}
                </td>
              ) : null}
              {tab === 'billing' && r.col1 === 'ciclo' ? (
                <td className="py-1">
                  {r.col2 !== 'CLOSED' ? (
                    <button type="button" className="text-indigo-600 text-xs" onClick={() => void onCloseCycle(r.key.replace('cy-', ''))}>
                      Fechar
                    </button>
                  ) : (
                    '—'
                  )}
                </td>
              ) : tab === 'billing' ? (
                <td className="py-1">—</td>
              ) : null}
              {tab === 'settlements' ? (
                <td className="py-1">
                  <button type="button" className="text-indigo-600 text-xs" onClick={() => void onReconcileSettlement(r.key)}>
                    Reconciliar
                  </button>
                </td>
              ) : null}
              {tab === 'invoices' && r.col2?.includes('fiscal') && !r.col2.includes('AUTHORIZED') ? (
                <td className="py-1">
                  <button type="button" className="text-indigo-600 text-xs" onClick={() => void onEmitFiscal(r.key)}>
                    Emitir NF
                  </button>
                </td>
              ) : tab === 'invoices' ? (
                <td className="py-1">—</td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-gray-500">{tableRows.length} registro(s) · aba {tab}</p>
    </div>
  )
}
