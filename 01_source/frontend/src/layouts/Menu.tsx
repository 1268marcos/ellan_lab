import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import OpsSidebarNav from '../components/navigation/OpsSidebarNav'
import { OPS_MENU_GROUPS } from '../navigation/opsMenuGroups'
import {
  buildGroupOpenState,
  buildSectionOpenState,
  mergeGroupOpenState,
} from '../navigation/opsNavExpandState'
import type { OpsNavGroup } from '../navigation/opsMenuTypes'

const DEFAULT_OPEN: Record<string, boolean> = {
  ops: false,
  cadastros: false,
  hardwareOps: true,
  paymentsOps: false,
  moneyOps: false,
  cambioOps: false,
  fiscalOps: false,
  partnersOps: false,
  orderPickup: false,
  workersOps: true,
  mlOps: false,
  financeOpsGlobal: false,
  financeOpsCommercial: false,
  financeOps: false,
  marketplace: false,
  privacyCompliance: false,
  usersSecurityOps: true,
  rentalsOps: false,
  marketing: false,
  productsCatalog: false,
  lifecycle: false,
  intelligence: false,
  runtime: false,
  operacional: false,
  fiscal: false,
}

function filterMenuGroups(profile: string | null): OpsNavGroup[] {
  if (!profile) return []
  return OPS_MENU_GROUPS.filter((g) => (g.key === 'runtime' ? profile === 'partner' : true))
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
          'workersOps',
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
          'usersSecurityOps',
        ])
        if (opsKeys.has(g.key)) return g
        if (g.key === 'intelligence') return { ...g, items: [], sections: undefined, hub: undefined }
        if (g.key === 'fiscal') return { ...g, items: [], sections: undefined, hub: undefined }
      }
      if (g.key === 'operacional') return { ...g, items: [], sections: undefined, hub: undefined }
      return { ...g, items: [], sections: undefined, hub: undefined }
    })
    .filter((g) => (g.items?.length ?? 0) > 0 || (g.sections?.length ?? 0) > 0 || g.hub)
}

export default function Menu() {
  const [open, setOpen] = useState<Record<string, boolean>>(DEFAULT_OPEN)
  const [sectionOpen, setSectionOpen] = useState<Record<string, boolean>>({})
  const { auth, logout, isAuthenticated, profile: authProfile } = useAuth()
  const navigate = useNavigate()
  const profile = isAuthenticated ? authProfile : null

  const filteredGroups = useMemo(() => filterMenuGroups(profile), [profile])

  useEffect(() => {
    setOpen((prev) => mergeGroupOpenState(prev, filteredGroups, false))
  }, [filteredGroups])

  const expandAll = useCallback((visible: OpsNavGroup[]) => {
    setOpen((prev) => ({ ...prev, ...buildGroupOpenState(visible, true) }))
    setSectionOpen((prev) => ({ ...prev, ...buildSectionOpenState(visible, true) }))
  }, [])

  const collapseAll = useCallback((visible: OpsNavGroup[]) => {
    setOpen((prev) => ({ ...prev, ...buildGroupOpenState(visible, false) }))
    setSectionOpen((prev) => ({ ...prev, ...buildSectionOpenState(visible, false) }))
  }, [])

  const toggleSection = useCallback(
    (groupKey: string, sectionKey: string) => {
      const id = `${groupKey}:${sectionKey}`
      setSectionOpen((prev) => {
        const group = filteredGroups.find((g) => g.key === groupKey)
        const section = group?.sections?.find((s) => s.key === sectionKey)
        const current = id in prev ? prev[id] : Boolean(section?.defaultOpen)
        return { ...prev, [id]: !current }
      })
    },
    [filteredGroups],
  )

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

  return (
    <aside className="flex h-full min-h-0 w-72 shrink-0 flex-col border-r border-slate-700 bg-slate-900">
      <div className="shrink-0 border-b border-slate-700 p-3">
        <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2">
          <div className="min-w-0">
            <p className="text-xs font-bold tracking-wide text-indigo-300">ELLAN LAB</p>
            <p className="truncate text-[11px] text-slate-400">
              {isAuthenticated ? auth?.partnerName || 'Parceiro' : 'Visitante — faça login para o menu OPS'}
            </p>
            {profileLabel ? (
              <p className="text-[10px] font-medium uppercase tracking-wide text-indigo-300">
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
              className="shrink-0 rounded bg-red-500 px-2 py-1 text-[11px] font-medium text-white hover:bg-red-600"
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
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {!profile ? (
          <nav className="ellan-sidebar-scroll min-h-0 flex-1 space-y-1 overflow-y-auto p-3 text-sm">
            {guestLinks.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="block rounded px-2 py-1.5 text-slate-200 hover:bg-slate-800"
              >
                {item.label}
              </Link>
            ))}
            <a
              href={import.meta.env.VITE_PUBLIC_PORTAL_URL || 'http://localhost:5174/v0/login'}
              className="mt-3 block rounded border border-indigo-500/40 px-2 py-1.5 text-indigo-300 hover:bg-slate-800"
            >
              Portal consumidor (v0)
            </a>
          </nav>
        ) : (
          <OpsSidebarNav
            groups={filteredGroups}
            open={open}
            onToggleGroup={(key) => setOpen((s) => ({ ...s, [key]: !s[key] }))}
            onExpandAll={expandAll}
            onCollapseAll={collapseAll}
            sectionOpen={sectionOpen}
            onToggleSection={toggleSection}
          />
        )}
      </div>
    </aside>
  )
}
