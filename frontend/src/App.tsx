import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Catalog from './pages/partners/Catalog'
import Webhooks from './pages/partners/Webhooks'
import Wallet from './pages/finance/Wallet'
import Reconcile from './pages/finance/Reconcile'

const navCls = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
  }`

export default function App() {
  return (
    <div className="min-h-screen">
      <nav className="border-b border-slate-800 bg-slate-900/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-3">
          <span className="mr-4 text-sm font-bold tracking-tight text-emerald-400">ELLAN</span>
          <NavLink to="/" end className={navCls}>
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
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route
          path="/inteligencia"
          element={
            <Placeholder title="Inteligência" body="Catálogo, forecast e ML — MVP em evolução." />
          }
        />
        <Route
          path="/fiscal"
          element={<Placeholder title="Fiscal" body="Faturação e conciliação — MVP em evolução." />}
        />
        <Route path="/partners/catalog" element={<Catalog />} />
        <Route path="/partners/webhooks" element={<Webhooks />} />
        <Route path="/finance/wallet" element={<Wallet />} />
        <Route path="/finance/reconcile" element={<Reconcile />} />
      </Routes>
    </div>
  )
}

function Placeholder({ title, body }: { title: string; body: string }) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-white">{title}</h1>
      <p className="mt-2 text-slate-400">{body}</p>
    </div>
  )
}
