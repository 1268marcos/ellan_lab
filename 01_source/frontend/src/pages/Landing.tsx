import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

type ModuleDef = {
  id: string
  title: string
  icon: string
  summary: string
  teaser: string
  modalTitle: string
  modalParagraphs: string[]
}

const MODULES: ModuleDef[] = [
  {
    id: 'inteligencia',
    title: 'Inteligência',
    icon: '🧠',
    summary: 'Dados de catálogo, integrações e compatibilidade entre o que o parceiro vende e o que os lockers aceitam.',
    teaser: 'Catálogo, webhooks e compatibilidade de produtos.',
    modalTitle: 'Inteligência',
    modalParagraphs: [
      'Centraliza o catálogo de SKUs do parceiro, webhooks para eventos de negócio e ferramentas de compatibilidade entre produto, tamanho de compartimento e restrições logísticas.',
      'Ideal para equipes comerciais e de integração que precisam manter oferta e operação alinhadas sem depender de planilhas paralelas.',
    ],
  },
  {
    id: 'fiscal',
    title: 'Fiscal',
    icon: '💼',
    summary: 'Visão financeira: saldo, movimentações e reconciliação com o ecossistema de cobrança.',
    teaser: 'Wallet, transações e reconciliação financeira.',
    modalTitle: 'Fiscal',
    modalParagraphs: [
      'Reúne wallet do parceiro, histórico de transações, ciclos de faturamento e ferramentas de reconciliação para reduzir divergência entre operação e financeiro.',
      'Útil para controladores e operações que precisam auditar valores e status de cobrança em um só lugar.',
    ],
  },
  {
    id: 'ciclo',
    title: 'Ciclo de Vida',
    icon: '♻️',
    summary: 'Acompanhe pedidos e entregas do ponto de vista de desempenho, ranking e saúde operacional.',
    teaser: 'Métricas, ranking e saúde do fluxo de pedidos e entregas.',
    modalTitle: 'Ciclo de Vida',
    modalParagraphs: [
      'Painéis de métricas, ranking de desempenho e indicadores de saúde do fluxo (SLA, filas, incidentes) ajudam a priorizar melhorias na jornada do pedido até a retirada no locker.',
      'Indicado para gestão operacional e CS que acompanham volume, gargalos e qualidade de serviço.',
    ],
  },
  {
    id: 'runtime',
    title: 'Runtime / Operacional',
    icon: '⚙️',
    summary: 'Estado ao vivo dos compartimentos: ocupação, portas e alocações via BFF seguro.',
    teaser: 'Slots, ocupação de armários e alocações em tempo real (BFF).',
    modalTitle: 'Runtime / Operacional',
    modalParagraphs: [
      'Exibe inventário runtime e alocações consultando o backend-for-frontend (BFF), sem expor o serviço de runtime diretamente ao navegador.',
      'Parceiros com perfil adequado podem monitorar slots, ocupação e vínculos de pedido após autenticação com API key.',
    ],
  },
]

export default function Landing() {
  const [openModuleId, setOpenModuleId] = useState<string | null>(null)

  return (
    <div className="ellan-page min-h-screen bg-[radial-gradient(ellipse_120%_80%_at_50%_-20%,rgba(99,102,241,0.22),transparent)] bg-slate-950 px-6 py-12">
      <div className="mx-auto max-w-5xl">
        <header className="flex flex-col gap-6 border-b border-slate-200/80 pb-10 dark:border-slate-700/80 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div
              className="mt-0.5 h-12 w-12 shrink-0 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25 ring-2 ring-white/60 dark:ring-slate-800/80"
              aria-hidden
            />
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-400">
                ELLAN LAB
              </p>
              <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 sm:text-3xl">
                Plataforma de Operações
              </h1>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                Operações de lockers, parceiros e fiscal em um único painel.
              </p>
            </div>
          </div>
          <Link
            to="/login"
            className="inline-flex shrink-0 items-center justify-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-600/30 transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
          >
            Acessar Plataforma
          </Link>
        </header>

        <section className="mt-12 space-y-10">
          <div className="max-w-2xl">
            <p className="text-lg leading-relaxed text-slate-700 dark:text-slate-300">
              Controle ponta a ponta do ecossistema ELLAN LAB com autenticação por API key de parceiro.
            </p>
            <Link
              to="/login"
              className="mt-6 inline-flex items-center justify-center rounded-xl bg-emerald-600 px-6 py-3.5 text-sm font-semibold text-white shadow-md shadow-emerald-600/25 transition hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-slate-950"
            >
              Acessar Plataforma
            </Link>
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Módulos
            </h2>
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {MODULES.map((m) => (
                <ModuleCard key={m.id} module={m} onOpen={() => setOpenModuleId(m.id)} />
              ))}
            </ul>
          </div>
        </section>

        <footer className="mt-16 border-t border-slate-200/80 pt-8 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
          <p className="text-slate-600 dark:text-slate-300">© 2026 ELLAN Lab Locker. Todos os direitos reservados.</p>
          <nav className="mt-3 flex flex-wrap items-center justify-center gap-x-1 gap-y-2 text-indigo-600 dark:text-indigo-400">
            <Link to="/legal/privacy" className="hover:underline">
              Política de Privacidade
            </Link>
            <span className="px-1 text-slate-400 dark:text-slate-600" aria-hidden>
              |
            </span>
            <Link to="/legal/terms" className="hover:underline">
              Termos de Uso
            </Link>
            <span className="px-1 text-slate-400 dark:text-slate-600" aria-hidden>
              |
            </span>
            <Link to="/support" className="hover:underline">
              Central de Suporte
            </Link>
          </nav>
        </footer>
      </div>

      {openModuleId != null && (
        <InfoModal
          module={MODULES.find((x) => x.id === openModuleId)!}
          onClose={() => setOpenModuleId(null)}
        />
      )}
    </div>
  )
}

function ModuleCard({ module, onOpen }: { module: ModuleDef; onOpen: () => void }) {
  return (
    <li>
      <article className="group flex h-full flex-col rounded-2xl border border-slate-200/90 bg-white/90 p-6 shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-700 dark:bg-slate-900/80 dark:hover:border-indigo-500/40">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-2xl dark:bg-slate-800">
          <span aria-hidden>{module.icon}</span>
        </div>
        <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">{module.title}</h3>
        <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-300">{module.teaser}</p>
        <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{module.summary}</p>
        <button
          type="button"
          onClick={onOpen}
          className="mt-4 w-full rounded-lg border border-indigo-200 bg-indigo-50/80 py-2.5 text-sm font-medium text-indigo-800 transition hover:bg-indigo-100 dark:border-indigo-500/30 dark:bg-indigo-950/40 dark:text-indigo-200 dark:hover:bg-indigo-900/50"
        >
          Mais informações
        </button>
      </article>
    </li>
  )
}

function InfoModal({ module, onClose }: { module: ModuleDef; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="module-modal-title">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-[1px]"
        onClick={onClose}
        aria-label="Fechar modal"
      />
      <div className="relative z-10 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-600 dark:bg-slate-900">
        <h2 id="module-modal-title" className="text-xl font-semibold text-slate-900 dark:text-slate-50">
          {module.modalTitle}
        </h2>
        <div className="mt-4 space-y-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          {module.modalParagraphs.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="mt-6 w-full rounded-xl bg-slate-900 py-3 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-indigo-600 dark:hover:bg-indigo-500"
        >
          Fechar
        </button>
      </div>
    </div>
  )
}
