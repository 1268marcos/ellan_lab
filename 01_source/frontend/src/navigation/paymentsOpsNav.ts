import type { OpsNavGroup } from './opsMenuTypes'

const BASE = '/ops/payments/admin'

/** Payments OPS — hierarquia IA-first (hub → cross-domain → mundial → valor → ledger). */
export const paymentsOpsNavGroup: OpsNavGroup = {
  key: 'paymentsOps',
  icon: '💳',
  label: 'Payments OPS',
  hub: {
    to: BASE,
    label: 'Centro de comando',
    newTag: 'Hub',
    keywords: 'kpi inteligencia readiness routing suggest global',
  },
  sections: [
    {
      key: 'hub',
      label: 'Hub & inteligência',
      defaultOpen: true,
      items: [
        { to: BASE, label: 'KPIs e prontidão global', newTag: 'Hub', keywords: 'summary intelligence readiness' },
        { to: `${BASE}?tab=graph`, label: 'Grafo ecossistema', newTag: 'Flow', keywords: 'react flow players relacoes' },
      ],
    },
    {
      key: 'cross',
      label: 'Cross-domain',
      defaultOpen: true,
      items: [
        {
          to: `${BASE}?tab=cross-domain`,
          label: 'Hub 360° · gaps · obrigações',
          newTag: 'New',
          keywords: 'registry external obligation order-360 finance fiscal marketplace',
        },
        { to: `${BASE}?tab=order-context`, label: 'Contexto pedido × parceiros', keywords: 'order context tenant locker' },
      ],
    },
    {
      key: 'world',
      label: 'Ecossistema mundial',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=ecosystem`, label: 'Players (InPost, DHL, Magalu…)', keywords: 'inpost dhl mercado livre amazon' },
        { to: `${BASE}?tab=segments`, label: 'Segmentos', keywords: 'locker carrier food marketplace' },
        { to: `${BASE}?tab=integrations`, label: 'Integrações · playbook', keywords: 'readiness sandbox production' },
        { to: `${BASE}?tab=coverage`, label: 'Cobertura por país', keywords: 'country coverage br pt es' },
        { to: `${BASE}?tab=relations`, label: 'Relações entre players', keywords: 'white label carrier channel' },
      ],
    },
    {
      key: 'value',
      label: 'Valor & roteamento',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=milestones`, label: 'Roadmap integração', newTag: 'CRUD', keywords: 'milestone discovery production' },
        { to: `${BASE}?tab=routing`, label: 'Roteamento PSP', newTag: 'CRUD', keywords: 'psp fallback primary' },
        { to: `${BASE}?tab=corridors`, label: 'Corredores FX / settlement', keywords: 'fx cross-border' },
        { to: `${BASE}?tab=compliance`, label: 'Compliance', keywords: 'lgpd gdpr pci aml' },
        { to: `${BASE}?tab=incidents`, label: 'Incidentes integração', keywords: 'sla webhook latency' },
      ],
    },
    {
      key: 'ledger',
      label: 'Ledger transacional',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=transactions`, label: 'Transações', keywords: 'payment_transactions' },
        { to: `${BASE}?tab=instructions`, label: 'Instruções (PIX, boleto…)', keywords: 'pix qr boleto' },
        { to: `${BASE}?tab=splits`, label: 'Splits marketplace / carrier', keywords: 'repasse split' },
        { to: `${BASE}?tab=payments`, label: 'Payments ledger', keywords: 'provider status' },
      ],
    },
    {
      key: 'reconcile',
      label: 'Conciliação',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=batches`, label: 'Lotes de conciliação', keywords: 'reconciliation batch' },
        {
          to: `${BASE}?tab=batches`,
          label: 'Workbench conciliação',
          keywords: 'reconcile status lote reconciliation',
        },
      ],
    },
    {
      key: 'integration',
      label: 'Webhooks & eventos',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=webhooks`, label: 'Endpoints · rotate secret', keywords: 'webhook endpoint' },
        { to: `${BASE}?tab=deliveries`, label: 'Entregas · DLQ', keywords: 'delivery retry dead letter' },
        { to: `${BASE}?tab=events`, label: 'Gateway events', keywords: 'auditoria runtime' },
      ],
    },
    {
      key: 'finance',
      label: 'Financeiro & vault',
      defaultOpen: false,
      items: [
        { to: `${BASE}?tab=holds`, label: 'Holds parceiro', keywords: 'partner hold finance' },
        { to: `${BASE}?tab=vault`, label: 'Cartões salvos', keywords: 'saved payment methods token' },
      ],
    },
  ],
}

/** Grupo legado (lista plana) para compatibilidade pontual. */
export function flattenPaymentsOpsGroup(): OpsNavGroup['items'] {
  const g = paymentsOpsNavGroup
  const flat: NonNullable<OpsNavGroup['items']> = []
  if (g.hub) flat.push(g.hub)
  for (const s of g.sections ?? []) flat.push(...s.items)
  return flat
}
