import { useState } from 'react'
import { integrationsApi } from '../../api/integrationsApi'

export default function WebhooksHub() {
  const [playerCode, setPlayerCode] = useState('MAGALU')
  const [capability, setCapability] = useState('ORDERS_WEBHOOK')
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function runTest() {
    setError(null)
    setResult(null)
    try {
      const { data } = await integrationsApi.testWebhook({
        player_code: playerCode,
        capability_code: capability,
      })
      setResult(JSON.stringify(data, null, 2))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha no teste')
    }
  }

  return (
    <div className="space-y-3 max-w-xl">
      <p className="text-sm text-gray-600">
        Dispara POST /api/v1/partners/webhook/test com assinatura HMAC-SHA256 (X-Ellan-Signature).
      </p>
      <label className="block text-sm">
        Player code
        <input
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
          value={playerCode}
          onChange={(e) => setPlayerCode(e.target.value)}
        />
      </label>
      <label className="block text-sm">
        Capability
        <input
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
          value={capability}
          onChange={(e) => setCapability(e.target.value)}
        />
      </label>
      <button type="button" className="ellan-btn ellan-btn-primary" onClick={() => void runTest()}>
        Testar webhook
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {result && (
        <pre className="rounded bg-gray-900 text-gray-100 p-3 text-xs overflow-auto">{result}</pre>
      )}
    </div>
  )
}
