import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/integrations/partners', label: 'Partners' },
  { to: '/integrations/marketplaces', label: 'Marketplaces' },
  { to: '/integrations/carriers', label: 'Carriers' },
  { to: '/integrations/webhooks', label: 'Webhooks' },
]

export default function IntegrationsShell() {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-gray-900">Integrations</h1>
        <nav className="flex flex-wrap gap-2 text-sm">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 ${isActive ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <Outlet />
    </div>
  )
}
