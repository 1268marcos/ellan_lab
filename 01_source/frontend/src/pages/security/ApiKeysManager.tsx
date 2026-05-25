import { FormEvent, useCallback, useEffect, useState } from 'react'
import { securityCrudApi, type ApiKeyMeta } from '../../api/securityCrud'

export default function ApiKeysManager() {
  const [keys, setKeys] = useState<ApiKeyMeta[]>([])
  const [userId, setUserId] = useState('usr-admin')
  const [rotated, setRotated] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const { data } = await securityCrudApi.listApiKeys()
      setKeys(data.items ?? [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onRotate = async (e: FormEvent) => {
    e.preventDefault()
    setRotated(null)
    try {
      const { data } = await securityCrudApi.rotateApiKey({
        user_id: userId,
        label: 'ops-console',
        scopes: ['ops:read', 'ops:write'],
      })
      setRotated(data.api_key)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na rotação')
    }
  }

  return (
    <div className="space-y-4">
      <form className="flex flex-wrap gap-2 items-end" onSubmit={(e) => void onRotate(e)}>
        <div>
          <label className="text-xs text-gray-500">user_id</label>
          <input className="ellan-field" value={userId} onChange={(e) => setUserId(e.target.value)} />
        </div>
        <button type="submit" className="ellan-btn ellan-btn-primary">
          Rotacionar API key
        </button>
      </form>
      {rotated && (
        <p className="rounded bg-amber-50 border border-amber-200 p-3 text-sm break-all">
          Nova chave (copie agora): <strong>{rotated}</strong>
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <table className="min-w-full text-sm border rounded-lg overflow-hidden">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="px-3 py-2">Prefix</th>
            <th className="px-3 py-2">User</th>
            <th className="px-3 py-2">Scopes</th>
            <th className="px-3 py-2">Revogada</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((k) => (
            <tr key={k.id} className="border-t">
              <td className="px-3 py-2">{k.key_prefix}</td>
              <td className="px-3 py-2">{k.user_id}</td>
              <td className="px-3 py-2">{k.scopes.join(', ')}</td>
              <td className="px-3 py-2">{k.revoked_at ? 'Sim' : 'Não'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
