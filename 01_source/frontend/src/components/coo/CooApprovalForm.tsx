import { useState } from 'react'
import { cooApi } from '../../api/coo'

type Mode = 'sla' | 'expansion'

export function CooApprovalForm({ mode }: { mode: Mode }) {
  const [subject, setSubject] = useState('')
  const [payloadJson, setPayloadJson] = useState('{}')
  const [result, setResult] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    setResult(null)
    let payload: Record<string, unknown> = {}
    try {
      payload = JSON.parse(payloadJson || '{}') as Record<string, unknown>
    } catch {
      setErr('JSON inválido no campo payload')
      return
    }
    setLoading(true)
    try {
      const fn =
        mode === 'sla' ? cooApi.postApprovalSlaAdjust : cooApi.postApprovalExpansion
      const r = await fn({ subject: subject || undefined, payload })
      setResult(JSON.stringify(r.data, null, 2))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erro ao enviar'
      setErr(msg)
    } finally {
      setLoading(false)
    }
  }

  const title = mode === 'sla' ? 'Ajuste de SLA regional' : 'Solicitação de expansão'

  return (
    <form className="coo-card coo-stack max-w-xl" onSubmit={onSubmit}>
      <h2 className="coo-card__title">{title}</h2>
      <label>
        <span className="coo-label">Assunto</span>
        <input
          className="coo-input mt-1"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Opcional"
        />
      </label>
      <label>
        <span className="coo-label">Payload (JSON)</span>
        <textarea
          className="coo-textarea mt-1 font-mono text-xs"
          rows={6}
          value={payloadJson}
          onChange={(e) => setPayloadJson(e.target.value)}
        />
      </label>
      <button type="submit" disabled={loading} className="coo-btn-primary w-fit">
        {loading ? 'Enviando…' : 'Enviar'}
      </button>
      {err && <p className="coo-text-error">{err}</p>}
      {result && <pre className="coo-pre text-xs">{result}</pre>}
    </form>
  )
}
