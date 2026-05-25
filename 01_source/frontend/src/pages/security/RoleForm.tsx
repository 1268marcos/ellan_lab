import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { securityCrudApi } from '../../api/securityCrud'

const ROLE_OPTIONS = ['admin', 'ops', 'finance', 'support', 'partner']

export default function RoleForm() {
  const { roleId } = useParams()
  const [search] = useSearchParams()
  const navigate = useNavigate()
  const isEdit = Boolean(roleId)
  const [form, setForm] = useState({
    user_id: search.get('user_id') ?? '',
    role: 'ops',
    scope_type: 'GLOBAL',
    scope_id: '',
  })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!roleId) return
    void securityCrudApi.getRole(roleId).then(({ data }) => {
      setForm({
        user_id: data.user_id,
        role: data.role,
        scope_type: data.scope_type,
        scope_id: data.scope_id ?? '',
      })
    })
  }, [roleId])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const body = {
        user_id: form.user_id,
        role: form.role,
        scope_type: form.scope_type,
        scope_id: form.scope_id || undefined,
      }
      if (isEdit && roleId) {
        await securityCrudApi.updateRole(roleId, { role: form.role, is_active: true })
        navigate(`/security/roles/${roleId}`)
      } else {
        const { data } = await securityCrudApi.createRole(body)
        navigate(`/security/roles/${data.id}`)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar')
    }
  }

  return (
    <form className="max-w-lg space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <h2 className="text-lg font-medium">{isEdit ? 'Editar papel' : 'Novo papel'}</h2>
      <input
        className="ellan-field w-full"
        placeholder="user_id"
        required
        disabled={isEdit}
        value={form.user_id}
        onChange={(e) => setForm((f) => ({ ...f, user_id: e.target.value }))}
      />
      <select
        className="ellan-field w-full"
        value={form.role}
        onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
      >
        {ROLE_OPTIONS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <input
        className="ellan-field w-full"
        placeholder="scope_type"
        value={form.scope_type}
        onChange={(e) => setForm((f) => ({ ...f, scope_type: e.target.value }))}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" className="ellan-btn ellan-btn-primary">
          Salvar
        </button>
        <Link to="/security/roles" className="ellan-btn ellan-btn-ghost">
          Voltar
        </Link>
      </div>
    </form>
  )
}
