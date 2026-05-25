import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { integrationsApi, type EcosystemPartner, type PlayerCapability } from '../../api/integrationsApi'

type Tab = 'capabilities' | 'webhooks' | 'health'

export default function PartnerDetail() {
  const { partnerId = '' } = useParams()
  const [tab, setTab] = useState<Tab>('capabilities')
  const [partner, setPartner] = useState<EcosystemPartner | null>(null)
  const [caps, setCaps] = useState<PlayerCapability[]>([])
  const [health, setHealth] = useState<Array<{ status: string; latency_ms: number; checked_at: string }>>([])
  const [rateLimit, setRateLimit] = useState('120')
  const [webhookResult, setWebhookResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!partnerId) return
    setLoading(true)
    setError(null)
    try {
      const [pRes, cRes, hRes] = await Promise.all([
        integrationsApi.getPartner(partnerId),
        integrationsApi.listCapabilities(partnerId),
        integrationsApi.getHealth(partnerId),
      ])
      setPartner(pRes.data)
      setCaps(cRes.data.items ?? [])
      setHealth(hRes.data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  async function runHealth() {
    try {
      await integrationsApi.runHealthCheck(partnerId)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Health falhou')
    }
  }

  async function saveRateLimit() {
    await integrationsApi.updateRateLimit(partnerId, Number(rateLimit))
  }

  async function testWebhook() {
    setWebhookResult(null)
    const { data } = await integrationsApi.testWebhook({
      player_code: partner?.code,
      ecosystem_player_id: partner?.id,
      capability_code: caps[0]?.capability_code || 'ORDERS_WEBHOOK',
    })
    setWebhookResult(`HTTP ${data.http_status} · assinatura ${data.signature?.slice(0, 24)}…`)
  }

  if (!partner && loading) return <p className="text-sm text-gray-500">Carregando…</p>
  if (!partner) return <p className="text-sm text-red-600">{error || 'Parceiro não encontrado'}</p>

  const tabs: { id: Tab; label: string }[] = [
    { id: 'capabilities', label: 'Capabilities' },
    { id: 'webhooks', label: 'Webhooks' },
    { id: 'health', label: 'Health' },
  ]

  return (
    <div className="space-y-4">
      <Link to="/integrations/partners" className="text-sm text-indigo-600 hover:underline">
        ← Partners
      </Link>
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          {partner.name} <span className="font-mono text-sm text-gray-500">({partner.code})</span>
        </h2>
        <p className="text-sm text-gray-600">
          {partner.parent_group} · {partner.country} · {partner.global_tier}
        </p>
      </div>
      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`px-3 py-2 text-sm ${tab === t.id ? 'border-b-2 border-indigo-600 font-medium text-indigo-700' : 'text-gray-600'}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'capabilities' && (
        <table className="min-w-full text-sm rounded-lg border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left">Capability</th>
              <th className="px-3 py-2 text-left">Protocolo</th>
              <th className="px-3 py-2 text-left">Direção</th>
              <th className="px-3 py-2 text-left">Prod</th>
            </tr>
          </thead>
          <tbody>
            {caps.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="px-3 py-2 font-mono text-xs">{c.capability_code}</td>
                <td className="px-3 py-2">{c.protocol}</td>
                <td className="px-3 py-2">{c.direction}</td>
                <td className="px-3 py-2">{c.production_ready ? 'Sim' : 'Não'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === 'webhooks' && (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">Teste com HMAC-SHA256 (header X-Ellan-Signature).</p>
          <div className="flex flex-wrap gap-2 items-end">
            <label className="text-sm">
              Rate limit / min
              <input
                className="ml-2 rounded border px-2 py-1 w-20"
                value={rateLimit}
                onChange={(e) => setRateLimit(e.target.value)}
              />
            </label>
            <button type="button" className="ellan-btn ellan-btn-ghost" onClick={() => void saveRateLimit()}>
              Salvar limite
            </button>
            <button type="button" className="ellan-btn ellan-btn-primary" onClick={() => void testWebhook()}>
              Enviar webhook.test
            </button>
          </div>
          {webhookResult && <p className="text-sm text-green-700">{webhookResult}</p>}
        </div>
      )}
      {tab === 'health' && (
        <div className="space-y-3">
          <button type="button" className="ellan-btn ellan-btn-primary" onClick={() => void runHealth()}>
            Executar health check
          </button>
          <ul className="text-sm space-y-1">
            {health.map((h, i) => (
              <li key={i} className="rounded bg-gray-50 px-3 py-2">
                {h.status} · {h.latency_ms}ms · {new Date(h.checked_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
