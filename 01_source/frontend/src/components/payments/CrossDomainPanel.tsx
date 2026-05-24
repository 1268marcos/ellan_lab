import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  paymentsAdminApi,
  type DomainGap,
  type PaymentDomainObligation,
  type PaymentDomainRegistry,
  type PaymentExternalReference,
  type PaymentOrder360,
} from '../../api/paymentsAdmin'

type Props = {
  orderFilter: string
  onMessage: (msg: string) => void
  onError: (msg: string) => void
}

export default function CrossDomainPanel({ orderFilter, onMessage, onError }: Props) {
  const [registry, setRegistry] = useState<PaymentDomainRegistry[]>([])
  const [refs, setRefs] = useState<PaymentExternalReference[]>([])
  const [obligations, setObligations] = useState<PaymentDomainObligation[]>([])
  const [gaps, setGaps] = useState<DomainGap[]>([])
  const [order360, setOrder360] = useState<PaymentOrder360 | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [reg, g, ob] = await Promise.all([
        paymentsAdminApi.listDomainRegistry(),
        paymentsAdminApi.listCrossDomainGaps(40),
        paymentsAdminApi.listDomainObligations({ status: 'PENDING' }),
      ])
      setRegistry(reg.data.items)
      setGaps(g.data.items)
      setObligations(ob.data.items)

      const oid = orderFilter.trim()
      if (oid) {
        const [r, o360] = await Promise.all([
          paymentsAdminApi.listExternalReferences({ order_id: oid }),
          paymentsAdminApi.order360(oid),
        ])
        setRefs(r.data.items)
        setOrder360(o360.data)
      } else {
        const r = await paymentsAdminApi.listExternalReferences()
        setRefs(r.data.items.slice(0, 50))
        setOrder360(null)
      }
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : 'Falha ao carregar cross-domain')
    } finally {
      setLoading(false)
    }
  }, [orderFilter, onError])

  useEffect(() => {
    void load()
  }, [load])

  const resolveObligation = async (id: string) => {
    try {
      await paymentsAdminApi.updateDomainObligation(id, { status: 'DONE' })
      onMessage('Obrigação resolvida.')
      await load()
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : 'Falha ao resolver obrigação')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => void load()} className="rounded border px-2 py-1 text-xs">
          {loading ? '…' : 'Atualizar hub'}
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border p-3 text-sm">
          <div className="text-gray-500">Domínios integrados</div>
          <div className="text-lg font-semibold">{registry.length}</div>
        </div>
        <div className="rounded-lg border p-3 text-sm">
          <div className="text-gray-500">Gaps detectados</div>
          <div className="text-lg font-semibold text-amber-700">{gaps.length}</div>
        </div>
        <div className="rounded-lg border p-3 text-sm">
          <div className="text-gray-500">Obrigações pendentes</div>
          <div className="text-lg font-semibold">{obligations.length}</div>
        </div>
        <div className="rounded-lg border p-3 text-sm">
          <div className="text-gray-500">Refs (filtro order)</div>
          <div className="text-lg font-semibold">{refs.length}</div>
        </div>
      </div>

      {order360 ? (
        <div className="rounded-lg border p-4 text-sm">
          <h3 className="font-semibold">Visão 360° — {order360.order_id}</h3>
          <p className="mt-1 text-xs text-gray-600">
            {order360.external_refs_total} vínculos · {order360.pending_obligations} obrigações ·{' '}
            {order360.blocking_obligations} bloqueantes · {order360.cross_domain_events_pending} eventos
            pendentes
          </p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {order360.domains.map((d) => (
              <div key={d.domain_code} className="rounded border p-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{d.domain_name}</span>
                  {d.ops_path ? (
                    <Link to={d.ops_path} className="text-xs text-blue-600 underline">
                      OPS →
                    </Link>
                  ) : null}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  {d.references.length} ref · {d.obligations.length} obrigação
                </p>
                <ul className="mt-1 text-xs">
                  {d.references.slice(0, 2).map((r) => (
                    <li key={r.id}>
                      {r.external_entity_type}: {r.external_entity_id}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border p-3">
          <h4 className="text-sm font-semibold">Registry domínios</h4>
          <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto text-xs">
            {registry.map((r) => (
              <li key={r.code} className="flex justify-between gap-2">
                <span>{r.code}</span>
                {r.ops_base_path ? (
                  <Link to={r.ops_base_path} className="text-blue-600 underline">
                    abrir
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border p-3">
          <h4 className="text-sm font-semibold">Gaps cross-domain</h4>
          <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto text-xs">
            {gaps.slice(0, 15).map((g, i) => (
              <li key={`${g.order_id}-${i}`} className={g.severity === 'CRITICAL' ? 'text-red-700' : ''}>
                {g.order_id}: {g.message}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full text-left text-xs">
          <thead className="bg-slate-100 dark:bg-slate-800">
            <tr>
              <th className="px-2 py-1">order</th>
              <th className="px-2 py-1">domínio</th>
              <th className="px-2 py-1">tipo</th>
              <th className="px-2 py-1">externo</th>
            </tr>
          </thead>
          <tbody>
            {refs.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-2 py-1 font-mono">{r.order_id}</td>
                <td className="px-2 py-1">{r.external_domain}</td>
                <td className="px-2 py-1">{r.external_entity_type}</td>
                <td className="px-2 py-1 font-mono">{r.external_entity_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="overflow-x-auto rounded-lg border">
        <table className="min-w-full text-left text-xs">
          <thead className="bg-slate-100 dark:bg-slate-800">
            <tr>
              <th className="px-2 py-1">order</th>
              <th className="px-2 py-1">domínio</th>
              <th className="px-2 py-1">obrigação</th>
              <th className="px-2 py-1">status</th>
              <th className="px-2 py-1">ação</th>
            </tr>
          </thead>
          <tbody>
            {obligations.slice(0, 20).map((o) => (
              <tr key={o.id} className="border-t">
                <td className="px-2 py-1">{o.order_id}</td>
                <td className="px-2 py-1">{o.domain_code}</td>
                <td className="px-2 py-1">
                  {o.obligation_type}
                  {o.blocking_payment ? ' ⛔' : ''}
                </td>
                <td className="px-2 py-1">{o.status}</td>
                <td className="px-2 py-1">
                  {o.status === 'PENDING' ? (
                    <button
                      type="button"
                      className="text-blue-600 underline"
                      onClick={() => void resolveObligation(o.id)}
                    >
                      resolver
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
