import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const PUBLIC_PORTAL_LOGIN =
  import.meta.env.VITE_PUBLIC_PORTAL_URL || 'http://localhost:5174/v0/login'

const PROFILE_HINTS = [
  {
    id: 'admin',
    title: 'Administrador',
    menu: 'Todos os grupos OPS (cadastros, hardware, marketplace, financeiro, etc.)',
  },
  {
    id: 'ops',
    title: 'Operações',
    menu: 'Grupos operacionais (lockers, pagamentos, fiscal OPS, order pickup, ML, …)',
  },
  {
    id: 'partner',
    title: 'Parceiro',
    menu: 'Catálogo, webhooks, wallet, inteligência limitada e runtime',
  },
] as const

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
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8">
      <div className="grid w-full max-w-4xl gap-6 lg:grid-cols-2">
        <form
          onSubmit={onSubmit}
          className="rounded-xl border border-slate-700 bg-slate-900/70 p-6"
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
            Console OPS · v1
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Login parceiro / OPS</h1>
          <p className="mt-1 text-sm text-slate-400">
            Autenticação B2B via <code className="text-slate-300">partner_id</code> +{' '}
            <code className="text-slate-300">api_key</code> (header <code className="text-slate-300">X-API-Key</code>
            ). O menu lateral é montado conforme o perfil retornado pela API.
          </p>

          <label className="mt-4 block text-xs text-slate-400">
            partner_id
            <input
              value={partnerId}
              onChange={(e) => setPartnerId(e.target.value)}
              required
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
              placeholder="ellan-ceo-dev-hub-000000000"
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
            {loading ? 'Entrando...' : 'Entrar no console v1'}
          </button>

          {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
        </form>

        <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-300">
          <h2 className="text-lg font-semibold text-white">Dois portais, dois logins</h2>
          <table className="mt-3 w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400">
                <th className="py-2 pr-2">Portal</th>
                <th className="py-2 pr-2">URL</th>
                <th className="py-2">Credencial</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800">
                <td className="py-2 pr-2 font-medium text-emerald-300">v1 OPS</td>
                <td className="py-2 pr-2">/v1/login</td>
                <td className="py-2">API key + perfil admin/ops/partner</td>
              </tr>
              <tr>
                <td className="py-2 pr-2 font-medium text-sky-300">v0 consumidor</td>
                <td className="py-2 pr-2">/v0/login</td>
                <td className="py-2">Email + senha (JWT público)</td>
              </tr>
            </tbody>
          </table>

          <p className="mt-4 text-slate-400">
            Checkout, catálogo público e política de autorização (roles) ficam no{' '}
            <strong className="text-slate-200">portal v0</strong>.
          </p>

          <a
            href={PUBLIC_PORTAL_LOGIN}
            className="mt-4 inline-block rounded border border-sky-600 px-3 py-2 text-sky-300 hover:bg-sky-950"
          >
            Ir para login consumidor (v0)
          </a>

          <h3 className="mt-6 text-sm font-semibold text-white">Menu após login v1</h3>
          <ul className="mt-2 space-y-2">
            {PROFILE_HINTS.map((row) => (
              <li key={row.id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                <p className="font-medium text-slate-100">{row.title}</p>
                <p className="mt-1 text-xs text-slate-400">{row.menu}</p>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  )
}
