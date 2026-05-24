import { navItem, opsGroup, section } from './opsNavHelpers'

const BASE = '/ops/money-cambio/admin'

export const moneyOpsNavGroup = opsGroup('moneyOps', '💵', 'Money OPS', {
  hub: navItem(BASE, 'Centro de comando', { newTag: 'Hub', keywords: 'overview kpi dashboard global' }),
  sections: [
    section('hub', 'Hub & inteligência', [
      navItem(BASE, 'Visão global (KPIs)', { newTag: 'Hub', keywords: 'overview dashboard' }),
      navItem(`${BASE}?tab=intelligence`, 'Intelligence · readiness', { newTag: 'New', keywords: 'insights analyze' }),
      navItem(`${BASE}?tab=players`, 'Players ecossistema', { keywords: 'locker inpost magalu' }),
      navItem(`${BASE}?tab=segments`, 'Segmentos', { keywords: 'carrier marketplace food' }),
      navItem(`${BASE}?tab=relations`, 'Relações entre players'),
    ], true),
    section('catalog', 'Catálogo monetário', [
      navItem(`${BASE}?tab=countries`, 'Países operacionais'),
      navItem(`${BASE}?tab=currencies`, 'Moedas ISO'),
      navItem(`${BASE}?tab=methods`, 'Métodos de pagamento'),
      navItem(`${BASE}?tab=matrix`, 'Matriz método × país'),
      navItem(`${BASE}?tab=aliases`, 'Aliases UI'),
      navItem(`${BASE}?tab=interfaces`, 'Interfaces (totem/app)'),
      navItem(`${BASE}?tab=wallets`, 'Wallet providers'),
      navItem(`${BASE}?tab=rails`, 'Payment rails', { newTag: 'New' }),
    ]),
    section('fx', 'FX & tesouraria', [
      navItem(`${BASE}?tab=corridors`, 'Corredores cross-border'),
      navItem(`${BASE}?tab=fx`, 'Taxas FX e conversão'),
      navItem(`${BASE}?tab=pricing`, 'Simulador de cotação', { newTag: 'New' }),
      navItem(`${BASE}?tab=fxlocks`, 'Travas FX (hedge)'),
      navItem(`${BASE}?tab=treasury`, 'Tesouraria / exposição', { newTag: 'New' }),
      navItem(`${BASE}?tab=settlements`, 'Calendário settlement (T+N)', { newTag: 'New' }),
    ]),
    section('governance', 'Compliance & integração', [
      navItem(`${BASE}?tab=compliance`, 'Limites AML/KYC'),
      navItem(`${BASE}?tab=audit`, 'Auditoria de taxas'),
      navItem(`${BASE}?tab=partners`, 'Parceiros FX (webhook/API)'),
    ]),
  ],
})

export const cambioOpsNavGroup = opsGroup('cambioOps', '💱', 'Câmbio OPS', {
  sections: [
    section('cambio', 'Atalhos Money & Cambio', [
      navItem(`${BASE}?tab=corridors`, 'Corredores cross-border'),
      navItem(`${BASE}?tab=fx`, 'Taxas FX e conversão'),
      navItem(`${BASE}?tab=pricing`, 'Simulador de cotação', { newTag: 'New' }),
      navItem(`${BASE}?tab=fxlocks`, 'Travas FX (hedge)'),
      navItem(`${BASE}?tab=compliance`, 'Limites AML/KYC'),
      navItem(`${BASE}?tab=audit`, 'Auditoria de taxas'),
      navItem(`${BASE}?tab=settlements`, 'Calendário settlement'),
      navItem(`${BASE}?tab=partners`, 'Parceiros integração'),
    ], true),
  ],
})
