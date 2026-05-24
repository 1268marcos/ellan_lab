import { NavLink } from 'react-router-dom'
import { useState } from 'react'

type Group = {
  key: string
  icon: string
  label: string
  items: Array<{ to: string; label: string }>
}

const groups: Group[] = [
  {
    key: 'ops',
    icon: '🛠️',
    label: 'OPS',
    items: [
      { to: '/dashboard', label: 'Dashboard' },
      { to: '/ops/lockers', label: 'Lockers' },
      { to: '/ops/lockers/create', label: 'Criar lockers' },
      { to: '/ops/manifestos', label: 'Manifestos' },
    ],
  },
  {
    key: 'partnersOps',
    icon: '🤝',
    label: 'Partners OPS',
    items: [
      { to: '/ops/partners/admin', label: 'Visão 360' },
      { to: '/ops/partners/admin?tab=ecosystem', label: 'Redes mundiais' },
      { to: '/ops/partners/admin?tab=global_ops', label: 'Global OPS (SLA · corredores)' },
      { to: '/ops/partners/admin?tab=capability_webhooks', label: 'Webhooks + dead-letter' },
      { to: '/ops/partners/admin?tab=onboarding', label: 'Onboarding B2B' },
      { to: '/ops/partners/admin?tab=settlements', label: 'Settlements' },
      { to: '/ops/tenants/admin', label: 'Tenants (white label)' },
    ],
  },
  {
    key: 'cadastros',
    icon: '📋',
    label: 'Cadastros OPS',
    items: [
      { to: '/ops/access/user-roles', label: 'Papéis de acesso (user_roles)' },
      { to: '/ops/payment-gateway/admin', label: 'Payment Gateway (PSP)' },
    ],
  },
  {
    key: 'moneyOps',
    icon: '💵',
    label: 'Money OPS',
    items: [
      { to: '/ops/money-cambio/admin', label: 'Visão global (KPIs)' },
      { to: '/ops/money-cambio/admin?tab=players', label: 'Players ecossistema' },
      { to: '/ops/money-cambio/admin?tab=segments', label: 'Segmentos' },
      { to: '/ops/money-cambio/admin?tab=relations', label: 'Relações players' },
      { to: '/ops/money-cambio/admin?tab=intelligence', label: 'Intelligence' },
      { to: '/ops/money-cambio/admin?tab=countries', label: 'Países operacionais' },
      { to: '/ops/money-cambio/admin?tab=matrix', label: 'Matriz método × país' },
      { to: '/ops/money-cambio/admin?tab=currencies', label: 'Moedas ISO' },
      { to: '/ops/money-cambio/admin?tab=methods', label: 'Métodos de pagamento' },
      { to: '/ops/money-cambio/admin?tab=wallets', label: 'Wallet providers' },
      { to: '/ops/money-cambio/admin?tab=rails', label: 'Payment rails' },
      { to: '/ops/money-cambio/admin?tab=treasury', label: 'Tesouraria FX' },
    ],
  },
  {
    key: 'cambioOps',
    icon: '💱',
    label: 'Câmbio OPS',
    items: [
      { to: '/ops/money-cambio/admin?tab=corridors', label: 'Corredores FX' },
      { to: '/ops/money-cambio/admin?tab=fx', label: 'Taxas e conversão' },
      { to: '/ops/money-cambio/admin?tab=pricing', label: 'Simulador cotação' },
      { to: '/ops/money-cambio/admin?tab=fxlocks', label: 'Travas FX' },
      { to: '/ops/money-cambio/admin?tab=compliance', label: 'Compliance AML/KYC' },
      { to: '/ops/money-cambio/admin?tab=audit', label: 'Auditoria FX' },
      { to: '/ops/money-cambio/admin?tab=settlements', label: 'Calendário settlement' },
      { to: '/ops/money-cambio/admin?tab=partners', label: 'Parceiros integração' },
    ],
  },
  {
    key: 'fiscalOps',
    icon: '🧾',
    label: 'Fiscal OPS',
    items: [
      { to: '/ops/fiscal/admin?tab=global', label: 'Global OPS' },
      { to: '/ops/fiscal/admin?tab=intelligence', label: 'Inteligência fiscal' },
      { to: '/ops/fiscal/admin', label: 'Emissores' },
      { to: '/ops/fiscal/admin?tab=corridors', label: 'Corredores fiscais' },
      { to: '/ops/fiscal/admin?tab=readiness', label: 'Prontidão' },
      { to: '/ops/fiscal/admin?tab=documents', label: 'Documentos' },
      { to: '/ops/fiscal/admin?tab=classification', label: 'NCM / CFOP' },
      { to: '/ops/fiscal/admin?tab=webhooks', label: 'Webhook DLQ' },
    ],
  },
  {
    key: 'mlOps',
    icon: '🤖',
    label: 'ML OPS',
    items: [
      { to: '/ops/ml/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/ml/admin?tab=partners', label: 'Parceiros de dados ML' },
      { to: '/ops/ml/admin?tab=networks', label: 'Redes locker mundiais' },
      { to: '/ops/ml/admin?tab=models', label: 'Modelos e versões' },
      { to: '/ops/ml/admin?tab=features', label: 'Features diárias' },
      { to: '/ops/ml/admin?tab=predictions', label: 'Log de predições' },
      { to: '/ops/ml/admin?tab=feedback', label: 'Feedback de modelo' },
    ],
  },
  {
    key: 'rentalsOps',
    icon: '🔑',
    label: 'Rentals OPS',
    items: [
      { to: '/ops/rentals/admin', label: 'Visão geral (hub)' },
      { to: '/ops/rentals/admin?tab=networks', label: 'Redes mundiais' },
      { to: '/ops/rentals/admin?tab=corridors', label: 'Corredores' },
      { to: '/ops/rentals/admin?tab=onboarding', label: 'Onboarding KYB' },
      { to: '/ops/rentals/admin?tab=capacity', label: 'Capacidade / utilização' },
      { to: '/ops/rentals/admin?tab=operators', label: 'Operadores B2B' },
      { to: '/ops/rentals/admin?tab=plans', label: 'Planos (CRUD)' },
      { to: '/ops/rentals/admin?tab=contracts', label: 'Contratos — cotação e seguro' },
      { to: '/ops/rentals/admin?tab=contracts', label: 'Preview pricing' },
      { to: '/ops/rentals/admin?tab=billing', label: 'Faturamento — multas automáticas' },
      { to: '/ops/rentals/admin?tab=billing', label: 'Aplicar multas' },
      { to: '/ops/rentals/admin?tab=settlements', label: 'Liquidações' },
      { to: '/ops/rentals/admin?tab=sla', label: 'Políticas SLA' },
      { to: '/ops/rentals/admin?tab=premium', label: 'Breaches, disputas, renovação' },
      { to: '/ops/rentals/admin?tab=events', label: 'Eventos / auditoria' },
      { to: '/ops/rentals/admin?tab=integrations', label: 'Webhooks e API keys' },
      { to: '/ops/rentals/admin?tab=advanced', label: 'Avançado — pricing, seguro, dunning' },
      { to: '/ops/rentals/admin?tab=advanced', label: 'Seguro de conteúdo' },
    ],
  },
  {
    key: 'financeOpsGlobal',
    icon: '🌍',
    label: 'Finance OPS — Global',
    items: [
      { to: '/ops/finance/admin?tab=networks', label: 'Redes mundiais · Como integrar' },
      {
        to: '/ops/finance/admin?tab=intelligence',
        label: 'Ecosystem Intelligence',
      },
      { to: '/ops/finance/admin?tab=ecosystem', label: 'Ecossistema e relações' },
      { to: '/ops/finance/admin?tab=readiness', label: 'Readiness score (A–D)' },
      { to: '/ops/finance/admin?tab=roadmap', label: 'Roadmap integração' },
      { to: '/ops/finance/admin?tab=contracts', label: 'Contratos comerciais (MSA)' },
      { to: '/ops/finance/admin?tab=slas', label: 'SLAs e breaches' },
    ],
  },
  {
    key: 'financeOpsCommercial',
    icon: '📊',
    label: 'Finance OPS — Comercial',
    items: [
      { to: '/ops/finance/admin?tab=dunning', label: 'Cobrança (dunning)' },
      { to: '/ops/finance/admin?tab=tiers', label: 'Níveis comerciais' },
      { to: '/ops/finance/admin?tab=fx', label: 'Câmbio (FX)' },
      { to: '/ops/finance/admin?tab=tax', label: 'Corredores fiscais' },
      { to: '/ops/finance/admin?tab=documents', label: 'Documentos NF' },
      { to: '/ops/finance/admin?tab=audit', label: 'Auditoria' },
      { to: '/ops/finance/admin?tab=revrec', label: 'Rev. receita' },
      { to: '/ops/finance/admin?tab=jobs', label: 'Jobs agendados' },
    ],
  },
  {
    key: 'financeOps',
    icon: '💰',
    label: 'Finance OPS',
    items: [
      { to: '/ops/finance/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/finance/admin?tab=partners', label: 'Parceiros financeiros' },
      { to: '/ops/finance/admin?tab=billing', label: 'Billing + line items' },
      { to: '/ops/finance/admin?tab=invoices', label: 'NF B2B' },
      { to: '/ops/finance/admin?tab=settlements', label: 'Settlements' },
      { to: '/ops/finance/admin?tab=treasury', label: 'Treasury' },
      { to: '/ops/finance/admin?tab=wallet', label: 'Wallet' },
      { to: '/ops/finance/admin?tab=pnl', label: 'PnL locker' },
      { to: '/ops/finance/admin?tab=reconciliation', label: 'Gaps fiscais' },
      { to: '/ops/finance/admin?tab=webhooks', label: 'Webhook DLQ + replay' },
      { to: '/ops/finance/admin?tab=ops', label: 'NF ops e eventos' },
    ],
  },
  {
    key: 'marketplace',
    icon: '🏪',
    label: 'Marketplace OPS',
    items: [
      { to: '/ops/marketplace/admin', label: 'Visão geral e cadastro' },
      { to: '/ops/marketplace/admin?tab=channels', label: 'Canais e redes' },
      { to: '/ops/marketplace/admin?tab=readiness', label: 'Prontidão + Global OPS' },
      { to: '/ops/marketplace/admin?tab=settlements', label: 'Repasses e liquidação' },
      { to: '/ops/marketplace/admin?tab=kyc', label: 'KYC / compliance' },
    ],
  },
  {
    key: 'marketing',
    icon: '🎯',
    label: 'Marketing',
    items: [
      { to: '/ops/marketing/promotions', label: 'Hub Promoções' },
      { to: '/ops/marketing/promotions?tab=campaigns', label: 'Campanhas' },
      { to: '/ops/marketing/promotions?tab=promotions', label: 'Promoções' },
      { to: '/ops/marketing/promotions?tab=redemptions', label: 'Resgates' },
      { to: '/ops/marketing/promotions?tab=lab', label: 'Laboratório' },
      { to: '/ops/products/pricing-fiscal', label: 'API lab PR3' },
      { to: '/ops/products/admin?tab=bundles', label: 'Bundles' },
    ],
  },
  {
    key: 'productsCatalog',
    icon: '📦',
    label: 'Produtos & Catálogo',
    items: [
      { to: '/ops/products/admin', label: 'Hub — visão geral' },
      { to: '/ops/products/admin?tab=ecosystem', label: 'Ecossistema mundial' },
      { to: '/ops/products/admin?tab=taxonomy', label: 'PIM — taxonomias' },
      { to: '/ops/products/admin?tab=channels', label: 'PIM — canais' },
      { to: '/ops/products/admin?tab=attributes', label: 'PIM — atributos' },
      { to: '/ops/products/catalog', label: 'Catálogo SKU' },
      { to: '/ops/products/categories', label: 'Categorias' },
      { to: '/ops/products/assets', label: 'Mídia & barcodes' },
      { to: '/ops/products/admin?tab=bundles', label: 'Bundles' },
      { to: '/ops/products/admin?tab=fiscal', label: 'Pricing & fiscal' },
      { to: '/ops/products/admin?tab=inventory', label: 'Estoque & reservas' },
    ],
  },
  {
    key: 'inteligencia',
    icon: '🧠',
    label: 'Inteligência',
    items: [
      { to: '/partners/catalog', label: 'Catálogo' },
      { to: '/partners/webhooks', label: 'Webhooks' },
      { to: '/inteligencia/compatibilidade', label: 'Compatibilidade' },
    ],
  },
  {
    key: 'fiscal',
    icon: '💼',
    label: 'Fiscal',
    items: [
      { to: '/finance/wallet', label: 'Wallet' },
      { to: '/finance/transactions', label: 'Transações' },
      { to: '/finance/reconcile', label: 'Reconciliação' },
    ],
  },
]

export default function Sidebar() {
  const [open, setOpen] = useState<Record<string, boolean>>({
    ops: true,
    partnersOps: true,
    cadastros: true,
    moneyOps: true,
    cambioOps: true,
    mlOps: true,
    financeOpsGlobal: true,
    financeOpsCommercial: true,
    financeOps: true,
    marketplace: true,
    fiscalOps: true,
    marketing: true,
    productsCatalog: true,
    inteligencia: true,
    fiscal: true,
  })

  return (
    <aside className="hidden h-full w-72 border-r border-gray-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:block">
      {groups.map((group) => (
        <div key={group.key} className="mb-2 rounded-lg">
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:text-slate-200 dark:hover:bg-slate-800"
            onClick={() => setOpen((s) => ({ ...s, [group.key]: !s[group.key] }))}
          >
            <span className="flex items-center gap-2">
              <span>{group.icon}</span>
              {group.label}
            </span>
            <span className="text-xs">{open[group.key] ? '▾' : '▸'}</span>
          </button>
          {open[group.key] && (
            <div className="mt-1 space-y-1 pl-2">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `ellan-nav-item ${isActive ? 'ellan-nav-item-active' : ''}`}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      ))}
    </aside>
  )
}
