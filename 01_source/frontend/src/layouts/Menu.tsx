import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

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
      { to: '/ops/manifests', label: 'Manifestos' },
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
    ops: true,
    intelligence: true,
    fiscal: true,
  })
  const { auth, logout } = useAuth()
  const navigate = useNavigate()
  const profile = auth?.profile ?? 'partner'

  const filteredGroups = groups
    .map((g) => {
      if (profile === 'admin') return g
      if (profile === 'partner') {
        if (g.key === 'ops') return { ...g, items: [] }
        if (g.key === 'intelligence') {
          return {
            ...g,
            items: g.items.filter(
              (i) => i.to.startsWith('/partners') || i.to.startsWith('/intelligence/'),
            ),
          }
        }
        if (g.key === 'fiscal') return { ...g, items: g.items.filter((i) => i.to.startsWith('/finance')) }
      }
      if (profile === 'ops') {
        if (g.key === 'ops') return g
        if (g.key === 'intelligence') return { ...g, items: [] }
        if (g.key === 'fiscal') return { ...g, items: [] }
      }
      return { ...g, items: [] }
    })
    .filter((g) => g.items.length > 0)

  return (
    <aside className="w-72 shrink-0 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between rounded-lg bg-indigo-50 px-3 py-2 dark:bg-slate-800">
        <div>
          <p className="text-xs font-bold tracking-wide text-indigo-600 dark:text-indigo-300">ELLAN LAB</p>
          <p className="text-[11px] text-gray-500 dark:text-slate-400">{auth?.partnerName || 'Parceiro'}</p>
        </div>
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
