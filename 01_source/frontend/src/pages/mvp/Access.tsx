import { Link } from 'react-router-dom'

type AccessCard = {
  title: string
  description: string
  href: string
  kind: 'page' | 'service'
  status: string
}

const appPages: AccessCard[] = [
  {
    title: 'App Campo',
    description: 'Checklist operacional, status do locker e smoke do runtime.',
    href: '/field/checklist',
    kind: 'page',
    status: 'MVP ativo',
  },
  {
    title: 'NOC / SIMT',
    description: 'Dashboard com polling 30s, health runtime/lifecycle e ACK de incidente.',
    href: '/noc/dashboard',
    kind: 'page',
    status: 'MVP+ ativo',
  },
  {
    title: 'Suporte N1/N2',
    description: 'Busca por order_id, timeline operacional e payload tecnico.',
    href: '/support/order/ORDER-MVP-001',
    kind: 'page',
    status: 'MVP+ ativo',
  },
  {
    title: 'Fiscal',
    description: 'Reconciliação fiscal canônica no frontend v1.',
    href: '/fiscal/reconcile',
    kind: 'page',
    status: 'Smoke OK',
  },
]

const serviceLinks: AccessCard[] = [
  {
    title: 'Frontend v1',
    description: 'Portal canônico React/Vite.',
    href: 'http://localhost:5173/v1/',
    kind: 'service',
    status: '5173',
  },
  {
    title: 'Runtime / App Campo',
    description: 'backend_runtime exposto no host.',
    href: 'http://localhost:8200/health',
    kind: 'service',
    status: '8200',
  },
  {
    title: 'Order Pickup / Suporte',
    description: 'order_pickup_service para timeline e suporte.',
    href: 'http://localhost:8003/health',
    kind: 'service',
    status: '8003',
  },
  {
    title: 'Order Lifecycle / NOC',
    description: 'order_lifecycle_service para dashboard NOC.',
    href: 'http://localhost:8010/health',
    kind: 'service',
    status: '8010',
  },
  {
    title: 'Billing Fiscal',
    description: 'billing_fiscal_service e smoke fiscal.',
    href: 'http://localhost:8020/health',
    kind: 'service',
    status: '8020',
  },
  {
    title: 'Payment Gateway',
    description: 'gateway de pagamento saudável.',
    href: 'http://localhost:8000/health',
    kind: 'service',
    status: '8000',
  },
  {
    title: 'Grafana',
    description: 'Dashboards operacionais.',
    href: 'http://localhost:8300',
    kind: 'service',
    status: '8300',
  },
  {
    title: 'Metabase',
    description: 'Analytics e reporting.',
    href: 'http://localhost:8301',
    kind: 'service',
    status: '8301',
  },
]

export default function MvpAccessPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="overflow-hidden rounded-3xl border border-cyan-400/20 bg-slate-900">
          <div className="border-b border-cyan-400/10 bg-cyan-950/30 px-6 py-5">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">
              ELLAN LAB MVP
            </p>
            <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">Acessos das Sprints MVP</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-cyan-50/80">
                  Hub canônico em <span className="font-mono text-amber-200">http://localhost:5173/v1/</span> com
                  páginas MVP e serviços nas portas atuais do Docker.
                </p>
              </div>
              <div className="rounded-2xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
                Branch: <span className="font-mono">sprint-mvp</span>
              </div>
            </div>
          </div>

          <div className="grid gap-4 p-6 md:grid-cols-4">
            <Stat label="Páginas MVP" value="4" />
            <Stat label="Serviços mapeados" value="8" />
            <Stat label="Runtime" value="8200" />
            <Stat label="Pickup" value="8003" />
          </div>
        </header>

        <section className="mt-8">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-cyan-50">Páginas canônicas v1</h2>
              <p className="mt-1 text-sm text-slate-400">Acesse pelo roteamento interno do frontend.</p>
            </div>
            <Link
              to="/"
              className="rounded-xl border border-cyan-400/30 px-4 py-2 text-sm font-medium text-cyan-100 hover:bg-cyan-400/10"
            >
              Voltar ao início
            </Link>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {appPages.map((card) => (
              <AccessTile key={card.href} card={card} />
            ))}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold text-cyan-50">Serviços e portas Docker</h2>
          <p className="mt-1 text-sm text-slate-400">Links externos abrem os endpoints expostos no host.</p>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {serviceLinks.map((card) => (
              <AccessTile key={card.href} card={card} />
            ))}
          </div>
        </section>

        <section className="mt-10 rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white">Comandos de smoke</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Command value="./smoke-app-campo.sh" />
            <Command value="./smoke-noc.sh" />
            <Command value="./smoke-suporte.sh" />
            <Command value="./smoke-fiscal.sh" />
            <Command value="./smoke-all-mvp.sh" />
          </div>
        </section>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-cyan-400/10 bg-slate-950/60 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-amber-200">{value}</p>
    </div>
  )
}

function AccessTile({ card }: { card: AccessCard }) {
  const className =
    card.kind === 'page'
      ? 'border-cyan-400/20 bg-cyan-950/20 hover:border-cyan-300/60'
      : 'border-amber-300/20 bg-amber-950/10 hover:border-amber-200/60'

  const content = (
    <article className={`h-full rounded-2xl border p-5 transition ${className}`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-white">{card.title}</h3>
        <span className="rounded-full bg-slate-950 px-2.5 py-1 text-xs font-medium text-amber-200">
          {card.status}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{card.description}</p>
      <p className="mt-4 break-all font-mono text-xs text-cyan-200">{card.href}</p>
    </article>
  )

  if (card.kind === 'page') {
    return <Link to={card.href}>{content}</Link>
  }

  return (
    <a href={card.href} target="_blank" rel="noreferrer">
      {content}
    </a>
  )
}

function Command({ value }: { value: string }) {
  return (
    <code className="block rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-cyan-100">
      {value}
    </code>
  )
}
