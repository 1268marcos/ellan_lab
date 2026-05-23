import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { rentalsOpsApi, type RentalContract, type RentalPlan } from '../../api/rentalsOps'

type Tab =
  | 'overview'
  | 'networks'
  | 'corridors'
  | 'operators'
  | 'plans'
  | 'contracts'
  | 'billing'
  | 'sla'
  | 'events'
  | 'integrations'
  | 'onboarding'
  | 'capacity'
  | 'settlements'
  | 'premium'
  | 'advanced'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Visão geral' },
  { id: 'networks', label: 'Redes' },
  { id: 'corridors', label: 'Corredores' },
  { id: 'operators', label: 'Operadores' },
  { id: 'plans', label: 'Planos' },
  { id: 'contracts', label: 'Contratos' },
  { id: 'billing', label: 'Faturamento' },
  { id: 'sla', label: 'SLA' },
  { id: 'events', label: 'Eventos' },
  { id: 'integrations', label: 'Integrações' },
  { id: 'onboarding', label: 'Onboarding' },
  { id: 'capacity', label: 'Capacidade' },
  { id: 'settlements', label: 'Liquidações' },
  { id: 'premium', label: 'SLA & disputas' },
  { id: 'advanced', label: 'Avançado' },
]

function formatBrl(cents: number) {
  return `R$ ${(cents / 100).toFixed(2)}`
}

export default function OpsRentalAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = (searchParams.get('tab') as Tab) || 'overview'
  const [tab, setTab] = useState<Tab>(TABS.some((t) => t.id === tabParam) ? tabParam : 'overview')
  const [plans, setPlans] = useState<RentalPlan[]>([])
  const [contracts, setContracts] = useState<RentalContract[]>([])
  const [summary, setSummary] = useState<Record<string, number> | null>(null)
  const [networks, setNetworks] = useState<unknown[]>([])
  const [corridors, setCorridors] = useState<unknown[]>([])
  const [operators, setOperators] = useState<unknown[]>([])
  const [invoices, setInvoices] = useState<unknown[]>([])
  const [slaPolicies, setSlaPolicies] = useState<unknown[]>([])
  const [webhooks, setWebhooks] = useState<unknown[]>([])
  const [apiKeys, setApiKeys] = useState<unknown[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastApiKey, setLastApiKey] = useState('')
  const [ecosystemCatalog, setEcosystemCatalog] = useState<{
    networks_total: number
    priority_codes: string[]
  } | null>(null)
  const [planForm, setPlanForm] = useState({
    name: '',
    locker_id: '',
    slot_size: 'M',
    billing_cycle: 'MONTHLY',
    amount_cents: 9900,
  })
  const [webhookTenant, setWebhookTenant] = useState('tenant-inpost-br')
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.example.com/rentals')
  const [premiumSummary, setPremiumSummary] = useState<Record<string, number> | null>(null)
  const [onboarding, setOnboarding] = useState<unknown[]>([])
  const [capacity, setCapacity] = useState<unknown[]>([])
  const [settlements, setSettlements] = useState<unknown[]>([])
  const [slaBreaches, setSlaBreaches] = useState<unknown[]>([])
  const [disputes, setDisputes] = useState<unknown[]>([])
  const [renewalOffers, setRenewalOffers] = useState<unknown[]>([])
  const [accessPasses, setAccessPasses] = useState<unknown[]>([])
  const [deposits, setDeposits] = useState<unknown[]>([])
  const [pricingRules, setPricingRules] = useState<unknown[]>([])
  const [dunningCases, setDunningCases] = useState<unknown[]>([])
  const [transfers, setTransfers] = useState<unknown[]>([])
  const [contentInsurance, setContentInsurance] = useState<unknown[]>([])
  const [pricingPreview, setPricingPreview] = useState<{
    pricing: Record<string, unknown>
    insurance?: Record<string, unknown>
    total_monthly_cents: number
  } | null>(null)
  const [contractForm, setContractForm] = useState({
    locker_id: '',
    slot_label: '',
    slot_size: 'M',
    renter_name: '',
    use_dynamic_pricing: true,
    content_insurance: false,
    declared_value_cents: 0,
  })

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
      const [s, p, c, n, cor, op, inv, sla, w, k, eco, ps, ob, cap, stl, br, disp, ren, ap, dep, pr, dun, tr, ins] =
        await Promise.all([
        rentalsOpsApi.analyticsSummary(),
        rentalsOpsApi.listPlans({ active_only: false }),
        rentalsOpsApi.listContracts({}),
        rentalsOpsApi.listNetworks({ active_only: false }),
        rentalsOpsApi.listCorridors(),
        rentalsOpsApi.listOperators(),
        rentalsOpsApi.listInvoices(),
        rentalsOpsApi.listSlaPolicies(),
        rentalsOpsApi.listWebhooks(),
        rentalsOpsApi.listApiKeys(),
        rentalsOpsApi.ecosystemCatalog(),
        rentalsOpsApi.premiumSummary(),
        rentalsOpsApi.listOnboarding(),
        rentalsOpsApi.listCapacity(),
        rentalsOpsApi.listSettlements(),
        rentalsOpsApi.listSlaBreaches(),
        rentalsOpsApi.listDisputes(),
        rentalsOpsApi.listRenewalOffers(),
        rentalsOpsApi.listAccessPasses(),
        rentalsOpsApi.listDeposits(),
        rentalsOpsApi.listPricingRules(),
        rentalsOpsApi.listDunning(),
        rentalsOpsApi.listTransfers(),
        rentalsOpsApi.listContentInsurance(),
      ])
      setSummary(s.data.summary ?? null)
      setPlans(p.data.items ?? [])
      setContracts(c.data.items ?? [])
      setNetworks(n.data.items ?? [])
      setCorridors(cor.data.items ?? [])
      setOperators(op.data.items ?? [])
      setInvoices(inv.data.items ?? [])
      setSlaPolicies(sla.data.items ?? [])
      setWebhooks(w.data.items ?? [])
      setApiKeys(k.data.items ?? [])
      if (eco.data.catalog) setEcosystemCatalog(eco.data.catalog)
      setPremiumSummary(ps.data.summary ?? null)
      setOnboarding(ob.data.items ?? [])
      setCapacity(cap.data.items ?? [])
      setSettlements(stl.data.items ?? [])
      setSlaBreaches(br.data.items ?? [])
      setDisputes(disp.data.items ?? [])
      setRenewalOffers(ren.data.items ?? [])
      setAccessPasses(ap.data.items ?? [])
      setDeposits(dep.data.items ?? [])
      setPricingRules(pr.data.items ?? [])
      setDunningCases(dun.data.items ?? [])
      setTransfers(tr.data.items ?? [])
      setContentInsurance(ins.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    setLoading(true)
    try {
      const { data } = await rentalsOpsApi.seed()
      setMessage(`Seed: ${JSON.stringify(data.seeded)}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreatePlan = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await rentalsOpsApi.createPlan({
        ...planForm,
        locker_id: planForm.locker_id || null,
        amount_cents: Number(planForm.amount_cents),
      })
      setMessage('Plano criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar plano')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    setLoading(true)
    try {
      const { data } = await rentalsOpsApi.upsertWebhook(webhookTenant, {
        tenant_id: webhookTenant,
        url: webhookUrl,
        events: ['rental.contract.created', 'rental.billing.due'],
      })
      setMessage(`Webhook salvo. Secret: ${(data as { webhook_secret?: string }).webhook_secret ?? 'ok'}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onPreviewContractPricing = async () => {
    setLoading(true)
    try {
      const { data } = await rentalsOpsApi.previewContractPricing({
        locker_id: contractForm.locker_id,
        slot_label: contractForm.slot_label,
        slot_size: contractForm.slot_size,
        billing_cycle: 'MONTHLY',
        use_dynamic_pricing: contractForm.use_dynamic_pricing,
        content_insurance: contractForm.content_insurance,
        declared_value_cents: contractForm.content_insurance ? contractForm.declared_value_cents : undefined,
      })
      setPricingPreview(data)
      setMessage('Cotação atualizada.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na cotação')
    } finally {
      setLoading(false)
    }
  }

  const onCreateContract = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await rentalsOpsApi.createContract({
        locker_id: contractForm.locker_id,
        slot_label: contractForm.slot_label,
        slot_size: contractForm.slot_size,
        billing_cycle: 'MONTHLY',
        renter_name: contractForm.renter_name || undefined,
        use_dynamic_pricing: contractForm.use_dynamic_pricing,
        content_insurance: contractForm.content_insurance,
        declared_value_cents: contractForm.content_insurance ? contractForm.declared_value_cents : undefined,
        status: 'PENDING',
      })
      setMessage('Contrato criado.')
      setPricingPreview(null)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar contrato')
    } finally {
      setLoading(false)
    }
  }

  const onApplyLateFees = async () => {
    setLoading(true)
    try {
      const { data } = await rentalsOpsApi.applyLateFees()
      setMessage(`Multas: ${data.applied} aplicada(s), ${data.skipped} ignorada(s).`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao aplicar multas')
    } finally {
      setLoading(false)
    }
  }

  const onRotate = async () => {
    setLoading(true)
    try {
      const { data } = await rentalsOpsApi.rotateApiKey(webhookTenant)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…)`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar')
    } finally {
      setLoading(false)
    }
  }

  const activeCount = summary?.active_contracts ?? contracts.filter((c) => c.status === 'ACTIVE').length

  const renderTable = (rows: unknown[], cols: string[], pick: (r: Record<string, unknown>, c: string) => string) => (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b text-slate-500">
          {cols.map((c) => (
            <th key={c} className="p-2">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b">
            {cols.map((c) => (
              <td key={c} className="p-2">
                {pick(row as Record<string, unknown>, c)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )

  return (
    <div className="space-y-4 p-4" data-testid="ops-rental-admin-page">
      <header>
        <h1 className="text-xl font-semibold">Rental OPS</h1>
        <p className="text-sm text-slate-500">
          Redes, carriers, marketplaces, agregadores e food delivery (50+ players) — ver catálogo / relações
        </p>
        {ecosystemCatalog ? (
          <p className="text-xs text-slate-400">
            Referência: {ecosystemCatalog.networks_total} redes · prioridade:{' '}
            {ecosystemCatalog.priority_codes.join(', ')}
          </p>
        ) : null}
      </header>

      {error ? <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="rounded bg-green-50 p-2 text-sm text-green-800">{message}</p> : null}
      {lastApiKey ? (
        <p className="rounded bg-amber-50 p-2 font-mono text-xs text-amber-900">API key: {lastApiKey}</p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`rounded px-3 py-1 text-sm ${tab === t.id ? 'bg-blue-600 text-white' : 'bg-slate-200'}`}
            onClick={() => setTabUrl(t.id)}
          >
            {t.label}
          </button>
        ))}
        <button type="button" className="rounded bg-slate-200 px-3 py-1 text-sm" onClick={() => void load()} disabled={loading}>
          Atualizar
        </button>
        <button type="button" className="rounded bg-blue-700 px-3 py-1 text-sm text-white" onClick={() => void onSeed()} disabled={loading}>
          Seed demo
        </button>
      </div>

      {tab === 'overview' ? (
        <div className="grid gap-3 sm:grid-cols-4">
          {[
            ['Redes', summary?.active_networks ?? networks.length],
            ['Operadores', summary?.active_operators ?? operators.length],
            ['Contratos ativos', activeCount],
            ['MRR', formatBrl(Number(summary?.mrr_cents ?? 0))],
            ['Onboarding LIVE', premiumSummary?.onboarding_live ?? '—'],
            ['SLA breaches', premiumSummary?.open_sla_breaches ?? '—'],
            ['Disputas', premiumSummary?.open_disputes ?? '—'],
          ].map(([label, val]) => (
            <div key={label} className="rounded border p-3">
              <div className="text-xs text-slate-500">{label}</div>
              <div className="text-2xl font-semibold">{val}</div>
            </div>
          ))}
        </div>
      ) : null}

      {tab === 'networks'
        ? renderTable(networks, ['code', 'name', 'network_type'], (r, c) => String(r[c] ?? '—'))
        : null}
      {tab === 'corridors'
        ? renderTable(
            corridors,
            ['network_code', 'origin_country', 'destination_country'],
            (r, c) => String(r[c] ?? '—'),
          )
        : null}
      {tab === 'operators'
        ? renderTable(operators, ['operator_code', 'legal_name', 'status'], (r, c) => String(r[c] ?? '—'))
        : null}
      {tab === 'billing' ? (
        <section className="space-y-3">
          <button
            type="button"
            className="rounded bg-amber-600 px-3 py-1 text-sm text-white"
            onClick={() => void onApplyLateFees()}
            disabled={loading}
          >
            Aplicar multas automáticas
          </button>
          {renderTable(invoices, ['invoice_number', 'status', 'amount_cents'], (r, c) =>
            c === 'amount_cents' ? formatBrl(Number(r.amount_cents)) : String(r[c] ?? '—'),
          )}
        </section>
      ) : null}
      {tab === 'sla'
        ? renderTable(slaPolicies, ['network_code', 'metric_code', 'target_value'], (r, c) => String(r[c] ?? '—'))
        : null}

      {tab === 'plans' ? (
        <section className="space-y-3">
          <form className="flex flex-wrap gap-2" onSubmit={onCreatePlan}>
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome"
              value={planForm.name}
              onChange={(e) => setPlanForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="locker_id"
              value={planForm.locker_id}
              onChange={(e) => setPlanForm((f) => ({ ...f, locker_id: e.target.value }))}
            />
            <input
              type="number"
              className="w-28 rounded border px-2 py-1 text-sm"
              value={planForm.amount_cents}
              onChange={(e) => setPlanForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
            />
            <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-sm text-white" disabled={loading}>
              Criar plano
            </button>
          </form>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">Nome</th>
                <th className="p-2">Locker</th>
                <th className="p-2">Ciclo</th>
                <th className="p-2">Valor</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.id} className="border-b">
                  <td className="p-2">{p.name}</td>
                  <td className="p-2">{p.locker_id ?? '—'}</td>
                  <td className="p-2">{p.billing_cycle}</td>
                  <td className="p-2">{formatBrl(p.amount_cents)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      {tab === 'contracts' ? (
        <section className="space-y-3">
          <form className="flex flex-wrap items-end gap-2" onSubmit={onCreateContract}>
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="locker_id"
              value={contractForm.locker_id}
              onChange={(e) => setContractForm((f) => ({ ...f, locker_id: e.target.value }))}
              required
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="slot_label"
              value={contractForm.slot_label}
              onChange={(e) => setContractForm((f) => ({ ...f, slot_label: e.target.value }))}
              required
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Locatário"
              value={contractForm.renter_name}
              onChange={(e) => setContractForm((f) => ({ ...f, renter_name: e.target.value }))}
            />
            <label className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={contractForm.use_dynamic_pricing}
                onChange={(e) => setContractForm((f) => ({ ...f, use_dynamic_pricing: e.target.checked }))}
              />
              Cotação dinâmica
            </label>
            <label className="flex items-center gap-1 text-sm">
              <input
                type="checkbox"
                checked={contractForm.content_insurance}
                onChange={(e) => setContractForm((f) => ({ ...f, content_insurance: e.target.checked }))}
              />
              Seguro conteúdo
            </label>
            {contractForm.content_insurance ? (
              <input
                type="number"
                className="w-36 rounded border px-2 py-1 text-sm"
                placeholder="Valor declarado (centavos)"
                value={contractForm.declared_value_cents}
                onChange={(e) =>
                  setContractForm((f) => ({ ...f, declared_value_cents: Number(e.target.value) }))
                }
              />
            ) : null}
            <button
              type="button"
              className="rounded bg-slate-600 px-3 py-1 text-sm text-white"
              onClick={() => void onPreviewContractPricing()}
              disabled={loading}
            >
              Preview cotação
            </button>
            <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-sm text-white" disabled={loading}>
              Criar contrato
            </button>
          </form>
          {pricingPreview ? (
            <p className="text-sm text-slate-600">
              Aluguel: {formatBrl(Number(pricingPreview.pricing.amount_cents))}
              {pricingPreview.insurance
                ? ` · Seguro: ${formatBrl(Number(pricingPreview.insurance.premium_cents))}`
                : ''}
              {' · Total: '}
              {formatBrl(pricingPreview.total_monthly_cents)}
            </p>
          ) : null}
          <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate-500">
              <th className="p-2">ID</th>
              <th className="p-2">Locker</th>
              <th className="p-2">Locatário</th>
              <th className="p-2">Status</th>
              <th className="p-2">Valor</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map((c) => (
              <tr key={c.id} className="border-b">
                <td className="p-2 font-mono text-xs">{c.id}</td>
                <td className="p-2">{c.locker_id}</td>
                <td className="p-2">{c.renter_name ?? '—'}</td>
                <td className="p-2">{c.status}</td>
                <td className="p-2">{formatBrl(c.amount_cents)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </section>
      ) : null}

      {tab === 'onboarding'
        ? renderTable(onboarding, ['network_code', 'status', 'kyb_tier', 'compliance_score'], (r, c) =>
            String(r[c] ?? '—'),
          )
        : null}
      {tab === 'capacity'
        ? renderTable(
            capacity,
            ['network_code', 'snapshot_date', 'utilization_pct', 'occupied_slots'],
            (r, c) => String(r[c] ?? '—'),
          )
        : null}
      {tab === 'settlements'
        ? renderTable(
            settlements,
            ['batch_code', 'operator_name', 'net_cents', 'status'],
            (r, c) => (c === 'net_cents' ? formatBrl(Number(r.net_cents)) : String(r[c] ?? '—')),
          )
        : null}
      {tab === 'premium' ? (
        <section className="space-y-6">
          <div>
            <h2 className="mb-2 text-sm font-medium text-slate-600">Incidentes SLA</h2>
            {renderTable(slaBreaches, ['network_code', 'metric_code', 'status', 'penalty_cents'], (r, c) =>
              c === 'penalty_cents' ? formatBrl(Number(r.penalty_cents)) : String(r[c] ?? '—'),
            )}
          </div>
          <div>
            <h2 className="mb-2 text-sm font-medium text-slate-600">Disputas</h2>
            {renderTable(disputes, ['contract_id', 'dispute_type', 'status', 'amount_cents'], (r, c) =>
              c === 'amount_cents' ? formatBrl(Number(r.amount_cents)) : String(r[c] ?? '—'),
            )}
          </div>
          <div>
            <h2 className="mb-2 text-sm font-medium text-slate-600">Renovações</h2>
            {renderTable(renewalOffers, ['renter_name', 'offer_amount_cents', 'valid_until', 'status'], (r, c) =>
              c === 'offer_amount_cents' ? formatBrl(Number(r.offer_amount_cents)) : String(r[c] ?? '—'),
            )}
          </div>
        </section>
      ) : null}

      {tab === 'advanced' ? (
        <section className="space-y-6">
          {renderTable(
            contentInsurance,
            ['policy_number', 'renter_name', 'premium_cents', 'status'],
            (r, c) => (c === 'premium_cents' ? formatBrl(Number(r.premium_cents)) : String(r[c] ?? '—')),
          )}
          {renderTable(accessPasses, ['contract_id', 'pass_type', 'pass_hint', 'status'], (r, c) =>
            String(r[c] ?? '—'),
          )}
          {renderTable(deposits, ['renter_name', 'amount_cents', 'status'], (r, c) =>
            c === 'amount_cents' ? formatBrl(Number(r.amount_cents)) : String(r[c] ?? '—'),
          )}
          {renderTable(pricingRules, ['code', 'name', 'base_amount_cents'], (r, c) =>
            c === 'base_amount_cents' ? formatBrl(Number(r.base_amount_cents)) : String(r[c] ?? '—'),
          )}
          {renderTable(dunningCases, ['stage', 'status', 'amount_due_cents'], (r, c) =>
            c === 'amount_due_cents' ? formatBrl(Number(r.amount_due_cents)) : String(r[c] ?? '—'),
          )}
          {renderTable(transfers, ['status', 'from_slot_label', 'to_slot_label'], (r, c) =>
            String(r[c] ?? '—'),
          )}
        </section>
      ) : null}

      {tab === 'integrations' ? (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <input
              className="rounded border px-2 py-1 text-sm"
              value={webhookTenant}
              onChange={(e) => setWebhookTenant(e.target.value)}
              placeholder="tenant_id"
            />
            <input
              className="min-w-[240px] flex-1 rounded border px-2 py-1 text-sm"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <button type="button" className="rounded bg-blue-600 px-3 py-1 text-sm text-white" onClick={() => void onWebhook()}>
              Salvar webhook
            </button>
            <button type="button" className="rounded bg-slate-700 px-3 py-1 text-sm text-white" onClick={() => void onRotate()}>
              Rotacionar API key
            </button>
          </div>
          <p className="text-xs text-slate-500">
            Referência:{' '}
            <Link className="text-blue-600 underline" to="/ops/lockers">
              lockers
            </Link>
          </p>
        </section>
      ) : null}
    </div>
  )
}
