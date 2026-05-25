import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { securityCrudApi, type SecurityRole, type SecurityUser } from '../../api/securityCrud'

export default function UserDetail() {
  const { userId = '' } = useParams()
  const [user, setUser] = useState<SecurityUser | null>(null)
  const [roles, setRoles] = useState<SecurityRole[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!userId) return
    setError(null)
    try {
      const [u, r] = await Promise.all([
        securityCrudApi.getUser(userId),
        securityCrudApi.listRoles(userId),
      ])
      setUser(u.data)
      setRoles(r.data.roles ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    }
  }, [userId])

  useEffect(() => {
    void load()
  }, [load])

  const onDelete = async () => {
    if (!userId || !window.confirm('Excluir usuário?')) return
    await securityCrudApi.deleteUser(userId)
    window.location.href = '/security/users'
  }

  if (!user) return <p className="text-sm text-gray-500">{error ?? 'Carregando…'}</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Link to={`/security/users/${userId}/edit`} className="ellan-btn ellan-btn-primary">
          Editar
        </Link>
        <button type="button" className="ellan-btn ellan-btn-ghost text-red-600" onClick={() => void onDelete()}>
          Excluir
        </button>
        <Link to="/security/users" className="ellan-btn ellan-btn-ghost">
          Lista
        </Link>
      </div>
      <dl className="grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-gray-500">ID</dt>
          <dd>{user.id}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Nome</dt>
          <dd>{user.full_name}</dd>
        </div>
        <div>
          <dt className="text-gray-500">E-mail</dt>
          <dd>{user.email}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Ativo</dt>
          <dd>{user.is_active ? 'Sim' : 'Não'}</dd>
        </div>
      </dl>
      <section>
        <h3 className="mb-2 font-medium">Papéis</h3>
        <ul className="list-disc pl-5 text-sm">
          {roles.map((r) => (
            <li key={r.id}>
              <Link to={`/security/roles/${r.id}`} className="text-indigo-600 hover:underline">
                {r.role}
              </Link>{' '}
              ({r.scope_type})
            </li>
          ))}
        </ul>
        <Link to={`/security/roles/new?user_id=${userId}`} className="mt-2 inline-block text-sm text-indigo-600">
          + papel
        </Link>
      </section>
    </div>
  )
}
