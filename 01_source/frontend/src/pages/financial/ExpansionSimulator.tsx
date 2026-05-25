import { FormEvent, useState } from 'react'
import { financialExecutiveApi, type ExpansionMetric } from '../../api/financialExecutive'

const inp =
  'w-full rounded-lg border border-slate-600/70 bg-slate-900/90 px-3 py-2 text-sm text-slate-100'

export default function ExpansionSimulator() {
  const [targetCity, setTargetCity] = useState('São Paulo')
  const [lockersCount, setLockersCount] = useState(5)
  const [revenuePerLocker, setRevenuePerLocker] = useState(450000)
  const [opexPerLocker, setOpexPerLocker] = useState(120000)
  const [installCost, setInstallCost] = useState(80000)
  const [hardwareCost, setHardwareCost] = useState(350000)
  const [usefulLife, setUsefulLife] = useState(60)
  const [occupancy, setOccupancy] = useState(70)
  const [results, setResults] = useState<ExpansionMetric[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await financialExecutiveApi.simulateExpansion({
        target_city: targetCity,
        lockers_count: lockersCount,
        estimated_monthly_revenue_per_locker_cents: revenuePerLocker,
        estimated_monthly_opex_per_locker_cents: opexPerLocker,
        installation_cost_per_locker_cents: installCost,
        hardware_cost_per_locker_cents: hardwareCost,
        useful_life_months: usefulLife,
        expected_occupancy_rate_pct: occupancy,
      })
      setResults(res.data.items ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha na simulação')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
        <label className="text-sm md:col-span-2">
          <span className="mb-1 block text-slate-400">Cidade alvo</span>
          <input className={inp} value={targetCity} onChange={(e) => setTargetCity(e.target.value)} required />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Lockers ({lockersCount})</span>
          <input
            type="range"
            min={1}
            max={50}
            value={lockersCount}
            onChange={(e) => setLockersCount(Number(e.target.value))}
            className="w-full"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Ocupação esperada ({occupancy}%)</span>
          <input
            type="range"
            min={10}
            max={100}
            value={occupancy}
            onChange={(e) => setOccupancy(Number(e.target.value))}
            className="w-full"
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Receita/mês por locker (centavos)</span>
          <input
            type="number"
            className={inp}
            value={revenuePerLocker}
            onChange={(e) => setRevenuePerLocker(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Opex/mês por locker (centavos)</span>
          <input
            type="number"
            className={inp}
            value={opexPerLocker}
            onChange={(e) => setOpexPerLocker(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Instalação/locker (centavos)</span>
          <input type="number" className={inp} value={installCost} onChange={(e) => setInstallCost(Number(e.target.value))} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Hardware/locker (centavos)</span>
          <input
            type="number"
            className={inp}
            value={hardwareCost}
            onChange={(e) => setHardwareCost(Number(e.target.value))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Vida útil (meses)</span>
          <input type="number" className={inp} value={usefulLife} onChange={(e) => setUsefulLife(Number(e.target.value))} />
        </label>
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {loading ? 'Simulando…' : 'Simular expansão'}
          </button>
        </div>
      </form>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      ) : null}

      {results.length ? (
        <div className="overflow-x-auto rounded-xl border border-slate-600/60">
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead className="bg-slate-900/90 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-3 py-2">Métrica</th>
                <th className="px-3 py-2">Valor</th>
                <th className="px-3 py-2">Descrição</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.scenario_metric} className="border-t border-slate-700/50">
                  <td className="px-3 py-2 font-mono text-xs">{r.scenario_metric}</td>
                  <td className="px-3 py-2 font-semibold">{Number(r.value).toLocaleString('pt-BR')}</td>
                  <td className="px-3 py-2 text-slate-400">{r.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
