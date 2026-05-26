import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  orderPickupSubscriptionsApi,
  type CustomerSubscription,
  type SubscriptionPlan,
} from '../../api/orderPickupSubscriptions'

type Tab =
  | 'overview'
  | 'analytics'
  | 'plans'
  | 'subscriptions'
  | 'benefits'
  | 'billing'
  | 'events'
  | 'partners'
  | 'entitlements'
  | 'dunning'
  | 'integrations'
  | 'deliveries'
  | 'relations'
  | 'food_delivery'
  | 'ecosystem'
  | 'premium'
  | 'global'
  | 'efficiency'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Visão geral' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'plans', label: 'Planos' },
  { id: 'subscriptions', label: 'Assinaturas' },
  { id: 'benefits', label: 'Benefícios' },
  { id: 'billing', label: 'Faturamento' },
  { id: 'events', label: 'Eventos' },
  { id: 'partners', label: 'Programas parceiros' },
  { id: 'entitlements', label: 'Entitlements' },
  { id: 'dunning', label: 'Dunning' },
  { id: 'integrations', label: 'Webhooks & keys' },
  { id: 'deliveries', label: 'Entregas webhook' },
  { id: 'relations', label: 'Relações' },
  { id: 'food_delivery', label: 'Food delivery' },
  { id: 'ecosystem', label: 'Ecossistema' },
  { id: 'premium', label: 'Premium & growth' },
  { id: 'global', label: 'Global & compliance' },
  { id: 'efficiency', label: 'Eficiência & Smart OPS' },
]

function formatBrl(cents: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

function statusBadge(status: string) {
  const base = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1'
  const s = status.toUpperCase()
  if (s === 'ACTIVE') return `${base} bg-emerald-500/20 text-emerald-300 ring-emerald-500/35`
  if (s === 'TRIALING') return `${base} bg-sky-500/20 text-sky-300 ring-sky-500/35`
  if (s === 'PAST_DUE') return `${base} bg-amber-500/20 text-amber-300 ring-amber-500/35`
  if (s === 'CANCELLED') return `${base} bg-slate-600/40 text-slate-300 ring-slate-500/40`
  return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/30`
}

export default function OpsSubscriptionsAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = (searchParams.get('tab') as Tab) || 'overview'
  const [tab, setTab] = useState<Tab>(TABS.some((t) => t.id === tabParam) ? tabParam : 'overview')
  const [summary, setSummary] = useState<Record<string, number> | null>(null)
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [subscriptions, setSubscriptions] = useState<CustomerSubscription[]>([])
  const [benefits, setBenefits] = useState<unknown[]>([])
  const [webhooks, setWebhooks] = useState<unknown[]>([])
  const [apiKeys, setApiKeys] = useState<unknown[]>([])
  const [catalog, setCatalog] = useState<Record<string, unknown> | null>(null)
  const [priorityPlayers, setPriorityPlayers] = useState<unknown[]>([])
  const [regionFilter, setRegionFilter] = useState('')
  const [relations, setRelations] = useState<unknown[]>([])
  const [foodHandoffs, setFoodHandoffs] = useState<unknown[]>([])
  const [trends, setTrends] = useState<unknown[]>([])
  const [invoices, setInvoices] = useState<unknown[]>([])
  const [events, setEvents] = useState<unknown[]>([])
  const [partnerPrograms, setPartnerPrograms] = useState<unknown[]>([])
  const [entitlements, setEntitlements] = useState<unknown[]>([])
  const [dunningCases, setDunningCases] = useState<unknown[]>([])
  const [deliveries, setDeliveries] = useState<unknown[]>([])
  const [compareMatrix, setCompareMatrix] = useState<unknown[]>([])
  const [healthByRisk, setHealthByRisk] = useState<unknown[]>([])
  const [atRisk, setAtRisk] = useState<unknown[]>([])
  const [referrals, setReferrals] = useState<unknown[]>([])
  const [gifts, setGifts] = useState<unknown[]>([])
  const [experiments, setExperiments] = useState<unknown[]>([])
  const [renewalQueue, setRenewalQueue] = useState<unknown[]>([])
  const [churnAlerts, setChurnAlerts] = useState<unknown[]>([])
  const [worldSummary, setWorldSummary] = useState<Record<string, number> | null>(null)
  const [regionalPrices, setRegionalPrices] = useState<unknown[]>([])
  const [addonCatalog, setAddonCatalog] = useState<unknown[]>([])
  const [settlements, setSettlements] = useState<unknown[]>([])
  const [retentionOffers, setRetentionOffers] = useState<unknown[]>([])
  const [slaTargets, setSlaTargets] = useState<unknown[]>([])
  const [efficiencySummary, setEfficiencySummary] = useState<Record<string, number> | null>(null)
  const [opsInbox, setOpsInbox] = useState<unknown[]>([])
  const [promoCodes, setPromoCodes] = useState<unknown[]>([])
  const [upgradeSuggestions, setUpgradeSuggestions] = useState<unknown[]>([])
  const [automationRules, setAutomationRules] = useState<unknown[]>([])
  const [usageMeters, setUsageMeters] = useState<unknown[]>([])
  const [inboxBulkOps, setInboxBulkOps] = useState<Array<{ operation: string; label: string }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [lastApiKey, setLastApiKey] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [webhookPartner, setWebhookPartner] = useState('magalu')
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.example.com/subscriptions')
  const [subForm, setSubForm] = useState({ user_id: '', plan_type: 'PREMIUM', partner_code: '', promo_code: '' })
  const [promoForm, setPromoForm] = useState({
    code: '',
    description: '',
    discount_pct: 10,
    discount_cents: 0,
    bonus_months: 0,
    eligible_plans: 'BASIC,PREMIUM',
    max_redemptions: 100,
  })
  const [ruleForm, setRuleForm] = useState({
    rule_code: '',
    name: '',
    trigger_event: 'subscription.past_due',
    action_type: 'ISSUE_RETENTION_OFFER',
    priority: 100,
  })
  const [showPromoForm, setShowPromoForm] = useState(false)
  const [showRuleForm, setShowRuleForm] = useState(false)

  useEffect(() => {
    const fromUrl = (searchParams.get('tab') as Tab) || 'overview'
    setTab(TABS.some((t) => t.id === fromUrl) ? fromUrl : 'overview')
  }, [searchParams])

  const setTabUrl = (id: Tab) => {
    setTab(id)
    const next = new URLSearchParams(searchParams)
    if (id === 'overview') next.delete('tab')
    else next.set('tab', id)
    setSearchParams(next, { replace: true })
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [
        m,
        p,
        s,
        b,
        w,
        k,
        eco,
        pri,
        rel,
        fh,
        tr,
        inv,
        ev,
        pp,
        ent,
        dun,
        del,
        matrix,
        hsum,
        risk,
        refs,
        gft,
        exps,
        renew,
        churn,
        wsum,
        reg,
        addons,
        sett,
        ret,
        sla,
        ...efficiencyResults
      ] = await Promise.all([
        orderPickupSubscriptionsApi.metricsSummary(),
        orderPickupSubscriptionsApi.listPlans({ active_only: false }),
        orderPickupSubscriptionsApi.listSubscriptions(statusFilter ? { status: statusFilter } : {}),
        orderPickupSubscriptionsApi.listBenefitsUsage(),
        orderPickupSubscriptionsApi.listWebhooks(),
        orderPickupSubscriptionsApi.listApiKeys(),
        orderPickupSubscriptionsApi.ecosystemCatalog(),
        orderPickupSubscriptionsApi.priorityPlayers(),
        orderPickupSubscriptionsApi.listEcosystemRelations(),
        orderPickupSubscriptionsApi.listFoodHandoffs(),
        orderPickupSubscriptionsApi.metricsTrends(6),
        orderPickupSubscriptionsApi.listInvoices(),
        orderPickupSubscriptionsApi.listEvents(),
        orderPickupSubscriptionsApi.listPartnerPrograms(),
        orderPickupSubscriptionsApi.listEntitlements(),
        orderPickupSubscriptionsApi.listDunning(),
        orderPickupSubscriptionsApi.listWebhookDeliveries(),
        orderPickupSubscriptionsApi.plansCompareMatrix(),
        orderPickupSubscriptionsApi.healthSummary(),
        orderPickupSubscriptionsApi.listAtRisk(),
        orderPickupSubscriptionsApi.listReferrals(),
        orderPickupSubscriptionsApi.listGifts(),
        orderPickupSubscriptionsApi.listExperiments(),
        orderPickupSubscriptionsApi.listRenewalQueue(),
        orderPickupSubscriptionsApi.listChurnAlerts(),
        orderPickupSubscriptionsApi.worldSummary(),
        orderPickupSubscriptionsApi.listRegionalPrices(),
        orderPickupSubscriptionsApi.listAddonCatalog(),
        orderPickupSubscriptionsApi.listSettlements(),
        orderPickupSubscriptionsApi.listRetentionOffers(),
        orderPickupSubscriptionsApi.listSlaTargets(),
        Promise.allSettled([
          orderPickupSubscriptionsApi.efficiencySummary(),
          orderPickupSubscriptionsApi.opsInbox(),
          orderPickupSubscriptionsApi.listPromoCodes(),
          orderPickupSubscriptionsApi.upgradeMatrix(),
          orderPickupSubscriptionsApi.listAutomationRules(),
          orderPickupSubscriptionsApi.listUsageMeters(),
        ]),
      ])
      const efficiencySettled = efficiencyResults[0] as PromiseSettledResult<unknown>[]
      const pickEfficiency = <T,>(idx: number, fallback: T): T => {
        const r = efficiencySettled[idx]
        if (r?.status === 'fulfilled') return (r.value as { data: T }).data
        return fallback
      }
      const efficiencyFailed = efficiencySettled.some((r) => r.status === 'rejected')
      const esum = { data: pickEfficiency(0, { counts: null as Record<string, number> | null }) }
      const inbox = {
        data: pickEfficiency(1, { items: [] as unknown[], bulk_operations: [] as { operation: string; label: string }[] }),
      }
      const promos = { data: pickEfficiency(2, { items: [] as unknown[] }) }
      const upgrades = { data: pickEfficiency(3, { items: [] as unknown[] }) }
      const rules = { data: pickEfficiency(4, { items: [] as unknown[] }) }
      const meters = { data: pickEfficiency(5, { items: [] as unknown[] }) }
      setSummary(m.data.summary ?? null)
      setPlans(p.data.items ?? [])
      setSubscriptions(s.data.items ?? [])
      setBenefits(b.data.items ?? [])
      setWebhooks(w.data.items ?? [])
      setApiKeys(k.data.items ?? [])
      setCatalog(eco.data.catalog ?? null)
      setPriorityPlayers(pri.data.items ?? [])
      setRelations(rel.data.items ?? [])
      setFoodHandoffs(fh.data.items ?? [])
      setTrends(tr.data.items ?? [])
      setInvoices(inv.data.items ?? [])
      setEvents(ev.data.items ?? [])
      setPartnerPrograms(pp.data.items ?? [])
      setEntitlements(ent.data.items ?? [])
      setDunningCases(dun.data.items ?? [])
      setDeliveries(del.data.items ?? [])
      setCompareMatrix(matrix.data.plans ?? [])
      setHealthByRisk(hsum.data.by_risk ?? [])
      setAtRisk(risk.data.items ?? [])
      setReferrals(refs.data.items ?? [])
      setGifts(gft.data.items ?? [])
      setExperiments(exps.data.items ?? [])
      setRenewalQueue(renew.data.items ?? [])
      setChurnAlerts(churn.data.items ?? [])
      setWorldSummary(wsum.data.counts ?? null)
      setRegionalPrices(reg.data.items ?? [])
      setAddonCatalog(addons.data.items ?? [])
      setSettlements(sett.data.items ?? [])
      setRetentionOffers(ret.data.items ?? [])
      setSlaTargets(sla.data.items ?? [])
      setEfficiencySummary(esum.data.counts ?? null)
      setOpsInbox(inbox.data.items ?? [])
      setInboxBulkOps(inbox.data.bulk_operations ?? [])
      setPromoCodes(promos.data.items ?? [])
      setUpgradeSuggestions(upgrades.data.items ?? [])
      setAutomationRules(rules.data.items ?? [])
      setUsageMeters(meters.data.items ?? [])
      if (efficiencyFailed) {
        setMessage(
          'Módulo Eficiência indisponível (404?). Reinicie o order_pickup_service após atualizar o código: docker compose build order_pickup_service && docker compose up -d order_pickup_service',
        )
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar assinaturas')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  const onSyncEcosystemFull = async () => {
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.syncEcosystemFull()
      setMessage(`Ecossistema: ${JSON.stringify(data.synced)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no sync ecossistema')
    } finally {
      setLoading(false)
    }
  }

  const onSyncGlobal = async () => {
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.syncGlobalPlayers()
      setMessage(`Sync global: ${JSON.stringify(data.synced)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no sync global')
    } finally {
      setLoading(false)
    }
  }

  const onSeed = async () => {
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.seed()
      setMessage(`Seed: ${JSON.stringify(data.seeded)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateSubscription = async (e: FormEvent) => {
    e.preventDefault()
    if (!subForm.user_id.trim()) return
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.createSubscription({
        user_id: subForm.user_id.trim(),
        plan_type: subForm.plan_type,
        partner_code: subForm.partner_code.trim() || undefined,
        promo_code: subForm.promo_code.trim() || undefined,
      })
      setMessage('Assinatura criada.')
      setSubForm({ user_id: '', plan_type: 'PREMIUM', partner_code: '', promo_code: '' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar assinatura')
    } finally {
      setLoading(false)
    }
  }

  const onCancel = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.cancelSubscription(id, true)
      setMessage(`Assinatura ${id} cancelada.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao cancelar')
    } finally {
      setLoading(false)
    }
  }

  const onRenew = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.renewSubscription(id)
      setMessage(`Assinatura ${id} renovada.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao renovar')
    } finally {
      setLoading(false)
    }
  }

  const onUpsertWebhook = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.upsertWebhook(webhookPartner, {
        url: webhookUrl,
        events: ['subscription.created', 'subscription.renewed', 'subscription.cancelled'],
      })
      const secret = (data as { secret?: string }).secret
      if (secret) setMessage(`Webhook salvo. Secret: ${secret.slice(0, 12)}…`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onResolveDunning = async (caseId: string) => {
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.resolveDunning(caseId, { resolution_note: 'Pagamento regularizado via OPS' })
      setMessage('Caso de dunning resolvido.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao resolver dunning')
    } finally {
      setLoading(false)
    }
  }

  const onAcceptRetention = async (offerId: string) => {
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.acceptRetentionOffer(offerId)
      setMessage('Oferta de retenção aceita.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao aceitar retenção')
    } finally {
      setLoading(false)
    }
  }

  const onInboxAction = async (item: Record<string, unknown>, action = 'primary') => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupSubscriptionsApi.inboxAct({
        kind: String(item.kind),
        id: String(item.id),
        action,
        notes: action === 'apply_upgrade' && item.suggested_plan ? String(item.suggested_plan) : undefined,
      })
      setMessage(`Inbox: ${data.ok ? 'ok' : 'feito'} (${String(item.kind)} / ${action})`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na ação do inbox')
    } finally {
      setLoading(false)
    }
  }

  const onInboxBulk = async (operation: 'renewals_run_due' | 'churn_resolve_high' | 'churn_resolve_all') => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupSubscriptionsApi.inboxBulk(operation)
      setMessage(`Bulk ${operation}: ${data.processed} processado(s).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na ação em lote')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePromo = async (e: FormEvent) => {
    e.preventDefault()
    if (!promoForm.code.trim()) return
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.createPromoCode({
        code: promoForm.code.trim(),
        description: promoForm.description.trim() || undefined,
        discount_pct: promoForm.discount_pct,
        discount_cents: promoForm.discount_cents,
        bonus_months: promoForm.bonus_months,
        eligible_plans: promoForm.eligible_plans
          .split(',')
          .map((p) => p.trim())
          .filter(Boolean),
        max_redemptions: promoForm.max_redemptions,
      })
      setMessage(`Cupom criado: ${data.code}`)
      setShowPromoForm(false)
      setPromoForm({
        code: '',
        description: '',
        discount_pct: 10,
        discount_cents: 0,
        bonus_months: 0,
        eligible_plans: 'BASIC,PREMIUM',
        max_redemptions: 100,
      })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar cupom')
    } finally {
      setLoading(false)
    }
  }

  const onCreateRule = async (e: FormEvent) => {
    e.preventDefault()
    if (!ruleForm.rule_code.trim() || !ruleForm.name.trim()) return
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.createAutomationRule({
        rule_code: ruleForm.rule_code.trim(),
        name: ruleForm.name.trim(),
        trigger_event: ruleForm.trigger_event,
        action_type: ruleForm.action_type,
        priority: ruleForm.priority,
        config_json: {},
      })
      setMessage('Regra de automação criada.')
      setShowRuleForm(false)
      setRuleForm({
        rule_code: '',
        name: '',
        trigger_event: 'subscription.past_due',
        action_type: 'ISSUE_RETENTION_OFFER',
        priority: 100,
      })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar regra')
    } finally {
      setLoading(false)
    }
  }

  const onSimulateDelivery = async () => {
    setLoading(true)
    try {
      await orderPickupSubscriptionsApi.simulateWebhookDelivery(webhookPartner)
      setMessage('Entrega webhook simulada (200).')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na simulação')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    setLoading(true)
    try {
      const { data } = await orderPickupSubscriptionsApi.rotateApiKey(webhookPartner)
      setLastApiKey(data.api_key)
      setMessage(`API key rotacionada (${data.key_prefix}).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na rotação')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Assinaturas / Subscriptions</h1>
          <p className="text-sm text-slate-400">
            Planos B2C, assinaturas de clientes, benefícios, webhooks e integração com players globais.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800"
          >
            Atualizar
          </button>
          <button
            type="button"
            onClick={() => void onSyncEcosystemFull()}
            disabled={loading}
            className="rounded-lg border border-emerald-500/50 px-3 py-1.5 text-sm text-emerald-200 hover:bg-emerald-950/40"
          >
            Sync ecossistema completo
          </button>
          <button
            type="button"
            onClick={() => void onSyncGlobal()}
            disabled={loading}
            className="rounded-lg border border-indigo-500/50 px-3 py-1.5 text-sm text-indigo-200 hover:bg-indigo-950/50"
          >
            Sync players mundial
          </button>
          <button
            type="button"
            onClick={() => void onSeed()}
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Seed demo
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-2 text-sm text-red-200">{error}</div>
      )}
      {message && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-200">
          {message}
        </div>
      )}
      {lastApiKey && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-4 py-2 font-mono text-xs text-amber-100">
          Nova API key (copie agora): {lastApiKey}
        </div>
      )}

      <nav className="flex flex-wrap gap-2 border-b border-slate-700 pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTabUrl(t.id)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              tab === t.id ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'analytics' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Mês</th>
                <th className="px-4 py-3">Plano</th>
                <th className="px-4 py-3">Assinantes</th>
                <th className="px-4 py-3">MRR</th>
              </tr>
            </thead>
            <tbody>
              {(trends as Array<Record<string, unknown>>).map((row, i) => (
                <tr key={`${row.month_ref}-${row.plan_type}-${i}`} className="border-t border-slate-800">
                  <td className="px-4 py-2">{String(row.month_ref)}</td>
                  <td className="px-4 py-2">{String(row.plan_type)}</td>
                  <td className="px-4 py-2">{String(row.active_subscribers)}</td>
                  <td className="px-4 py-2">{formatBrl(Number(row.mrr_cents))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'overview' && summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <p className="text-xs text-slate-400">MRR</p>
            <p className="text-xl font-semibold text-white">{formatBrl(summary.mrr_cents ?? 0)}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <p className="text-xs text-slate-400">Ativas</p>
            <p className="text-xl font-semibold text-white">{summary.active_subscriptions ?? 0}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <p className="text-xs text-slate-400">Trial</p>
            <p className="text-xl font-semibold text-white">{summary.trialing_subscriptions ?? 0}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <p className="text-xs text-slate-400">Planos ativos</p>
            <p className="text-xl font-semibold text-white">{summary.active_plans ?? 0}</p>
          </div>
        </div>
      )}

      {tab === 'plans' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Código</th>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Mensal</th>
                <th className="px-4 py-3">Benefícios</th>
                <th className="px-4 py-3">Ativo</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.id} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono text-indigo-300">{p.code}</td>
                  <td className="px-4 py-2">{p.name}</td>
                  <td className="px-4 py-2">{formatBrl(p.monthly_fee_cents)}</td>
                  <td className="px-4 py-2 text-xs">
                    {[p.free_shipping && 'frete', p.priority_shelf && 'prateleira', p.exclusive_deals && 'ofertas']
                      .filter(Boolean)
                      .join(' · ') || '—'}
                  </td>
                  <td className="px-4 py-2">{p.is_active ? 'Sim' : 'Não'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'subscriptions' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
            <label className="text-xs text-slate-400">
              Status
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="mt-1 block rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              >
                <option value="">Todos</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="TRIALING">TRIALING</option>
                <option value="PAST_DUE">PAST_DUE</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </label>
          </div>
          <form onSubmit={onCreateSubscription} className="flex flex-wrap gap-3 rounded-xl border border-slate-700 p-4">
            <input
              placeholder="user_id"
              value={subForm.user_id}
              onChange={(e) => setSubForm((f) => ({ ...f, user_id: e.target.value }))}
              className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            />
            <select
              value={subForm.plan_type}
              onChange={(e) => setSubForm((f) => ({ ...f, plan_type: e.target.value }))}
              className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            >
              {['BASIC', 'PREMIUM', 'PRO', 'ENTERPRISE'].map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <input
              placeholder="partner_code (opcional)"
              value={subForm.partner_code}
              onChange={(e) => setSubForm((f) => ({ ...f, partner_code: e.target.value }))}
              className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            />
            <input
              placeholder="cupom (opcional)"
              value={subForm.promo_code}
              onChange={(e) => setSubForm((f) => ({ ...f, promo_code: e.target.value.toUpperCase() }))}
              className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            />
            <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Nova assinatura
            </button>
          </form>
          <div className="overflow-x-auto rounded-xl border border-slate-700">
            <table className="min-w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3">Plano</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">MRR</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((s) => (
                  <tr key={s.id} className="border-t border-slate-800">
                    <td className="max-w-[8rem] truncate px-4 py-2 font-mono text-xs">
                      <Link to={`/ops/subscriptions/subscribers/${s.id}`} className="text-indigo-400 hover:underline">
                        {s.id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td className="px-4 py-2">{s.user_id ?? '—'}</td>
                    <td className="px-4 py-2">{s.plan_type}</td>
                    <td className="px-4 py-2">
                      <span className={statusBadge(s.status)}>{s.status}</span>
                    </td>
                    <td className="px-4 py-2">{formatBrl(s.monthly_fee_cents)}</td>
                    <td className="px-4 py-2 space-x-2">
                      <button
                        type="button"
                        onClick={() => void onRenew(s.id)}
                        className="text-xs text-indigo-400 hover:underline"
                      >
                        Renovar
                      </button>
                      <button
                        type="button"
                        onClick={() => void onCancel(s.id)}
                        className="text-xs text-red-400 hover:underline"
                      >
                        Cancelar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'benefits' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Assinatura</th>
                <th className="px-4 py-3">Mês</th>
                <th className="px-4 py-3">Benefício</th>
                <th className="px-4 py-3">Uso / Limite</th>
              </tr>
            </thead>
            <tbody>
              {(benefits as Array<Record<string, unknown>>).map((b) => (
                <tr key={String(b.id)} className="border-t border-slate-800">
                  <td className="max-w-[8rem] truncate px-4 py-2 font-mono text-xs">{String(b.subscription_id)}</td>
                  <td className="px-4 py-2">{String(b.usage_month)}</td>
                  <td className="px-4 py-2">{String(b.benefit_type)}</td>
                  <td className="px-4 py-2">
                    {String(b.usage_count)} / {b.usage_limit != null ? String(b.usage_limit) : '∞'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'billing' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Assinatura</th>
                <th className="px-4 py-3">Período</th>
                <th className="px-4 py-3">Valor</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {(invoices as Array<Record<string, unknown>>).map((inv) => (
                <tr key={String(inv.id)} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono text-xs">{String(inv.subscription_id).slice(0, 8)}…</td>
                  <td className="px-4 py-2 text-xs">
                    {String(inv.period_start ?? '').slice(0, 10)} → {String(inv.period_end ?? '').slice(0, 10)}
                  </td>
                  <td className="px-4 py-2">{formatBrl(Number(inv.amount_cents))}</td>
                  <td className="px-4 py-2">{String(inv.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'events' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Assinatura</th>
                <th className="px-4 py-3">Evento</th>
                <th className="px-4 py-3">Quando</th>
              </tr>
            </thead>
            <tbody>
              {(events as Array<Record<string, unknown>>).map((ev) => (
                <tr key={String(ev.id)} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono text-xs">{String(ev.subscription_id).slice(0, 8)}…</td>
                  <td className="px-4 py-2">{String(ev.event_type)}</td>
                  <td className="px-4 py-2 text-xs">{String(ev.created_at).slice(0, 19)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'partners' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Código</th>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Plano default</th>
                <th className="px-4 py-3">Rev.share</th>
              </tr>
            </thead>
            <tbody>
              {(partnerPrograms as Array<Record<string, unknown>>).map((p) => (
                <tr key={String(p.id)} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono text-indigo-300">{String(p.partner_code)}</td>
                  <td className="px-4 py-2">{String(p.partner_name)}</td>
                  <td className="px-4 py-2 text-xs">{String(p.partner_type)}</td>
                  <td className="px-4 py-2">{String(p.default_plan_code ?? '—')}</td>
                  <td className="px-4 py-2">{String(p.revenue_share_pct)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'entitlements' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Plano</th>
                <th className="px-4 py-3">Player</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Regiões</th>
              </tr>
            </thead>
            <tbody>
              {(entitlements as Array<Record<string, unknown>>).map((e) => (
                <tr key={String(e.id)} className="border-t border-slate-800">
                  <td className="px-4 py-2">{String(e.plan_code)}</td>
                  <td className="px-4 py-2">{String(e.player_name)}</td>
                  <td className="px-4 py-2 text-xs">{String(e.player_type)}</td>
                  <td className="px-4 py-2 text-xs">{JSON.stringify(e.region_codes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'dunning' && (
        <div className="space-y-3">
          <div className="overflow-x-auto rounded-xl border border-slate-700">
            <table className="min-w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3">Estágio</th>
                  <th className="px-4 py-3">Devido</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {(dunningCases as Array<Record<string, unknown>>).map((d) => (
                  <tr key={String(d.id)} className="border-t border-slate-800">
                    <td className="px-4 py-2">{String(d.user_id)}</td>
                    <td className="px-4 py-2">{String(d.stage)}</td>
                    <td className="px-4 py-2">{formatBrl(Number(d.amount_due_cents))}</td>
                    <td className="px-4 py-2">{String(d.status)}</td>
                    <td className="px-4 py-2">
                      {String(d.status) === 'OPEN' && (
                        <button
                          type="button"
                          onClick={() => void onResolveDunning(String(d.id))}
                          className="text-xs text-emerald-400 hover:underline"
                        >
                          Resolver
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'deliveries' && (
        <div className="space-y-3">
          <button
            type="button"
            onClick={() => void onSimulateDelivery()}
            className="rounded bg-slate-700 px-3 py-1 text-sm text-white hover:bg-slate-600"
          >
            Simular entrega ({webhookPartner})
          </button>
          <div className="overflow-x-auto rounded-xl border border-slate-700">
            <table className="min-w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Evento</th>
                  <th className="px-4 py-3">HTTP</th>
                  <th className="px-4 py-3">Tentativa</th>
                  <th className="px-4 py-3">Quando</th>
                </tr>
              </thead>
              <tbody>
                {(deliveries as Array<Record<string, unknown>>).map((d) => (
                  <tr key={String(d.id)} className="border-t border-slate-800">
                    <td className="px-4 py-2">{String(d.event_type)}</td>
                    <td className="px-4 py-2">{String(d.http_status)}</td>
                    <td className="px-4 py-2">{String(d.attempt_no)}</td>
                    <td className="px-4 py-2 text-xs">{String(d.delivered_at).slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'integrations' && (
        <div className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={onUpsertWebhook} className="space-y-3 rounded-xl border border-slate-700 p-4">
            <h2 className="font-medium text-white">Webhook config</h2>
            <input
              value={webhookPartner}
              onChange={(e) => setWebhookPartner(e.target.value)}
              placeholder="partner_code"
              className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            />
            <input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="URL"
              className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            />
            <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
              Salvar webhook
            </button>
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {(webhooks as Array<Record<string, unknown>>).map((w) => (
                <li key={String(w.id)}>
                  {String(w.partner_code)} → {String(w.url)}
                </li>
              ))}
            </ul>
          </form>
          <div className="space-y-3 rounded-xl border border-slate-700 p-4">
            <h2 className="font-medium text-white">API key rotation</h2>
            <button
              type="button"
              onClick={() => void onRotateKey()}
              className="rounded bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-500"
            >
              Rotacionar key ({webhookPartner})
            </button>
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {(apiKeys as Array<Record<string, unknown>>).map((k) => (
                <li key={String(k.id)}>
                  {String(k.partner_code)} · {String(k.key_prefix)}…
                  {k.revoked_at ? ' (revogada)' : ''}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {tab === 'relations' && (
        <div className="overflow-x-auto rounded-xl border border-slate-700">
          <table className="min-w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">De</th>
                <th className="px-4 py-3">Para</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Modo</th>
                <th className="px-4 py-3">Plano mín.</th>
              </tr>
            </thead>
            <tbody>
              {(relations as Array<Record<string, unknown>>).map((r, i) => (
                <tr key={String(r.id ?? i)} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono text-xs text-indigo-300">{String(r.from_player_code ?? r.from)}</td>
                  <td className="px-4 py-2 font-mono text-xs">{String(r.to_player_code ?? r.to)}</td>
                  <td className="px-4 py-2">{String(r.relation_type ?? r.type)}</td>
                  <td className="px-4 py-2 text-xs">{String(r.integration_mode ?? r.mode)}</td>
                  <td className="px-4 py-2">{String(r.min_plan_code ?? r.min_plan ?? '—')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'food_delivery' && (
        <div className="space-y-4">
          <p className="text-sm text-slate-400">
            Handoffs food → locker/PUDO (iFood, Rappi, Uber Eats, Glovo, Deliveroo, DoorDash…)
          </p>
          <div className="overflow-x-auto rounded-xl border border-slate-700">
            <table className="min-w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Plataforma</th>
                  <th className="px-4 py-3">Ponto retirada</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">SLA</th>
                  <th className="px-4 py-3">Plano</th>
                </tr>
              </thead>
              <tbody>
                {(foodHandoffs as Array<Record<string, unknown>>).map((h) => (
                  <tr key={String(h.id)} className="border-t border-slate-800">
                    <td className="px-4 py-2">{String(h.food_platform_code)}</td>
                    <td className="px-4 py-2">{String(h.pickup_player_code)}</td>
                    <td className="px-4 py-2">{String(h.handoff_type)}</td>
                    <td className="px-4 py-2">{String(h.sla_minutes)} min</td>
                    <td className="px-4 py-2">{String(h.min_plan_code)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {catalog && (catalog.food_delivery as unknown[])?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {(catalog.food_delivery as Array<Record<string, unknown>>).map((p) => (
                <span key={String(p.code)} className="rounded-full bg-orange-500/20 px-2 py-0.5 text-xs text-orange-200">
                  {String(p.name)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'ecosystem' && catalog && (
        <div className="space-y-4">
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4">
            <h2 className="mb-2 text-sm font-medium text-indigo-200">Players prioritários (lockers mundial)</h2>
            <div className="flex flex-wrap gap-2">
              {(priorityPlayers as Array<Record<string, unknown>>).map((p) => (
                <span
                  key={String(p.code)}
                  className="rounded-full bg-indigo-600/30 px-2 py-0.5 text-xs text-indigo-100 ring-1 ring-indigo-500/40"
                  title={String(p.player_type)}
                >
                  {String(p.name)}
                </span>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              InPost · DHL · Magalu · Mercado Livre · Amazon · DPD · Correios · CTT · Worten · El Corte Inglés
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
            >
              <option value="">Todas regiões</option>
              <option value="BR">BR</option>
              <option value="PT">PT</option>
              <option value="ES">ES</option>
              <option value="EU">EU</option>
              <option value="UK">UK</option>
              <option value="DE">DE</option>
              <option value="US">US</option>
            </select>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {(
              [
                ['locker_operators', 'Operadores locker'],
                ['marketplaces', 'Marketplaces'],
                ['collection_points', 'Pontos de coleta'],
                ['carriers', 'Carriers'],
                ['aggregators', 'Agregadores'],
                ['food_delivery', 'Food delivery'],
              ] as const
            ).map(([key, label]) => {
              const list = (catalog[key] as Array<Record<string, unknown>>) || []
              const filtered = regionFilter
                ? list.filter((p) =>
                    (p.regions as string[] | undefined)?.some((r) => r.toUpperCase() === regionFilter.toUpperCase()),
                  )
                : list
              if (!filtered.length) return null
              return (
                <div key={key} className="rounded-xl border border-slate-700 bg-slate-900/50 p-3">
                  <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">{label}</h3>
                  <ul className="space-y-1 text-sm text-slate-300">
                    {filtered.slice(0, 12).map((p) => (
                      <li key={String(p.code)} className="flex justify-between gap-2">
                        <span>{String(p.name)}</span>
                        <span className="text-xs text-slate-500">{String(p.code)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
          {Array.isArray(catalog.interoperability_notes) && (
            <ul className="list-inside list-disc text-xs text-slate-400">
              {(catalog.interoperability_notes as string[]).map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          )}
          <details className="rounded-xl border border-slate-700 p-3 text-xs text-slate-400">
            <summary className="cursor-pointer text-slate-300">Mapa tier → players (JSON)</summary>
            <pre className="mt-2 max-h-64 overflow-auto">{JSON.stringify(catalog.tier_player_map, null, 2)}</pre>
          </details>
        </div>
      )}

      {tab === 'premium' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await orderPickupSubscriptionsApi.premiumSeed()
                  setMessage(`Premium seed: ${JSON.stringify(data.seeded)}`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha no seed premium')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded bg-violet-600 px-3 py-1.5 text-sm text-white hover:bg-violet-500"
            >
              Seed premium
            </button>
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await orderPickupSubscriptionsApi.computeAllHealth()
                  setMessage(`Health calculado: ${data.computed} assinaturas`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha ao calcular health')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-600"
            >
              Calcular health
            </button>
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await orderPickupSubscriptionsApi.runDueRenewals()
                  setMessage(`Renovações processadas: ${data.processed}`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha nas renovações')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded bg-emerald-700 px-3 py-1.5 text-sm text-white hover:bg-emerald-600"
            >
              Processar renovações vencidas
            </button>
          </div>

          <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-4">
            <h2 className="mb-2 text-sm font-medium text-violet-200">Matriz comparativa de planos</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="p-2">Plano</th>
                    <th className="p-2">Mensal</th>
                    <th className="p-2">Players</th>
                    <th className="p-2">Benefícios</th>
                  </tr>
                </thead>
                <tbody>
                  {(compareMatrix as Array<Record<string, unknown>>).map((row) => (
                    <tr key={String(row.code)} className="border-t border-slate-800">
                      <td className="p-2 font-medium">{String(row.name)}</td>
                      <td className="p-2">{formatBrl(Number(row.monthly_fee_cents))}</td>
                      <td className="p-2">{String(row.entitled_players ?? 0)}</td>
                      <td className="p-2 text-xs">
                        {JSON.stringify(row.benefits ?? {})}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-3">
              <h3 className="mb-2 text-xs font-semibold uppercase text-slate-500">Health por risco</h3>
              <ul className="space-y-1 text-sm">
                {(healthByRisk as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.churn_risk)} className="flex justify-between">
                    <span>{String(r.churn_risk)}</span>
                    <span className="text-slate-400">{String(r.cnt)} subs · score médio {Number(r.avg_score).toFixed(0)}</span>
                  </li>
                ))}
                {!healthByRisk.length && <li className="text-slate-500">Sem snapshots — use Calcular health</li>}
              </ul>
            </div>
            <div className="rounded-xl border border-amber-500/30 bg-amber-950/15 p-3">
              <h3 className="mb-2 text-xs font-semibold uppercase text-amber-400">Em risco ({atRisk.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-300">
                {(atRisk as Array<Record<string, unknown>>).slice(0, 8).map((r) => (
                  <li key={String(r.subscription_id)}>
                    {String(r.user_id)} · {String(r.churn_risk)} · score {String(r.health_score)}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Referrals ({referrals.length})</h3>
              <ul className="max-h-32 space-y-1 overflow-auto text-xs text-slate-400">
                {(referrals as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.id)}>
                    {String(r.referral_code)} · {String(r.status)} · {formatBrl(Number(r.reward_cents))}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Gift codes ({gifts.length})</h3>
              <ul className="max-h-32 space-y-1 overflow-auto text-xs text-slate-400">
                {(gifts as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.id)}>
                    {String(r.gift_code)} · {String(r.plan_code)} · {String(r.status)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Experimentos A/B ({experiments.length})</h3>
              <ul className="max-h-32 space-y-1 overflow-auto text-xs text-slate-400">
                {(experiments as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.id)}>
                    {String(r.experiment_code)} / {String(r.variant)} · {formatBrl(Number(r.monthly_fee_cents))}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Fila renovação ({renewalQueue.length})</h3>
              <ul className="max-h-32 space-y-1 overflow-auto text-xs text-slate-400">
                {(renewalQueue as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.id)}>
                    {String(r.user_id)} · {String(r.status)} · {String(r.scheduled_at)}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="rounded-xl border border-rose-500/30 bg-rose-950/15 p-3">
            <h3 className="mb-2 text-sm text-rose-200">Alertas de churn ({churnAlerts.length})</h3>
            <ul className="space-y-1 text-xs text-slate-300">
              {(churnAlerts as Array<Record<string, unknown>>).map((a) => (
                <li key={String(a.id)} className="flex justify-between gap-2">
                  <span>
                    [{String(a.severity)}] {String(a.alert_type)} — {String(a.message)}
                  </span>
                  <span className="text-slate-500">{String(a.user_id)}</span>
                </li>
              ))}
              {!churnAlerts.length && <li className="text-slate-500">Nenhum alerta aberto</li>}
            </ul>
          </div>
        </div>
      )}

      {tab === 'global' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await orderPickupSubscriptionsApi.worldSeed()
                  setMessage(`World seed: ${JSON.stringify(data.seeded)}`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha no seed global')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded bg-cyan-700 px-3 py-1.5 text-sm text-white hover:bg-cyan-600"
            >
              Seed global
            </button>
          </div>
          {worldSummary && (
            <div className="grid gap-2 sm:grid-cols-4">
              {Object.entries(worldSummary).map(([k, v]) => (
                <div key={k} className="rounded-lg border border-slate-700 bg-slate-900/60 p-2 text-center">
                  <div className="text-lg font-semibold text-cyan-300">{v}</div>
                  <div className="text-xs text-slate-500">{k}</div>
                </div>
              ))}
            </div>
          )}
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Preços regionais ({regionalPrices.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(regionalPrices as Array<Record<string, unknown>>).slice(0, 12).map((r) => (
                  <li key={`${r.plan_code}-${r.region_code}`}>
                    {String(r.plan_code)} · {String(r.region_code)} · {formatBrl(Number(r.monthly_fee_cents))}{' '}
                    {String(r.currency)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Add-ons ({addonCatalog.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(addonCatalog as Array<Record<string, unknown>>).map((a) => (
                  <li key={String(a.code)}>
                    {String(a.name)} · {formatBrl(Number(a.monthly_fee_cents))}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">SLA por plano ({slaTargets.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(slaTargets as Array<Record<string, unknown>>).map((s, i) => (
                  <li key={`${s.plan_code}-${s.metric_code}-${i}`}>
                    {String(s.plan_code)} · {String(s.metric_code)} = {String(s.target_value)} {String(s.unit)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Settlements parceiros ({settlements.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(settlements as Array<Record<string, unknown>>).map((s) => (
                  <li key={String(s.id)}>
                    {String(s.partner_code)} · {String(s.period_month)} · {formatBrl(Number(s.net_cents))} ({String(s.status)})
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/15 p-3">
            <h3 className="mb-2 text-sm text-emerald-200">Ofertas de retenção ({retentionOffers.length})</h3>
            <ul className="space-y-1 text-xs text-slate-300">
              {(retentionOffers as Array<Record<string, unknown>>).map((o) => (
                <li key={String(o.id)}>
                  {String(o.offer_code)} · {String(o.discount_pct)}% · user {String(o.user_id)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {tab === 'efficiency' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                setLoading(true)
                try {
                  const { data } = await orderPickupSubscriptionsApi.efficiencySeed()
                  setMessage(`Efficiency seed: ${JSON.stringify(data.seeded)}`)
                  await load()
                } catch (err: unknown) {
                  setError(err instanceof Error ? err.message : 'Falha no seed eficiência')
                } finally {
                  setLoading(false)
                }
              }}
              className="rounded bg-violet-700 px-3 py-1.5 text-sm text-white hover:bg-violet-600"
            >
              Seed eficiência
            </button>
          </div>
          {efficiencySummary && (
            <div className="grid gap-2 sm:grid-cols-5">
              {Object.entries(efficiencySummary).map(([k, v]) => (
                <div key={k} className="rounded-lg border border-slate-700 bg-slate-900/60 p-2 text-center">
                  <div className="text-lg font-semibold text-violet-300">{v}</div>
                  <div className="text-xs text-slate-500">{k}</div>
                </div>
              ))}
            </div>
          )}
          <div className="rounded-xl border border-amber-500/30 bg-amber-950/15 p-3">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm text-amber-200">OPS Inbox ({opsInbox.length})</h3>
              <div className="flex flex-wrap gap-1">
                {inboxBulkOps.map((op) => (
                  <button
                    key={op.operation}
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      void onInboxBulk(
                        op.operation as 'renewals_run_due' | 'churn_resolve_high' | 'churn_resolve_all',
                      )
                    }
                    className="rounded border border-amber-600/50 bg-amber-950/40 px-2 py-0.5 text-[10px] text-amber-100 hover:bg-amber-900/50"
                  >
                    {op.label}
                  </button>
                ))}
              </div>
            </div>
            <ul className="max-h-56 space-y-2 overflow-auto text-xs text-slate-300">
              {(opsInbox as Array<Record<string, unknown>>).map((item, i) => {
                const actions = (item.actions as Array<{ action: string; label: string }> | undefined) ?? []
                return (
                  <li
                    key={`${String(item.kind)}-${String(item.id ?? i)}`}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-700/80 bg-slate-950/50 px-2 py-1.5"
                  >
                    <span>
                      [{String(item.kind)}] {String(item.title ?? '—')}
                      {item.user_id ? (
                        <span className="ml-1 text-slate-500">· {String(item.user_id)}</span>
                      ) : null}
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {actions.map((a) => (
                        <button
                          key={a.action}
                          type="button"
                          disabled={loading}
                          onClick={() => void onInboxAction(item, a.action)}
                          className={
                            a.action === 'decline'
                              ? 'rounded bg-slate-700/80 px-2 py-0.5 text-[11px] text-slate-200 hover:bg-slate-600'
                              : 'rounded bg-emerald-800/80 px-2 py-0.5 text-[11px] text-emerald-100 hover:bg-emerald-700'
                          }
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setShowPromoForm((v) => !v)}
              className="rounded border border-violet-600 px-3 py-1.5 text-sm text-violet-200"
            >
              {showPromoForm ? 'Fechar cupom' : 'Novo cupom'}
            </button>
            <button
              type="button"
              onClick={() => setShowRuleForm((v) => !v)}
              className="rounded border border-violet-600 px-3 py-1.5 text-sm text-violet-200"
            >
              {showRuleForm ? 'Fechar regra' : 'Nova automação'}
            </button>
            <Link to="/assinatura" className="rounded border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:text-white">
              Fluxo B2C assinar
            </Link>
          </div>
          {showPromoForm ? (
            <form onSubmit={onCreatePromo} className="grid gap-2 rounded-xl border border-violet-500/30 bg-violet-950/10 p-3 sm:grid-cols-2">
              <input
                required
                placeholder="Código (ex. SUMMER25)"
                value={promoForm.code}
                onChange={(e) => setPromoForm((f) => ({ ...f, code: e.target.value.toUpperCase() }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <input
                placeholder="Descrição"
                value={promoForm.description}
                onChange={(e) => setPromoForm((f) => ({ ...f, description: e.target.value }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <input
                type="number"
                min={0}
                max={100}
                placeholder="% desconto"
                value={promoForm.discount_pct}
                onChange={(e) => setPromoForm((f) => ({ ...f, discount_pct: Number(e.target.value) }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <input
                placeholder="Planos (BASIC,PREMIUM)"
                value={promoForm.eligible_plans}
                onChange={(e) => setPromoForm((f) => ({ ...f, eligible_plans: e.target.value }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <button type="submit" className="rounded bg-violet-700 px-3 py-1 text-sm text-white sm:col-span-2">
                Criar cupom
              </button>
            </form>
          ) : null}
          {showRuleForm ? (
            <form onSubmit={onCreateRule} className="grid gap-2 rounded-xl border border-violet-500/30 bg-violet-950/10 p-3 sm:grid-cols-2">
              <input
                required
                placeholder="rule_code"
                value={ruleForm.rule_code}
                onChange={(e) => setRuleForm((f) => ({ ...f, rule_code: e.target.value.toUpperCase() }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <input
                required
                placeholder="Nome"
                value={ruleForm.name}
                onChange={(e) => setRuleForm((f) => ({ ...f, name: e.target.value }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <input
                placeholder="trigger_event"
                value={ruleForm.trigger_event}
                onChange={(e) => setRuleForm((f) => ({ ...f, trigger_event: e.target.value }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              />
              <select
                value={ruleForm.action_type}
                onChange={(e) => setRuleForm((f) => ({ ...f, action_type: e.target.value }))}
                className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-white"
              >
                <option value="ISSUE_RETENTION_OFFER">ISSUE_RETENTION_OFFER</option>
                <option value="WEBHOOK_NOTIFY">WEBHOOK_NOTIFY</option>
                <option value="SEND_EVENT">SEND_EVENT</option>
              </select>
              <button type="submit" className="rounded bg-violet-700 px-3 py-1 text-sm text-white sm:col-span-2">
                Criar regra
              </button>
            </form>
          ) : null}
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Cupons ({promoCodes.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(promoCodes as Array<Record<string, unknown>>).map((p) => (
                  <li key={String(p.code)}>
                    {String(p.code)} · {String(p.discount_pct)}% · {String(p.description)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Upgrade matrix ({upgradeSuggestions.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(upgradeSuggestions as Array<Record<string, unknown>>).map((u, i) => (
                  <li key={String(u.subscription_id ?? i)}>
                    {String(u.current_plan)} → {String(u.suggested_plan)} · uso {String(u.usage_pct)}%
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Automações ({automationRules.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(automationRules as Array<Record<string, unknown>>).map((r) => (
                  <li key={String(r.rule_code)}>
                    {String(r.name)} · {String(r.trigger_event)} → {String(r.action_type)}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-slate-700 p-3">
              <h3 className="mb-2 text-sm text-slate-300">Medidores de uso ({usageMeters.length})</h3>
              <ul className="max-h-40 space-y-1 overflow-auto text-xs text-slate-400">
                {(usageMeters as Array<Record<string, unknown>>).map((m, i) => (
                  <li key={String(m.id ?? i)}>
                    {String(m.meter_code)} · {String(m.period_month)} · qty {String(m.quantity)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
