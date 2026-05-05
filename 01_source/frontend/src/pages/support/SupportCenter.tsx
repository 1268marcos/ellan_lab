import { Link } from 'react-router-dom'

export default function SupportCenter() {
  return (
    <div className="mx-auto max-w-3xl p-6 text-slate-800 dark:text-slate-200">
      <p className="text-sm">
        <Link to="/" className="text-indigo-600 hover:underline dark:text-indigo-400">
          ← Voltar ao início
        </Link>
      </p>
      <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-50">Central de Suporte</h1>
      <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Canal oficial de ajuda para parceiros da ELLAN Lab Locker. Esta página será integrada a tickets,
        base de conhecimento e SLA de atendimento.
      </p>
      <div className="mt-8 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/60">
        <p className="text-sm font-medium text-slate-800 dark:text-slate-200">Contato (placeholder)</p>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          E-mail: <span className="font-mono">suporte@ellan.lab</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">Horário e canais definitivos serão divulgados pela operação.</p>
      </div>
    </div>
  )
}
