import { Link } from 'react-router-dom'

type Props = {
  tables?: string
  policyTab?: string
}

export default function CriticalAppLayerBanner({
  tables = 'users, privacy_consents, audit_logs',
  policyTab = 'critical-policies',
}: Props) {
  return (
    <div className="mb-4 rounded-lg border border-amber-600/50 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
      <p className="font-medium">Camada de aplicação (sem RLS nativo)</p>
      <p className="mt-1 text-amber-200/90">
        Tabelas críticas: <span className="font-mono">{tables}</span>. Acesso validado por role e escopo
        (GLOBAL / SELF) via <span className="font-mono">app_critical_table_policy</span>.
      </p>
      <p className="mt-2">
        <Link
          to={`/ops/access/security-admin?tab=${policyTab}`}
          className="text-indigo-300 underline hover:text-indigo-200"
        >
          Ver políticas no hub segurança
        </Link>
        {' · '}
        <Link
          to="/ops/access/security-admin?tab=critical-access-log"
          className="text-indigo-300 underline hover:text-indigo-200"
        >
          Log de decisões
        </Link>
      </p>
    </div>
  )
}
