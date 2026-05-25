import { FormEvent, useCallback, useState } from 'react'
import { partnerAdminApi, type UserRole, type UserSummary } from '../../api/partnerAdmin'

const ROLES = ['admin_operacao', 'suporte', 'auditoria', 'usuario_comum']

export default function OpsUserRoles() {
  const [users, setUsers] = useState<UserSummary[]>([])
  const [roles, setRoles] = useState<UserRole[]>([])
  const [userId, setUserId] = useState('')
  const [role, setRole] = useState('admin_operacao')
  const [scopeType, setScopeType] = useState('GLOBAL')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [u, r] = await Promise.all([
        partnerAdminApi.listUsers(),
        partnerAdminApi.listUserRoles({ active_only: false }),
      ])
      setUsers(u.data.users ?? [])
      setRoles(r.data.roles ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!userId) return
    setLoading(true)
    setError(null)
    try {
      await partnerAdminApi.createUserRole({ user_id: userId, role, scope_type: scopeType })
      setMessage('Role concedida.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao conceder role')
    } finally {
      setLoading(false)
    }
  }

  const onRevoke = async (roleId: string) => {
    setLoading(true)
    try {
      await partnerAdminApi.revokeUserRole(roleId)
      setMessage('Role revogada.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao revogar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Papéis (user_roles)</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Gerenciar associações usuário → role → escopo (GLOBAL, locker, parceiro).
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Atualizar
        </button>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
        <select className="ellan-field" value={userId} onChange={(e) => setUserId(e.target.value)} required>
          <option value="">Usuário</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.email}
            </option>
          ))}
        </select>
        <select className="ellan-field" value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <input className="ellan-field" value={scopeType} onChange={(e) => setScopeType(e.target.value)} placeholder="scope_type" />
        <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
          Conceder role
        </button>
      </form>

      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
          <tr>
            <th className="px-3 py-2">Usuário</th>
            <th className="px-3 py-2">Role</th>
            <th className="px-3 py-2">Escopo</th>
            <th className="px-3 py-2">Ativa</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {roles.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-3 py-6 text-center text-gray-500">
                Nenhuma role (use Seed em Parceiros ou Atualizar)
              </td>
            </tr>
          ) : (
            roles.map((r) => (
              <tr key={r.id} className="border-t dark:border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{r.user_id}</td>
                <td className="px-3 py-2">{r.role}</td>
                <td className="px-3 py-2">
                  {r.scope_type}
                  {r.scope_id ? ` / ${r.scope_id}` : ''}
                </td>
                <td className="px-3 py-2">{r.is_active && !r.revoked_at ? 'sim' : 'não'}</td>
                <td className="px-3 py-2">
                  {r.is_active && !r.revoked_at && (
                    <button type="button" onClick={() => void onRevoke(r.id)} className="text-xs text-red-600">
                      Revogar
                    </button>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
