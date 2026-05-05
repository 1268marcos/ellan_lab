import { Link } from 'react-router-dom'

export default function PrivacyPolicy() {
  return (
    <div className="mx-auto max-w-3xl p-6 text-slate-800 dark:text-slate-200">
      <p className="text-sm">
        <Link to="/" className="text-indigo-600 hover:underline dark:text-indigo-400">
          ← Voltar ao início
        </Link>
      </p>
      <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-50">Política de Privacidade</h1>
      <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Esta página descreve como a ELLAN Lab Locker pode tratar dados pessoais e operacionais no contexto da
        plataforma de parceiros. O texto completo será publicado pela equipe jurídica; por ora serve como
        placeholder para navegação e conformidade de interface.
      </p>
      <ul className="mt-6 list-disc space-y-2 pl-5 text-sm text-slate-600 dark:text-slate-400">
        <li>Coleta mínima de dados necessários à prestação do serviço.</li>
        <li>Uso de API key e credenciais conforme política interna de segurança.</li>
        <li>Direitos do titular: acesso, correção e exclusão mediante solicitação formal.</li>
      </ul>
      <p className="mt-6 text-xs text-slate-500">Última atualização: maio de 2026 (rascunho).</p>
    </div>
  )
}
