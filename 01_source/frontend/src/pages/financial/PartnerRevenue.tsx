import { useCallback, useEffect, useState } from 'react'
import { financialExecutiveApi } from '../../api/financialExecutive'
import { loadAuth } from '../../api/auth'

function brlCents(cents?: number | null) {
  if (cents == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(cents) / 100)
}

export default function PartnerRevenue() {
  const [partnerId, setPartnerId] = useState('')
  const [revenue, setRevenue] = useState<Array<Record<string, unknown>>>([])
  const [settlements, setSettlements] = useState<Array<Record<string, unknown>>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await financialExecutiveApi.partnerRevenue({
        partner_id: partnerId || undefined,
      })
      setRevenue(res.data.revenue ?? [])
      setSettlements(res.data.settlements ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar parceiros')
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  function exportFile(format: 'csv' | 'pdf') {
    const auth = loadAuth()
    const url = financialExecutiveApi.exportUrl(format, 'partner-revenue')
    const headers: Record<string, string> = {}
    if (auth?.apiKey) {
      headers['X-API-Key'] = auth.apiKey
      headers.Authorization = `Bearer ${auth.token || auth.apiKey}`
    }
    fetch(url, { headers })
      .then((r) => r.blob())
      .then((blob) => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `partner-revenue.${format}`
        a.click()
        URL.revokeObjectURL(a.href)
      })
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap gap-2">
        <input
          className="min-w-[200px] flex-1 rounded-lg border border-slate-600/70 bg-slate-900/90 px-3 py-2 text-sm text-slate-100"
          placeholder="Partner ID (opcional)"
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value)}
        />
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Atualizar
        </button>
        <button type="button" onClick={() => exportFile('csv')} className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200">
          CSV
        </button>
        <button type="button" onClick={() => exportFile('pdf')} className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200">
          PDF
        </button>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      ) : null}

      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Receita reconhecida (mensal)</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-600/60">
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead className="bg-slate-900/90 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-3 py-2">Mês</th>
                <th className="px-3 py-2">Parceiro</th>
                <th className="px-3 py-2">Receita</th>
                <th className="px-3 py-2">Diferido</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                    Carregando…
                  </td>
                </tr>
              ) : revenue.length ? (
                revenue.map((r, i) => (
                  <tr key={`${r.month_ref}-${r.partner_id}-${i}`} className="border-t border-slate-700/50">
                    <td className="px-3 py-2">{String(r.month_ref ?? '').slice(0, 10)}</td>
                    <td className="px-3 py-2">{String(r.partner_name ?? r.partner_id)}</td>
                    <td className="px-3 py-2">{brlCents(r.revenue_recognized_cents as number)}</td>
                    <td className="px-3 py-2">{brlCents(r.deferred_amount_cents as number)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                    Sem receita.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Settlements</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-600/60">
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead className="bg-slate-900/90 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-3 py-2">Período</th>
                <th className="px-3 py-2">Parceiro</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Líquido</th>
                <th className="px-3 py-2">Comissão %</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    Carregando…
                  </td>
                </tr>
              ) : settlements.length ? (
                settlements.map((s) => (
                  <tr key={String(s.id)} className="border-t border-slate-700/50">
                    <td className="px-3 py-2">
                      {String(s.period_start ?? '').slice(0, 10)} — {String(s.period_end ?? '').slice(0, 10)}
                    </td>
                    <td className="px-3 py-2">{String(s.partner_name ?? s.partner_id)}</td>
                    <td className="px-3 py-2">{String(s.status)}</td>
                    <td className="px-3 py-2">{brlCents(s.net_amount_cents as number)}</td>
                    <td className="px-3 py-2">{Number(s.revenue_share_pct ?? 0).toFixed(2)}%</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500">
                    Sem settlements.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
