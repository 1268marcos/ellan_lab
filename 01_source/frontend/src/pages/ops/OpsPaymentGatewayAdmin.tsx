import { FormEvent, useCallback, useState } from 'react'
import {
  paymentGatewayAdminApi,
  type PaymentMethodCatalog,
  type PaymentProviderPartner,
} from '../../api/paymentGatewayAdmin'

type Tab = 'catalog' | 'providers' | 'ops'

export default function OpsPaymentGatewayAdmin() {
  const [tab, setTab] = useState<Tab>('catalog')
  const [methods, setMethods] = useState<PaymentMethodCatalog[]>([])
  const [providers, setProviders] = useState<PaymentProviderPartner[]>([])
  const [devices, setDevices] = useState<unknown[]>([])
  const [idem, setIdem] = useState<unknown[]>([])
  const [risk, setRisk] = useState<unknown[]>([])
  const [methodCode, setMethodCode] = useState('')
  const [methodName, setMethodName] = useState('')
  const [providerForm, setProviderForm] = useState({ name: '', code: '', provider_type: 'STRIPE' })
  const [selectedProvider, setSelectedProvider] = useState('')
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
      const [m, p, d, i, r] = await Promise.all([
        paymentGatewayAdminApi.listMethods(),
        paymentGatewayAdminApi.listProviders(),
        paymentGatewayAdminApi.listDevices(),
        paymentGatewayAdminApi.listIdempotency(),
        paymentGatewayAdminApi.listRiskEvents(),
      ])
      setMethods(m.data.items ?? [])
      setProviders(p.data.partners ?? [])
      setDevices(d.data.items ?? [])
      setIdem(i.data.items ?? [])
      setRisk(r.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  const onSeed = async () => {
    setLoading(true)
    try {
      await paymentGatewayAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateMethod = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await paymentGatewayAdminApi.createMethod({ code: methodCode, name: methodName })
      setMessage(`Método ${methodCode} criado.`)
      setMethodCode('')
      setMethodName('')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar método')
    } finally {
      setLoading(false)
    }
  }

  const onCreateProvider = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await paymentGatewayAdminApi.createProvider(providerForm)
      setMessage(`PSP ${data.code} criado.`)
      setSelectedProvider(data.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar PSP')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedProvider || !webhookUrl) return
    setLoading(true)
    try {
      await paymentGatewayAdminApi.configureWebhook(selectedProvider, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['payment.completed', 'payment.failed'],
      })
      setMessage('Webhook configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedProvider) return
    setLoading(true)
    try {
      const { data } = await paymentGatewayAdminApi.rotateApiKey(selectedProvider)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onPurgeIdem = async () => {
    setLoading(true)
    try {
      const { data } = await paymentGatewayAdminApi.purgeExpiredIdempotency()
      setMessage(`Idempotência expirada removida: ${(data as { purged?: number }).purged ?? 0}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao purgar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Payment Gateway</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Catálogo de métodos, PSP/adquirentes, device registry, idempotência e risk events.
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

      <div className="flex gap-2">
        {(['catalog', 'providers', 'ops'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {t === 'catalog' ? 'Catálogo' : t === 'providers' ? 'PSP / Parceiros' : 'Operações'}
          </button>
        ))}
      </div>

      {tab === 'catalog' && (
        <form onSubmit={onCreateMethod} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
          <input
            className="rounded border px-2 py-1 text-sm"
            placeholder="Código (ex. PIX)"
            required
            value={methodCode}
            onChange={(e) => setMethodCode(e.target.value)}
          />
          <input
            className="rounded border px-2 py-1 text-sm"
            placeholder="Nome"
            required
            value={methodName}
            onChange={(e) => setMethodName(e.target.value)}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
            Criar método de pagamento
          </button>
        </form>
      )}

      {tab === 'providers' && (
        <>
          <form
            onSubmit={onCreateProvider}
            className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-3"
          >
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome PSP"
              required
              value={providerForm.name}
              onChange={(e) => setProviderForm((f) => ({ ...f, name: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Código"
              required
              value={providerForm.code}
              onChange={(e) => setProviderForm((f) => ({ ...f, code: e.target.value }))}
            />
            <select
              className="rounded border px-2 py-1 text-sm"
              value={providerForm.provider_type}
              onChange={(e) => setProviderForm((f) => ({ ...f, provider_type: e.target.value }))}
            >
              <option value="STRIPE">STRIPE</option>
              <option value="MERCADOPAGO">MERCADOPAGO</option>
              <option value="OTHER">OTHER</option>
            </select>
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-3">
              Criar PSP
            </button>
          </form>
          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
            <div className="flex flex-wrap gap-2">
              <select
                className="rounded border px-2 py-1 text-sm"
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
              >
                <option value="">PSP</option>
                {providers.map((p) => (
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

      {tab === 'ops' && (
        <div className="flex gap-2">
          <button type="button" onClick={() => void onPurgeIdem()} className="rounded border px-3 py-2 text-sm">
            Purgar idempotência expirada
          </button>
        </div>
      )}

      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
          <tr>
            <th className="px-3 py-2">Tipo</th>
            <th className="px-3 py-2">Código / ID</th>
            <th className="px-3 py-2">Detalhe</th>
          </tr>
        </thead>
        <tbody>
          {tab === 'catalog' &&
            (methods.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-3 py-6 text-center text-gray-500">
                  Nenhum método (Seed ou Atualizar)
                </td>
              </tr>
            ) : (
              methods.map((m) => (
                <tr key={m.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">method</td>
                  <td className="px-3 py-2 font-mono text-xs">{m.code}</td>
                  <td className="px-3 py-2">{m.name}</td>
                </tr>
              ))
            ))}
          {tab === 'providers' &&
            providers.map((p) => (
              <tr key={p.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2">psp</td>
                <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
                <td className="px-3 py-2">
                  {p.name} · {p.provider_type}
                </td>
              </tr>
            ))}
          {tab === 'ops' && (
            <>
              {devices.map((d) => {
                const row = d as { device_hash: string; locker_id?: string }
                return (
                  <tr key={row.device_hash} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2">device</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.device_hash.slice(0, 16)}…</td>
                    <td className="px-3 py-2">{row.locker_id ?? '—'}</td>
                  </tr>
                )
              })}
              {idem.map((x) => {
                const row = x as { id: string; status: string }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2">idem</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                    <td className="px-3 py-2">{row.status}</td>
                  </tr>
                )
              })}
              {risk.map((x) => {
                const row = x as { id: string; decision: string; score: number }
                return (
                  <tr key={row.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2">risk</td>
                    <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                    <td className="px-3 py-2">
                      {row.decision} · score {row.score}
                    </td>
                  </tr>
                )
              })}
            </>
          )}
        </tbody>
      </table>
    </div>
  )
}
