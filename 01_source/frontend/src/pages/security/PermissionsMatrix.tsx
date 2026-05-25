import { FormEvent, useCallback, useEffect, useState } from 'react'
import { securityCrudApi, type PermissionMatrix } from '../../api/securityCrud'

export default function PermissionsMatrix() {
  const [matrix, setMatrix] = useState<PermissionMatrix | null>(null)
  const [groupForm, setGroupForm] = useState({ name: '', description: '' })
  const [permForm, setPermForm] = useState({ group_id: '', object_key: '' })
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const { data } = await securityCrudApi.matrix()
      setMatrix(data)
      if (!permForm.group_id && data.groups[0]) {
        setPermForm((f) => ({ ...f, group_id: data.groups[0].group_id }))
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    }
  }, [permForm.group_id])

  useEffect(() => {
    void load()
  }, [load])

  const onSeed = async () => {
    await securityCrudApi.seed()
    await load()
  }

  const onAddGroup = async (e: FormEvent) => {
    e.preventDefault()
    await securityCrudApi.createGroup(groupForm)
    setGroupForm({ name: '', description: '' })
    await load()
  }

  const onAddPerm = async (e: FormEvent) => {
    e.preventDefault()
    await securityCrudApi.createPermission(permForm)
    setPermForm((f) => ({ ...f, object_key: '' }))
    await load()
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button type="button" className="ellan-btn ellan-btn-ghost" onClick={() => void onSeed()}>
          Seed baseline
        </button>
        <button type="button" className="ellan-btn ellan-btn-ghost" onClick={() => void load()}>
          Atualizar
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <form className="grid gap-2 md:grid-cols-2" onSubmit={(e) => void onAddGroup(e)}>
        <input
          className="ellan-field"
          placeholder="Novo grupo"
          value={groupForm.name}
          onChange={(e) => setGroupForm((f) => ({ ...f, name: e.target.value }))}
        />
        <button type="submit" className="ellan-btn ellan-btn-primary">
          Criar grupo
        </button>
      </form>
      <form className="grid gap-2 md:grid-cols-3" onSubmit={(e) => void onAddPerm(e)}>
        <select
          className="ellan-field"
          value={permForm.group_id}
          onChange={(e) => setPermForm((f) => ({ ...f, group_id: e.target.value }))}
        >
          {(matrix?.groups ?? []).map((g) => (
            <option key={g.group_id} value={g.group_id}>
              {g.group_name}
            </option>
          ))}
        </select>
        <input
          className="ellan-field"
          placeholder="object_key"
          value={permForm.object_key}
          onChange={(e) => setPermForm((f) => ({ ...f, object_key: e.target.value }))}
        />
        <button type="submit" className="ellan-btn ellan-btn-primary">
          Adicionar permissão
        </button>
      </form>
      {(matrix?.groups ?? []).map((g) => (
        <div key={g.group_id} className="rounded-lg border border-gray-200 p-3">
          <h3 className="font-medium">
            {g.group_name}{' '}
            <span className="text-xs text-gray-500">({g.member_user_ids.length} membros)</span>
          </h3>
          <ul className="mt-2 list-disc pl-5 text-sm text-gray-700">
            {g.permissions.map((p) => (
              <li key={p.id}>{p.object_key}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
