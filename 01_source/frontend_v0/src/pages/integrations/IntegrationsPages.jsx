import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useParams } from 'react-router-dom'
import { integrationsApi } from '../../api/integrationsApi'

export function IntegrationsShell() {
  const nav = [
    { to: '/integrations/partners', label: 'Partners' },
    { to: '/integrations/marketplaces', label: 'Marketplaces' },
    { to: '/integrations/carriers', label: 'Carriers' },
    { to: '/integrations/webhooks', label: 'Webhooks' },
  ]
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Integrations</h1>
      <nav className="flex flex-wrap gap-2 text-sm">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 ${isActive ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}

export function PartnersList() {
  const [items, setItems] = useState([])
  const [parentGroup, setParentGroup] = useState('')
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { active: 'true' }
      if (parentGroup) params.parent_group = parentGroup
      const { data } = await integrationsApi.listPartners(params)
      setItems(data.items || [])
    } finally {
      setLoading(false)
    }
  }, [parentGroup])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="space-y-3">
      <select className="rounded border px-2 py-1 text-sm" value={parentGroup} onChange={(e) => setParentGroup(e.target.value)}>
        <option value="">Todos</option>
        <option value="LOCKER_NETWORK">Hardware</option>
        <option value="CARRIER_LAST_MILE">Carriers</option>
        <option value="MARKETPLACE">Marketplaces</option>
        <option value="AGGREGATOR">Aggregators</option>
      </select>
      <button type="button" className="ellan-btn ellan-btn-ghost ml-2" disabled={loading} onClick={load}>
        Atualizar
      </button>
      <table className="min-w-full text-sm border rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left">Código</th>
            <th className="px-3 py-2 text-left">Nome</th>
            <th className="px-3 py-2 text-left">Grupo</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id} className="border-t">
              <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
              <td className="px-3 py-2">{p.name}</td>
              <td className="px-3 py-2">{p.parent_group}</td>
              <td className="px-3 py-2 text-right">
                <Link to={`/integrations/partners/${p.id}`}>Detalhe</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function PartnerDetail() {
  const { partnerId } = useParams()
  const [tab, setTab] = useState('capabilities')
  const [partner, setPartner] = useState(null)
  const [caps, setCaps] = useState([])
  const [health, setHealth] = useState([])

  useEffect(() => {
    if (!partnerId) return
    Promise.all([
      integrationsApi.getPartner(partnerId),
      integrationsApi.listCapabilities(partnerId),
      integrationsApi.getHealth(partnerId),
    ]).then(([p, c, h]) => {
      setPartner(p.data)
      setCaps(c.data.items || [])
      setHealth(h.data.items || [])
    })
  }, [partnerId])

  return (
    <div className="space-y-3">
      <Link to="/integrations/partners">← Partners</Link>
      {partner && (
        <h2 className="text-lg font-semibold">
          {partner.name} ({partner.code})
        </h2>
      )}
      <div className="flex gap-2">
        {['capabilities', 'webhooks', 'health'].map((t) => (
          <button key={t} type="button" className={`px-3 py-1 text-sm rounded ${tab === t ? 'bg-indigo-600 text-white' : 'bg-gray-100'}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'capabilities' &&
        caps.map((c) => (
          <div key={c.id} className="text-sm border rounded px-3 py-2">
            {c.capability_code} · {c.protocol}
          </div>
        ))}
      {tab === 'webhooks' && (
        <button
          type="button"
          className="ellan-btn ellan-btn-primary"
          onClick={() =>
            integrationsApi.testWebhook({ player_code: partner?.code, ecosystem_player_id: partner?.id })
          }
        >
          Test webhook
        </button>
      )}
      {tab === 'health' && (
        <>
          <button type="button" className="ellan-btn ellan-btn-primary" onClick={() => integrationsApi.runHealthCheck(partnerId).then(() => integrationsApi.getHealth(partnerId).then((h) => setHealth(h.data.items || [])))}>
            Health check
          </button>
          <ul className="text-sm">
            {health.map((h, i) => (
              <li key={i}>
                {h.status} {h.latency_ms}ms
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export function MarketplaceConnections() {
  const [items, setItems] = useState([])
  useEffect(() => {
    integrationsApi.listMarketplaceConnections({ active: 'true' }).then((r) => setItems(r.data.items || []))
  }, [])
  return (
    <table className="min-w-full text-sm border rounded-lg">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-3 py-2 text-left">Código</th>
          <th className="px-3 py-2 text-left">Nome</th>
          <th className="px-3 py-2 text-left">País</th>
        </tr>
      </thead>
      <tbody>
        {items.map((m) => (
          <tr key={m.id} className="border-t">
            <td className="px-3 py-2 font-mono text-xs">{m.code}</td>
            <td className="px-3 py-2">{m.name}</td>
            <td className="px-3 py-2">{m.country}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function CarrierRatesManager() {
  const [items, setItems] = useState([])
  useEffect(() => {
    integrationsApi.listCarrierRates({ active: 'true' }).then((r) => setItems(r.data.items || []))
  }, [])
  return (
    <table className="min-w-full text-sm border rounded-lg">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-3 py-2 text-left">Carrier</th>
          <th className="px-3 py-2 text-left">Rota</th>
          <th className="px-3 py-2 text-left">Valor</th>
        </tr>
      </thead>
      <tbody>
        {items.map((r) => (
          <tr key={r.id} className="border-t">
            <td className="px-3 py-2">{r.carrier_code}</td>
            <td className="px-3 py-2">
              {r.origin_zone} → {r.destination_zone}
            </td>
            <td className="px-3 py-2">
              {(r.amount_cents / 100).toFixed(2)} {r.currency}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function WebhooksHub() {
  const [playerCode, setPlayerCode] = useState('MAGALU')
  const [result, setResult] = useState(null)
  return (
    <div className="space-y-3 max-w-lg">
      <input className="w-full border rounded px-2 py-1" value={playerCode} onChange={(e) => setPlayerCode(e.target.value)} />
      <button
        type="button"
        className="ellan-btn ellan-btn-primary"
        onClick={() =>
          integrationsApi.testWebhook({ player_code: playerCode }).then((r) => setResult(JSON.stringify(r.data, null, 2)))
        }
      >
        Testar
      </button>
      {result && <pre className="text-xs bg-gray-900 text-white p-3 rounded overflow-auto">{result}</pre>}
    </div>
  )
}
