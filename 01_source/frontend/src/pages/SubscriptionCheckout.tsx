import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { publicSubscriptionsApi, type PublicPlan, type PromoValidation } from '../api/publicSubscriptions'

function formatBrl(cents: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

export default function SubscriptionCheckout() {
  const [plans, setPlans] = useState<PublicPlan[]>([])
  const [planCode, setPlanCode] = useState('PREMIUM')
  const [promoInput, setPromoInput] = useState('')
  const [promoPreview, setPromoPreview] = useState<PromoValidation | null>(null)
  const [hasSubscription, setHasSubscription] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const selectedPlan = plans.find((p) => p.code === planCode)
  const baseFee = selectedPlan?.monthly_fee_cents ?? 0
  const discount = promoPreview?.valid ? promoPreview.discount_cents ?? 0 : 0
  const finalFee = Math.max(0, baseFee - discount)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [my, catalog] = await Promise.all([
        publicSubscriptionsApi.my(),
        publicSubscriptionsApi.listPlans(),
      ])
      setHasSubscription(my.data.has_subscription)
      const items = catalog.data.items ?? []
      setPlans(items)
      if (items.length && !items.some((p) => p.code === planCode)) {
        setPlanCode(items[0].code)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar planos')
    } finally {
      setLoading(false)
    }
  }, [planCode])

  useEffect(() => {
    void load()
  }, [load])

  const onValidatePromo = async () => {
    if (!promoInput.trim()) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await publicSubscriptionsApi.validatePromo(promoInput.trim(), planCode)
      setPromoPreview(data)
      if (!data.valid) {
        setError(data.reason ?? 'Cupom inválido')
      }
    } catch (err: unknown) {
      setPromoPreview(null)
      setError(err instanceof Error ? err.message : 'Falha ao validar cupom')
    } finally {
      setLoading(false)
    }
  }

  const onSubscribe = async (e: FormEvent) => {
    e.preventDefault()
    if (hasSubscription) return
    setLoading(true)
    setError(null)
    setMessage(null)
    try {
      const { data } = await publicSubscriptionsApi.subscribe({
        plan_code: planCode,
        promo_code: promoPreview?.valid ? promoInput.trim().toUpperCase() : undefined,
      })
      setHasSubscription(true)
      const promo = data.promo_applied
      setMessage(
        promo
          ? `Assinatura ${data.subscription.plan_type} ativa. Cupom ${promo.promo_code}: −${formatBrl(promo.discount_cents)}.`
          : `Assinatura ${data.subscription.plan_type} ativa.`
      )
      await load()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: { message?: string; type?: string } } } }
      const detail = ax.response?.data?.detail
      setError(
        typeof detail === 'object' && detail?.message
          ? `${detail.type ?? 'Erro'}: ${detail.message}`
          : err instanceof Error
            ? err.message
            : 'Falha ao assinar'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-lg p-6 text-slate-200">
      <p className="mb-4 text-sm text-slate-400">
        <Link to="/" className="text-indigo-400 hover:underline">
          Início
        </Link>
        {' · '}
        Assinatura Ellan
      </p>
      <h1 className="mb-2 text-2xl font-semibold text-white">Assinar plano</h1>
      <p className="mb-6 text-sm text-slate-400">
        Escolha o plano, valide um cupom e confirme. O desconto é aplicado na primeira mensalidade.
      </p>

      {error ? <p className="mb-3 rounded bg-red-950/50 px-3 py-2 text-sm text-red-300">{error}</p> : null}
      {message ? <p className="mb-3 rounded bg-emerald-950/50 px-3 py-2 text-sm text-emerald-300">{message}</p> : null}

      {hasSubscription ? (
        <p className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-sm">
          Você já possui assinatura ativa.{' '}
          <Link to="/ops/subscriptions/admin" className="text-indigo-400 hover:underline">
            Ver no OPS
          </Link>
        </p>
      ) : (
        <form onSubmit={onSubscribe} className="space-y-4 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
          <label className="block text-xs text-slate-400">
            Plano
            <select
              value={planCode}
              onChange={(e) => {
                setPlanCode(e.target.value)
                setPromoPreview(null)
              }}
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
            >
              {plans.map((p) => (
                <option key={p.code} value={p.code}>
                  {p.name} — {formatBrl(p.monthly_fee_cents)}/mês
                </option>
              ))}
            </select>
          </label>

          <div className="flex flex-wrap items-end gap-2">
            <label className="flex-1 text-xs text-slate-400">
              Cupom promocional
              <input
                value={promoInput}
                onChange={(e) => setPromoInput(e.target.value.toUpperCase())}
                placeholder="WELCOME20"
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
              />
            </label>
            <button
              type="button"
              disabled={loading || !promoInput.trim()}
              onClick={() => void onValidatePromo()}
              className="rounded border border-violet-600 px-3 py-2 text-sm text-violet-200 hover:bg-violet-950"
            >
              Validar
            </button>
          </div>

          {promoPreview?.valid ? (
            <p className="text-xs text-violet-300">
              Cupom válido: −{formatBrl(promoPreview.discount_cents ?? 0)}
              {promoPreview.bonus_months ? ` · +${promoPreview.bonus_months} mês(es) bônus` : ''}
            </p>
          ) : null}

          <div className="rounded-lg border border-slate-700 bg-slate-950/80 p-3 text-sm">
            <div className="flex justify-between text-slate-400">
              <span>Valor do plano</span>
              <span>{formatBrl(baseFee)}</span>
            </div>
            {discount > 0 ? (
              <div className="flex justify-between text-violet-300">
                <span>Desconto cupom</span>
                <span>−{formatBrl(discount)}</span>
              </div>
            ) : null}
            <div className="mt-2 flex justify-between font-semibold text-white">
              <span>Primeira cobrança</span>
              <span>{formatBrl(finalFee)}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            Confirmar assinatura
          </button>
        </form>
      )}
    </div>
  )
}
