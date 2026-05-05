import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Header() {
  const { auth, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg bg-indigo-500" />
        <div>
          <p className="text-sm font-bold tracking-wide text-indigo-600 dark:text-indigo-300">ELLAN LAB</p>
          <p className="text-xs text-gray-500 dark:text-slate-400">Painel Operacional</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm font-medium text-gray-800 dark:text-slate-100">{auth?.partnerName || 'Parceiro'}</p>
          <p className="text-xs text-gray-500 dark:text-slate-400">{auth?.partnerId || '-'}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-white">
          {(auth?.partnerName || 'P').slice(0, 1).toUpperCase()}
        </div>
        <button
          type="button"
          onClick={() => {
            logout()
            navigate('/login', { replace: true })
          }}
          className="rounded-md bg-red-500 px-3 py-2 text-sm font-medium text-white hover:bg-red-600"
        >
          Sair
        </button>
      </div>
    </header>
  )
}
