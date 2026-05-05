import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [partnerId, setPartnerId] = useState(import.meta.env.VITE_PARTNER_ID ?? '')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const from = (location.state as { from?: string } | null)?.from

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const user = await login({ partnerId: partnerId.trim(), apiKey: apiKey.trim() })
      const target =
        user.profile === 'admin'
          ? '/dashboard/admin'
          : user.profile === 'ops'
            ? '/dashboard/ops'
            : '/dashboard/partner'
      navigate(from || target, { replace: true })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900/70 p-6">
        <h1 className="text-2xl font-semibold text-white">Login Parceiro</h1>
        <p className="mt-1 text-sm text-slate-400">Autenticação via API key (`X-API-Key`)</p>

        <label className="mt-4 block text-xs text-slate-400">
          partner_id
          <input
            value={partnerId}
            onChange={(e) => setPartnerId(e.target.value)}
            required
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
            placeholder="00000000-0000-0000-0000-000000000001"
          />
        </label>

        <label className="mt-3 block text-xs text-slate-400">
          api_key
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            required
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
            placeholder="pk_live_..."
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="mt-5 w-full rounded bg-emerald-600 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>

        {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
      </form>
    </div>
  )
}
