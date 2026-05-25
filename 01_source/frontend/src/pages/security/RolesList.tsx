import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { securityCrudApi, type SecurityRole } from '../../api/securityCrud'

export default function RolesList() {
  const [roles, setRoles] = useState<SecurityRole[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const { data } = await securityCrudApi.listRoles()
      setRoles(data.roles ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Link to="/security/roles/new" className="ellan-btn ellan-btn-primary">
          Novo papel
        </Link>
        <Link to="/security/users" className="ellan-btn ellan-btn-ghost">
          Usuários
        </Link>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <table className="min-w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="px-3 py-2">Papel</th>
            <th className="px-3 py-2">User</th>
            <th className="px-3 py-2">Escopo</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {roles.map((r) => (
            <tr key={r.id} className="border-t">
              <td className="px-3 py-2">{r.role}</td>
              <td className="px-3 py-2">{r.user_id}</td>
              <td className="px-3 py-2">{r.scope_type}</td>
              <td className="px-3 py-2">
                <Link to={`/security/roles/${r.id}`} className="text-indigo-600">
                  Detalhe
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
