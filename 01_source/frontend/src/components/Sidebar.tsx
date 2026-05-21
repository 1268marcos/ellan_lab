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
    key: 'acesso',
    icon: '🔐',
    label: 'Acesso & Parceiros',
    items: [
      { to: '/ops/partners/admin', label: 'Parceiros' },
      { to: '/ops/access/user-roles', label: 'Papéis (user_roles)' },
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
    acesso: true,
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
