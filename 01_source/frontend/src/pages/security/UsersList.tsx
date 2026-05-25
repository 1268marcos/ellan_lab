import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { securityCrudApi, type SecurityUser } from '../../api/securityCrud'

export default function UsersList() {
  const [users, setUsers] = useState<SecurityUser[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await securityCrudApi.listUsers()
      setUsers(data.users ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Link to="/security/users/new" className="ellan-btn ellan-btn-primary">
          Novo usuário
        </Link>
        <Link to="/security/roles" className="ellan-btn ellan-btn-ghost">
          Papéis
        </Link>
        <button type="button" className="ellan-btn ellan-btn-ghost" disabled={loading} onClick={() => void load()}>
          Atualizar
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">E-mail</th>
              <th className="px-3 py-2">Ativo</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-gray-100">
                <td className="px-3 py-2">{u.full_name}</td>
                <td className="px-3 py-2">{u.email}</td>
                <td className="px-3 py-2">{u.is_active ? 'Sim' : 'Não'}</td>
                <td className="px-3 py-2 text-right">
                  <Link to={`/security/users/${u.id}`} className="text-indigo-600 hover:underline">
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
