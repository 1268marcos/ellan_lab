import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-white px-6 py-10 dark:from-slate-950 dark:to-slate-900">
      <div className="mx-auto max-w-6xl">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-600" />
            <div>
              <p className="text-sm font-bold tracking-wide text-indigo-600 dark:text-indigo-300">ELLAN LAB</p>
              <p className="text-xs text-gray-500 dark:text-slate-400">Plataforma de Operações</p>
            </div>
          </div>
          <Link to="/login" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Acessar Plataforma
          </Link>
        </header>

        <section className="mt-14 grid gap-8 lg:grid-cols-2">
          <div>
            <h1 className="text-4xl font-bold leading-tight text-gray-900 dark:text-slate-100">
              Operações de lockers, parceiros e fiscal em um único painel
            </h1>
            <p className="mt-4 text-base text-gray-600 dark:text-slate-300">
              Controle ponta a ponta do ecossistema ELLAN LAB com autenticação por API key de parceiro.
            </p>
            <div className="mt-6">
              <Link to="/login" className="rounded-lg bg-emerald-500 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-600">
                Acessar Plataforma
              </Link>
            </div>
          </div>
          <div className="grid gap-3">
            <ServiceCard title="OPS" desc="Dashboard, lockers e manifestos para operação diária." icon="🛠️" />
            <ServiceCard title="Inteligência" desc="Catálogo, webhooks e compatibilidade de produtos." icon="🧠" />
            <ServiceCard title="Fiscal" desc="Wallet, transações e reconciliação financeira." icon="💼" />
          </div>
        </section>
      </div>
    </div>
  )
}

function ServiceCard({ title, desc, icon }: { title: string; desc: string; icon: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <p className="text-2xl">{icon}</p>
      <h3 className="mt-2 text-lg font-semibold text-gray-900 dark:text-slate-100">{title}</h3>
      <p className="mt-1 text-sm text-gray-600 dark:text-slate-300">{desc}</p>
    </div>
  )
}

