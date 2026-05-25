import { FormEvent, useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  orderPickupProductsApi,
  type ProductCategory,
} from '../../api/orderPickupProducts'

type CategoryForm = {
  id: string
  name: string
  description: string
  parent_category: string
  temperature_zone: string
  security_level: string
  is_hazardous: boolean
  requires_age_verification: boolean
  requires_id: boolean
  requires_signature: boolean
  max_weight_g: string
}

const emptyForm = (): CategoryForm => ({
  id: '',
  name: '',
  description: '',
  parent_category: '',
  temperature_zone: 'AMBIENT',
  security_level: 'STANDARD',
  is_hazardous: false,
  requires_age_verification: false,
  requires_id: false,
  requires_signature: false,
  max_weight_g: '',
})

function buildTree(items: ProductCategory[]) {
  const byId = new Map<string, ProductCategory & { children: (ProductCategory & { children: unknown[] })[] }>()
  for (const raw of items) {
    byId.set(raw.id, { ...raw, children: [] })
  }
  const roots: (ProductCategory & { children: typeof roots })[] = []
  for (const node of byId.values()) {
    const pid = node.parent_category ? String(node.parent_category) : ''
    if (pid && byId.has(pid)) {
      byId.get(pid)!.children.push(node)
    } else {
      roots.push(node)
    }
  }
  const sortRec = (nodes: typeof roots) => {
    nodes.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
    for (const n of nodes) sortRec(n.children as typeof roots)
  }
  sortRec(roots)
  return roots
}

const inp =
  'w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100'

export default function OpsProductCategories() {
  const [items, setItems] = useState<ProductCategory[]>([])
  const [form, setForm] = useState<CategoryForm | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const tree = useMemo(() => buildTree(items), [items])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await orderPickupProductsApi.listCategories()
      setItems(data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar categorias')
    } finally {
      setLoading(false)
    }
  }, [])

  const openCreate = () => {
    setEditId(null)
    setForm(emptyForm())
  }

  const openEdit = (row: ProductCategory) => {
    const meta = row.metadata_json ?? {}
    setEditId(row.id)
    setForm({
      id: row.id,
      name: row.name,
      description: row.description ?? '',
      parent_category: row.parent_category ?? '',
      temperature_zone: String(meta.temperature_zone ?? meta.default_temperature_zone ?? 'AMBIENT'),
      security_level: String(meta.security_level ?? meta.default_security_level ?? 'STANDARD'),
      is_hazardous: Boolean(meta.is_hazardous),
      requires_age_verification: Boolean(row.requires_age_verification),
      requires_id: Boolean(row.requires_id),
      requires_signature: Boolean(row.requires_signature),
      max_weight_g: row.max_weight_g != null ? String(row.max_weight_g) : '',
    })
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!form) return
    setLoading(true)
    setError(null)
    try {
      const body = {
        name: form.name.trim(),
        description: form.description.trim() || null,
        parent_category: form.parent_category.trim() || null,
        metadata_json: {
          temperature_zone: form.temperature_zone,
          security_level: form.security_level,
          is_hazardous: form.is_hazardous,
        },
        requires_age_verification: form.requires_age_verification,
        requires_id: form.requires_id,
        requires_signature: form.requires_signature,
        max_weight_g: form.max_weight_g.trim() ? Number(form.max_weight_g) : null,
      }
      if (editId) {
        await orderPickupProductsApi.updateCategory(editId, body)
        setMessage(`Categoria ${editId} atualizada.`)
      } else {
        await orderPickupProductsApi.createCategory({ ...body, id: form.id.trim() })
        setMessage(`Categoria ${form.id} criada.`)
      }
      setForm(null)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar')
    } finally {
      setLoading(false)
    }
  }

  const onDelete = async (row: ProductCategory) => {
    if (!window.confirm(`Excluir categoria ${row.id}?`)) return
    setLoading(true)
    try {
      await orderPickupProductsApi.deleteCategory(row.id)
      setMessage(`Categoria ${row.id} removida.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao excluir')
    } finally {
      setLoading(false)
    }
  }

  const renderRows = (
    nodes: ReturnType<typeof buildTree>,
    depth: number,
  ): JSX.Element[] =>
    nodes.flatMap((node) => [
      <tr key={node.id} className="border-b border-gray-100 dark:border-slate-800">
        <td className="px-3 py-2 text-sm" style={{ paddingLeft: 12 + depth * 16 }}>
          <code className="text-xs">{node.id}</code>
        </td>
        <td className="px-3 py-2 text-sm">{node.name}</td>
        <td className="px-3 py-2 text-xs text-gray-500">{node.parent_category ?? '—'}</td>
        <td className="px-3 py-2 text-xs">
          {(node.metadata_json as Record<string, unknown>)?.temperature_zone as string} /{' '}
          {(node.metadata_json as Record<string, unknown>)?.security_level as string}
        </td>
        <td className="px-3 py-2 text-xs">
          {node.requires_age_verification ? 'idade ' : ''}
          {node.requires_id ? 'doc ' : ''}
          {node.requires_signature ? 'assin. ' : ''}
          {node.max_weight_g != null ? `${node.max_weight_g}g` : '—'}
        </td>
        <td className="px-3 py-2 text-right text-xs">
          <button type="button" className="mr-2 text-indigo-600 hover:underline" onClick={() => openEdit(node)}>
            Editar
          </button>
          <button type="button" className="text-red-500 hover:underline" onClick={() => void onDelete(node)}>
            Excluir
          </button>
        </td>
      </tr>,
      ...renderRows(node.children as ReturnType<typeof buildTree>, depth + 1),
    ])

  return (
    <div className="p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Categorias de produto</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Tabela <code>product_categories</code> — hierarquia, zonas térmicas e restrições de locker.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/ops/products/catalog" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">
            Catálogo de produtos
          </Link>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Carregando…' : 'Atualizar'}
          </button>
          <button
            type="button"
            onClick={openCreate}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm dark:border-slate-600"
          >
            Nova categoria
          </button>
        </div>
      </div>

      {message ? <p className="mb-3 text-sm text-emerald-600">{message}</p> : null}
      {error ? <p className="mb-3 text-sm text-red-500">{error}</p> : null}

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-700">
        <table className="min-w-full text-left">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Pai</th>
              <th className="px-3 py-2">Zona / segurança</th>
              <th className="px-3 py-2">Compliance</th>
              <th className="px-3 py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>{renderRows(tree, 0)}</tbody>
        </table>
        {!items.length && !loading ? (
          <p className="p-4 text-sm text-gray-500">Nenhuma categoria. Execute o seed do order_pickup ou crie manualmente.</p>
        ) : null}
      </div>

      {form ? (
        <form
          onSubmit={(e) => void onSubmit(e)}
          className="mt-6 max-w-lg space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-slate-700 dark:bg-slate-800/50"
        >
          <h2 className="font-semibold">{editId ? `Editar ${editId}` : 'Nova categoria'}</h2>
          {!editId ? (
            <label className="block text-sm">
              ID
              <input className={inp} required value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} />
            </label>
          ) : null}
          <label className="block text-sm">
            Nome
            <input className={inp} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label className="block text-sm">
            Categoria pai
            <input
              className={inp}
              value={form.parent_category}
              onChange={(e) => setForm({ ...form, parent_category: e.target.value })}
              placeholder="opcional"
            />
          </label>
          <label className="block text-sm">
            Descrição
            <textarea
              className={inp}
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm">
              Zona térmica
              <select
                className={inp}
                value={form.temperature_zone}
                onChange={(e) => setForm({ ...form, temperature_zone: e.target.value })}
              >
                {['AMBIENT', 'REFRIGERATED', 'FROZEN'].map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Segurança
              <select
                className={inp}
                value={form.security_level}
                onChange={(e) => setForm({ ...form, security_level: e.target.value })}
              >
                {['STANDARD', 'ENHANCED', 'HIGH', 'VAULT'].map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_hazardous}
              onChange={(e) => setForm({ ...form, is_hazardous: e.target.checked })}
            />
            Perigoso (hazardous)
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.requires_age_verification}
              onChange={(e) => setForm({ ...form, requires_age_verification: e.target.checked })}
            />
            Verificação de idade
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.requires_id} onChange={(e) => setForm({ ...form, requires_id: e.target.checked })} />
            Exige documento
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.requires_signature}
              onChange={(e) => setForm({ ...form, requires_signature: e.target.checked })}
            />
            Exige assinatura
          </label>
          <label className="block text-sm">
            Peso máx. (g)
            <input
              className={inp}
              type="number"
              min={0}
              value={form.max_weight_g}
              onChange={(e) => setForm({ ...form, max_weight_g: e.target.value })}
            />
          </label>
          <div className="flex gap-2">
            <button type="submit" disabled={loading} className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white">
              Salvar
            </button>
            <button type="button" onClick={() => setForm(null)} className="ellan-btn-outline">
              Cancelar
            </button>
          </div>
        </form>
      ) : null}
    </div>
  )
}
