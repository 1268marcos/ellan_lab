import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { securityCrudApi, type SecurityRole } from '../../api/securityCrud'

export default function RoleDetail() {
  const { roleId = '' } = useParams()
  const [role, setRole] = useState<SecurityRole | null>(null)

  useEffect(() => {
    if (!roleId) return
    void securityCrudApi.getRole(roleId).then(({ data }) => setRole(data))
  }, [roleId])

  const onDelete = async () => {
    if (!roleId || !window.confirm('Excluir papel?')) return
    await securityCrudApi.deleteRole(roleId)
    window.location.href = '/security/roles'
  }

  if (!role) return <p className="text-sm text-gray-500">Carregando…</p>

  return (
    <div className="space-y-3 text-sm">
      <div className="flex gap-2">
        <Link to={`/security/roles/${roleId}/edit`} className="ellan-btn ellan-btn-primary">
          Editar
        </Link>
        <button type="button" className="ellan-btn ellan-btn-ghost text-red-600" onClick={() => void onDelete()}>
          Excluir
        </button>
        <Link to={`/security/users/${role.user_id}`} className="ellan-btn ellan-btn-ghost">
          Usuário
        </Link>
      </div>
      <p>
        <strong>Papel:</strong> {role.role}
      </p>
      <p>
        <strong>User:</strong> {role.user_id}
      </p>
      <p>
        <strong>Escopo:</strong> {role.scope_type} {role.scope_id ?? ''}
      </p>
    </div>
  )
}
