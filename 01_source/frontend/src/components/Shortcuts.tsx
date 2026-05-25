import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const hints = [
  { key: 'F1', label: 'Dashboard' },
  { key: 'F2', label: 'Catálogo' },
  { key: 'F3', label: 'Wallet' },
  { key: 'F4', label: 'Logout' },
]

export default function Shortcuts() {
  const navigate = useNavigate()
  const { logout, isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'F1') {
        e.preventDefault()
        navigate('/dashboard')
      } else if (e.key === 'F2') {
        e.preventDefault()
        navigate('/partners/catalog')
      } else if (e.key === 'F3') {
        e.preventDefault()
        navigate('/finance/wallet')
      } else if (e.key === 'F4') {
        e.preventDefault()
        logout()
        navigate('/login', { replace: true })
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isAuthenticated, logout, navigate])

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 hidden gap-2 md:flex">
      {hints.map((hint) => (
        <div
          key={hint.key}
          title={`${hint.key} - ${hint.label}`}
          className="rounded-md border border-slate-600 bg-slate-900 px-2 py-1 text-xs text-slate-300 shadow"
        >
          <span className="font-semibold">{hint.key}</span> {hint.label}
        </div>
      ))}
    </div>
  )
}
