import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { orderPickupProductsApi } from '../../api/orderPickupProducts'

const TYPE_LABELS: Record<string, string> = {
  LOCKER_NETWORK: 'Rede locker',
  MARKETPLACE: 'Marketplace',
  CARRIER: 'Carrier',
  POSTAL: 'Postal',
  FOOD_DELIVERY: 'Food delivery',
}

export default function OpsProductsEcosystem() {
  const [overview, setOverview] = useState<Awaited<ReturnType<typeof orderPickupProductsApi.getEcosystemOverview>>['data'] | null>(null)
  const [players, setPlayers] = useState<Awaited<ReturnType<typeof orderPickupProductsApi.listGlobalPlayers>>['data']['items']>([])
  const [eligibility, setEligibility] = useState<
    Awaited<ReturnType<typeof orderPickupProductsApi.listCategoryEligibility>>['data']['items']
  >([])
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [form, setForm] = useState({
    category_id: 'LOCKER_PARCEL',
    player_code: 'INPOST',
    eligibility: 'PREFERRED',
  })

  const load = useCallback(async () => {
    try {
      const [ov, pl, el] = await Promise.all([
        orderPickupProductsApi.getEcosystemOverview(),
        orderPickupProductsApi.listGlobalPlayers({ limit: 200 }),
        orderPickupProductsApi.listCategoryEligibility(),
      ])
      setOverview(ov.data)
      setPlayers(pl.data.items ?? [])
      setEligibility(el.data.items ?? [])
      setErr(null)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro ao carregar ecossistema')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    try {
      const { data } = await orderPickupProductsApi.seedGlobalPlayers()
      setMsg(
        `Seed: ${data.players} players, ${data.operators_created} operadores, ${data.ecommerce_links + data.logistics_links} ligações`,
      )
      await load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro no seed')
    }
  }

  const onSync = async () => {
    try {
      const { data } = await orderPickupProductsApi.syncGlobalPlayersPartners()
      setMsg(`Sync: ${JSON.stringify(data)}`)
      await load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro no sync')
    }
  }

  const onElig = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await orderPickupProductsApi.createCategoryEligibility(form)
      setMsg('Elegibilidade criada.')
      await load()
    } catch (ex: unknown) {
      setErr(ex instanceof Error ? ex.message : 'Erro')
    }
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500">
        Hub mundial: players InPost, ML, Amazon, food delivery, PUDO e ligações com{' '}
        <code>ecommerce_partners</code> / <code>logistics_partners</code>. Detalhe PIM em{' '}
        <Link to="/ops/products/admin?tab=taxonomy" className="text-indigo-600 hover:underline">
          taxonomias
        </Link>
        .
      </p>
      {msg ? <p className="text-sm text-emerald-600">{msg}</p> : null}
      {err ? <p className="text-sm text-red-500">{err}</p> : null}

      {overview ? (
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Kpi label="Players" value={overview.players_total} />
          <Kpi label="Locker-ready" value={overview.players_locker_ready} />
          <Kpi label="Taxonomias" value={overview.taxonomy_mappings} />
          <Kpi label="Listings" value={overview.channel_listings} />
          <Kpi label="Elegibilidade" value={overview.eligibility_rules} />
          <Kpi label="Integrações" value={overview.integration_targets} />
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button type="button" className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white" onClick={() => void load()}>
          Atualizar
        </button>
        <button type="button" className="ellan-btn-outline" onClick={() => void onSeed()}>
          Seed global players
        </button>
        <button type="button" className="ellan-btn-outline" onClick={() => void onSync()}>
          Sync parceiros B2B
        </button>
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold">Players ({players.length})</h2>
        <div className="max-h-64 overflow-auto rounded border dark:border-slate-700">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="p-2 text-left">Código</th>
                <th className="p-2 text-left">Nome</th>
                <th className="p-2 text-left">Tipo</th>
                <th className="p-2 text-left">Operador</th>
              </tr>
            </thead>
            <tbody>
              {players.slice(0, 40).map((p) => (
                <tr key={p.code} className="border-t dark:border-slate-700">
                  <td className="p-2 font-mono text-xs">{p.code}</td>
                  <td className="p-2">{p.name}</td>
                  <td className="p-2">{TYPE_LABELS[p.player_type] || p.player_type}</td>
                  <td className="p-2 font-mono text-xs">{p.operator_id || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold">Nova elegibilidade categoria × player</h2>
        <form onSubmit={(e) => void onElig(e)} className="flex flex-wrap gap-2 items-end">
          <input
            className="ellan-field dark:border-slate-600 dark:bg-slate-900"
            placeholder="category_id"
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          />
          <input
            className="ellan-field dark:border-slate-600 dark:bg-slate-900"
            placeholder="player_code"
            value={form.player_code}
            onChange={(e) => setForm({ ...form, player_code: e.target.value })}
          />
          <select
            className="ellan-field dark:border-slate-600 dark:bg-slate-900"
            value={form.eligibility}
            onChange={(e) => setForm({ ...form, eligibility: e.target.value })}
          >
            <option value="PREFERRED">PREFERRED</option>
            <option value="ALLOWED">ALLOWED</option>
            <option value="RESTRICTED">RESTRICTED</option>
          </select>
          <button type="submit" className="rounded bg-indigo-600 px-3 py-1 text-sm text-white">
            Adicionar
          </button>
        </form>
        <ul className="mt-3 text-sm space-y-1">
          {eligibility.map((row) => (
            <li key={row.id}>
              <code>{row.category_id}</code> + <code>{row.player_code}</code> → {row.eligibility}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border p-3 dark:border-slate-700">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  )
}
