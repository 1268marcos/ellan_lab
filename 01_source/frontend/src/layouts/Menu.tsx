import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

type Group = {
  key: string
  icon: string
  label: string
  items: Array<{ to: string; label: string; newTag?: string }>
}

const groups: Group[] = [
  {
    key: 'ops',
    icon: '🛠️',
    label: 'OPS',
    items: [
      { to: '/dashboard', label: 'Dashboard' },
      { to: '/ops/lockers', label: 'Lockers' },
      { to: '/ops/lockers/create', label: 'Criar lockers' },
      { to: '/ops/manifests', label: 'Manifestos' },
    ],
  },
  {
    key: 'cadastros',
    icon: '📋',
    label: 'Cadastros OPS',
    items: [
      { to: '/ops/access/user-roles', label: 'Papéis de acesso (user_roles)' },
      { to: '/ops/payment-gateway/admin', label: 'Payment Gateway (PSP)' },
    ],
  },
  {
    key: 'orderPickup',
    icon: '📦',
    label: 'Order Pickup OPS',
    items: [
      { to: '/ops/order-pickup/admin', label: 'Cadastro (pedidos / integração)' },
    ],
  },
  {
    key: 'mlOps',
    icon: '🤖',
    label: 'ML OPS',
    items: [
      { to: '/ops/ml/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/ml/admin?tab=partners', label: 'Parceiros de dados ML' },
      { to: '/ops/ml/admin?tab=networks', label: 'Redes locker mundiais' },
      { to: '/ops/ml/admin?tab=models', label: 'Modelos e versões' },
      { to: '/ops/ml/admin?tab=features', label: 'Features diárias' },
      { to: '/ops/ml/admin?tab=predictions', label: 'Log de predições' },
      { to: '/ops/ml/admin?tab=feedback', label: 'Feedback de modelo' },
      { to: '/ops/ml/admin?tab=use_cases', label: 'Casos de uso' },
      { to: '/ops/ml/admin?tab=registry', label: 'Model registry' },
      { to: '/ops/ml/admin?tab=training', label: 'Experimentos' },
      { to: '/ops/ml/admin?tab=catalog', label: 'Catálogo features' },
      { to: '/ops/ml/admin?tab=drift', label: 'Drift / PSI' },
      { to: '/ops/ml/admin?tab=governance', label: 'SLO e alertas' },
      { to: '/ops/ml/admin?tab=deployments', label: 'Deployments' },
    ],
  },
  {
    key: 'partnersOps',
    icon: '🤝',
    label: 'Partners OPS',
    items: [
      { to: '/ops/partners/admin', label: 'Visão 360', newTag: 'New1' },
      { to: '/ops/partners/admin?tab=onboarding', label: 'Onboarding B2B', newTag: 'New2' },
      { to: '/ops/partners/admin?tab=ecommerce', label: 'E-commerce' },
      { to: '/ops/partners/admin?tab=logistics', label: 'Logística' },
      { to: '/ops/partners/admin?tab=integrations', label: 'Webhook e API keys' },
      { to: '/ops/partners/admin?tab=webhook_monitor', label: 'Entregas webhook', newTag: 'New3' },
      { to: '/ops/partners/admin?tab=integration_health', label: 'Saúde integração', newTag: 'New4' },
      { to: '/ops/partners/admin?tab=outbox', label: 'Outbox eventos', newTag: 'New5' },
      { to: '/ops/partners/admin?tab=settlements', label: 'Settlements', newTag: 'New6' },
      { to: '/ops/partners/admin?tab=billing', label: 'Billing e line items', newTag: 'New7' },
      { to: '/ops/partners/admin?tab=invoices', label: 'NF B2B', newTag: 'New8' },
      { to: '/ops/partners/admin?tab=credits', label: 'Créditos', newTag: 'New9' },
      { to: '/ops/partners/admin?tab=holds', label: 'Retenções pagamento', newTag: 'New10' },
      { to: '/ops/partners/admin?tab=sla', label: 'SLA', newTag: 'New11' },
      { to: '/ops/partners/admin?tab=status', label: 'Histórico status', newTag: 'New12' },
      { to: '/ops/partners/admin?tab=stores', label: 'Lojas C&C' },
      {
        to: '/ops/partners/admin?tab=ecosystem',
        label: 'Redes mundiais (InPost, DHL…)',
        newTag: 'New13',
      },
      {
        to: '/ops/partners/admin?tab=global_ops',
        label: 'Global OPS (corredores · SLA · certificações)',
        newTag: 'New14',
      },
      {
        to: '/ops/partners/admin?tab=capability_webhooks',
        label: 'Webhooks capability + dead-letter',
        newTag: 'New15',
      },
      { to: '/ops/partners/admin?tab=contacts', label: 'Contatos B2B' },
      { to: '/ops/tenants/admin', label: 'Tenants (white label)' },
      { to: '/ops/partners/dashboard', label: 'Dashboard OPS (v0)' },
      { to: '/ops/partners/settlement', label: 'Settlement export (v0)' },
    ],
  },
  {
    key: 'marketplace',
    icon: '🏪',
    label: 'Marketplace OPS',
    items: [
      { to: '/ops/marketplace/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/marketplace/admin?tab=sellers', label: 'Sellers' },
      { to: '/ops/marketplace/admin?tab=channels', label: 'Canais e redes (InPost, ML…)' },
      {
        to: '/ops/marketplace/admin?tab=readiness',
        label: 'Prontidão integração + Global OPS',
        newTag: 'New1',
      },
      { to: '/ops/marketplace/admin?tab=settlements', label: 'Repasses e liquidação' },
      { to: '/ops/marketplace/admin?tab=kyc', label: 'KYC / compliance' },
      { to: '/ops/marketplace/admin?tab=disputes', label: 'Disputas comissão' },
      { to: '/ops/marketplace/admin?tab=commissions', label: 'Comissões' },
    ],
  },
  {
    key: 'lifecycle',
    icon: '♻️',
    label: 'Ciclo de Vida',
    items: [
      { to: '/lifecycle/metrics', label: 'Métricas' },
      { to: '/lifecycle/ranking', label: 'Ranking' },
      { to: '/lifecycle/health', label: 'Saúde' },
    ],
  },
  {
    key: 'intelligence',
    icon: '🧠',
    label: 'Inteligência',
    items: [
      { to: '/partners/catalog', label: 'Catálogo' },
      { to: '/partners/webhooks', label: 'Webhooks' },
      { to: '/intelligence/compatibility', label: 'Compatibilidade' },
      { to: '/intelligence/predictive-health', label: 'Saúde preditiva' },
      { to: '/intelligence/occupancy-forecast', label: 'Previsão de ocupação' },
      { to: '/intelligence/feedback-insights', label: 'Insights de feedback' },
    ],
  },
  {
    key: 'runtime',
    icon: '⚙️',
    label: 'Runtime / Operacional',
    items: [
      { to: '/runtime/slots', label: 'Slots e ocupação' },
      { to: '/runtime/allocations', label: 'Alocações' },
    ],
  },
  {
    key: 'operacional',
    icon: '📡',
    label: 'Operacional',
    items: [
      { to: '/partners/ops/lockers', label: 'Lockers' },
      { to: '/partners/ops/pickups', label: 'Pickups ativos' },
    ],
  },
  {
    key: 'fiscal',
    icon: '💼',
    label: 'Fiscal',
    items: [
      { to: '/finance/wallet', label: 'Wallet' },
      { to: '/finance/transactions', label: 'Transações' },
      { to: '/finance/billing/cycles', label: 'Ciclos' },
      { to: '/finance/invoices', label: 'Notas B2B' },
      { to: '/finance/credit-notes', label: 'Créditos' },
      { to: '/finance/disputes', label: 'Disputas' },
      { to: '/fiscal/reconcile', label: 'Reconciliação' },
    ],
  },
]

export default function Menu() {
  const [open, setOpen] = useState<Record<string, boolean>>({
    ops: false,
    cadastros: true,
    partnersOps: true,
    orderPickup: true,
    mlOps: true,
    marketplace: true,
    lifecycle: false,
    intelligence: false,
    runtime: false,
    operacional: false,
    fiscal: false,
  })
  const { auth, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const profile = auth?.profile ?? 'partner'

  const filteredGroups = groups
    .filter((g) => (g.key === 'runtime' ? profile === 'partner' : true))
    .map((g) => {
      if (profile === 'admin') return g
      if (profile === 'partner') {
        if (g.key === 'ops') return { ...g, items: [] }
        if (g.key === 'lifecycle') return g
        if (g.key === 'intelligence') {
          return {
            ...g,
            items: g.items.filter(
              (i) => i.to.startsWith('/partners') || i.to.startsWith('/intelligence/'),
            ),
          }
        }
        if (g.key === 'runtime') return g
        if (g.key === 'fiscal') return { ...g, items: g.items.filter((i) => i.to.startsWith('/finance')) }
      }
      if (profile === 'ops') {
        if (g.key === 'ops') return g
        if (g.key === 'cadastros') return g
        if (g.key === 'partnersOps') return g
        if (g.key === 'orderPickup') return g
        if (g.key === 'mlOps') return g
        if (g.key === 'marketplace') return g
        if (g.key === 'lifecycle') return g
        if (g.key === 'operacional') return g
        if (g.key === 'intelligence') return { ...g, items: [] }
        if (g.key === 'fiscal') return { ...g, items: [] }
      }
      if (g.key === 'operacional') return { ...g, items: [] }
      return { ...g, items: [] }
    })
    .filter((g) => g.items.length > 0)

  return (
    <aside className="w-72 shrink-0 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between gap-2 rounded-lg bg-indigo-50 px-3 py-2 dark:bg-slate-800">
        <div>
          <p className="text-xs font-bold tracking-wide text-indigo-600 dark:text-indigo-300">ELLAN LAB</p>
          <p className="text-[11px] text-gray-500 dark:text-slate-400">
            {isAuthenticated ? auth?.partnerName || 'Parceiro' : 'Visitante'}
          </p>
        </div>
        {isAuthenticated ? (
          <button
            type="button"
            onClick={() => {
              logout()
              navigate('/login', { replace: true })
            }}
            className="rounded bg-red-500 px-2 py-1 text-[11px] font-medium text-white hover:bg-red-600"
          >
            Sair
          </button>
        ) : (
          <Link
            to="/login"
            className="shrink-0 rounded bg-indigo-600 px-2 py-1 text-[11px] font-medium text-white hover:bg-indigo-500"
          >
            Entrar
          </Link>
        )}
      </div>

      {filteredGroups.map((group) => (
        <div key={group.key} className="mb-2">
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:text-slate-200 dark:hover:bg-slate-800"
            onClick={() => setOpen((s) => ({ ...s, [group.key]: !s[group.key] }))}
          >
            <span className="flex items-center gap-2">
              <span>{group.icon}</span>
              {group.label}
            </span>
            <span className="text-xs">{open[group.key] ? '▾' : '▸'}</span>
          </button>

          {open[group.key] && (
            <div className="mt-1 space-y-1 pl-2">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-700 dark:bg-slate-800 dark:text-indigo-300'
                        : 'text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-800'
                    }`
                  }
                >
                  <span className="flex items-center justify-between gap-2">
                    <span>{item.label}</span>
                    {item.newTag ? (
                      <span className="shrink-0 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        {item.newTag}
                      </span>
                    ) : null}
                  </span>
                </NavLink>
              ))}
            </div>
          )}
        </div>
      ))}
    </aside>
  )
}
