import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { partnersApi } from '../../api/partners'
import { BulkUpload } from '../../components/BulkUpload'
import { CompatibilityChecker } from '../../components/CompatibilityChecker'

type ProductRow = {
  sku_id?: string
  partner_sku?: string
  name?: string
  category_id?: string
  price_cents?: number
  currency?: string
}

const DEFAULT_PARTNER =
  (typeof import.meta.env.VITE_PARTNER_ID === 'string' && import.meta.env.VITE_PARTNER_ID) ||
  '00000000-0000-0000-0000-000000000001'

export default function Catalog() {
  const [partnerId, setPartnerId] = useState(DEFAULT_PARTNER)
  const [rows, setRows] = useState<ProductRow[]>([])
  const [listErr, setListErr] = useState<string | null>(null)
  const [form, setForm] = useState({
    partner_sku: '',
    name: '',
    category_id: 'default',
    price_cents: '100',
    currency: 'BRL',
  })
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const load = useCallback(async () => {
    setListErr(null)
    try {
      const { data } = await partnersApi.getProducts(partnerId)
      if (Array.isArray(data)) setRows(data as ProductRow[])
      else if (data && typeof data === 'object' && 'items' in data && Array.isArray((data as { items: unknown }).items))
        setRows((data as { items: ProductRow[] }).items)
      else setRows([])
    } catch {
      setRows([])
      setListErr('GET /v1/partners/{id}/products indisponível ou vazio — cadastre abaixo.')
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  async function createOne(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setSaveMsg(null)
    try {
      await partnersApi.createProduct(partnerId, {
        partner_sku: form.partner_sku,
        name: form.name,
        category_id: form.category_id,
        price_cents: Number(form.price_cents),
        currency: form.currency,
        dimensions: {},
        images: [],
        compatibility_rules: {
          requires_signature: false,
          is_fragile: false,
          temperature_zone: 'AMBIENT',
        },
      })
      setSaveMsg('Produto criado.')
      setForm((f) => ({ ...f, partner_sku: '', name: '' }))
      await load()
    } catch (err: unknown) {
      setSaveMsg(err instanceof Error ? err.message : 'Erro ao criar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Catálogo parceiro</h1>
          <p className="text-sm text-slate-400">Produtos · bulk · compatibilidade locker</p>
        </div>
        <Link to="/partners/webhooks" className="text-sm text-emerald-400 hover:underline">
          Webhooks →
        </Link>
      </div>

      <label className="block max-w-xl text-xs text-slate-400">
        Partner ID
        <input
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value.trim())}
          onBlur={() => void load()}
          className="ellan-field mt-1 w-full font-mono"
        />
      </label>

      {listErr && <p className="text-sm text-amber-400">{listErr}</p>}

      <section className="overflow-hidden rounded-xl border border-slate-700">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-700 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Categoria</th>
              <th className="px-3 py-2">Preço</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                  Nenhum produto listado
                </td>
              </tr>
            ) : (
              rows.map((r, i) => (
                <tr key={r.sku_id ?? r.partner_sku ?? i} className="border-b border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs text-slate-300">{r.partner_sku ?? r.sku_id}</td>
                  <td className="px-3 py-2 text-slate-200">{r.name}</td>
                  <td className="px-3 py-2 text-slate-400">{r.category_id}</td>
                  <td className="px-3 py-2 text-slate-300">
                    {(r.price_cents ?? 0) / 100} {r.currency ?? ''}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <form onSubmit={createOne} className="grid gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4 sm:grid-cols-2">
        <h2 className="sm:col-span-2 text-sm font-semibold text-slate-200">Novo produto</h2>
        <input
          required
          placeholder="partner_sku"
          value={form.partner_sku}
          onChange={(e) => setForm((f) => ({ ...f, partner_sku: e.target.value }))}
          className="ellan-field"
        />
        <input
          required
          placeholder="name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          className="ellan-field"
        />
        <input
          required
          placeholder="category_id"
          value={form.category_id}
          onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
          className="ellan-field"
        />
        <input
          required
          type="number"
          min={0}
          placeholder="price_cents"
          value={form.price_cents}
          onChange={(e) => setForm((f) => ({ ...f, price_cents: e.target.value }))}
          className="ellan-field"
        />
        <button
          type="submit"
          disabled={saving}
          className="sm:col-span-2 rounded-md bg-emerald-600 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {saving ? 'Salvando…' : 'POST /products'}
        </button>
        {saveMsg && <p className="sm:col-span-2 text-xs text-slate-400">{saveMsg}</p>}
      </form>

      <BulkUpload partnerId={partnerId} onDone={() => void load()} />

      <CompatibilityChecker partnerId={partnerId} />
    </div>
  )
}
