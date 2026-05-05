import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../AuthContext'

type PartnerProfile = {
  id?: string
  name?: string
  legal_name?: string
  contact_email?: string
  status?: string
}

export default function Profile() {
  const { auth } = useAuth()
  const [profile, setProfile] = useState<PartnerProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      if (!auth?.partnerId) {
        setLoading(false)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const { data } = await api.get<PartnerProfile>(`/v1/partners/${auth.partnerId}`)
        if (!cancelled) setProfile(data)
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Falha ao carregar perfil')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [auth?.partnerId])

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Perfil do Parceiro</h1>
      {loading && <p className="text-sm text-gray-500 dark:text-slate-400">Carregando...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-sm"><strong>ID:</strong> {profile?.id ?? auth?.partnerId ?? '—'}</p>
        <p className="text-sm"><strong>Nome:</strong> {profile?.name ?? '—'}</p>
        <p className="text-sm"><strong>Razão social:</strong> {profile?.legal_name ?? '—'}</p>
        <p className="text-sm"><strong>E-mail:</strong> {profile?.contact_email ?? '—'}</p>
        <p className="text-sm"><strong>Status:</strong> {profile?.status ?? '—'}</p>
      </div>
    </div>
  )
}

