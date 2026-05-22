import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  partnerAdminApi,
  type EcommercePartner,
  type LogisticsPartner,
  type OnboardingMilestone,
  type EcosystemLink,
  type EcosystemPlayer,
  type Partner360,
  type PartnerContact,
  type PartnerDashboard,
  type SettlementBatch,
} from '../../api/partnerAdmin'

type Tab =
  | 'overview'
  | 'onboarding'
  | 'ecommerce'
  | 'logistics'
  | 'integrations'
  | 'webhook_monitor'
  | 'integration_health'
  | 'outbox'
  | 'contacts'
  | 'settlements'
  | 'service_areas'
  | 'billing'
  | 'invoices'
  | 'credits'
  | 'holds'
  | 'commission'
  | 'sla'
  | 'status'
  | 'stores'
  | 'ecosystem'
  | 'global_ops'
  | 'capability_webhooks'

const TAB_KEYS: Tab[] = [
  'overview',
  'onboarding',
  'ecommerce',
  'logistics',
  'integrations',
  'webhook_monitor',
  'integration_health',
  'outbox',
  'contacts',
  'settlements',
  'service_areas',
  'billing',
  'invoices',
  'credits',
  'holds',
  'commission',
  'sla',
  'status',
  'stores',
  'ecosystem',
  'global_ops',
  'capability_webhooks',
]

const tabs: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Visão 360' },
  { key: 'onboarding', label: 'Onboarding' },
  { key: 'ecommerce', label: 'E-commerce' },
  { key: 'logistics', label: 'Logística' },
  { key: 'integrations', label: 'Webhook / API keys' },
  { key: 'webhook_monitor', label: 'Entregas webhook' },
  { key: 'integration_health', label: 'Saúde integração' },
  { key: 'outbox', label: 'Outbox eventos' },
  { key: 'contacts', label: 'Contatos' },
  { key: 'settlements', label: 'Settlements' },
  { key: 'service_areas', label: 'Service areas' },
  { key: 'billing', label: 'Billing' },
  { key: 'invoices', label: 'NF B2B' },
  { key: 'credits', label: 'Créditos' },
  { key: 'holds', label: 'Retenções' },
  { key: 'commission', label: 'Comissão' },
  { key: 'sla', label: 'SLA' },
  { key: 'status', label: 'Histórico status' },
  { key: 'stores', label: 'Lojas C&C' },
  { key: 'ecosystem', label: 'Redes mundiais' },
  { key: 'global_ops', label: 'Global OPS' },
  { key: 'capability_webhooks', label: 'Webhooks capability' },
]

const emptyEc = () => ({
  id: '',
  name: '',
  code: '',
  integration_type: 'REST',
  status: 'DRAFT',
  country: 'BR',
  active: true,
})

const emptyLg = () => ({
  id: '',
  name: '',
  code: '',
  integration_type: 'REST',
  country: 'BR',
  active: true,
})

export default function OpsPartnersAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as Tab) || 'overview'
  const [tab, setTab] = useState<Tab>(TAB_KEYS.includes(initialTab) ? initialTab : 'overview')

  const [ecForm, setEcForm] = useState(emptyEc)
  const [lgForm, setLgForm] = useState(emptyLg)
  const [ecItems, setEcItems] = useState<EcommercePartner[]>([])
  const [lgItems, setLgItems] = useState<LogisticsPartner[]>([])
  const [selectedId, setSelectedId] = useState('partner_demo_001')
  const [partnerType, setPartnerType] = useState('ECOMMERCE')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [contacts, setContacts] = useState<PartnerContact[]>([])
  const [contactName, setContactName] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [settlements, setSettlements] = useState<SettlementBatch[]>([])
  const [performance, setPerformance] = useState<unknown[]>([])
  const [serviceAreas, setServiceAreas] = useState<unknown[]>([])
  const [billingPlans, setBillingPlans] = useState<unknown[]>([])
  const [billingCycles, setBillingCycles] = useState<unknown[]>([])
  const [stores, setStores] = useState<unknown[]>([])
  const [dashboard, setDashboard] = useState<PartnerDashboard | null>(null)
  const [p360, setP360] = useState<Partner360 | null>(null)
  const [onboarding, setOnboarding] = useState<OnboardingMilestone[]>([])
  const [onboardingPct, setOnboardingPct] = useState(0)
  const [webhookDeliveries, setWebhookDeliveries] = useState<unknown[]>([])
  const [integrationHealth, setIntegrationHealth] = useState<unknown[]>([])
  const [outbox, setOutbox] = useState<unknown[]>([])
  const [invoices, setInvoices] = useState<unknown[]>([])
  const [lineItems, setLineItems] = useState<unknown[]>([])
  const [creditNotes, setCreditNotes] = useState<unknown[]>([])
  const [paymentHolds, setPaymentHolds] = useState<unknown[]>([])
  const [commissions, setCommissions] = useState<unknown[]>([])
  const [slaItems, setSlaItems] = useState<unknown[]>([])
  const [statusHistory, setStatusHistory] = useState<unknown[]>([])
  const [ecosystemPlayers, setEcosystemPlayers] = useState<EcosystemPlayer[]>([])
  const [ecosystemLinks, setEcosystemLinks] = useState<EcosystemLink[]>([])
  const [ecoPriorityOnly, setEcoPriorityOnly] = useState(true)
  const [ecoSummary, setEcoSummary] = useState<Record<string, unknown> | null>(null)
  const [ecoRelations, setEcoRelations] = useState<{ from_player_code?: string; to_player_code?: string; relation_type: string }[]>([])
  const [globalOpsSummary, setGlobalOpsSummary] = useState<Record<string, unknown> | null>(null)
  const [globalCorridors, setGlobalCorridors] = useState<{ corridor_code: string; name: string; origin_country: string; dest_country: string; primary_player_code: string }[]>([])
  const [ecoReadiness, setEcoReadiness] = useState<{ player_code: string; readiness_band: string; score_total: number }[]>([])
  const [relationHealth, setRelationHealth] = useState<{ from_player_code: string; to_player_code: string; health_status: string }[]>([])
  const [corridorSla, setCorridorSla] = useState<{ corridor_code: string; compliance_status: string; max_transit_hours: number }[]>([])
  const [deadLetterDeliveries, setDeadLetterDeliveries] = useState<{ id: string; status: string; event_type: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const partnerOptions = useMemo(() => {
    const ec = ecItems.map((p) => ({ id: p.id, code: p.code, type: 'ECOMMERCE' }))
    const lg = lgItems.map((p) => ({ id: p.id, code: p.code, type: 'LOGISTICS' }))
    return [...ec, ...lg]
  }, [ecItems, lgItems])

  const setTabAndUrl = (next: Tab) => {
    setTab(next)
    setSearchParams(next === 'overview' ? {} : { tab: next }, { replace: true })
  }

  const loadPartners = useCallback(async () => {
    const [ec, lg] = await Promise.all([partnerAdminApi.listEcommerce(), partnerAdminApi.listLogistics()])
    setEcItems(ec.data.partners ?? [])
    setLgItems(lg.data.partners ?? [])
  }, [])

  const loadDomain = useCallback(async () => {
    if (!selectedId) return
    const [
      s,
      p,
      sa,
      bp,
      bc,
      p360r,
      onb,
      wh,
      ih,
      ob,
      inv,
      li,
      cn,
      ph,
      comm,
      sla,
      st,
      ecoLinks,
      ecoPlayers,
      ecoSummaryRes,
      ecoRelationsRes,
    ] = await Promise.all([
      partnerAdminApi.listSettlements(selectedId),
      partnerAdminApi.listPerformance(selectedId),
      partnerAdminApi.listServiceAreas(selectedId),
      partnerAdminApi.listBillingPlans(selectedId),
      partnerAdminApi.listBillingCycles(selectedId),
      partnerAdminApi.partner360(selectedId, partnerType),
      partnerAdminApi.listOnboarding(selectedId, partnerType),
      partnerAdminApi.listWebhookDeliveries(selectedId),
      partnerAdminApi.listIntegrationHealth(selectedId),
      partnerAdminApi.listOutbox(selectedId),
      partnerAdminApi.listInvoices(selectedId),
      partnerAdminApi.listBillingLineItems(selectedId, 'cycle-demo-001'),
      partnerAdminApi.listCreditNotes(selectedId),
      partnerAdminApi.listPaymentHolds(selectedId),
      partnerAdminApi.listCommissions(selectedId),
      partnerAdminApi.listSla(selectedId),
      partnerAdminApi.listStatusHistory(selectedId),
      partnerAdminApi.listEcosystemLinks(selectedId, partnerType),
      partnerAdminApi.listEcosystemPlayers({ priority_only: ecoPriorityOnly }),
      partnerAdminApi.ecosystemSummary(),
      partnerAdminApi.ecosystemRelations(),
    ])
    setSettlements(s.data.items ?? [])
    setPerformance(p.data.items ?? [])
    setServiceAreas(sa.data.items ?? [])
    setBillingPlans(bp.data.items ?? [])
    setBillingCycles(bc.data.items ?? [])
    setP360(p360r.data)
    setOnboarding(onb.data.items ?? [])
    setOnboardingPct(onb.data.progress_pct ?? 0)
    setWebhookDeliveries(wh.data.items ?? [])
    setIntegrationHealth(ih.data.items ?? [])
    setOutbox(ob.data.items ?? [])
    setInvoices(inv.data.items ?? [])
    setLineItems(li.data.items ?? [])
    setCreditNotes(cn.data.items ?? [])
    setPaymentHolds(ph.data.items ?? [])
    setCommissions(comm.data.items ?? [])
    setSlaItems(sla.data.items ?? [])
    setStatusHistory(st.data.items ?? [])
    setEcosystemLinks(ecoLinks.data.items ?? [])
    setEcosystemPlayers(ecoPlayers.data.items ?? [])
    setEcoSummary(ecoSummaryRes.data as Record<string, unknown>)
    setEcoRelations(ecoRelationsRes.data ?? [])
  }, [selectedId, partnerType, ecoPriorityOnly])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      await loadPartners()
      const dash = await partnerAdminApi.opsDashboard({ partner_id: selectedId || undefined })
      setDashboard(dash.data)
      if (selectedId) {
        await loadDomain()
        const c = await partnerAdminApi.listContacts(selectedId, partnerType)
        setContacts(c.data.contacts ?? [])
      }
      const st = await partnerAdminApi.listStores()
      setStores(st.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [loadDomain, loadPartners, partnerType, selectedId])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      await partnerAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onSubmitEc = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await partnerAdminApi.createEcommerce(ecForm)
      setMessage(`Parceiro e-commerce ${data.code} criado.`)
      setSelectedId(data.id)
      setPartnerType('ECOMMERCE')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar')
    } finally {
      setLoading(false)
    }
  }

  const onSubmitLg = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await partnerAdminApi.createLogistics(lgForm)
      setMessage(`Parceiro logística ${data.code} criado.`)
      setSelectedId(data.id)
      setPartnerType('LOGISTICS')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return
    setLoading(true)
    try {
      await partnerAdminApi.configureWebhook(selectedId, partnerType, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['order.created', 'order.updated'],
      })
      setMessage(`Webhook salvo para ${selectedId}.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const { data } = await partnerAdminApi.rotateApiKey(selectedId, partnerType)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onCreateContact = async () => {
    if (!selectedId || !contactName) return
    setLoading(true)
    try {
      await partnerAdminApi.createContact(selectedId, partnerType, {
        name: contactName,
        email: contactEmail || undefined,
        is_primary: contacts.length === 0,
      })
      setContactName('')
      setContactEmail('')
      const c = await partnerAdminApi.listContacts(selectedId, partnerType)
      setContacts(c.data.contacts ?? [])
      setMessage('Contato criado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar contato')
    } finally {
      setLoading(false)
    }
  }

  const onGenerateSettlement = async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      await partnerAdminApi.generateSettlement(selectedId, {
        period_start: '2026-05-01',
        period_end: '2026-05-15',
        revenue_share_pct: 0.15,
        fees_cents: 2500,
        total_orders: 5,
        gross_revenue_cents: 50000,
      })
      setMessage('Settlement gerado.')
      await loadDomain()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao gerar settlement')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Partners</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Cadastro, integrações, settlements, service areas e billing (partner-admin).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
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

      <div className="flex flex-wrap gap-1 border-b border-gray-200 pb-2 dark:border-slate-700">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTabAndUrl(t.key)}
            className={`rounded px-3 py-1 text-sm ${
              tab === t.key ? 'bg-indigo-600 text-white' : 'text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
        <label className="text-xs text-gray-500">Parceiro</label>
        <select
          className="rounded border px-2 py-1 text-sm"
          value={selectedId}
          onChange={(e) => {
            const opt = partnerOptions.find((p) => p.id === e.target.value)
            setSelectedId(e.target.value)
            if (opt) setPartnerType(opt.type)
          }}
        >
          <option value="">—</option>
          {partnerOptions.map((p) => (
            <option key={p.id} value={p.id}>
              {p.code} ({p.type})
            </option>
          ))}
        </select>
        <select className="rounded border px-2 py-1 text-sm" value={partnerType} onChange={(e) => setPartnerType(e.target.value)}>
          <option value="ECOMMERCE">ECOMMERCE</option>
          <option value="LOGISTICS">LOGISTICS</option>
        </select>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      {tab === 'overview' && (p360 || dashboard) && (
        <section className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4">
          {p360 ? (
            <>
              <Kpi label="Onboarding" value={`${p360.onboarding_progress_pct}%`} />
              <Kpi label="Integração" value={p360.integration_status} />
              <Kpi label="Settlements draft" value={String(p360.settlements_draft)} />
              <Kpi label="Outbox pendente" value={String(p360.pending_outbox)} />
              <Kpi label="Ciclos abertos" value={String(p360.open_billing_cycles)} />
              <Kpi label="NF pendentes" value={String(p360.pending_invoices)} />
              <Kpi label="Webhook falhas 24h" value={String(p360.webhook_failures_24h)} />
              <Kpi label="SLA ativo" value={p360.sla_active ? 'sim' : 'não'} />
              <Kpi label="Redes vinculadas" value={String(p360.ecosystem_links ?? 0)} />
              <Kpi label="Players prioritários" value={String(p360.ecosystem_priority_links ?? 0)} />
            </>
          ) : (
            <>
              <Kpi label="Eventos" value={String(dashboard?.kpis.total_events ?? 0)} />
              <Kpi label="Erro %" value={`${dashboard?.kpis.error_rate_pct ?? 0}%`} />
              <Kpi label="Confiança" value={dashboard?.compare.confidence_level ?? '—'} />
            </>
          )}
        </section>
      )}

      {tab === 'onboarding' && (
        <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="mb-3 text-sm text-gray-500">Progresso: {onboardingPct}%</p>
          <ul className="space-y-2 text-sm">
            {onboarding.map((m) => (
              <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 border-t py-2 dark:border-slate-800">
                <span>
                  {m.milestone_label} <span className="font-mono text-xs text-gray-400">({m.milestone_code})</span>
                </span>
                <button
                  type="button"
                  className="rounded bg-indigo-600 px-2 py-1 text-xs text-white"
                  onClick={() =>
                    void partnerAdminApi.patchOnboarding(selectedId, m.id, { status: 'DONE' }).then(() => load())
                  }
                >
                  Marcar DONE
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'ecommerce' && (
        <>
          <form onSubmit={onSubmitEc} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
            <input className="rounded border px-2 py-1 text-sm md:col-span-2" placeholder="ID (opcional)" value={ecForm.id} onChange={(e) => setEcForm((f) => ({ ...f, id: e.target.value }))} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="Nome" required value={ecForm.name} onChange={(e) => setEcForm((f) => ({ ...f, name: e.target.value }))} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="Código" required value={ecForm.code} onChange={(e) => setEcForm((f) => ({ ...f, code: e.target.value }))} />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
              Criar e-commerce
            </button>
          </form>
          <PartnerTable items={ecItems} />
        </>
      )}

      {tab === 'logistics' && (
        <>
          <form onSubmit={onSubmitLg} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
            <input className="rounded border px-2 py-1 text-sm md:col-span-2" placeholder="ID (opcional)" value={lgForm.id} onChange={(e) => setLgForm((f) => ({ ...f, id: e.target.value }))} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="Nome" required value={lgForm.name} onChange={(e) => setLgForm((f) => ({ ...f, name: e.target.value }))} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="Código" required value={lgForm.code} onChange={(e) => setLgForm((f) => ({ ...f, code: e.target.value }))} />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
              Criar logística
            </button>
          </form>
          <PartnerTable items={lgItems} />
        </>
      )}

      {tab === 'integrations' && (
        <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
          <div className="flex flex-wrap gap-2">
            <input className="min-w-[14rem] flex-1 rounded border px-2 py-1 text-sm" placeholder="Webhook URL" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="Secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} />
            <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
              Webhook
            </button>
            <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
              Rotacionar API key
            </button>
          </div>
        </section>
      )}

      {tab === 'contacts' && (
        <section className="space-y-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex flex-wrap gap-2">
            <input className="rounded border px-2 py-1 text-sm" placeholder="Nome" value={contactName} onChange={(e) => setContactName(e.target.value)} />
            <input className="rounded border px-2 py-1 text-sm" placeholder="E-mail" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} />
            <button type="button" onClick={() => void onCreateContact()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Adicionar contato
            </button>
          </div>
          <ul className="text-sm">
            {contacts.map((c) => (
              <li key={c.id} className="border-t py-2 dark:border-slate-800">
                {c.name} — {c.email || '—'} {c.is_primary ? '(principal)' : ''}
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'settlements' && (
        <section className="space-y-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <button type="button" onClick={() => void onGenerateSettlement()} className="rounded bg-teal-600 px-3 py-1 text-sm text-white">
            Gerar settlement (demo)
          </button>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase text-gray-500">
                <th className="py-2">Período</th>
                <th>Status</th>
                <th>Líquido</th>
              </tr>
            </thead>
            <tbody>
              {settlements.map((s) => (
                <tr key={s.id} className="border-t dark:border-slate-800">
                  <td className="py-2 font-mono text-xs">
                    {s.period_start} → {s.period_end}
                  </td>
                  <td>{s.status}</td>
                  <td>
                    {(s.net_amount_cents / 100).toFixed(2)} {s.currency}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'service_areas' && (
        <JsonList title="Service areas" items={serviceAreas} />
      )}

      {tab === 'billing' && (
        <div className="grid gap-4 md:grid-cols-2">
          <JsonList title="Planos" items={billingPlans} />
          <JsonList title="Ciclos" items={billingCycles} />
          <div className="md:col-span-2">
            <JsonList title="Line items (cycle-demo-001)" items={lineItems} />
          </div>
        </div>
      )}

      {tab === 'webhook_monitor' && <JsonList title="Entregas webhook" items={webhookDeliveries} />}
      {tab === 'integration_health' && (
        <section className="space-y-3">
          <button
            type="button"
            className="rounded bg-teal-600 px-3 py-1 text-sm text-white"
            onClick={() =>
              void partnerAdminApi.probeIntegration(selectedId, partnerType).then(() => {
                setMessage('Probe registrado.')
                void load()
              })
            }
          >
            Executar probe
          </button>
          <JsonList title="Histórico de saúde" items={integrationHealth} />
        </section>
      )}
      {tab === 'outbox' && <JsonList title="Outbox de eventos" items={outbox} />}
      {tab === 'invoices' && <JsonList title="Notas fiscais B2B" items={invoices} />}
      {tab === 'credits' && <JsonList title="Credit notes" items={creditNotes} />}
      {tab === 'holds' && <JsonList title="Payment holds" items={paymentHolds} />}
      {tab === 'commission' && <JsonList title="Estrutura de comissão" items={commissions} />}
      {tab === 'sla' && <JsonList title="Acordos SLA" items={slaItems} />}
      {tab === 'status' && <JsonList title="Histórico de status" items={statusHistory} />}
      {tab === 'stores' && <JsonList title="Lojas click & collect" items={stores} />}

      {tab === 'ecosystem' && (
        <section className="space-y-4">
          {ecoSummary ? (
            <div className="grid gap-2 rounded-xl border p-3 text-sm dark:border-slate-700 md:grid-cols-4">
              <div>Players: {String(ecoSummary.total_players)}</div>
              <div>Relações: {String(ecoSummary.player_relations)}</div>
              <div>Mercados: {String(ecoSummary.market_presence_rows)}</div>
              <div>Prioritários: {String(ecoSummary.priority_players)}</div>
            </div>
          ) : null}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="rounded bg-indigo-600 px-3 py-1 text-sm text-white"
              onClick={async () => {
                await partnerAdminApi.syncEcosystemCatalog()
                await partnerAdminApi.seedProfessionalEcosystem()
                const wh = await partnerAdminApi.mirrorCapabilityWebhooks()
                setMessage(
                  `Catálogo + ecossistema OK. Webhooks por capability: ${wh.data.total} (${wh.data.mirrored_from_marketplace} espelho marketplace)`,
                )
                await loadDomain()
              }}
            >
              Sync catálogo mundial
            </button>
            <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-300">
              <input
                type="checkbox"
                checked={ecoPriorityOnly}
                onChange={(e) => setEcoPriorityOnly(e.target.checked)}
              />
              Só prioritários (InPost, DHL, Magalu, ML, Amazon, DPD, Correios, CTT, Worten, El Corte…)
            </label>
          </div>
          <p className="text-sm text-gray-500">
            Catálogo alinhado a Marketplace OPS e ML Admin. Vínculos do partner selecionado abaixo.
          </p>
          <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-700 dark:bg-slate-900">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase text-gray-500">
                  <th className="p-2">Código</th>
                  <th className="p-2">Nome</th>
                  <th className="p-2">Grupo</th>
                  <th className="p-2">País</th>
                  <th className="p-2">Tier</th>
                  <th className="p-2">Locker ref</th>
                </tr>
              </thead>
              <tbody>
                {ecosystemPlayers.map((p) => (
                  <tr key={p.id} className="border-t dark:border-slate-800">
                    <td className="p-2 font-mono text-xs">{p.code}</td>
                    <td className="p-2">{p.name}</td>
                    <td className="p-2">{p.parent_group}</td>
                    <td className="p-2">{p.country}</td>
                    <td className="p-2">{p.global_tier}</td>
                    <td className="p-2 font-mono text-xs">{p.locker_operator_ref ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3 className="text-sm font-semibold">Relações entre players (grafo)</h3>
          <ul className="max-h-40 overflow-auto text-xs text-gray-600 dark:text-slate-400">
            {ecoRelations.slice(0, 24).map((r, i) => (
              <li key={i}>
                {r.from_player_code} → {r.to_player_code} ({r.relation_type})
              </li>
            ))}
          </ul>
          <h3 className="text-sm font-semibold">Vínculos — {selectedId}</h3>
          <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-700 dark:bg-slate-900">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase text-gray-500">
                  <th className="p-2">Player</th>
                  <th className="p-2">Papel</th>
                  <th className="p-2">Status</th>
                  <th className="p-2">Primário</th>
                </tr>
              </thead>
              <tbody>
                {ecosystemLinks.map((l) => (
                  <tr key={l.id} className="border-t dark:border-slate-800">
                    <td className="p-2">
                      {l.player_name} <span className="font-mono text-xs text-gray-400">({l.player_code})</span>
                    </td>
                    <td className="p-2">{l.link_role}</td>
                    <td className="p-2">{l.integration_status}</td>
                    <td className="p-2">{l.is_primary ? 'sim' : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === 'global_ops' && (
        <section className="space-y-4">
          <p className="text-sm text-gray-500">
            Corredores internacionais, certificações (espelho Marketplace), SLA por rota e prontidão por player.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded bg-indigo-600 px-3 py-1 text-sm text-white"
              onClick={async () => {
                const seed = await partnerAdminApi.seedGlobalOps()
                await partnerAdminApi.mirrorCertifications()
                const [sum, corridors, readiness, health, sla] = await Promise.all([
                  partnerAdminApi.globalOpsSummary(),
                  partnerAdminApi.listGlobalCorridors(),
                  partnerAdminApi.listEcosystemReadiness(),
                  partnerAdminApi.listRelationHealth(),
                  partnerAdminApi.listCorridorSla(),
                ])
                setGlobalOpsSummary(sum.data as Record<string, unknown>)
                setGlobalCorridors(corridors.data)
                setEcoReadiness(readiness.data)
                setRelationHealth(health.data)
                setCorridorSla(sla.data)
                setMessage(
                  `Global OPS: ${seed.data.certifications} certificações, ${seed.data.corridors} corredores`,
                )
              }}
            >
              Seed Global OPS + espelho certificações
            </button>
          </div>
          {globalOpsSummary ? (
            <div className="grid gap-2 rounded-xl border border-emerald-600/30 bg-emerald-50/50 p-3 text-sm dark:bg-emerald-950/20 md:grid-cols-4">
              <div>Certificações válidas: {String(globalOpsSummary.certifications_valid)}</div>
              <div>Corredores ativos: {String(globalOpsSummary.corridors_active)}</div>
              <div>SLA corredores: {String(globalOpsSummary.corridor_sla_rows ?? 0)}</div>
              <div>Espelhadas: {String(globalOpsSummary.certifications_mirrored ?? 0)}</div>
            </div>
          ) : null}
          {globalCorridors.length > 0 ? (
            <JsonList title="Corredores" items={globalCorridors} />
          ) : null}
          {corridorSla.length > 0 ? <JsonList title="SLA por corredor" items={corridorSla} /> : null}
          {ecoReadiness.length > 0 ? <JsonList title="Prontidão por player" items={ecoReadiness} /> : null}
          {relationHealth.length > 0 ? <JsonList title="Saúde em cascata (grafo)" items={relationHealth} /> : null}
        </section>
      )}

      {tab === 'capability_webhooks' && (
        <section className="space-y-4">
          <p className="text-sm text-gray-500">
            Webhooks por capability (espelho marketplace), fila dead-letter e replay em lote.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="rounded bg-indigo-600 px-3 py-1 text-sm text-white"
              onClick={async () => {
                const wh = await partnerAdminApi.mirrorCapabilityWebhooks()
                setMessage(`Webhooks: ${wh.data.total} (${wh.data.mirrored_from_marketplace} marketplace)`)
              }}
            >
              Espelhar webhooks do catálogo
            </button>
            <button
              type="button"
              className="rounded border px-3 py-1 text-sm dark:border-slate-600"
              onClick={async () => {
                const dlq = await partnerAdminApi.listCapabilityDeliveries({ status: 'DEAD_LETTER' })
                setDeadLetterDeliveries(dlq.data.items ?? [])
                setMessage(`${dlq.data.total} entregas em dead-letter`)
              }}
            >
              Atualizar fila DLQ
            </button>
            <button
              type="button"
              className="rounded border border-amber-600 px-3 py-1 text-sm text-amber-800 dark:text-amber-300"
              onClick={async () => {
                const r = await partnerAdminApi.replayDeadLetterBatch(25)
                setMessage(`Replay DLQ: ${r.data.replayed}/${r.data.requested} (${r.data.succeeded} OK)`)
                const dlq = await partnerAdminApi.listCapabilityDeliveries({ status: 'DEAD_LETTER' })
                setDeadLetterDeliveries(dlq.data.items ?? [])
              }}
            >
              Replay dead-letter (lote)
            </button>
          </div>
          {deadLetterDeliveries.length > 0 ? (
            <div className="overflow-x-auto rounded-xl border bg-white dark:border-slate-700 dark:bg-slate-900">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase text-gray-500">
                    <th className="p-2">ID</th>
                    <th className="p-2">Evento</th>
                    <th className="p-2">Status</th>
                    <th className="p-2" />
                  </tr>
                </thead>
                <tbody>
                  {deadLetterDeliveries.map((d) => (
                    <tr key={d.id} className="border-t dark:border-slate-800">
                      <td className="p-2 font-mono text-xs">{d.id.slice(0, 12)}</td>
                      <td className="p-2">{d.event_type}</td>
                      <td className="p-2">{d.status}</td>
                      <td className="p-2">
                        <button
                          type="button"
                          className="text-indigo-600 hover:underline"
                          onClick={() =>
                            void partnerAdminApi.replayCapabilityDelivery(d.id).then(() =>
                              setMessage(`Replay ${d.id}`),
                            )
                          }
                        >
                          replay
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Nenhuma entrega em dead-letter.</p>
          )}
        </section>
      )}

      {tab === 'overview' && performance.length > 0 && (
        <JsonList title="Performance (últimos meses)" items={performance} />
      )}
    </div>
  )
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-slate-800 dark:bg-slate-950">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  )
}

function PartnerTable({ items }: { items: Array<{ id: string; code: string; name: string; active: boolean }> }) {
  return (
    <table className="w-full text-left text-sm">
      <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
        <tr>
          <th className="px-3 py-2">Código</th>
          <th className="px-3 py-2">Nome</th>
          <th className="px-3 py-2">Ativo</th>
        </tr>
      </thead>
      <tbody>
        {items.length === 0 ? (
          <tr>
            <td colSpan={3} className="px-3 py-6 text-center text-gray-500">
              Nenhum parceiro
            </td>
          </tr>
        ) : (
          items.map((p) => (
            <tr key={p.id} className="border-t dark:border-slate-800">
              <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
              <td className="px-3 py-2">{p.name}</td>
              <td className="px-3 py-2">{p.active ? 'sim' : 'não'}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  )
}

function JsonList({ title, items }: { title: string; items: unknown[] }) {
  return (
    <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-2 text-lg font-medium">{title}</h2>
      <pre className="max-h-64 overflow-auto rounded bg-gray-50 p-2 text-xs dark:bg-slate-950">
        {JSON.stringify(items, null, 2)}
      </pre>
    </section>
  )
}
