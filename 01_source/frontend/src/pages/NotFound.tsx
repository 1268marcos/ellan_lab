import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold text-indigo-600 dark:text-indigo-300">404</p>
      <h1 className="mt-2 text-3xl font-bold text-gray-900 dark:text-slate-100">Página não encontrada</h1>
      <p className="mt-2 text-sm text-gray-500 dark:text-slate-400">
        A rota solicitada não existe neste ambiente.
      </p>
      <Link
        to="/dashboard"
        className="mt-6 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
      >
        Voltar ao Dashboard
      </Link>
    </div>
  )
}

