import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/financial', label: 'Executive Dashboard', end: true },
  { to: '/financial/locker-pnl', label: 'Locker P&L' },
  { to: '/financial/expansion', label: 'Expansion Simulator' },
  { to: '/financial/partners', label: 'Partner Settlements' },
]

export default function FinancialShell() {
  return (
    <div className="space-y-6 p-4 md:p-6">
      <header>
        <p className="text-xs uppercase tracking-wide text-slate-500">Financial</p>
        <h1 className="text-2xl font-bold text-slate-50">Dashboards financeiros executivos</h1>
      </header>
      <nav className="flex flex-wrap gap-2 border-b border-slate-700/80 pb-3">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
              }`
            }
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}
