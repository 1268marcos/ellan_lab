import { useCallback, useEffect, useState } from 'react'
import { integrationsApi, type MarketplaceConnection } from '../../api/integrationsApi'

export default function MarketplaceConnections() {
  const [items, setItems] = useState<MarketplaceConnection[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await integrationsApi.listMarketplaceConnections({ active: 'true' })
      setItems(data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-3">
      <button type="button" className="ellan-btn ellan-btn-ghost" disabled={loading} onClick={() => void load()}>
        Atualizar
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Marketplace</th>
              <th className="px-3 py-2">País</th>
              <th className="px-3 py-2">Lockers</th>
              <th className="px-3 py-2">Modo</th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => (
              <tr key={m.id} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono text-xs">{m.code}</td>
                <td className="px-3 py-2">{m.name}</td>
                <td className="px-3 py-2">{m.country}</td>
                <td className="px-3 py-2">{m.supports_lockers ? 'Sim' : 'Não'}</td>
                <td className="px-3 py-2">{m.integration_mode || 'DIRECT_API'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
