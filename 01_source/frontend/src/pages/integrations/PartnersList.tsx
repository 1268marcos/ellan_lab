import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { integrationsApi, type EcosystemPartner } from '../../api/integrationsApi'

const GROUPS = ['', 'LOCKER_NETWORK', 'CARRIER_LAST_MILE', 'MARKETPLACE', 'AGGREGATOR']

export default function PartnersList() {
  const [items, setItems] = useState<EcosystemPartner[]>([])
  const [parentGroup, setParentGroup] = useState('')
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = { active: 'true' }
      if (parentGroup) params.parent_group = parentGroup
      if (q) params.q = q
      const { data } = await integrationsApi.listPartners(params)
      setItems(data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar')
    } finally {
      setLoading(false)
    }
  }, [parentGroup, q])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <select
          className="rounded border border-gray-300 px-2 py-1 text-sm"
          value={parentGroup}
          onChange={(e) => setParentGroup(e.target.value)}
        >
          {GROUPS.map((g) => (
            <option key={g || 'all'} value={g}>
              {g || 'Todos os grupos'}
            </option>
          ))}
        </select>
        <input
          className="rounded border border-gray-300 px-2 py-1 text-sm"
          placeholder="Buscar nome ou código"
          value={q}
          onChange={(e) => setQ(e.target.value)}
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
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Grupo</th>
              <th className="px-3 py-2">País</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
                <td className="px-3 py-2">{p.name}</td>
                <td className="px-3 py-2">{p.parent_group}</td>
                <td className="px-3 py-2">{p.country}</td>
                <td className="px-3 py-2">{p.integration_status || '—'}</td>
                <td className="px-3 py-2 text-right">
                  <Link to={`/integrations/partners/${p.id}`} className="text-indigo-600 hover:underline">
                    Detalhe
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
