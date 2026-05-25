import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { securityCrudApi } from '../../api/securityCrud'

export default function UserForm() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(userId)
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', is_active: true })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    void securityCrudApi.getUser(userId).then(({ data }) => {
      setForm({
        full_name: data.full_name,
        email: data.email,
        phone: data.phone ?? '',
        is_active: data.is_active,
      })
    })
  }, [userId])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      if (isEdit && userId) {
        await securityCrudApi.updateUser(userId, form)
        navigate(`/security/users/${userId}`)
      } else {
        const { data } = await securityCrudApi.createUser(form)
        navigate(`/security/users/${data.id}`)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="max-w-lg space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <h2 className="text-lg font-medium">{isEdit ? 'Editar usuário' : 'Novo usuário'}</h2>
      <input
        className="ellan-field w-full"
        placeholder="Nome"
        required
        value={form.full_name}
        onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
      />
      <input
        className="ellan-field w-full"
        placeholder="E-mail"
        type="email"
        required
        value={form.email}
        onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
      />
      <input
        className="ellan-field w-full"
        placeholder="Telefone"
        value={form.phone}
        onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
      />
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
        />
        Ativo
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" className="ellan-btn ellan-btn-primary" disabled={loading}>
          Salvar
        </button>
        <Link to="/security/users" className="ellan-btn ellan-btn-ghost">
          Voltar
        </Link>
      </div>
    </form>
  )
}
