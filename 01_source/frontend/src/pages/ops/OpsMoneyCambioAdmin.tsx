import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { moneyCambioAdminApi } from '../../api/moneyCambioAdmin'
import { useOpsTabFromUrl } from '../../hooks/useOpsTabFromUrl'

const MONEY_PATH = '/ops/money-cambio/admin'

const TAB_KEYS = [
  'overview',
  'countries',
  'currencies',
  'methods',
  'matrix',
  'aliases',
  'interfaces',
  'wallets',
  'corridors',
  'fx',
  'compliance',
  'audit',
  'players',
  'segments',
  'relations',
  'intelligence',
  'settlements',
  'pricing',
  'rails',
  'treasury',
  'fxlocks',
  'partners',
] as const

type Tab = (typeof TAB_KEYS)[number]

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Visão global',
  countries: 'Países',
  currencies: 'Moedas',
  methods: 'Métodos',
  matrix: 'Matriz',
  aliases: 'Aliases',
  interfaces: 'Interfaces',
  wallets: 'Wallets',
  corridors: 'Corredores',
  fx: 'FX',
  compliance: 'Compliance',
  audit: 'Auditoria',
  players: 'Players',
  segments: 'Segmentos',
  relations: 'Relações',
  intelligence: 'Intelligence',
  settlements: 'Settlement',
  pricing: 'Simulador',
  rails: 'Rails',
  treasury: 'Tesouraria',
  fxlocks: 'Travas FX',
  partners: 'Integração',
}

type Row = { id: string; detail: string }

export default function OpsMoneyCambioAdmin() {
  const { tab, setTab } = useOpsTabFromUrl(MONEY_PATH, TAB_KEYS, 'overview')

  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null)
  const [operatingCountries, setOperatingCountries] = useState<unknown[]>([])
  const [currencies, setCurrencies] = useState<unknown[]>([])
  const [methods, setMethods] = useState<unknown[]>([])
  const [methodMatrix, setMethodMatrix] = useState<unknown[]>([])
  const [aliases, setAliases] = useState<unknown[]>([])
  const [interfaces, setInterfaces] = useState<unknown[]>([])
  const [wallets, setWallets] = useState<unknown[]>([])
  const [corridors, setCorridors] = useState<unknown[]>([])
  const [fxRates, setFxRates] = useState<unknown[]>([])
  const [compliance, setCompliance] = useState<unknown[]>([])
  const [fxAudit, setFxAudit] = useState<unknown[]>([])
  const [lockerPlayers, setLockerPlayers] = useState<unknown[]>([])
  const [ecosystemSegments, setEcosystemSegments] = useState<unknown[]>([])
  const [playerRelations, setPlayerRelations] = useState<unknown[]>([])
  const [readiness, setReadiness] = useState<unknown[]>([])
  const [insights, setInsights] = useState<unknown[]>([])
  const [settlementSchedules, setSettlementSchedules] = useState<unknown[]>([])
  const [paymentRails, setPaymentRails] = useState<unknown[]>([])
  const [treasury, setTreasury] = useState<Record<string, unknown> | null>(null)
  const [fxLocks, setFxLocks] = useState<unknown[]>([])
  const [partners, setPartners] = useState<unknown[]>([])
  const [playerSegmentFilter, setPlayerSegmentFilter] = useState('')
  const [pricingForm, setPricingForm] = useState({
    amount_cents: '100000',
    player_code: 'MAGALU',
    country_code: 'BR',
    payment_method_code: 'PIX',
  })
  const [pricingResult, setPricingResult] = useState<Record<string, unknown> | null>(null)
  const [currencyForm, setCurrencyForm] = useState({ code: '', name: '', symbol: '' })
  const [methodForm, setMethodForm] = useState({ code: '', name: '' })
  const [fxForm, setFxForm] = useState({ base_currency: 'USD', quote_currency: 'BRL', rate: '5.05' })
  const [partnerForm, setPartnerForm] = useState({ name: '', code: '', partner_type: 'FX_FEED' })
  const [selectedPartner, setSelectedPartner] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const results = await Promise.allSettled([
        moneyCambioAdminApi.globalDashboard(),
        moneyCambioAdminApi.listOperatingCountries(),
        moneyCambioAdminApi.listCurrencies(),
        moneyCambioAdminApi.listMethods(),
        moneyCambioAdminApi.listMethodMatrix(),
        moneyCambioAdminApi.listAliases(),
        moneyCambioAdminApi.listInterfaces(),
        moneyCambioAdminApi.listWallets(),
        moneyCambioAdminApi.listCorridors(),
        moneyCambioAdminApi.listFxRates(),
        moneyCambioAdminApi.listCompliance(),
        moneyCambioAdminApi.listFxAudit(),
        moneyCambioAdminApi.listLockerPlayers(),
        moneyCambioAdminApi.listEcosystemSegments(),
        moneyCambioAdminApi.listPlayerRelations(),
        moneyCambioAdminApi.intelligenceDashboard(),
        moneyCambioAdminApi.listReadiness(),
        moneyCambioAdminApi.listInsights(),
        moneyCambioAdminApi.listSettlementSchedules(),
        moneyCambioAdminApi.listPaymentRails(),
        moneyCambioAdminApi.treasuryDashboard(),
        moneyCambioAdminApi.listFxLocks(),
        moneyCambioAdminApi.listPartners(),
      ])
      const pick = <T,>(i: number): T | null =>
        results[i].status === 'fulfilled' ? (results[i] as PromiseFulfilledResult<{ data: T }>).value.data : null

      const dash = pick<Record<string, unknown>>(0)
      if (!dash && results[0].status === 'rejected') {
        throw results[0].reason
      }
      setDashboard(dash)
      setOperatingCountries((pick<{ items: unknown[] }>(1)?.items as unknown[]) ?? [])
      setCurrencies((pick<{ items: unknown[] }>(2)?.items as unknown[]) ?? [])
      setMethods((pick<{ items: unknown[] }>(3)?.items as unknown[]) ?? [])
      setMethodMatrix((pick<{ items: unknown[] }>(4)?.items as unknown[]) ?? [])
      setAliases((pick<{ items: unknown[] }>(5)?.items as unknown[]) ?? [])
      setInterfaces((pick<{ items: unknown[] }>(6)?.items as unknown[]) ?? [])
      setWallets((pick<{ items: unknown[] }>(7)?.items as unknown[]) ?? [])
      setCorridors((pick<{ items: unknown[] }>(8)?.items as unknown[]) ?? [])
      setFxRates((pick<{ items: unknown[] }>(9)?.items as unknown[]) ?? [])
      setCompliance((pick<{ items: unknown[] }>(10)?.items as unknown[]) ?? [])
      setFxAudit((pick<{ items: unknown[] }>(11)?.items as unknown[]) ?? [])
      setLockerPlayers((pick<{ items: unknown[] }>(12)?.items as unknown[]) ?? [])
      setEcosystemSegments((pick<{ items: unknown[] }>(13)?.items as unknown[]) ?? [])
      setPlayerRelations((pick<{ items: unknown[] }>(14)?.items as unknown[]) ?? [])
      setReadiness((pick<{ items: unknown[] }>(16)?.items as unknown[]) ?? [])
      setInsights((pick<{ items: unknown[] }>(17)?.items as unknown[]) ?? [])
      setSettlementSchedules((pick<{ items: unknown[] }>(18)?.items as unknown[]) ?? [])
      setPaymentRails((pick<{ items: unknown[] }>(19)?.items as unknown[]) ?? [])
      const treas = pick<Record<string, unknown>>(20)
      setTreasury(treas?.players_active != null ? treas : null)
      setFxLocks((pick<{ items: unknown[] }>(21)?.items as unknown[]) ?? [])
      setPartners((pick<{ partners: unknown[] }>(22)?.partners as unknown[]) ?? [])
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'message' in err
          ? String((err as { message?: string }).message)
          : 'Falha ao carregar Money & Câmbio (porta 8125).'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const filteredPlayers = useMemo(() => {
    if (!playerSegmentFilter) return lockerPlayers
    return lockerPlayers.filter((x) => (x as { segment?: string }).segment === playerSegmentFilter)
  }, [lockerPlayers, playerSegmentFilter])

  const overviewCards = useMemo(() => {
    if (!dashboard) return []
    return [
      ['Moedas', String(dashboard.currencies ?? '—')],
      ['Países', String(dashboard.countries ?? '—')],
      ['Métodos', String(dashboard.payment_methods ?? '—')],
      ['Corredores', String(dashboard.corridors ?? '—')],
      ['Players', String(dashboard.locker_players ?? '—')],
      ['Readiness médio', String(dashboard.avg_player_readiness ?? '—')],
      ['Insights abertos', String(dashboard.open_insights ?? '—')],
      ['Cobertura', `${dashboard.readiness_grade ?? '—'} · ${dashboard.world_coverage_pct ?? 0}%`],
    ]
  }, [dashboard])

  const rows: Row[] = useMemo(() => {
    const r = (id: unknown, detail: string): Row => ({ id: String(id ?? '—'), detail })
    switch (tab) {
      case 'overview':
        return overviewCards.map(([label, val]) => r(label, val))
      case 'countries':
        return operatingCountries.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.country_code, `${o.name} · ${o.default_currency_code}`)
        })
      case 'currencies':
        return currencies.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.code, String(o.name))
        })
      case 'methods':
        return methods.map((x) => r((x as { code?: string }).code, String((x as { name?: string }).name)))
      case 'matrix':
        return methodMatrix.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.country_code}/${o.payment_method_code}`, `min ${o.min_amount_cents}`)
        })
      case 'aliases':
        return aliases.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.ui_code, String(o.canonical_method_code))
        })
      case 'interfaces':
        return interfaces.map((x) => r((x as { code?: string }).code, String((x as { name?: string }).name)))
      case 'wallets':
        return wallets.map((x) => r((x as { code?: string }).code, String((x as { name?: string }).name)))
      case 'corridors':
        return corridors.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.corridor_code, `${o.origin_country_code}→${o.destination_country_code}`)
        })
      case 'fx':
        return fxRates.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.base_currency}/${o.quote_currency}`, `${o.rate} · ${o.rate_date}`)
        })
      case 'compliance':
        return compliance.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.country_code}/${o.limit_type}`, `${o.amount_cents} ${o.currency_code}`)
        })
      case 'audit':
        return fxAudit.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.base_currency}/${o.quote_currency}`, `${o.old_rate ?? '—'} → ${o.new_rate}`)
        })
      case 'players':
        return filteredPlayers.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.player_code, `${o.name} · ${o.segment}`)
        })
      case 'segments':
        return ecosystemSegments.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.code, `${o.name} · ${o.player_count ?? 0} players`)
        })
      case 'relations':
        return playerRelations.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.from_player_code}→${o.to_player_code}`, String(o.relation_type))
        })
      case 'intelligence':
        return [
          ...readiness.slice(0, 40).map((x) => {
            const o = x as Record<string, unknown>
            return r(`${o.player_code} · ${o.grade}`, `score ${o.readiness_score}`)
          }),
          ...insights.slice(0, 20).map((x) => {
            const o = x as Record<string, unknown>
            return r(o.title, String(o.suggested_action ?? o.insight_type))
          }),
        ]
      case 'settlements':
        return settlementSchedules.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.scope_type}/${o.scope_code}`, `T+${o.settlement_days} · ${o.settlement_currency}`)
        })
      case 'rails':
        return paymentRails.map((x) => {
          const o = x as Record<string, unknown>
          return r(`${o.player_code}/${o.country_code}`, String(o.payment_method_code ?? '—'))
        })
      case 'treasury':
        return ((treasury?.exposures as unknown[]) ?? []).map((x) => {
          const o = x as Record<string, unknown>
          return r(o.currency_code, `${o.player_count} players · risco ${o.risk_hint}`)
        })
      case 'fxlocks':
        return fxLocks.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.lock_reference, `${o.corridor_code} · ${o.locked_rate}`)
        })
      case 'pricing':
        return pricingResult
          ? [r('preview', JSON.stringify(pricingResult))]
          : [{ id: '—', detail: 'Preencha o simulador e clique em Simular cotação.' }]
      case 'partners':
        return partners.map((x) => {
          const o = x as Record<string, unknown>
          return r(o.code, `${o.name} · ${o.partner_type}`)
        })
      default:
        return []
    }
  }, [
    tab,
    overviewCards,
    operatingCountries,
    currencies,
    methods,
    methodMatrix,
    aliases,
    interfaces,
    wallets,
    corridors,
    fxRates,
    compliance,
    fxAudit,
    filteredPlayers,
    ecosystemSegments,
    playerRelations,
    readiness,
    insights,
    settlementSchedules,
    paymentRails,
    treasury,
    fxLocks,
    pricingResult,
    partners,
  ])

  const onSeed = async () => {
    setLoading(true)
    try {
      await moneyCambioAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateCurrency = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await moneyCambioAdminApi.createCurrency(currencyForm)
      setMessage(`Moeda ${currencyForm.code} criada.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar moeda')
    } finally {
      setLoading(false)
    }
  }

  const onCreateMethod = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await moneyCambioAdminApi.createMethod(methodForm)
      setMessage(`Método ${methodForm.code} criado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar método')
    } finally {
      setLoading(false)
    }
  }

  const onUpsertFx = async () => {
    setLoading(true)
    try {
      const today = new Date().toISOString().slice(0, 10)
      await moneyCambioAdminApi.upsertFxRate({ ...fxForm, rate_date: today })
      setMessage('Taxa FX gravada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha FX')
    } finally {
      setLoading(false)
    }
  }

  const onPricingPreview = async () => {
    setLoading(true)
    try {
      const { data } = await moneyCambioAdminApi.pricingPreview({
        amount_cents: Number(pricingForm.amount_cents) || 0,
        player_code: pricingForm.player_code,
        country_code: pricingForm.country_code,
        payment_method_code: pricingForm.payment_method_code,
      })
      setPricingResult(data)
      setMessage('Cotação simulada.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no simulador')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap gap-2 text-sm">
        <Link to="/ops/payment-gateway/admin" className="text-indigo-600 underline">
          Payment Gateway
        </Link>
        <Link to="/ops/payments/admin" className="text-indigo-600 underline">
          Payments OPS
        </Link>
        <Link to="/ops/fiscal/admin?tab=corridors" className="text-indigo-600 underline">
          Fiscal corredores
        </Link>
      </div>

      <header>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">OPS — Money &amp; Câmbio</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Catálogo monetário mundial, FX, intelligence e tesouraria (8125).
        </p>
      </header>

      {loading ? (
        <p className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm text-indigo-800 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200">
          Carregando dados…
        </p>
      ) : null}
      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30">
          {error}
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

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => void load()} className="rounded-lg border px-3 py-2 text-sm">
          Atualizar
        </button>
        <button type="button" onClick={() => void onSeed()} className="rounded-lg border px-3 py-2 text-sm">
          Seed
        </button>
      </div>

      {tab === 'currencies' ? (
        <form onSubmit={onCreateCurrency} className="flex flex-wrap gap-2">
          <input
            placeholder="BRL"
            value={currencyForm.code}
            onChange={(e) => setCurrencyForm((f) => ({ ...f, code: e.target.value }))}
            className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <input
            placeholder="Nome"
            value={currencyForm.name}
            onChange={(e) => setCurrencyForm((f) => ({ ...f, name: e.target.value }))}
            className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
            Criar moeda
          </button>
        </form>
      ) : null}

      {tab === 'methods' ? (
        <form onSubmit={onCreateMethod} className="flex flex-wrap gap-2">
          <input
            placeholder="PIX"
            value={methodForm.code}
            onChange={(e) => setMethodForm((f) => ({ ...f, code: e.target.value }))}
            className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
            Criar método
          </button>
        </form>
      ) : null}

      {tab === 'fx' ? (
        <div className="flex flex-wrap gap-2">
          <input
            value={fxForm.base_currency}
            onChange={(e) => setFxForm((f) => ({ ...f, base_currency: e.target.value }))}
            className="w-16 rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <input
            value={fxForm.quote_currency}
            onChange={(e) => setFxForm((f) => ({ ...f, quote_currency: e.target.value }))}
            className="w-16 rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <input
            value={fxForm.rate}
            onChange={(e) => setFxForm((f) => ({ ...f, rate: e.target.value }))}
            className="w-20 rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <button type="button" onClick={() => void onUpsertFx()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
            Gravar taxa
          </button>
        </div>
      ) : null}

      {tab === 'pricing' ? (
        <div className="flex flex-wrap gap-2">
          <input
            value={pricingForm.amount_cents}
            onChange={(e) => setPricingForm((f) => ({ ...f, amount_cents: e.target.value }))}
            className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <input
            value={pricingForm.player_code}
            onChange={(e) => setPricingForm((f) => ({ ...f, player_code: e.target.value }))}
            className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
          />
          <button type="button" onClick={() => void onPricingPreview()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
            Simular cotação
          </button>
        </div>
      ) : null}

      {tab === 'players' ? (
        <select
          value={playerSegmentFilter}
          onChange={(e) => setPlayerSegmentFilter(e.target.value)}
          className="rounded border px-2 py-1 text-sm dark:bg-slate-900"
        >
          <option value="">Todos os segmentos</option>
          {ecosystemSegments.map((s) => (
            <option key={String((s as { code: string }).code)} value={String((s as { code: string }).code)}>
              {(s as { code: string }).code}
            </option>
          ))}
        </select>
      ) : null}

      {tab === 'overview' && !dashboard && !loading && !error ? (
        <p className="text-sm text-amber-700">
          Sem KPIs — confira se o serviço money-cambio-admin está em execução na porta 8125 e rode Seed.
        </p>
      ) : null}

      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-100 dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">id / código</th>
              <th className="px-3 py-2">detalhe</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${tab}-${row.id}`} className="border-t">
                <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                <td className="px-3 py-2 text-xs">{row.detail}</td>
              </tr>
            ))}
            {!rows.length && !loading ? (
              <tr>
                <td colSpan={2} className="px-3 py-4 text-gray-500">
                  Nenhum registro para esta aba.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  )
}
