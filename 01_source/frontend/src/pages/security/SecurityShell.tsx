import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/security/users', label: 'Users & Roles' },
  { to: '/security/permissions', label: 'Permissions' },
  { to: '/security/api-keys', label: 'API Keys' },
  { to: '/security/webhooks', label: 'Webhooks' },
]

export default function SecurityShell() {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-gray-900">Security</h1>
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
          <NavLink
            to="/ops/access/security-admin?tab=overview"
            className="rounded-md px-3 py-1.5 bg-gray-50 text-gray-500 hover:bg-gray-100"
          >
            Hub legado
          </NavLink>
        </nav>
      </div>
      <Outlet />
    </div>
  )
}
