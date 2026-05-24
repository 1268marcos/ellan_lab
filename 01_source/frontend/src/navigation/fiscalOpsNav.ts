import { navItem, opsGroup, section } from './opsNavHelpers'

const BASE = '/ops/fiscal/admin'

export const fiscalOpsNavGroup = opsGroup('fiscalOps', '🧾', 'Fiscal OPS', {
  hub: navItem(`${BASE}?tab=global`, 'Global OPS (KPIs)', { newTag: 'Hub', keywords: 'jurisdictions summary' }),
  sections: [
    section('hub', 'Hub & inteligência', [
      navItem(`${BASE}?tab=global`, 'Global OPS · jurisdições', { newTag: 'Hub' }),
      navItem(`${BASE}?tab=intelligence`, 'Inteligência fiscal', { newTag: 'New', keywords: 'scan contingencia' }),
      navItem(`${BASE}?tab=issuers`, 'Emissores e integração'),
    ], true),
    section('world', 'Mundial & prontidão', [
      navItem(`${BASE}?tab=corridors`, 'Corredores fiscais mundiais'),
      navItem(`${BASE}?tab=readiness`, 'Prontidão por emissor'),
      navItem(`${BASE}?tab=certifications`, 'Certificações (A1, LGPD…)'),
    ]),
    section('ops', 'Operação documental', [
      navItem(`${BASE}?tab=documents`, 'Documentos NFC-e / NF-e'),
      navItem(`${BASE}?tab=classification`, 'Classificação NCM / CFOP'),
      navItem(`${BASE}?tab=gaps`, 'Gaps unificados', { newTag: 'Workbench' }),
      navItem(`${BASE}?tab=slo`, 'SLA de emissão'),
    ]),
    section('integration', 'Integração & config', [
      navItem(`${BASE}?tab=webhooks`, 'Webhook DLQ'),
      navItem(`${BASE}?tab=config`, 'Tenant / SKU / Health'),
      navItem(`${BASE}?tab=governance`, 'Aprovações SEFAZ'),
    ]),
    section('legacy', 'Legado', [
      navItem('/fiscal/reconcile', 'Reconciliação legado', { keywords: 'reconcile billing' }),
    ]),
  ],
})
