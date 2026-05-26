import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { orderPickupSubscriptionsApi } from '../../api/orderPickupSubscriptions'

function formatBrl(cents: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

export default function OpsSubscriptionDetail() {
  const { subscriptionId } = useParams<{ subscriptionId: string }>()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!subscriptionId) return
    setLoading(true)
    setError(null)
    try {
      const { data: res } = await orderPickupSubscriptionsApi.subscription360(subscriptionId)
      setData(res as Record<string, unknown>)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar 360°')
    } finally {
      setLoading(false)
    }
  }, [subscriptionId])

  useEffect(() => {
    void load()
  }, [load])

  const sub = data?.subscription as Record<string, unknown> | undefined

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div className="flex items-center gap-3">
        <Link to="/ops/subscriptions/admin?tab=subscriptions" className="text-sm text-indigo-400 hover:underline">
          ← Assinaturas
        </Link>
        <h1 className="text-xl font-semibold text-white">Assinatura 360°</h1>
      </div>
      {loading && <p className="text-slate-400">Carregando…</p>}
      {error && <p className="text-red-300">{error}</p>}
      {sub && (
        <>
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-sm text-slate-300">
            <p>
              <span className="text-slate-500">ID:</span> <code className="text-indigo-300">{String(sub.id)}</code>
            </p>
            <p>
              <span className="text-slate-500">Usuário:</span> {String(sub.user_id ?? '—')} ·{' '}
              <span className="text-slate-500">Plano:</span> {String(sub.plan_type)} ·{' '}
              <span className="text-slate-500">Status:</span> {String(sub.status)}
            </p>
            <p>
              <span className="text-slate-500">Mensal:</span> {formatBrl(Number(sub.monthly_fee_cents))} ·{' '}
              <span className="text-slate-500">Parceiro:</span> {String(sub.partner_code ?? '—')}
            </p>
          </div>
          <Section title="Entitlements do plano" items={(data?.plan_entitlements as unknown[]) ?? []} />
          <Section title="Faturas" items={(data?.invoices as unknown[]) ?? []} />
          <Section title="Eventos" items={(data?.events as unknown[]) ?? []} />
          <Section title="Dunning" items={(data?.dunning_cases as unknown[]) ?? []} />
          <Section title="Uso de benefícios" items={(data?.benefits_usage as unknown[]) ?? []} />
        </>
      )}
    </div>
  )
}

function Section({ title, items }: { title: string; items: unknown[] }) {
  if (!items.length) return null
  return (
    <div className="rounded-xl border border-slate-700 p-4">
      <h2 className="mb-2 text-sm font-medium text-white">{title}</h2>
      <pre className="max-h-48 overflow-auto text-xs text-slate-400">{JSON.stringify(items, null, 2)}</pre>
    </div>
  )
}
