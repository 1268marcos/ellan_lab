import { FormEvent, useCallback, useEffect, useState } from 'react'
import {
  marketplaceAdminApi,
  type MarketplaceCommission,
  type MarketplaceSeller,
  type SellerProduct,
  type SellerReview,
} from '../../api/marketplaceAdmin'

type Tab = 'sellers' | 'products' | 'commissions' | 'reviews'

const emptySeller = () => ({
  legal_name: '',
  trade_name: '',
  tax_id: '',
  email: '',
  commission_pct: '5.00',
  status: 'PENDING_APPROVAL',
})

const emptyProduct = () => ({
  seller_id: '',
  locker_id: '',
  product_id: '',
  price_cents: 1000,
  quantity: 1,
})

export default function OpsMarketplaceAdmin() {
  const [tab, setTab] = useState<Tab>('sellers')
  const [sellers, setSellers] = useState<MarketplaceSeller[]>([])
  const [products, setProducts] = useState<SellerProduct[]>([])
  const [commissions, setCommissions] = useState<MarketplaceCommission[]>([])
  const [reviews, setReviews] = useState<SellerReview[]>([])
  const [sellerForm, setSellerForm] = useState(emptySeller)
  const [productForm, setProductForm] = useState(emptyProduct)
  const [selectedSeller, setSelectedSeller] = useState('')
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
      const [s, p, c, r] = await Promise.all([
        marketplaceAdminApi.listSellers(),
        marketplaceAdminApi.listProducts(),
        marketplaceAdminApi.listCommissions(),
        marketplaceAdminApi.listReviews(),
      ])
      const sellerList = s.data.sellers ?? []
      setSellers(sellerList)
      setProducts(p.data.products ?? [])
      setCommissions(c.data.commissions ?? [])
      setReviews(r.data.reviews ?? [])
      setSelectedSeller((prev) => prev || sellerList[0]?.id || '')
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
      await marketplaceAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateSeller = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await marketplaceAdminApi.createSeller(sellerForm)
      setMessage(`Seller ${data.legal_name} criado.`)
      setSelectedSeller(data.id)
      setSellerForm(emptySeller())
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar seller')
    } finally {
      setLoading(false)
    }
  }

  const onCreateProduct = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await marketplaceAdminApi.createProduct({
        ...productForm,
        seller_id: productForm.seller_id || selectedSeller,
      })
      setMessage('Produto do seller criado.')
      setProductForm(emptyProduct())
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar produto')
    } finally {
      setLoading(false)
    }
  }

  const onApproveSeller = async (sellerId: string) => {
    setLoading(true)
    try {
      await marketplaceAdminApi.updateSeller(sellerId, { status: 'ACTIVE' })
      setMessage('Seller aprovado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao aprovar')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedSeller || !webhookUrl) return
    setLoading(true)
    try {
      await marketplaceAdminApi.configureWebhook(selectedSeller, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['order.created', 'commission.settled'],
      })
      setMessage('Webhook salvo.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedSeller) return
    setLoading(true)
    try {
      const { data } = await marketplaceAdminApi.rotateApiKey(selectedSeller)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…). Copie agora.`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onSettleCommission = async (id: string) => {
    setLoading(true)
    try {
      await marketplaceAdminApi.updateCommission(id, { status: 'SETTLED' })
      setMessage('Comissão liquidada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao liquidar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Marketplace</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Sellers, produtos por locker, comissões, avaliações, webhook e API key.
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
        {(['sellers', 'products', 'commissions', 'reviews'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {t === 'sellers' ? 'Sellers' : t === 'products' ? 'Produtos' : t === 'commissions' ? 'Comissões' : 'Avaliações'}
          </button>
        ))}
      </div>

      <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-2 text-lg font-medium">Integração (seller selecionado)</h2>
        <div className="flex flex-wrap gap-2">
          <select
            className="rounded border px-2 py-1 text-sm"
            value={selectedSeller}
            onChange={(e) => setSelectedSeller(e.target.value)}
          >
            <option value="">Seller</option>
            {sellers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.trade_name || s.legal_name}
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

      {tab === 'sellers' && (
        <>
          <form
            onSubmit={onCreateSeller}
            className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2"
          >
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Razão social"
              required
              value={sellerForm.legal_name}
              onChange={(e) => setSellerForm((f) => ({ ...f, legal_name: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome fantasia"
              value={sellerForm.trade_name}
              onChange={(e) => setSellerForm((f) => ({ ...f, trade_name: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="CNPJ"
              required
              value={sellerForm.tax_id}
              onChange={(e) => setSellerForm((f) => ({ ...f, tax_id: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="E-mail"
              required
              value={sellerForm.email}
              onChange={(e) => setSellerForm((f) => ({ ...f, email: e.target.value }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
              Criar seller
            </button>
          </form>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Nome</th>
                <th className="px-3 py-2">CNPJ</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Comissão %</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {sellers.map((s) => (
                <tr key={s.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{s.trade_name || s.legal_name}</td>
                  <td className="px-3 py-2 font-mono text-xs">{s.tax_id}</td>
                  <td className="px-3 py-2">{s.status}</td>
                  <td className="px-3 py-2">{s.commission_pct}</td>
                  <td className="px-3 py-2">
                    {s.status === 'PENDING_APPROVAL' && (
                      <button
                        type="button"
                        className="text-indigo-600 hover:underline"
                        onClick={() => void onApproveSeller(s.id)}
                      >
                        Aprovar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {tab === 'products' && (
        <>
          <form
            onSubmit={onCreateProduct}
            className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-2"
          >
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Locker ID"
              required
              value={productForm.locker_id}
              onChange={(e) => setProductForm((f) => ({ ...f, locker_id: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Product ID"
              required
              value={productForm.product_id}
              onChange={(e) => setProductForm((f) => ({ ...f, product_id: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              type="number"
              placeholder="Preço (centavos)"
              value={productForm.price_cents}
              onChange={(e) => setProductForm((f) => ({ ...f, price_cents: Number(e.target.value) }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white md:col-span-2">
              Criar produto (seller selecionado)
            </button>
          </form>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Locker</th>
                <th className="px-3 py-2">Produto</th>
                <th className="px-3 py-2">Preço</th>
                <th className="px-3 py-2">Qtd</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs">{p.locker_id}</td>
                  <td className="px-3 py-2">{p.product_id}</td>
                  <td className="px-3 py-2">R$ {(p.price_cents / 100).toFixed(2)}</td>
                  <td className="px-3 py-2">{p.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {tab === 'commissions' && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Pedido</th>
              <th className="px-3 py-2">Comissão</th>
              <th className="px-3 py-2">Líquido seller</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {commissions.map((c) => (
              <tr key={c.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{c.order_id}</td>
                <td className="px-3 py-2">R$ {(c.commission_amount_cents / 100).toFixed(2)}</td>
                <td className="px-3 py-2">R$ {(c.net_to_seller_cents / 100).toFixed(2)}</td>
                <td className="px-3 py-2">{c.status}</td>
                <td className="px-3 py-2">
                  {c.status === 'PENDING' && (
                    <button
                      type="button"
                      className="text-indigo-600 hover:underline"
                      onClick={() => void onSettleCommission(c.id)}
                    >
                      Liquidar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'reviews' && (
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">Pedido</th>
              <th className="px-3 py-2">Nota</th>
              <th className="px-3 py-2">Comentário</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((r) => (
              <tr key={r.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{r.order_id}</td>
                <td className="px-3 py-2">{r.rating}/5</td>
                <td className="px-3 py-2">{r.comment ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
