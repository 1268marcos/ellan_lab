import { useCallback, useState } from 'react'
import {
  EmptyState,
  OpsErrorBanner,
  OpsWorkspaceCard,
  formatMoney,
  BTN_GHOST,
  BTN_PRIMARY,
} from '../../components/ops/OpsMarketingUi'
import {
  orderPickupPromotionsApi,
  type PromotionConflict,
  type PromotionMatchItem,
  type PromotionSimulateOut,
} from '../../api/orderPickupPromotions'

const FEATURED = ['INPOST', 'MAGALU', 'MERCADO_LIVRE', 'CORREIOS', 'AMAZON_HUB', 'DHL_PACKSTATION'] as const

const inputCls =
  'w-full rounded-lg border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-slate-100'

type Props = { embedded?: boolean }

export default function OpsPromotionsLabPage({ embedded = false }: Props) {
  const [promoCode, setPromoCode] = useState('MAGALU10')
  const [orderId, setOrderId] = useState('LAB-PREVIEW-001')
  const [totalCents, setTotalCents] = useState('10000')
  const [player, setPlayer] = useState('MAGALU')
  const [country, setCountry] = useState('BR')
  const [simulateResult, setSimulateResult] = useState<PromotionSimulateOut | null>(null)
  const [matchResult, setMatchResult] = useState<{ total: number; items: PromotionMatchItem[] } | null>(null)
  const [conflicts, setConflicts] = useState<{ total: number; items: PromotionConflict[] } | null>(null)
  const [matrix, setMatrix] = useState<{ player_code: string; active_promotions: number }[] | null>(null)
  const [loading, setLoading] = useState('')
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (key: string, fn: () => Promise<void>) => {
    setLoading(key)
    setError(null)
    try {
      await fn()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha na API')
    } finally {
      setLoading('')
    }
  }, [])

  const onSimulate = () =>
    void run('simulate', async () => {
      const { data } = await orderPickupPromotionsApi.simulate({
        promotion_code: promoCode.trim(),
        order_id: orderId.trim(),
        total_amount_cents: Number(totalCents) || 0,
        player_code: player.trim() || null,
        country_code: country.trim() || null,
      })
      setSimulateResult(data)
    })

  const onMatch = () =>
    void run('match', async () => {
      const { data } = await orderPickupPromotionsApi.match({
        total_amount_cents: Number(totalCents) || 0,
        player_code: player.trim() || null,
        country_code: country.trim() || null,
        limit: 15,
      })
      setMatchResult({ total: data.total ?? 0, items: data.items ?? [] })
    })

  const onConflicts = () =>
    void run('conflicts', async () => {
      const { data } = await orderPickupPromotionsApi.conflicts()
      setConflicts({ total: data.total ?? 0, items: data.items ?? [] })
    })

  const onMatrix = () =>
    void run('matrix', async () => {
      const { data } = await orderPickupPromotionsApi.playerMatrix()
      setMatrix(data.items ?? [])
    })

  return (
    <div className={embedded ? 'space-y-4' : 'space-y-4 p-4'}>
      <OpsWorkspaceCard
        title="Laboratório de promoções"
        hint="Simule desconto (dry-run), descubra promoções elegíveis, conflitos de escopo e matriz player — sem gravar resgate."
      >
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
          <label className="text-xs text-slate-400">
            Código promoção
            <input className={inputCls} value={promoCode} onChange={(e) => setPromoCode(e.target.value)} />
          </label>
          <label className="text-xs text-slate-400">
            Pedido
            <input className={inputCls} value={orderId} onChange={(e) => setOrderId(e.target.value)} />
          </label>
          <label className="text-xs text-slate-400">
            Total (centavos)
            <input className={inputCls} value={totalCents} onChange={(e) => setTotalCents(e.target.value)} />
          </label>
          <label className="text-xs text-slate-400">
            Player
            <input className={inputCls} value={player} onChange={(e) => setPlayer(e.target.value)} placeholder="MAGALU" />
          </label>
          <label className="text-xs text-slate-400">
            País
            <input className={inputCls} value={country} onChange={(e) => setCountry(e.target.value)} maxLength={8} />
          </label>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {FEATURED.map((code) => (
            <button
              key={code}
              type="button"
              className={`${BTN_GHOST} text-xs`}
              onClick={() => {
                setPlayer(code)
                if (code.includes('MAGALU')) setPromoCode('MAGALU10')
              }}
            >
              {code}
            </button>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button type="button" className={BTN_PRIMARY} onClick={onSimulate} disabled={!!loading}>
            {loading === 'simulate' ? '…' : 'Simular desconto'}
          </button>
          <button type="button" className={BTN_GHOST} onClick={onMatch} disabled={!!loading}>
            Match elegíveis
          </button>
          <button type="button" className={BTN_GHOST} onClick={onConflicts} disabled={!!loading}>
            Conflitos escopo
          </button>
          <button type="button" className={BTN_GHOST} onClick={onMatrix} disabled={!!loading}>
            Matriz players
          </button>
        </div>
      </OpsWorkspaceCard>

      {error ? <OpsErrorBanner>{error}</OpsErrorBanner> : null}

      {simulateResult ? (
        <OpsWorkspaceCard title="Resultado simulação">
          <p className="text-sm text-slate-300">
            {simulateResult.valid ? (
              <>
                <strong>Válida</strong> — desconto {formatMoney(simulateResult.discount_cents)} · líquido{' '}
                {formatMoney(simulateResult.net_amount_cents)}
              </>
            ) : (
              <>
                <strong>Inválida</strong> — {simulateResult.reason || 'sem motivo'}
              </>
            )}
          </p>
        </OpsWorkspaceCard>
      ) : null}

      {matchResult?.items?.length ? (
        <OpsWorkspaceCard title={`Match (${matchResult.total} promoções)`}>
          <div className="overflow-x-auto rounded-lg border dark:border-slate-700">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-2">Código</th>
                  <th className="px-3 py-2">Elegível</th>
                  <th className="px-3 py-2">Desconto est.</th>
                  <th className="px-3 py-2">Motivo</th>
                </tr>
              </thead>
              <tbody>
                {matchResult.items.map((row) => (
                  <tr key={row.promotion_id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{row.promotion_code}</td>
                    <td className="px-3 py-2">{row.eligible ? 'Sim' : 'Não'}</td>
                    <td className="px-3 py-2">
                      {row.eligible ? formatMoney(row.estimated_discount_cents) : '—'}
                    </td>
                    <td className="px-3 py-2 text-slate-400">{row.reason || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </OpsWorkspaceCard>
      ) : null}

      {conflicts?.items?.length ? (
        <OpsWorkspaceCard title={`Conflitos de escopo (${conflicts.total})`}>
          <ul className="space-y-2 text-sm">
            {conflicts.items.map((c) => (
              <li key={`${c.scope_type}:${c.scope_value}`}>
                <strong>
                  {c.scope_type}={c.scope_value}
                </strong>{' '}
                ({c.promotions_count} promoções) — {c.hint}
                <div className="mt-1 text-xs text-slate-500">
                  {(c.promotions || []).map((p) => p.code).join(', ')}
                </div>
              </li>
            ))}
          </ul>
        </OpsWorkspaceCard>
      ) : null}

      {matrix?.length ? (
        <OpsWorkspaceCard title="Matriz player → promoções ativas">
          <div className="flex flex-wrap gap-2">
            {matrix.map((m) => (
              <span
                key={m.player_code}
                className="rounded-lg border border-blue-500/40 px-2.5 py-1 text-xs text-blue-100"
              >
                {m.player_code}: {m.active_promotions}
              </span>
            ))}
          </div>
        </OpsWorkspaceCard>
      ) : null}

      {!simulateResult && !matchResult?.items?.length && !conflicts?.items?.length && !matrix?.length && !loading ? (
        <EmptyState>Use os botões acima para simular, fazer match ou inspecionar conflitos e matriz.</EmptyState>
      ) : null}
    </div>
  )
}
