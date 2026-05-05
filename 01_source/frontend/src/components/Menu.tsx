import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const navCls = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
  }`

export default function Menu() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <nav className="border-b border-slate-800 bg-slate-900/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3">
        <span className="mr-3 text-sm font-bold tracking-tight text-emerald-400">ELLAN</span>
        <NavLink to="/dashboard" className={navCls}>
          OPS
        </NavLink>
        <NavLink to="/inteligencia" className={navCls}>
          Inteligência
        </NavLink>
        <NavLink to="/fiscal" className={navCls}>
          Fiscal
        </NavLink>
        <NavLink to="/finance/wallet" className={navCls}>
          Financeiro
        </NavLink>
        <NavLink to="/partners/catalog" className={navCls}>
          Parceiros
        </NavLink>

        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-slate-300">
            {auth?.partnerName ?? 'Parceiro'} <span className="text-slate-500">({auth?.partnerId})</span>
          </span>
          <button
            type="button"
            onClick={() => {
              logout()
              navigate('/login', { replace: true })
            }}
            className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-600"
          >
            Sair
          </button>
        </div>
      </div>
    </nav>
  )
}
