import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import OpsSidebarNav from '../components/navigation/OpsSidebarNav'
import { OPS_MENU_GROUPS } from '../navigation/opsMenuGroups'

export default function Menu() {
  const [open, setOpen] = useState<Record<string, boolean>>({
    ops: false,
    cadastros: true,
    hardwareOps: true,
    paymentsOps: true,
    moneyOps: true,
    cambioOps: false,
    fiscalOps: true,
    partnersOps: true,
    orderPickup: true,
    mlOps: true,
    financeOpsGlobal: true,
    financeOpsCommercial: true,
    financeOps: true,
    marketplace: true,
    privacyCompliance: false,
    rentalsOps: true,
    marketing: true,
    productsCatalog: true,
    lifecycle: false,
    intelligence: false,
    runtime: false,
    operacional: false,
    fiscal: false,
  })
  const { auth, logout, isAuthenticated, profile: authProfile } = useAuth()
  const navigate = useNavigate()
  const profile = isAuthenticated ? authProfile : null

  const profileLabel =
    profile === 'admin'
      ? 'Administrador'
      : profile === 'ops'
        ? 'Operações'
        : profile === 'partner'
          ? 'Parceiro'
          : null

  const guestLinks = [
    { to: '/', label: 'Início' },
    { to: '/login', label: 'Login OPS (API key)' },
    { to: '/legal/privacy', label: 'Privacidade' },
    { to: '/support', label: 'Suporte' },
  ]

  const filteredGroups = !profile
    ? []
    : OPS_MENU_GROUPS.filter((g) => (g.key === 'runtime' ? profile === 'partner' : true))
    .map((g) => {
      if (profile === 'admin') return g
      if (profile === 'partner') {
        if (g.key === 'ops') return { ...g, items: [], sections: undefined, hub: undefined }
        if (g.key === 'lifecycle') return g
        if (g.key === 'intelligence') {
          return {
            ...g,
            items: (g.items ?? []).filter(
              (i) => i.to.startsWith('/partners') || i.to.startsWith('/intelligence/'),
            ),
            sections: undefined,
            hub: undefined,
          }
        }
        if (g.key === 'runtime') return g
        if (g.key === 'fiscal') {
          return {
            ...g,
            items: (g.items ?? []).filter((i) => i.to.startsWith('/finance')),
            sections: undefined,
            hub: undefined,
          }
        }
      }
      if (profile === 'ops') {
        const opsKeys = new Set([
          'ops',
          'cadastros',
          'hardwareOps',
          'paymentsOps',
          'moneyOps',
          'cambioOps',
          'fiscalOps',
          'partnersOps',
          'orderPickup',
          'mlOps',
          'financeOpsGlobal',
          'financeOpsCommercial',
          'financeOps',
          'marketplace',
          'marketing',
          'productsCatalog',
          'lifecycle',
          'operacional',
          'rentalsOps',
          'privacyCompliance',
        ])
        if (opsKeys.has(g.key)) return g
        if (g.key === 'intelligence') return { ...g, items: [], sections: undefined, hub: undefined }
        if (g.key === 'fiscal') return { ...g, items: [], sections: undefined, hub: undefined }
      }
      if (g.key === 'operacional') return { ...g, items: [], sections: undefined, hub: undefined }
      return { ...g, items: [], sections: undefined, hub: undefined }
    })
    .filter((g) => (g.items?.length ?? 0) > 0 || (g.sections?.length ?? 0) > 0 || g.hub)

  return (
    <aside className="w-72 shrink-0 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex items-center justify-between gap-2 rounded-lg bg-indigo-50 px-3 py-2 dark:bg-slate-800">
        <div>
          <p className="text-xs font-bold tracking-wide text-indigo-600 dark:text-indigo-300">ELLAN LAB</p>
          <p className="text-[11px] text-gray-500 dark:text-slate-400">
            {isAuthenticated ? auth?.partnerName || 'Parceiro' : 'Visitante — faça login para o menu OPS'}
          </p>
          {profileLabel ? (
            <p className="text-[10px] font-medium uppercase tracking-wide text-indigo-500 dark:text-indigo-300">
              Perfil: {profileLabel}
            </p>
          ) : null}
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

      {!profile ? (
        <nav className="space-y-1 text-sm">
          {guestLinks.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="block rounded px-2 py-1.5 text-slate-700 hover:bg-indigo-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {item.label}
            </Link>
          ))}
          <a
            href={
              import.meta.env.VITE_PUBLIC_PORTAL_URL || 'http://localhost:5174/v0/login'
            }
            className="mt-3 block rounded border border-indigo-200 px-2 py-1.5 text-indigo-700 hover:bg-indigo-50 dark:border-indigo-800 dark:text-indigo-300 dark:hover:bg-slate-800"
          >
            Portal consumidor (v0)
          </a>
        </nav>
      ) : (
        <OpsSidebarNav
          groups={filteredGroups}
          open={open}
          onToggleGroup={(key) => setOpen((s) => ({ ...s, [key]: !s[key] }))}
        />
      )}
    </aside>
  )
}
