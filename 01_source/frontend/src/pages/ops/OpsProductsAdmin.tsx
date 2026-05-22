import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  orderPickupProductsApi,
  type CategoryTaxonomy,
  type ProductAttributeDefinition,
  type ProductChannelListing,
} from '../../api/orderPickupProducts'
import OpsProductsCatalog from './OpsProductsCatalog'
import OpsProductCategories from './OpsProductCategories'
import OpsProductsEcosystem from './OpsProductsEcosystem'

type Tab =
  | 'overview'
  | 'ecosystem'
  | 'catalog'
  | 'categories'
  | 'taxonomy'
  | 'channels'
  | 'attributes'
  | 'bundles'
  | 'fiscal'
  | 'inventory'

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Visão geral' },
  { key: 'ecosystem', label: 'Ecossistema mundial' },
  { key: 'catalog', label: 'Catálogo (SKU)' },
  { key: 'categories', label: 'Categorias' },
  { key: 'taxonomy', label: 'Taxonomias globais' },
  { key: 'channels', label: 'Canais / marketplaces' },
  { key: 'attributes', label: 'Atributos' },
  { key: 'bundles', label: 'Bundles' },
  { key: 'fiscal', label: 'Pricing / fiscal' },
  { key: 'inventory', label: 'Estoque & reservas' },
]

const inp =
  'w-full rounded border border-gray-300 bg-white px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100'

function TabButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-3 py-1.5 text-sm ${
        active
          ? 'bg-indigo-600 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-200'
      }`}
    >
      {label}
    </button>
  )
}

function TaxonomyPanel() {
  const [items, setItems] = useState<CategoryTaxonomy[]>([])
  const [schemes, setSchemes] = useState<string[]>(['MERCADO_LIVRE', 'INPOST', 'DHL_PACKSTATION', 'CORREIOS', 'CTT'])
  const [form, setForm] = useState({
    category_id: 'ELECTRONICS',
    taxonomy_scheme: 'MERCADO_LIVRE',
    external_code: '',
    external_name: '',
    country_code: 'BR',
  })
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [{ data }, ref] = await Promise.all([
        orderPickupProductsApi.listCategoryTaxonomy(),
        orderPickupProductsApi.getPlayersReference().catch(() => null),
      ])
      setItems(data.items ?? [])
      if (ref?.data?.taxonomy_schemes?.length) {
        setSchemes(ref.data.taxonomy_schemes)
      }
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    try {
      const { data } = await orderPickupProductsApi.seedCatalogProfessional()
      setMsg(
        `Seed mundial: ${data.taxonomy_rows} taxonomias, ${data.channel_rows} canais, ${data.attribute_definitions} attrs` +
          (data.locker_categories_created ? `, ${data.locker_categories_created} cats locker` : ''),
      )
      await load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro no seed')
    }
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await orderPickupProductsApi.createCategoryTaxonomy({ ...form, is_primary: false })
      setMsg('Taxonomia criada.')
      await load()
    } catch (ex: unknown) {
      setErr(ex instanceof Error ? ex.message : 'Erro')
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Mapeamento <code>product_categories</code> → InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT,
        Worten, El Corte Inglés e demais redes ({schemes.length} esquemas).
      </p>
      <div className="flex gap-2">
        <button type="button" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white" onClick={() => void load()}>
          Atualizar
        </button>
        <button type="button" className="rounded border px-3 py-1 text-sm dark:border-slate-600" onClick={() => void onSeed()}>
          Seed profissional
        </button>
      </div>
      {msg ? <p className="text-sm text-emerald-600">{msg}</p> : null}
      {err ? <p className="text-sm text-red-500">{err}</p> : null}
      <form onSubmit={(e) => void onCreate(e)} className="grid max-w-xl gap-2 rounded border p-3 dark:border-slate-700">
        <input className={inp} placeholder="category_id" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} />
        <select
          className={inp}
          value={form.taxonomy_scheme}
          onChange={(e) => setForm({ ...form, taxonomy_scheme: e.target.value })}
        >
          {schemes.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input className={inp} placeholder="external_code" value={form.external_code} onChange={(e) => setForm({ ...form, external_code: e.target.value })} />
        <input className={inp} placeholder="external_name" value={form.external_name} onChange={(e) => setForm({ ...form, external_name: e.target.value })} />
        <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white w-fit">
          Adicionar mapeamento
        </button>
      </form>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-gray-500">
            <th className="p-2">Categoria</th>
            <th className="p-2">Scheme</th>
            <th className="p-2">Código</th>
            <th className="p-2">Nome</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id} className="border-t dark:border-slate-800">
              <td className="p-2 font-mono text-xs">{r.category_id}</td>
              <td className="p-2">{r.taxonomy_scheme}</td>
              <td className="p-2">{r.external_code}</td>
              <td className="p-2">{r.external_name ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ChannelsPanel() {
  const [items, setItems] = useState<ProductChannelListing[]>([])
  const [form, setForm] = useState({
    product_id: '',
    channel_code: 'MERCADO_LIVRE',
    external_sku: '',
    listing_status: 'DRAFT',
  })

  const load = useCallback(async () => {
    const { data } = await orderPickupProductsApi.listChannelListings({ limit: 200 })
    setItems(data.items ?? [])
  }, [])

  useEffect(() => {
    void load().catch(() => setItems([]))
  }, [load])

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    await orderPickupProductsApi.createChannelListing(form)
    await load()
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Listings por canal (Magalu, ML, Amazon Hub, InPost, DPD, Shopee…) — tabela <code>product_channel_listings</code>.
      </p>
      <form onSubmit={(e) => void onCreate(e)} className="grid max-w-xl gap-2 rounded border p-3 dark:border-slate-700">
        <input className={inp} placeholder="product_id (SKU)" required value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })} />
        <input className={inp} placeholder="channel_code" value={form.channel_code} onChange={(e) => setForm({ ...form, channel_code: e.target.value })} />
        <input className={inp} placeholder="external_sku" value={form.external_sku} onChange={(e) => setForm({ ...form, external_sku: e.target.value })} />
        <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white w-fit">
          Criar listing
        </button>
      </form>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-500">
            <th className="p-2 text-left">SKU</th>
            <th className="p-2 text-left">Canal</th>
            <th className="p-2 text-left">SKU externo</th>
            <th className="p-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id} className="border-t dark:border-slate-800">
              <td className="p-2 font-mono text-xs">{r.product_id}</td>
              <td className="p-2">{r.channel_code}</td>
              <td className="p-2">{r.external_sku ?? '—'}</td>
              <td className="p-2">{r.listing_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AttributesPanel() {
  const [defs, setDefs] = useState<ProductAttributeDefinition[]>([])
  const [productId, setProductId] = useState('')
  const [defForm, setDefForm] = useState({
    category_id: 'ELECTRONICS',
    attr_key: '',
    attr_label: '',
    data_type: 'STRING',
  })

  const loadDefs = useCallback(async () => {
    const { data } = await orderPickupProductsApi.listAttributeDefinitions()
    setDefs(data.items ?? [])
  }, [])

  useEffect(() => {
    void loadDefs()
  }, [loadDefs])

  const onCreateDef = async (e: FormEvent) => {
    e.preventDefault()
    await orderPickupProductsApi.createAttributeDefinition(defForm)
    await loadDefs()
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Atributos extensíveis por categoria (marca, tamanho, cor, compliance) — padrão PIM mundial.
      </p>
      <form onSubmit={(e) => void onCreateDef(e)} className="grid max-w-md gap-2 rounded border p-3 dark:border-slate-700">
        <input className={inp} placeholder="category_id" value={defForm.category_id} onChange={(e) => setDefForm({ ...defForm, category_id: e.target.value })} />
        <input className={inp} placeholder="attr_key" value={defForm.attr_key} onChange={(e) => setDefForm({ ...defForm, attr_key: e.target.value })} />
        <input className={inp} placeholder="attr_label" value={defForm.attr_label} onChange={(e) => setDefForm({ ...defForm, attr_label: e.target.value })} />
        <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white w-fit">
          Nova definição
        </button>
      </form>
      <ul className="text-sm">
        {defs.map((d) => (
          <li key={d.id} className="border-b py-1 dark:border-slate-800">
            <code>{d.category_id ?? 'GLOBAL'}</code> · {d.attr_key} — {d.attr_label} ({d.data_type})
            {d.is_required ? ' *' : ''}
          </li>
        ))}
      </ul>
      <p className="text-xs text-gray-500">
        Valores por produto: PUT /catalog-professional/products/{'{product_id}'}/attributes (use API ou expandir UI).
      </p>
      <input className={inp} placeholder="product_id para valores" value={productId} onChange={(e) => setProductId(e.target.value)} />
    </div>
  )
}

function BundlesPanel() {
  const [items, setItems] = useState<{ id: string; name: string; code: string; is_active: boolean }[]>([])
  useEffect(() => {
    void orderPickupProductsApi.listBundles({ limit: 100 }).then((r) => setItems(r.data.items ?? []))
  }, [])
  return (
    <div>
      <p className="mb-2 text-sm text-gray-500">
        Bundles em <code>/products/bundles</code>. Mídia e barcodes:{' '}
        <Link to="/ops/products/assets" className="text-indigo-600 hover:underline">
          página de assets
        </Link>
        .
      </p>
      <ul className="text-sm">
        {items.map((b) => (
          <li key={b.id}>
            {b.code} — {b.name} {b.is_active ? '' : '(inativo)'}
          </li>
        ))}
      </ul>
    </div>
  )
}

function FiscalPanel() {
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null)
  useEffect(() => {
    void orderPickupProductsApi.pricingFiscalOverview().then((r) => setOverview(r.data))
  }, [])
  return (
    <div>
      <p className="mb-2 text-sm text-gray-500">Overview Pr-3 (NCM, bundles, promoções).</p>
      <pre className="max-h-96 overflow-auto rounded bg-gray-900 p-3 text-xs text-gray-100">
        {JSON.stringify(overview, null, 2)}
      </pre>
    </div>
  )
}

function InventoryPanel() {
  const [inv, setInv] = useState<unknown[]>([])
  const [health, setHealth] = useState<unknown>(null)
  useEffect(() => {
    void orderPickupProductsApi.listProductInventory({ limit: 50 }).then((r) => setInv(r.data.items ?? []))
    void orderPickupProductsApi.reservationHealth({ limit: 20 }).then((r) => setHealth(r.data))
  }, [])
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <h3 className="font-semibold text-sm">product_inventory</h3>
        <pre className="mt-2 max-h-64 overflow-auto rounded border p-2 text-xs dark:border-slate-700">
          {JSON.stringify(inv, null, 2)}
        </pre>
      </div>
      <div>
        <h3 className="font-semibold text-sm">Saúde de reservas</h3>
        <pre className="mt-2 max-h-64 overflow-auto rounded border p-2 text-xs dark:border-slate-700">
          {JSON.stringify(health, null, 2)}
        </pre>
      </div>
    </div>
  )
}

export default function OpsProductsAdmin() {
  const [params, setParams] = useSearchParams()
  const tab = (params.get('tab') as Tab) || 'overview'
  const setTab = (key: Tab) => setParams({ tab: key })

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold">Produtos & Catálogo OPS</h1>
      <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
        Domínio marketplace mundial: SKU, categorias, taxonomias, canais, atributos, bundles, fiscal e estoque.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <TabButton key={t.key} active={tab === t.key} label={t.label} onClick={() => setTab(t.key)} />
        ))}
      </div>
      <div className="mt-6">
        {tab === 'overview' && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {TABS.filter((t) => t.key !== 'overview').map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className="rounded-lg border p-4 text-left hover:bg-gray-50 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                <span className="font-medium">{t.label}</span>
              </button>
            ))}
            <Link
              to="/ops/products/assets"
              className="rounded-lg border p-4 hover:bg-gray-50 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              <span className="font-medium">Mídia & barcodes</span>
            </Link>
            <Link
              to="/ops/products/pricing-rules"
              className="rounded-lg border p-4 hover:bg-gray-50 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              <span className="font-medium">Regras de preço (pricing_rules)</span>
            </Link>
          </div>
        )}
        {tab === 'ecosystem' && <OpsProductsEcosystem />}
        {tab === 'catalog' && <OpsProductsCatalog />}
        {tab === 'categories' && <OpsProductCategories />}
        {tab === 'taxonomy' && <TaxonomyPanel />}
        {tab === 'channels' && <ChannelsPanel />}
        {tab === 'attributes' && <AttributesPanel />}
        {tab === 'bundles' && <BundlesPanel />}
        {tab === 'fiscal' && <FiscalPanel />}
        {tab === 'inventory' && <InventoryPanel />}
      </div>
    </div>
  )
}
