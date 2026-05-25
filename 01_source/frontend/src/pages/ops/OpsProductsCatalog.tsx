import { FormEvent, useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  orderPickupProductsApi,
  type ProductCategory,
  type ProductListItem,
} from '../../api/orderPickupProducts'

const STATUS_OPTIONS = ['', 'DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED']

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  DRAFT: ['ACTIVE', 'DISCONTINUED'],
  ACTIVE: ['INACTIVE', 'DISCONTINUED'],
  INACTIVE: ['ACTIVE', 'DISCONTINUED'],
  DISCONTINUED: [],
}

const inp =
  'w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100'

function formatBrl(cents: number) {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function OpsProductsCatalog() {
  const [items, setItems] = useState<ProductListItem[]>([])
  const [categories, setCategories] = useState<ProductCategory[]>([])
  const [total, setTotal] = useState(0)
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [limit, setLimit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({
    id: '',
    name: '',
    amount_reais: '',
    category_id: '',
    status: 'DRAFT',
  })
  const [priceEdit, setPriceEdit] = useState<{ id: string; reais: string } | null>(null)

  const loadCategories = useCallback(async () => {
    try {
      const { data } = await orderPickupProductsApi.listCategories()
      setCategories(data.items ?? [])
    } catch {
      setCategories([])
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupProductsApi.listProducts({
        status: status || undefined,
        category: category || undefined,
        limit,
        offset,
      })
      setItems(data.items ?? [])
      setTotal(data.total ?? 0)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar produtos')
    } finally {
      setLoading(false)
    }
  }, [status, category, limit, offset])

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const reais = Number(createForm.amount_reais.replace(',', '.'))
      const amount_cents = Math.round(reais * 100)
      await orderPickupProductsApi.createProduct({
        id: createForm.id.trim(),
        name: createForm.name.trim(),
        amount_cents,
        category_id: createForm.category_id.trim() || null,
        status: createForm.status,
      })
      setMessage(`Produto ${createForm.id} criado.`)
      setShowCreate(false)
      setCreateForm({ id: '', name: '', amount_reais: '', category_id: '', status: 'DRAFT' })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar produto')
    } finally {
      setLoading(false)
    }
  }

  const onStatusChange = async (row: ProductListItem, toStatus: string) => {
    setLoading(true)
    try {
      await orderPickupProductsApi.patchStatus(row.id, toStatus)
      setMessage(`${row.id} → ${toStatus}`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Transição inválida')
    } finally {
      setLoading(false)
    }
  }

  const onSavePrice = async () => {
    if (!priceEdit) return
    const reais = Number(priceEdit.reais.replace(',', '.'))
    if (!Number.isFinite(reais) || reais < 0) return
    setLoading(true)
    try {
      await orderPickupProductsApi.patchPrice(priceEdit.id, Math.round(reais * 100))
      setMessage(`Preço de ${priceEdit.id} atualizado.`)
      setPriceEdit(null)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar preço')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Catálogo de produtos</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Tabela <code>products</code> (SKU central) — preço, status e vínculo com categorias.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/ops/products/categories"
            className="text-sm text-indigo-600 hover:underline dark:text-indigo-300"
          >
            Categorias
          </Link>
          <button
            type="button"
            onClick={() => {
              void loadCategories()
              void load()
            }}
            disabled={loading}
            className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Carregando…' : 'Atualizar'}
          </button>
          <button
            type="button"
            onClick={() => setShowCreate((v) => !v)}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm dark:border-slate-600"
          >
            Novo produto
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <label className="text-sm">
          Status
          <select className={`${inp} mt-1 min-w-[140px]`} value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUS_OPTIONS.map((s) => (
              <option key={s || 'ALL'} value={s}>
                {s || 'Todos'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Categoria
          <input
            className={`${inp} mt-1 min-w-[160px]`}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="category_id"
            list="cat-ids"
          />
          <datalist id="cat-ids">
            {categories.map((c) => (
              <option key={c.id} value={c.id} />
            ))}
          </datalist>
        </label>
        <label className="text-sm">
          Limite
          <input
            type="number"
            min={1}
            max={500}
            className={`${inp} mt-1 w-24`}
            value={limit}
            onChange={(e) => setLimit(Math.max(1, Math.min(500, Number(e.target.value) || 50)))}
          />
        </label>
      </div>

      {message ? <p className="mb-3 text-sm text-emerald-600">{message}</p> : null}
      {error ? <p className="mb-3 text-sm text-red-500">{error}</p> : null}

      {showCreate ? (
        <form
          onSubmit={(e) => void onCreate(e)}
          className="mb-6 grid max-w-xl gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-slate-700 dark:bg-slate-800/50"
        >
          <h2 className="font-semibold">Novo produto (SKU)</h2>
          <label className="text-sm">
            ID / SKU
            <input
              className={inp}
              required
              value={createForm.id}
              onChange={(e) => setCreateForm({ ...createForm, id: e.target.value })}
            />
          </label>
          <label className="text-sm">
            Nome
            <input
              className={inp}
              required
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </label>
          <label className="text-sm">
            Preço (R$)
            <input
              className={inp}
              required
              value={createForm.amount_reais}
              onChange={(e) => setCreateForm({ ...createForm, amount_reais: e.target.value })}
            />
          </label>
          <label className="text-sm">
            category_id
            <input
              className={inp}
              value={createForm.category_id}
              onChange={(e) => setCreateForm({ ...createForm, category_id: e.target.value })}
              list="cat-ids"
            />
          </label>
          <label className="text-sm">
            Status inicial
            <select
              className={inp}
              value={createForm.status}
              onChange={(e) => setCreateForm({ ...createForm, status: e.target.value })}
            >
              {['DRAFT', 'ACTIVE'].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={loading} className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white w-fit">
            Criar
          </button>
        </form>
      ) : null}

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-700">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800">
            <tr>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Preço</th>
              <th className="px-3 py-2">Categoria</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Ativo</th>
              <th className="px-3 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id} className="border-b border-gray-100 dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                <td className="px-3 py-2">{row.name}</td>
                <td className="px-3 py-2">{formatBrl(row.amount_cents)}</td>
                <td className="px-3 py-2 text-xs">{row.category_id ?? '—'}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-700">{row.status}</span>
                </td>
                <td className="px-3 py-2">{row.is_active ? 'sim' : 'não'}</td>
                <td className="px-3 py-2 flex flex-wrap gap-1">
                  <button
                    type="button"
                    className="text-xs text-indigo-600 hover:underline"
                    onClick={() => setPriceEdit({ id: row.id, reais: String(row.amount_cents / 100) })}
                  >
                    Preço
                  </button>
                  {(ALLOWED_TRANSITIONS[row.status] ?? []).map((target) => (
                    <button
                      key={target}
                      type="button"
                      className="text-xs text-gray-600 hover:underline dark:text-slate-300"
                      onClick={() => void onStatusChange(row, target)}
                    >
                      → {target}
                    </button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && !loading ? (
          <p className="p-4 text-sm text-gray-500">Nenhum produto. Clique em Atualizar após o seed.</p>
        ) : null}
      </div>

      <div className="mt-3 flex items-center gap-3 text-sm text-gray-500">
        <button
          type="button"
          disabled={offset <= 0 || loading}
          onClick={() => setOffset((o) => Math.max(0, o - limit))}
          className="ellan-field"
        >
          Anterior
        </button>
        <span>
          offset={offset} · total={total}
        </span>
        <button
          type="button"
          disabled={offset + limit >= total || loading}
          onClick={() => setOffset((o) => o + limit)}
          className="ellan-field"
        >
          Próxima
        </button>
      </div>

      {priceEdit ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-lg bg-white p-4 shadow dark:bg-slate-900">
            <h3 className="font-semibold">Preço — {priceEdit.id}</h3>
            <input
              className={`${inp} mt-2`}
              value={priceEdit.reais}
              onChange={(e) => setPriceEdit({ ...priceEdit, reais: e.target.value })}
            />
            <div className="mt-3 flex gap-2">
              <button type="button" onClick={() => void onSavePrice()} className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
                Salvar
              </button>
              <button type="button" onClick={() => setPriceEdit(null)} className="ellan-btn-outline">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
