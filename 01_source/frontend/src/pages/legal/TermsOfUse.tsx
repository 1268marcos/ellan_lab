import { Link } from 'react-router-dom'

export default function TermsOfUse() {
  return (
    <div className="mx-auto max-w-3xl p-6 text-slate-800 dark:text-slate-200">
      <p className="text-sm">
        <Link to="/" className="text-indigo-600 hover:underline dark:text-indigo-400">
          ← Voltar ao início
        </Link>
      </p>
      <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-50">Termos de Uso</h1>
      <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Ao utilizar a plataforma ELLAN Lab Locker, o parceiro concorda em cumprir as regras de uso dos
        serviços, APIs e painéis disponibilizados. Este documento é um placeholder até a versão oficial
        dos termos ser anexada aqui.
      </p>
      <ul className="mt-6 list-disc space-y-2 pl-5 text-sm text-slate-600 dark:text-slate-400">
        <li>Uso responsável das credenciais e chaves de API.</li>
        <li>Proibição de uso que comprometa disponibilidade ou segurança do ecossistema.</li>
        <li>Alterações nos termos poderão ser comunicadas pela plataforma.</li>
      </ul>
      <p className="mt-6 text-xs text-slate-500">Última atualização: maio de 2026 (rascunho).</p>
    </div>
  )
}
