import { NavLink } from 'react-router-dom'
import { useState } from 'react'

type Group = {
  key: string
  icon: string
  label: string
  items: Array<{ to: string; label: string }>
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
      { to: '/ops/manifestos', label: 'Manifestos' },
    ],
  },
  {
    key: 'partnersOps',
    icon: '🤝',
    label: 'Partners OPS',
    items: [
      { to: '/ops/partners/admin', label: 'Visão 360' },
      { to: '/ops/partners/admin?tab=ecosystem', label: 'Redes mundiais' },
      { to: '/ops/partners/admin?tab=global_ops', label: 'Global OPS (SLA · corredores)' },
      { to: '/ops/partners/admin?tab=capability_webhooks', label: 'Webhooks + dead-letter' },
      { to: '/ops/partners/admin?tab=onboarding', label: 'Onboarding B2B' },
      { to: '/ops/partners/admin?tab=settlements', label: 'Settlements' },
      { to: '/ops/tenants/admin', label: 'Tenants (white label)' },
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
    ],
  },
  {
    key: 'marketplace',
    icon: '🏪',
    label: 'Marketplace OPS',
    items: [
      { to: '/ops/marketplace/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/marketplace/admin?tab=channels', label: 'Canais e redes' },
      { to: '/ops/marketplace/admin?tab=readiness', label: 'Prontidão + Global OPS' },
      { to: '/ops/marketplace/admin?tab=settlements', label: 'Repasses e liquidação' },
      { to: '/ops/marketplace/admin?tab=kyc', label: 'KYC / compliance' },
    ],
  },
  {
    key: 'inteligencia',
    icon: '🧠',
    label: 'Inteligência',
    items: [
      { to: '/partners/catalog', label: 'Catálogo' },
      { to: '/partners/webhooks', label: 'Webhooks' },
      { to: '/inteligencia/compatibilidade', label: 'Compatibilidade' },
    ],
  },
  {
    key: 'fiscal',
    icon: '💼',
    label: 'Fiscal',
    items: [
      { to: '/finance/wallet', label: 'Wallet' },
      { to: '/finance/transactions', label: 'Transações' },
      { to: '/finance/reconcile', label: 'Reconciliação' },
    ],
  },
]

export default function Sidebar() {
  const [open, setOpen] = useState<Record<string, boolean>>({
    ops: true,
    partnersOps: true,
    cadastros: true,
    mlOps: true,
    marketplace: true,
    inteligencia: true,
    fiscal: true,
  })

  return (
    <aside className="hidden h-full w-72 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:block">
      {groups.map((group) => (
        <div key={group.key} className="mb-2 rounded-lg">
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
                  className={({ isActive }) => `ellan-nav-item ${isActive ? 'ellan-nav-item-active' : ''}`}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      ))}
    </aside>
  )
}
