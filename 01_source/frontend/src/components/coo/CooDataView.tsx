import { useEffect, useState } from 'react'
import { cooApi } from '../../api/coo'

type Props = {
  title: string
  /** Caminho após `/v1/coo/` (ex: `dashboard/consolidated`) */
  endpoint: string
  query?: Record<string, string | number | undefined>
}

function stableQueryKey(q?: Record<string, string | number | undefined>) {
  if (!q || Object.keys(q).length === 0) return ''
  return Object.keys(q)
    .sort()
    .map((k) => `${k}=${q[k] ?? ''}`)
    .join('&')
}

export function CooDataView({ title, endpoint, query }: Props) {
  const [data, setData] = useState<unknown>(null)
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const qKey = stableQueryKey(query)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErr(null)
    cooApi
      .getJson(endpoint, query)
      .then((r) => {
        if (!cancelled) setData(r.data)
      })
      .catch((e: Error) => {
        if (!cancelled) setErr(e.message || 'Falha ao carregar')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [endpoint, qKey])

  return (
    <div className="coo-card coo-stack">
      <h2 className="coo-card__title">{title}</h2>
      {loading && <p className="coo-text-muted">Carregando…</p>}
      {err && <p className="coo-text-error">{err}</p>}
      {!loading && !err && (
        <pre className="coo-pre">{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  )
}
