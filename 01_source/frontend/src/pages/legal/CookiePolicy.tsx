import { Link } from 'react-router-dom'

export default function CookiePolicy() {
  return (
    <div className="mx-auto max-w-3xl p-6 text-slate-800 dark:text-slate-200">
      <p className="text-sm">
        <Link to="/" className="text-indigo-600 hover:underline dark:text-indigo-400">
          ← Voltar ao início
        </Link>
      </p>
      <h1 className="mt-6 text-2xl font-bold text-slate-900 dark:text-slate-50">Política de Cookies</h1>
      <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        Utilizamos cookies essenciais para sessão, checkout e lockers; cookies opcionais de desempenho e marketing
        apenas com consentimento quando exigido (LGPD/GDPR). Versão completa no portal público v0.
      </p>
      <p className="mt-4 text-sm">
        <a
          href="http://localhost:5174/v0/cookies"
          className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
          target="_blank"
          rel="noopener noreferrer"
        >
          Abrir política completa (v0)
        </a>
      </p>
      <p className="mt-6 text-xs text-slate-500">Última atualização: maio de 2026.</p>
    </div>
  )
}
