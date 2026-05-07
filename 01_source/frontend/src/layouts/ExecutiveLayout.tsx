import type { ComponentType, ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

type NavItem = { to: string; label: string; Icon: ComponentType<{ className?: string }> }

function IconDashboard({ className }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="3" y="3" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="13" y="3" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="3" y="13" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="13" y="13" width="8" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function IconChart({ className }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M4 19V5M4 19h16M8 16V11M12 16V8M16 16v-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconFinance({ className }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M6 4h12v16H6V4Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M9 8h6M9 12h6M9 16h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function IconIntel({ className }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 3v2M12 19v2M4 12h2M18 12h2M6.34 6.34l1.42 1.42M16.24 16.24l1.42 1.42M6.34 17.66l1.42-1.42M16.24 7.76l1.42-1.42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function IconUser({ className }: { className?: string }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 12a4 4 0 100-8 4 4 0 000 8ZM4 20a8 8 0 0116 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const NAV: NavItem[] = [
  { to: '/dashboard/ceo', label: 'Visão 360°', Icon: IconDashboard },
  { to: '/analytics/dashboard', label: 'Analytics', Icon: IconChart },
  { to: '/finance/billing/cycles', label: 'Finanças', Icon: IconFinance },
  { to: '/intelligence/occupancy-forecast', label: 'Inteligência', Icon: IconIntel },
  { to: '/settings/profile', label: 'Perfil', Icon: IconUser },
]

export default function ExecutiveLayout({ children }: { children: ReactNode }) {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col bg-[#F7FAFC] font-sans text-[#2D3748] antialiased">
      <header className="sticky top-0 z-50 border-b border-[#1A365D]/15 bg-[#1A365D] shadow-[0_4px_24px_rgba(26,54,93,0.25)]">
        <div className="mx-auto flex max-w-[1600px] flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between lg:gap-6">
          <div className="min-w-0 space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/65">
              🏢 C-LEVEL & EXECUTIVE
            </p>
            <p className="font-semibold leading-tight text-white" style={{ fontSize: 'clamp(1rem, 2vw, 1.125rem)' }}>
              CEO · Head of Locker Division
            </p>
            <p className="text-xs leading-snug text-white/55">
              Portal 5180 · Desktop executivo · reuniões estratégicas
            </p>
          </div>

          <nav
            className="flex flex-wrap items-center gap-2 lg:justify-center lg:gap-1"
            aria-label="Navegação principal executiva"
          >
            {NAV.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  [
                    'ceo-nav-item group flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-white/15 text-white shadow-[inset_0_-2px_0_0_#38A169]'
                      : 'text-white/80 hover:bg-white/10 hover:text-white hover:shadow-md',
                  ].join(' ')
                }
              >
                <Icon className="shrink-0 opacity-90 group-hover:opacity-100" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-3 border-t border-white/10 pt-3 lg:border-t-0 lg:pt-0">
            <span className="hidden max-w-[11rem] truncate text-xs text-white/70 sm:inline" title={auth?.partnerName}>
              {auth?.partnerName}
            </span>
            <button
              type="button"
              onClick={() => {
                logout()
                navigate('/login', { replace: true })
              }}
              className="rounded-lg border border-white/25 bg-white/5 px-3 py-2 text-xs font-medium text-white transition hover:bg-white/15 hover:shadow-md"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-x-hidden overflow-y-auto">
        <div className="mx-auto max-w-[1600px] px-6 py-10">{children}</div>
      </main>
    </div>
  )
}
