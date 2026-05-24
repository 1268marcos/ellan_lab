import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { moneyCambioAdminApi, type FxRate, type MoneyCurrency } from '../../api/moneyCambioAdmin'

const TABS = [
  ['currencies', 'Moedas'],
  ['methods', 'Métodos'],
  ['interfaces', 'Interfaces'],
  ['wallets', 'Wallets'],
  ['fx', 'Câmbio (FX)'],
  ['partners', 'Integração'],
] as const

type Tab = (typeof TABS)[number][0]

export default function OpsMoneyCambioAdmin() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = (searchParams.get('tab') || 'currencies') as Tab
  const setTab = (k: Tab) => setSearchParams({ tab: k }, { replace: true })

  const [currencies, setCurrencies] = useState<MoneyCurrency[]>([])
  const [methods, setMethods] = useState<unknown[]>([])
  const [interfaces, setInterfaces] = useState<unknown[]>([])
  const [wallets, setWallets] = useState<unknown[]>([])
  const [fxRates, setFxRates] = useState<FxRate[]>([])
  const [partners, setPartners] = useState<unknown[]>([])
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
      const [c, m, i, w, f, p] = await Promise.all([
        moneyCambioAdminApi.listCurrencies(),
        moneyCambioAdminApi.listMethods(),
        moneyCambioAdminApi.listInterfaces(),
        moneyCambioAdminApi.listWallets(),
        moneyCambioAdminApi.listFxRates(),
        moneyCambioAdminApi.listPartners(),
      ])
      setCurrencies(c.data.items ?? [])
      setMethods(m.data.items ?? [])
      setInterfaces(i.data.items ?? [])
      setWallets(w.data.items ?? [])
      setFxRates(f.data.items ?? [])
      setPartners(p.data.partners ?? [])
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
      setCurrencyForm({ code: '', name: '', symbol: '' })
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
      setMethodForm({ code: '', name: '' })
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

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await moneyCambioAdminApi.createPartner(partnerForm)
      setMessage('Parceiro criado.')
      setSelectedPartner((data as { id?: string }).id ?? '')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha parceiro')
    } finally {
      setLoading(false)
    }
  }

  const rows =
    tab === 'currencies'
      ? currencies
      : tab === 'methods'
        ? methods
        : tab === 'interfaces'
          ? interfaces
          : tab === 'wallets'
            ? wallets
            : tab === 'fx'
              ? fxRates
              : partners

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex flex-wrap gap-3 text-sm">
        <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
          Payment Gateway
        </Link>
        <Link to="/ops/finance/admin?tab=fx" className="text-indigo-600 hover:underline">
          Finance FX
        </Link>
      </div>

      <header>
        <h1 className="text-2xl font-semibold text-slate-900">OPS — Money &amp; Câmbio</h1>
        <p className="text-sm text-slate-600 mt-1">
          Moedas, catálogo de pagamento, wallets, taxas FX e integrações (porta 8125).
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {TABS.map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setTab(k)}
            className={`px-3 py-1 rounded text-sm ${tab === k ? 'bg-indigo-600 text-white' : 'bg-slate-100'}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => void load()} disabled={loading} className="px-3 py-1 border rounded text-sm">
          Atualizar
        </button>
        <button type="button" onClick={() => void onSeed()} disabled={loading} className="px-3 py-1 border rounded text-sm">
          Seed
        </button>
      </div>

      {tab === 'currencies' ? (
        <form onSubmit={onCreateCurrency} className="flex flex-wrap gap-2 items-end">
          <input
            placeholder="BRL"
            value={currencyForm.code}
            onChange={(e) => setCurrencyForm((f) => ({ ...f, code: e.target.value }))}
            className="border rounded px-2 py-1 text-sm"
          />
          <input
            placeholder="Nome"
            value={currencyForm.name}
            onChange={(e) => setCurrencyForm((f) => ({ ...f, name: e.target.value }))}
            className="border rounded px-2 py-1 text-sm"
          />
          <button type="submit" className="px-3 py-1 bg-indigo-600 text-white rounded text-sm">
            Criar moeda
          </button>
        </form>
      ) : null}

      {tab === 'methods' ? (
        <form onSubmit={onCreateMethod} className="flex flex-wrap gap-2 items-end">
          <input
            placeholder="PIX"
            value={methodForm.code}
            onChange={(e) => setMethodForm((f) => ({ ...f, code: e.target.value }))}
            className="border rounded px-2 py-1 text-sm"
          />
          <input
            placeholder="Nome"
            value={methodForm.name}
            onChange={(e) => setMethodForm((f) => ({ ...f, name: e.target.value }))}
            className="border rounded px-2 py-1 text-sm"
          />
          <button type="submit" className="px-3 py-1 bg-indigo-600 text-white rounded text-sm">
            Criar método
          </button>
        </form>
      ) : null}

      {tab === 'fx' ? (
        <div className="flex flex-wrap gap-2 items-end">
          <input
            value={fxForm.base_currency}
            onChange={(e) => setFxForm((f) => ({ ...f, base_currency: e.target.value }))}
            className="border rounded px-2 py-1 text-sm w-20"
          />
          <input
            value={fxForm.quote_currency}
            onChange={(e) => setFxForm((f) => ({ ...f, quote_currency: e.target.value }))}
            className="border rounded px-2 py-1 text-sm w-20"
          />
          <input
            value={fxForm.rate}
            onChange={(e) => setFxForm((f) => ({ ...f, rate: e.target.value }))}
            className="border rounded px-2 py-1 text-sm w-24"
          />
          <button type="button" onClick={() => void onUpsertFx()} className="px-3 py-1 bg-indigo-600 text-white rounded text-sm">
            Gravar taxa
          </button>
        </div>
      ) : null}

      {tab === 'partners' ? (
        <div className="space-y-3">
          <form onSubmit={onCreatePartner} className="flex flex-wrap gap-2 items-end">
            <input
              placeholder="Nome"
              value={partnerForm.name}
              onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
              className="border rounded px-2 py-1 text-sm"
            />
            <input
              placeholder="CODE"
              value={partnerForm.code}
              onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))}
              className="border rounded px-2 py-1 text-sm"
            />
            <button type="submit" className="px-3 py-1 bg-indigo-600 text-white rounded text-sm">
              Criar parceiro
            </button>
          </form>
          <div className="flex flex-wrap gap-2">
            <select
              value={selectedPartner}
              onChange={(e) => setSelectedPartner(e.target.value)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="">Parceiro</option>
              {(partners as { id: string; code: string }[]).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input
              placeholder="Webhook URL"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="border rounded px-2 py-1 text-sm flex-1 min-w-[200px]"
            />
            <button
              type="button"
              onClick={async () => {
                if (!selectedPartner || !webhookUrl) return
                const { data } = await moneyCambioAdminApi.configureWebhook(selectedPartner, { url: webhookUrl })
                setMessage(`Webhook: ${(data as { url?: string }).url}`)
              }}
              className="px-3 py-1 border rounded text-sm"
            >
              Webhook
            </button>
            <button
              type="button"
              onClick={async () => {
                if (!selectedPartner) return
                const { data } = await moneyCambioAdminApi.rotateApiKey(selectedPartner)
                setLastApiKey(data.api_key)
                setMessage('API key rotacionada.')
              }}
              className="px-3 py-1 border rounded text-sm"
            >
              Rotacionar key
            </button>
          </div>
          {lastApiKey ? (
            <pre className="text-xs bg-amber-50 border border-amber-200 p-2 rounded overflow-x-auto">{lastApiKey}</pre>
          ) : null}
        </div>
      ) : null}

      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <pre className="text-xs bg-slate-50 border rounded p-3 overflow-auto max-h-96">
        {JSON.stringify(rows, null, 2)}
      </pre>
    </div>
  )
}
