import { useCallback, useEffect, useState } from 'react'
import { integrationsApi, type CarrierRate } from '../../api/integrationsApi'

export default function CarrierRatesManager() {
  const [items, setItems] = useState<CarrierRate[]>([])
  const [carrierCode, setCarrierCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = { active: 'true' }
      if (carrierCode) params.carrier_code = carrierCode
      const { data } = await integrationsApi.listCarrierRates(params)
      setItems(data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }, [carrierCode])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <input
          className="rounded border border-gray-300 px-2 py-1 text-sm"
          placeholder="Carrier code (ex. DHL)"
          value={carrierCode}
          onChange={(e) => setCarrierCode(e.target.value.toUpperCase())}
        />
        <button type="button" className="ellan-btn ellan-btn-ghost" disabled={loading} onClick={() => void load()}>
          Atualizar
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-3 py-2">Carrier</th>
              <th className="px-3 py-2">Origem</th>
              <th className="px-3 py-2">Destino</th>
              <th className="px-3 py-2">Peso (g)</th>
              <th className="px-3 py-2">Valor</th>
              <th className="px-3 py-2">Válido desde</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono text-xs">{r.carrier_code}</td>
                <td className="px-3 py-2">{r.origin_zone}</td>
                <td className="px-3 py-2">{r.destination_zone}</td>
                <td className="px-3 py-2">{r.weight_tier_g}</td>
                <td className="px-3 py-2">
                  {(r.amount_cents / 100).toFixed(2)} {r.currency}
                </td>
                <td className="px-3 py-2">{r.valid_from}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
