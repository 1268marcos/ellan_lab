import { FormEvent, useCallback, useState } from 'react'
import { partnerAdminApi, type EcommercePartner, type LogisticsPartner } from '../../api/partnerAdmin'

type Tab = 'ecommerce' | 'logistics'

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
  const [tab, setTab] = useState<Tab>('ecommerce')
  const [ecForm, setEcForm] = useState(emptyEc)
  const [lgForm, setLgForm] = useState(emptyLg)
  const [ecItems, setEcItems] = useState<EcommercePartner[]>([])
  const [lgItems, setLgItems] = useState<LogisticsPartner[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [partnerType, setPartnerType] = useState('ECOMMERCE')
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
      const [ec, lg] = await Promise.all([partnerAdminApi.listEcommerce(), partnerAdminApi.listLogistics()])
      setEcItems(ec.data.partners ?? [])
      setLgItems(lg.data.partners ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao listar parceiros')
    } finally {
      setLoading(false)
    }
  }, [])

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
    setError(null)
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
    setError(null)
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

  const items = tab === 'ecommerce' ? ecItems : lgItems

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Parceiros</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            CRUD e-commerce e logística, webhook e rotação de API key.
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
        {(['ecommerce', 'logistics'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {t === 'ecommerce' ? 'E-commerce' : 'Logística'}
          </button>
        ))}
      </div>

      {tab === 'ecommerce' ? (
        <form onSubmit={onSubmitEc} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
          <input className="rounded border px-2 py-1 text-sm md:col-span-2" placeholder="ID (opcional)" value={ecForm.id} onChange={(e) => setEcForm((f) => ({ ...f, id: e.target.value }))} />
          <input className="rounded border px-2 py-1 text-sm" placeholder="Nome" required value={ecForm.name} onChange={(e) => setEcForm((f) => ({ ...f, name: e.target.value }))} />
          <input className="rounded border px-2 py-1 text-sm" placeholder="Código" required value={ecForm.code} onChange={(e) => setEcForm((f) => ({ ...f, code: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
            Criar e-commerce
          </button>
        </form>
      ) : (
        <form onSubmit={onSubmitLg} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2">
          <input className="rounded border px-2 py-1 text-sm md:col-span-2" placeholder="ID (opcional)" value={lgForm.id} onChange={(e) => setLgForm((f) => ({ ...f, id: e.target.value }))} />
          <input className="rounded border px-2 py-1 text-sm" placeholder="Nome" required value={lgForm.name} onChange={(e) => setLgForm((f) => ({ ...f, name: e.target.value }))} />
          <input className="rounded border px-2 py-1 text-sm" placeholder="Código" required value={lgForm.code} onChange={(e) => setLgForm((f) => ({ ...f, code: e.target.value }))} />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
            Criar logística
          </button>
        </form>
      )}

      <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-2 text-lg font-medium">Webhook e API key</h2>
        <div className="flex flex-wrap gap-2">
          <select className="rounded border px-2 py-1 text-sm" value={partnerType} onChange={(e) => setPartnerType(e.target.value)}>
            <option value="ECOMMERCE">ECOMMERCE</option>
            <option value="LOGISTICS">LOGISTICS</option>
          </select>
          <select className="rounded border px-2 py-1 text-sm" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            <option value="">Parceiro</option>
            {(partnerType === 'ECOMMERCE' ? ecItems : lgItems).map((p) => (
              <option key={p.id} value={p.id}>
                {p.code}
              </option>
            ))}
          </select>
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
                Nenhum parceiro (Atualizar ou Seed)
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
    </div>
  )
}
