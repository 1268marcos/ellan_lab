import type { OpsNavGroup } from './opsMenuTypes'
import { fiscalOpsNavGroup } from './fiscalOpsNav'
import { ordersOpsNavGroup } from './ordersOpsNav'
import { cambioOpsNavGroup, moneyOpsNavGroup } from './moneyOpsNav'
import { navItem, opsGroup, section } from './opsNavHelpers'
import { paymentsOpsNavGroup } from './paymentsOpsNav'

const P = '/ops/partners/admin'
const F = '/ops/finance/admin'
const M = '/ops/marketplace/admin'
const ML = '/ops/ml/admin'
const BI = '/ops/bi-analytics/admin'
const R = '/ops/rentals/admin'
const PR = '/ops/products/admin'
const PC = '/ops/privacy-compliance/admin'
const MK = '/ops/marketing/promotions'
const SUB = '/ops/subscriptions/admin'

const H = '/ops/hardware/admin'

export const OPS_MENU_GROUPS: OpsNavGroup[] = [
  opsGroup('ops', '🛠️', 'OPS', {
    hub: navItem('/ops', 'Monitoramento OPS', { newTag: 'Live' }),
    items: [
      navItem('/ops', 'Monitoramento OPS', { newTag: 'Hub' }),
      navItem('/dashboard', 'Dashboard'),
      navItem('/ops/lockers', 'Lockers'),
      navItem('/ops/lockers/create', 'Criar lockers'),
      navItem('/ops/manifests', 'Manifestos'),
    ],
  }),
  opsGroup('operations', '📡', 'Operations', {
    hub: navItem('/ops/lockers/map', 'Lockers Map', { newTag: 'Live' }),
    sections: [
      section('opsMap', 'Rede & NOC', [
        navItem('/ops/lockers/map', 'Lockers Map', { newTag: 'Map' }),
        navItem('/ops/noc-alerts', 'NOC Alerts', { newTag: 'WS' }),
        navItem('/ops/maintenance', 'Maintenance', { newTag: 'Kanban' }),
        navItem('/ops/sla-reports', 'SLA Reports'),
      ], true),
    ],
  }),
  opsGroup('cadastros', '📋', 'Cadastros OPS', {
    items: [
      navItem('/ops/payment-gateway/admin', 'Payment Gateway (PSP)'),
      navItem('/ops/capability/admin', 'Capability (config)', { newTag: 'Hub' }),
    ],
  }),
  opsGroup('capabilityOps', '⚡', 'Capability OPS', {
    hub: navItem('/ops/capability/admin', 'Hub Capability', { newTag: 'Hub' }),
    sections: [
      section('capHub', 'Configuração de capacidade', [
        navItem('/ops/capability/admin', 'Visão geral', { newTag: 'Hub' }),
        navItem('/ops/capability/admin?tab=profiles', 'Perfis region×canal'),
        navItem('/ops/capability/admin?tab=channels', 'Canais & contextos'),
        navItem('/ops/capability/admin?tab=regions', 'Regiões & moeda'),
        navItem('/ops/capability/admin?tab=catalogs', 'Catálogos pagamento'),
        navItem('/ops/capability/admin?tab=geo', 'País · província · locker'),
        navItem('/ops/capability/admin?tab=composition', 'Ações · métodos · constraints'),
        navItem('/ops/capability/admin?tab=webhooks', 'Webhook & API keys', {
          keywords: 'InPost DHL DPD Magalu MercadoLivre Amazon Correios CTT Worten',
        }),
        navItem('/ops/capability/admin?tab=deliveries', 'Entregas · DLQ replay'),
        navItem('/ops/capability/admin?tab=audit', 'Auditoria mudanças'),
      ], true),
      section('capMatrixEco', 'Matriz & ecossistema mundial', [
        navItem('/ops/capability/admin?tab=matrix', 'Matriz cobertura', { newTag: 'Pro' }),
        navItem('/ops/capability/admin?tab=ecosystem', 'Players & segmentos', {
          keywords: 'InPost DHL DPD Magalu MercadoLivre Amazon Correios CTT Worten El Corte Ingles',
        }),
        navItem('/ops/capability/admin?tab=ecosystem&view=locker', 'Locker world (InPost DHL…)', {
          keywords: 'locker-presence packstation parcel locker Correios CTT',
        }),
      ]),
      section('capTools', 'Ferramentas OPS', [
        navItem('/ops/capability/admin?tab=tools', 'Resolver · simular · templates', { newTag: 'Novo' }),
      ]),
      section('capIntelligence', 'Inteligência OPS', [
        navItem('/ops/capability/admin?tab=intelligence', 'World report', { newTag: 'Pro' }),
        navItem('/ops/capability/admin?tab=intelligence&view=readiness', 'Readiness por perfil'),
        navItem('/ops/capability/admin?tab=intelligence&view=insights', 'Insights abertos'),
        navItem('/ops/capability/admin?tab=intelligence&view=recommendations', 'Recomendações'),
        navItem('/ops/capability/admin?tab=intelligence&view=corridors', 'Corredores regionais'),
        navItem('/ops/capability/admin?tab=intelligence&view=flags', 'Feature flags'),
      ]),
      section('capIntegrations', 'Integrações cruzadas', [
        navItem('/ops/partners/admin?tab=capability_webhooks', 'Partner webhooks'),
        navItem(`${M}?tab=webhooks`, 'Marketplace webhooks'),
        navItem(`${ML}?tab=capabilities`, 'ML rede locker'),
        navItem('/ops/payment-gateway/admin', 'Payment Gateway'),
        navItem('/integrations/partners', 'Integrations hub'),
      ]),
    ],
  }),
  opsGroup('securityCrud', '🔐', 'Security', {
    hub: navItem('/security/users', 'Users & Roles', { newTag: 'CRUD' }),
    sections: [
      section('securityMain', 'Security', [
        navItem('/security/users', 'Users & Roles'),
        navItem('/security/permissions', 'Permissions'),
        navItem('/security/api-keys', 'API Keys'),
        navItem('/security/webhooks', 'Webhooks'),
      ]),
    ],
  }),
  opsGroup('integrationsOps', '🔌', 'Integrations', {
    hub: navItem('/integrations/partners', 'Partners', { newTag: 'Hub' }),
    sections: [
      section('integrationsMain', 'Integrations', [
        navItem('/integrations/partners', 'Partners', {
          keywords: 'SwipBox Cleveron InPost DPD DHL Magalu Mercado Livre',
        }),
        navItem('/integrations/marketplaces', 'Marketplaces', {
          keywords: 'Amazon Walmart Shopee Temu TikTok Shop',
        }),
        navItem('/integrations/carriers', 'Carriers', {
          keywords: 'Royal Mail La Poste Colissimo Yodel Swiss Post',
        }),
        navItem('/integrations/webhooks', 'Webhooks', { keywords: 'HMAC SHA256 webhook test' }),
      ]),
      section('biMl', 'BI · Analytics · ML', [
        navItem(BI, 'BI & Analytics OPS', { newTag: 'Hub' }),
        navItem(`${BI}?tab=players`, 'Players locker mundial'),
        navItem(ML, 'ML OPS', { newTag: 'Hub' }),
        navItem(`${ML}?tab=networks`, 'Redes locker ML'),
      ]),
    ],
  }),
  opsGroup('usersSecurityOps', '🔐', 'Users & Security OPS', {
    hub: navItem('/ops/access/security-admin?tab=overview', 'Hub segurança', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub', [
        navItem('/ops/access/security-admin?tab=overview', 'Visão geral', { newTag: 'Hub' }),
        navItem('/ops/access/security-admin?tab=domains', 'Domínios OPS · health'),
      ], true),
      section('governanca', 'Governança & valor', [
        navItem('/ops/access/security-admin?tab=intelligence', 'Inteligência OPS', { newTag: 'Pro' }),
        navItem('/ops/access/security-admin?tab=access-review', 'Certificação de acesso'),
        navItem('/ops/access/security-admin?tab=break-glass', 'Break-glass emergência', { newTag: 'P1' }),
        navItem('/ops/access/security-admin?tab=access-requests', 'Pedidos de acesso cross-domain'),
        navItem('/ops/access/security-admin?tab=jit-access', 'Acesso JIT temporário'),
        navItem('/ops/access/security-admin?tab=delegations', 'Delegação act-as'),
        navItem('/ops/access/security-admin?tab=entitlements', 'Entitlements remotos'),
        navItem('/ops/access/security-admin?tab=alerts', 'Alertas segurança'),
        navItem('/ops/access/security-admin?tab=compliance', 'LGPD · SOC2 · PCI'),
        navItem('/ops/access/security-admin?tab=templates', 'Templates onboarding'),
        navItem('/ops/access/security-admin?tab=matrix', 'Matriz usuário×domínio'),
      ]),
      section('ecosistema', 'Ecossistema mundial', [
        navItem('/ops/access/security-admin?tab=ecosystem', 'Mapa ecossistema'),
        navItem('/ops/access/security-admin?tab=locker-players', 'Players locker mundial', {
          newTag: 'Pro',
          keywords: 'InPost DHL Magalu Mercado Livre Amazon DPD Correios CTT Worten',
        }),
        navItem('/ops/access/security-admin?tab=taxonomy', 'Taxonomia mundial', {
          keywords: 'segmento food delivery PUDO agregador carrier',
        }),
        navItem('/ops/access/security-admin?tab=relations', 'Relações player↔player', { newTag: 'Pro' }),
      ]),
      section('identidade', 'Identidade', [
        navItem('/ops/access/security-admin?tab=users', 'Usuários'),
        navItem('/ops/access/security-admin?tab=user-360', 'Usuário 360°', { newTag: 'Pro' }),
        navItem('/ops/access/security-admin?tab=roles', 'Papéis (user_roles)'),
        navItem('/ops/access/security-admin?tab=role-catalog', 'Catálogo de roles'),
        navItem('/ops/access/security-admin?tab=permissions', 'Grupos de permissão'),
      ]),
      section(
        'appLayer',
        'Camada aplicação (sem RLS)',
        [
          navItem('/ops/access/security-admin?tab=critical-tables', 'Tabelas críticas · registry', {
            newTag: 'App',
            keywords: 'users privacy_consents audit_logs APPLICATION enforcement',
          }),
          navItem('/ops/access/security-admin?tab=critical-policies', 'Políticas por role × operação', {
            newTag: 'App',
          }),
          navItem('/ops/access/security-admin?tab=critical-access-log', 'Log de decisões de acesso', {
            keywords: 'ALLOWED DENIED critical_table',
          }),
          navItem('/ops/access/security-admin?tab=critical-audit-public', 'audit_logs público (imutável)', {
            newTag: 'App',
          }),
        ],
        true,
      ),
      section('rls', 'Autorização RLS (PostgreSQL)', [
        navItem('/ops/access/security-admin?tab=rls-middleware', 'Middleware JWT · API Key · RBAC', {
          newTag: 'RLS',
        }),
        navItem('/ops/access/security-admin?tab=rls-session', 'Variáveis de sessão PG', { newTag: 'RLS' }),
      ]),
      section('integracao', 'Integração & auditoria', [
        navItem('/ops/access/security-admin?tab=grants', 'Grants cross-domain', { newTag: 'Pro' }),
        navItem('/ops/access/security-admin?tab=webhooks', 'Webhooks OPS'),
        navItem('/ops/access/security-admin?tab=deliveries', 'Entregas webhook'),
        navItem('/ops/access/security-admin?tab=api-keys', 'API keys · rotação'),
        navItem('/ops/access/security-admin?tab=sessions', 'Sessões ativas'),
        navItem('/ops/access/security-admin?tab=identity', 'Identity / SSO (Okta)'),
        navItem('/ops/access/security-admin?tab=policy', 'Policy snapshots'),
        navItem('/ops/access/security-admin?tab=audit', 'Trilha security_audit_logs'),
      ]),
      section('cross', 'Cross-domain', [
        navItem('/ops/access/security-admin?tab=cross-domain', 'Vínculos legado'),
        navItem('/ops/partners/admin', 'Parceiros (InPost, DPD…)'),
        navItem('/ops/marketplace/admin', 'Marketplace (Magalu, ML…)'),
        navItem('/ops/hardware/admin', 'Hardware (SwipBox, InPost)'),
        navItem('/ops/payment-gateway/admin', 'Payment Gateway'),
      ]),
      section('legado', 'Legado', [navItem('/ops/access/user-roles', 'Papéis de acesso (legado)')]),
    ],
  }),
  opsGroup('hardwareOps', '🔧', 'Hardware OPS', {
    hub: navItem(H, 'Dashboard 360°', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub & vendors', [
        navItem(`${H}?tab=dashboard`, 'Dashboard cross-domain', { newTag: 'Hub' }),
        navItem(`${H}?tab=vendors`, 'Redes locker e vendors'),
        navItem(`${H}?tab=ecosystem`, 'Ecossistema mundial'),
      ], true),
      section('cross', 'Cross-domain', [
        navItem(`${H}?tab=marketplace`, 'Marketplace ↔ locker'),
        navItem(`${H}?tab=payments`, 'Payment Gateway ↔ locker'),
        navItem(`${H}?tab=carriers`, 'Carriers globais'),
        navItem(`${H}?tab=channels`, 'Integration Hub · canais', { newTag: 'Hub' }),
        navItem(`${H}?tab=world`, 'World Ops · certificações', {
          newTag: 'Pro',
          keywords: 'webhook DLQ replay dead-letter mirror marketplace certifications corridors SLA',
        }),
        navItem(`${H}?tab=references`, 'Refs outros domínios'),
        navItem(`${H}?tab=links`, 'Locker 360 · cross-domain', { newTag: 'New' }),
      ]),
      section('assets', 'Ativos & financeiro', [
        navItem(`${H}?tab=assets`, 'Ativos hardware'),
        navItem(`${H}?tab=finance`, 'CAPEX / OPEX'),
        navItem(`${H}?tab=operators`, 'Operadores de rede'),
      ]),
      section('runtime', 'Runtime & ops', [
        navItem(`${H}?tab=runtime`, 'Runtime MQTT'),
        navItem(`${H}?tab=topology`, 'Features · slots'),
        navItem(`${H}?tab=ops`, 'Devices · sync · telemetria'),
      ]),
    ],
  }),
  paymentsOpsNavGroup,
  moneyOpsNavGroup,
  cambioOpsNavGroup,
  fiscalOpsNavGroup,
  ordersOpsNavGroup,
  opsGroup('workersOps', '⚙️', 'Workers PostgreSQL', {
    hub: navItem('/ops/workers/admin', 'Visão geral', { newTag: 'Node' }),
    sections: [
      section('queues', 'Filas', [
        navItem('/ops/workers/admin?tab=overview', 'Dashboard filas', { newTag: 'Hub' }),
        navItem('/ops/workers/admin?tab=domain', 'Domain event outbox'),
        navItem('/ops/workers/admin?tab=lifecycle', 'Lifecycle deadlines'),
        navItem('/ops/workers/admin?tab=inventory', 'Inventory sync (Shopee · Magalu · ML)'),
        navItem('/ops/workers/admin?tab=dlq', 'Dead letter queue'),
      ], true),
      section('cross', 'Atalhos', [
        navItem('/ops/orders/admin?tab=overview', 'Pedidos OPS · hub'),
        navItem('/ops/orders/admin?tab=lookup', 'Pedidos OPS · Order 360'),
        navItem('/ops/orders/admin?tab=integration', 'Pedidos OPS · outbox & health'),
      ]),
    ],
  }),
  opsGroup('biAnalyticsOps', '📊', 'BI & Analytics OPS', {
    hub: navItem(BI, 'Hub BI/Analytics', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub & inteligência', [
        navItem(BI, 'Visão geral', { newTag: 'Hub' }),
        navItem(`${BI}?tab=intelligence`, 'Ops intelligence', { newTag: 'Pro' }),
        navItem(`${BI}?tab=readiness`, 'Prontidão dados', { newTag: 'New' }),
      ], true),
      section('data', 'Dados & marts', [
        navItem(`${BI}?tab=facts`, 'Analytics facts', { keywords: 'order_channel payload occurred_at' }),
        navItem(`${BI}?tab=marts`, 'Marts financeiros', {
          keywords: 'MRR locker_pnl partner_revenue_monthly company_mrr_trend',
        }),
        navItem(`${BI}?tab=refresh`, 'Refresh marts', { newTag: 'ETL' }),
        navItem(`${BI}?tab=lineage`, 'Data lineage'),
        navItem(`${BI}?tab=alerts`, 'Alertas KPI'),
      ]),
      section('ecosystem', 'Ecossistema mundial', [
        navItem(`${BI}?tab=players`, 'Players locker mundial', {
          keywords:
            'InPost DHL Magalu MercadoLivre Mercado Livre Amazon DPD Correios CTT Worten El Corte Ingles tier1',
        }),
        navItem(`${BI}?tab=taxonomy`, 'Taxonomia & presença mercado', { newTag: 'Global' }),
        navItem(`${BI}?tab=webhooks`, 'Webhooks capability'),
        navItem(`${BI}?tab=partners`, 'Parceiros BI · API keys'),
        navItem(`${BI}?tab=audit`, 'Auditoria OPS'),
      ]),
      section('monitoring', 'Monitoramento', [
        navItem(`${BI}?tab=kpis`, 'Definições KPI'),
        navItem(`${BI}?tab=reports`, 'Catálogo relatórios'),
        navItem(`${BI}?tab=exports`, 'Export jobs', { newTag: 'ETL' }),
        navItem(`${BI}?tab=efficiency`, 'Eficiência OPS', { newTag: 'Smart' }),
      ]),
      section('cross', 'Integração ML & Finance', [
        navItem(`${BI}?tab=integration`, 'Hub domínios unificados'),
        navItem('/ops/ml/admin', 'ML OPS'),
        navItem('/ops/analytics/financial', 'Analytics financeiro (MV)'),
        navItem('/intelligence/dashboard', 'Inteligência preditiva'),
      ]),
    ],
  }),
  opsGroup('mlOps', '🤖', 'ML OPS', {
    hub: navItem(ML, 'Visão geral', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub', [navItem(ML, 'Visão geral e cadastro', { newTag: 'Hub' })], true),
      section('data', 'Dados & modelos', [
        navItem(`${ML}?tab=partners`, 'Parceiros de dados'),
        navItem(`${ML}?tab=networks`, 'Redes locker mundiais'),
        navItem(`${ML}?tab=readiness`, 'Prontidão integração', { newTag: 'New' }),
        navItem(`${ML}?tab=models`, 'Modelos e versões'),
        navItem(`${ML}?tab=features`, 'Features diárias'),
        navItem(`${ML}?tab=catalog`, 'Catálogo features'),
      ]),
      section('runtime', 'Predição & ops', [
        navItem(`${ML}?tab=predictions`, 'Log de predições'),
        navItem(`${ML}?tab=feedback`, 'Feedback de modelo'),
        navItem(`${ML}?tab=use_cases`, 'Casos de uso'),
        navItem(`${ML}?tab=registry`, 'Model registry'),
        navItem(`${ML}?tab=training`, 'Experimentos'),
        navItem(`${ML}?tab=drift`, 'Drift / PSI'),
        navItem(`${ML}?tab=governance`, 'SLO e alertas'),
        navItem(`${ML}?tab=deployments`, 'Deployments'),
        navItem(`${ML}?tab=grants`, 'Grants cross-domain', { newTag: 'Pro' }),
        navItem(`${ML}?tab=efficiency`, 'Eficiência ML', { newTag: 'Smart' }),
      ]),
      section('cross', 'BI & Analytics', [
        navItem(BI, 'BI · Analytics · ML hub', { newTag: 'New' }),
        navItem(`${BI}?tab=players`, 'Players Tier-1 (InPost DHL ML…)', {
          keywords: 'Worten El Corte Ingles Correios CTT',
        }),
      ]),
    ],
  }),
  opsGroup('partnersOps', '🤝', 'Partners OPS', {
    hub: navItem(P, 'Visão 360', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub & onboarding', [
        navItem(P, 'Visão 360', { newTag: 'Hub' }),
        navItem(`${P}?tab=onboarding`, 'Onboarding B2B', { newTag: 'New' }),
        navItem(`${P}?tab=ecommerce`, 'E-commerce'),
        navItem(`${P}?tab=logistics`, 'Logística'),
      ], true),
      section('integration', 'Integração', [
        navItem(`${P}?tab=integrations`, 'Webhook e API keys'),
        navItem(`${P}?tab=webhook_monitor`, 'Entregas webhook'),
        navItem(`${P}?tab=integration_health`, 'Saúde integração'),
        navItem(`${P}?tab=outbox`, 'Outbox eventos'),
        navItem(`${P}?tab=capability_webhooks`, 'Webhooks + dead-letter'),
      ]),
      section('finance', 'Financeiro', [
        navItem(`${P}?tab=settlements`, 'Settlements'),
        navItem(`${P}?tab=billing`, 'Billing e line items'),
        navItem(`${P}?tab=invoices`, 'NF B2B'),
        navItem(`${P}?tab=credits`, 'Créditos'),
        navItem(`${P}?tab=holds`, 'Retenções pagamento'),
      ]),
      section('world', 'Mundial', [
        navItem(`${P}?tab=ecosystem`, 'Redes mundiais'),
        navItem(`${P}?tab=global_ops`, 'Global OPS'),
        navItem(`${P}?tab=stores`, 'Lojas C&C'),
        navItem(`${P}?tab=contacts`, 'Contatos B2B'),
        navItem('/ops/tenants/admin', 'Tenants white label'),
      ]),
      section('legacy', 'Legado v0', [
        navItem('/ops/partners/dashboard', 'Dashboard OPS'),
        navItem('/ops/partners/settlement', 'Settlement export'),
        navItem(`${P}?tab=sla`, 'SLA'),
        navItem(`${P}?tab=status`, 'Histórico status'),
      ]),
    ],
  }),
  opsGroup('rentalsOps', '🔑', 'Rentals OPS', {
    hub: navItem(R, 'Visão geral', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub & redes', [
        navItem(R, 'Visão geral', { newTag: 'Hub' }),
        navItem(`${R}?tab=networks`, 'Redes mundiais'),
        navItem(`${R}?tab=corridors`, 'Corredores'),
        navItem(`${R}?tab=onboarding`, 'Onboarding KYB'),
      ], true),
      section('ops', 'Operação', [
        navItem(`${R}?tab=capacity`, 'Capacidade'),
        navItem(`${R}?tab=operators`, 'Operadores B2B'),
        navItem(`${R}?tab=plans`, 'Planos'),
        navItem(`${R}?tab=contracts`, 'Contratos'),
        navItem(`${R}?tab=billing`, 'Faturamento'),
        navItem(`${R}?tab=settlements`, 'Liquidações'),
        navItem(`${R}?tab=sla`, 'Políticas SLA'),
        navItem(`${R}?tab=premium`, 'Breaches e disputas'),
      ]),
      section('tech', 'Eventos & integração', [
        navItem(`${R}?tab=events`, 'Eventos / auditoria'),
        navItem(`${R}?tab=integrations`, 'Webhooks e API keys'),
        navItem(`${R}?tab=advanced`, 'Avançado'),
      ]),
    ],
  }),
  opsGroup('privacyCompliance', '🔒', 'Privacy & Compliance OPS', {
    hub: navItem(PC, 'Compliance global', { newTag: 'Hub' }),
    sections: [
      section('hub', 'Hub', [
        navItem(PC, 'Visão geral'),
        navItem(`${PC}?tab=compliance`, 'Score compliance', { newTag: 'New' }),
        navItem(`${PC}?tab=regulation_hub`, 'Hub GDPR / LGPD / CCPA'),
      ], true),
      section('registry', 'Registro & políticas', [
        navItem(`${PC}?tab=regulations`, 'Marcos regulatórios'),
        navItem(`${PC}?tab=policies`, 'Políticas'),
        navItem(`${PC}?tab=legal_bases`, 'Bases legais'),
        navItem(`${PC}?tab=data_categories`, 'Categorias de dados'),
        navItem(`${PC}?tab=ropa`, 'ROPA · grafo', { newTag: 'New' }),
      ]),
      section(
        'appLayer',
        'Camada aplicação (sem RLS)',
        [
          navItem(`${PC}?tab=consents`, 'Consentimentos · enforcement app', {
            newTag: 'App',
            keywords: 'privacy_consents recorded_by_service access_policy_version',
          }),
          navItem('/ops/access/security-admin?tab=critical-policies', 'Políticas privacy (hub segurança)'),
        ],
        true,
      ),
      section('rights', 'Titulares & incidentes', [
        navItem(`${PC}?tab=consents`, 'Consentimentos'),
        navItem(`${PC}?tab=deletions`, 'Eliminação'),
        navItem(`${PC}?tab=subject_requests`, 'DSAR'),
        navItem(`${PC}?tab=breaches`, 'Incidentes 72h'),
        navItem(`${PC}?tab=dpia`, 'DPIA / LIA'),
        navItem(`${PC}?tab=transfers`, 'Transferências', { newTag: 'New' }),
      ]),
      section('ecosystem', 'Ecossistema & público', [
        navItem(`${PC}?tab=ecosystem`, 'Ecossistema locker'),
        navItem(`${PC}?tab=audit`, 'Auditoria'),
        navItem(`${PC}?tab=integrations`, 'Webhooks DLQ'),
        navItem('/legal/privacy/players', 'Docs por player'),
        navItem('/privacidade', 'Página pública'),
        navItem('/legal/cookies', 'Política de Cookies'),
      ]),
    ],
  }),
  opsGroup('financeOpsGlobal', '🌍', 'Finance OPS — Global', {
    sections: [
      section('global', 'Global', [
        navItem(`${F}?tab=networks`, 'Redes mundiais', { newTag: 'Global' }),
        navItem(`${F}?tab=intelligence`, 'Ecosystem Intelligence', { newTag: 'New' }),
        navItem(`${F}?tab=ecosystem`, 'Ecossistema e relações'),
        navItem(`${F}?tab=readiness`, 'Readiness score'),
        navItem(`${F}?tab=roadmap`, 'Roadmap integração'),
        navItem(`${F}?tab=contracts`, 'Contratos MSA'),
        navItem(`${F}?tab=slas`, 'SLAs e breaches'),
      ], true),
    ],
  }),
  opsGroup('financeOpsCommercial', '📊', 'Finance OPS — Comercial', {
    sections: [
      section('commercial', 'Comercial', [
        navItem(`${F}?tab=dunning`, 'Cobrança (dunning)'),
        navItem(`${F}?tab=tiers`, 'Níveis comerciais'),
        navItem(`${F}?tab=fx`, 'Câmbio (FX)'),
        navItem(`${F}?tab=tax`, 'Corredores fiscais'),
        navItem(`${F}?tab=documents`, 'Documentos NF'),
        navItem(`${F}?tab=audit`, 'Auditoria'),
        navItem(`${F}?tab=revrec`, 'Rev. receita'),
        navItem(`${F}?tab=jobs`, 'Jobs agendados'),
        navItem('/financial', 'Dashboard executivo', { newTag: 'CFO' }),
        navItem('/ops/analytics/financial', 'Analytics financeiro', { newTag: 'MV' }),
      ], true),
    ],
  }),
  opsGroup('financialExecutive', '📈', 'Financial', {
    hub: navItem('/financial', 'Executive Dashboard', { newTag: 'CFO' }),
    sections: [
      section('executive', 'Executivo', [
        navItem('/financial', 'Executive Dashboard', { newTag: 'CFO' }),
        navItem('/financial/locker-pnl', 'Locker P&L'),
        navItem('/financial/expansion', 'Expansion Simulator'),
        navItem('/financial/partners', 'Partner Settlements'),
      ], true),
    ],
  }),
  opsGroup('financeOps', '💰', 'Finance OPS', {
    hub: navItem(F, 'Visão geral', { newTag: 'Hub' }),
    sections: [
      section('core', 'Núcleo', [
        navItem(F, 'Visão geral', { newTag: 'Hub' }),
        navItem(`${F}?tab=partners`, 'Parceiros financeiros'),
        navItem(`${F}?tab=billing`, 'Billing'),
        navItem(`${F}?tab=invoices`, 'NF B2B'),
        navItem(`${F}?tab=settlements`, 'Settlements'),
      ], true),
      section('treasury', 'Tesouraria', [
        navItem(`${F}?tab=treasury`, 'Créditos e holds'),
        navItem(`${F}?tab=wallet`, 'Wallet'),
        navItem(`${F}?tab=pnl`, 'PnL locker'),
        navItem('/financial', 'Dashboard executivo', { newTag: 'CFO' }),
        navItem('/ops/analytics/financial', 'Analytics financeiro', { newTag: 'MV' }),
        navItem(`${F}?tab=reconciliation`, 'Gaps fiscais'),
      ]),
      section('ops', 'Ops & billing', [
        navItem(`${F}?tab=webhooks`, 'Webhook DLQ'),
        navItem(`${F}?tab=ops`, 'NF ops e eventos'),
      ]),
    ],
  }),
  opsGroup('marketplace', '🏪', 'Marketplace OPS', {
    hub: navItem(`${M}?tab=overview`, 'Visão geral', { newTag: 'Hub' }),
    sections: [
      section('core', 'Núcleo', [
        navItem(`${M}?tab=overview`, 'Dashboard KPIs', { newTag: 'Hub' }),
        navItem(`${M}?tab=sellers`, 'Sellers'),
        navItem(`${M}?tab=products`, 'Produtos'),
        navItem(`${M}?tab=categories`, 'Categorias'),
        navItem(`${M}?tab=channels`, 'Canais e redes locker', {
          keywords: 'InPost DHL Magalu Mercado Livre Amazon DPD Correios CTT Worten El Corte Ingles coverage',
        }),
        navItem(`${M}?tab=reviews`, 'Avaliações'),
      ], true),
      section('integration', 'Integração & Global OPS', [
        navItem(`${M}?tab=readiness`, 'Prontidão integração', { newTag: 'New' }),
        navItem(`${M}?tab=readiness`, 'Global OPS · corredores · SLA', {
          keywords: 'certifications corridors capability webhooks DLQ replay seed',
        }),
        navItem('/ops/workers/admin?tab=inventory', 'Sync estoque (Shopee · Magalu · ML)', {
          newTag: 'Node',
        }),
      ]),
      section('finance', 'Financeiro', [
        navItem(`${M}?tab=settlements`, 'Repasses'),
        navItem(`${M}?tab=payouts`, 'Contas PIX'),
        navItem(`${M}?tab=contacts`, 'Contatos'),
        navItem(`${M}?tab=commissions`, 'Comissões'),
        navItem(`${M}?tab=kyc`, 'KYC / compliance'),
        navItem(`${M}?tab=disputes`, 'Disputas'),
      ]),
      section('sellerIntegrations', 'Seller · integrações', [
        navItem(`${M}?tab=integrations`, 'Webhooks & API keys', {
          keywords: 'seller_webhook_endpoints seller_api_keys rotate HMAC',
        }),
        navItem(`${M}?tab=audit`, 'Auditoria sync', {
          keywords: 'marketplace_sync_audit_log readiness channel',
        }),
      ]),
      section('sellerProfessional', 'Seller · programa global', [
        navItem(`${M}?tab=tiers`, 'Programas & tiers', {
          keywords: 'STARTER GROWTH ENTERPRISE Magalu Mercado Livre commission',
        }),
        navItem(`${M}?tab=compliance`, 'Compliance fiscal', {
          keywords: 'IOSS VAT OSS BR PT ES cross-border fiscal',
        }),
        navItem(`${M}?tab=performance`, 'Performance mensal', { keywords: 'GMV OTD defect chargeback' }),
        navItem(`${M}?tab=agreements`, 'Contratos & DPA', { keywords: 'MARKETPLACE_TERMS DATA_PROCESSING signed' }),
        navItem(`${M}?tab=risk`, 'Risco & fraude', { keywords: 'risk_score LOW MEDIUM HIGH KYC' }),
      ]),
    ],
  }),
  opsGroup('marketing', '🎯', 'Marketing', {
    hub: navItem(MK, 'Hub Promoções', { newTag: 'Hub' }),
    sections: [
      section('promo', 'Promoções', [
        navItem(MK, 'Hub Promoções', { newTag: 'Hub' }),
        navItem(`${MK}?tab=campaigns`, 'Campanhas'),
        navItem(`${MK}?tab=promotions`, 'Promoções'),
        navItem(`${MK}?tab=redemptions`, 'Resgates'),
        navItem(`${MK}?tab=lab`, 'Laboratório', { newTag: 'Lab' }),
      ], true),
      section('catalog', 'Catálogo', [
        navItem('/ops/products/pricing-fiscal', 'Pricing & fiscal lab'),
        navItem(`${PR}?tab=bundles`, 'Bundles'),
        navItem('/ops/products/pricing-rules', 'Regras de preço'),
      ]),
    ],
  }),
  opsGroup('subscriptions', '💳', 'Assinaturas', {
    hub: navItem(SUB, 'Hub Assinaturas', { newTag: 'Hub' }),
    sections: [
      section('subHub', 'Hub & analytics', [
        navItem(SUB, 'Visão geral & MRR', { newTag: 'Hub' }),
        navItem(`${SUB}?tab=analytics`, 'Analytics & tendências MRR', {
          keywords: 'MRR ARR churn trends metrics',
        }),
        navItem(`${SUB}?tab=ecosystem`, 'Ecossistema mundial', {
          keywords:
            'InPost DHL Magalu Mercado Livre Amazon DPD Correios CTT Worten El Corte Inglés SwipBox Packeta sync',
        }),
      ], true),
      section('subCatalog', 'Planos & catálogo', [
        navItem(`${SUB}?tab=plans`, 'Planos BASIC · PREMIUM · PRO · ENTERPRISE', {
          keywords: 'subscription_plans pricing tier',
        }),
        navItem(`${SUB}?tab=entitlements`, 'Entitlements por player', {
          keywords: 'subscription_plan_entitlements locker marketplace',
        }),
        navItem(`${SUB}?tab=partners`, 'Programas parceiros B2B', {
          keywords: 'Magalu Mercado Livre InPost DHL marketplace carrier KYB revenue share',
        }),
      ]),
      section('subOps', 'Operação & assinantes', [
        navItem(`${SUB}?tab=subscriptions`, 'Assinaturas ativas · 360°', {
          keywords: 'customer_subscriptions trial cancel renew subscriber detail 360',
        }),
        navItem(`${SUB}?tab=benefits`, 'Uso de benefícios', {
          keywords: 'FREE_SHIPPING PRIORITY_SHELF subscription_benefits_usage',
        }),
        navItem(`${SUB}?tab=billing`, 'Faturamento & invoices', {
          keywords: 'subscription_invoices mark-paid generate',
        }),
        navItem(`${SUB}?tab=events`, 'Eventos de lifecycle', {
          keywords: 'subscription_events created renewed cancelled',
        }),
        navItem(`${SUB}?tab=dunning`, 'Dunning & inadimplência', {
          newTag: 'P1',
          keywords: 'PAST_DUE subscription_dunning_cases resolve',
        }),
      ]),
      section('subIntegrations', 'Integrações & rede', [
        navItem(`${SUB}?tab=integrations`, 'Webhooks & API keys', {
          keywords: 'webhook HMAC rotate api key sub_ partner',
        }),
        navItem(`${SUB}?tab=deliveries`, 'Entregas webhook', {
          newTag: 'Log',
          keywords: 'subscription_webhook_deliveries simulate delivery',
        }),
        navItem(`${SUB}?tab=relations`, 'Relações player↔player', {
          newTag: 'Pro',
          keywords: 'subscription_player_relations FOOD_HANDOFF integration',
        }),
        navItem(`${SUB}?tab=food_delivery`, 'Food delivery handoffs', {
          keywords: 'iFood Rappi Uber Eats Glovo Deliveroo DoorDash subscription_food_delivery_handoffs',
        }),
      ]),
      section('subGrowth', 'Growth & retenção', [
        navItem(`${SUB}?tab=premium`, 'Premium · health & referrals', {
          newTag: 'Pro',
          keywords:
            'health churn referral gift loyalty experiment renewal benefit-check compare-matrix at-risk',
        }),
        navItem(`${SUB}?tab=global`, 'Global · preços & compliance', {
          newTag: 'World',
          keywords:
            'regional pricing addon pause SLA settlement LGPD consent retention BR PT EU UK US ENTERPRISE',
        }),
        navItem(`${SUB}?tab=efficiency`, 'Eficiência · inbox & cupons', {
          newTag: 'Smart',
          keywords:
            'promo code plan change upgrade matrix automation family usage meter ops inbox proration',
        }),
      ]),
    ],
  }),
  opsGroup('productsCatalog', '📦', 'Produtos & Catálogo', {
    hub: navItem(PR, 'Hub produtos', { newTag: 'Hub' }),
    sections: [
      section('pim', 'PIM & mundial', [
        navItem(PR, 'Hub visão geral'),
        navItem(`${PR}?tab=ecosystem`, 'Ecossistema mundial'),
        navItem(`${PR}?tab=taxonomy`, 'Taxonomias'),
        navItem(`${PR}?tab=channels`, 'Canais'),
        navItem(`${PR}?tab=attributes`, 'Atributos'),
      ], true),
      section('sku', 'SKU & estoque', [
        navItem('/ops/products/catalog', 'Catálogo SKU'),
        navItem('/ops/products/categories', 'Categorias'),
        navItem('/ops/products/assets', 'Mídia & barcodes'),
        navItem(`${PR}?tab=bundles`, 'Bundles'),
        navItem(`${PR}?tab=fiscal`, 'Pricing & fiscal'),
        navItem(`${PR}?tab=inventory`, 'Estoque'),
      ]),
    ],
  }),
  opsGroup('lifecycle', '♻️', 'Ciclo de Vida', {
    items: [
      navItem('/lifecycle/metrics', 'Métricas'),
      navItem('/lifecycle/ranking', 'Ranking'),
      navItem('/lifecycle/health', 'Saúde'),
    ],
  }),
  opsGroup('intelligence', '🧠', 'Inteligência', {
    hub: navItem('/intelligence/dashboard', 'Dashboard preditivo', { newTag: 'ML' }),
    sections: [
      section('intel', 'Predição', [
        navItem('/intelligence/dashboard', 'Dashboard preditivo'),
        navItem('/intelligence/compatibility', 'Compatibilidade'),
        navItem('/intelligence/predictive-health', 'Saúde preditiva'),
        navItem('/intelligence/occupancy-forecast', 'Previsão ocupação'),
        navItem('/intelligence/feedback-insights', 'Insights feedback'),
      ], true),
      section('intelOps', 'OPS BI · ML', [
        navItem(BI, 'BI & Analytics OPS'),
        navItem(ML, 'ML OPS'),
        navItem('/ops/analytics/financial', 'Analytics financeiro (MV)'),
      ]),
      section('intelPartners', 'Parceiros', [
        navItem('/partners/catalog', 'Catálogo'),
        navItem('/partners/webhooks', 'Webhooks'),
      ]),
    ],
  }),
  opsGroup('runtime', '⚙️', 'Runtime / Operacional', {
    items: [
      navItem('/runtime/slots', 'Slots e ocupação'),
      navItem('/runtime/allocations', 'Alocações'),
    ],
  }),
  opsGroup('operacional', '📡', 'Operacional', {
    items: [
      navItem('/partners/ops/lockers', 'Lockers'),
      navItem('/partners/ops/pickups', 'Pickups ativos'),
    ],
  }),
  opsGroup('fiscal', '💼', 'Fiscal (parceiro)', {
    items: [
      navItem('/finance/wallet', 'Wallet'),
      navItem('/finance/transactions', 'Transações'),
      navItem('/finance/billing/cycles', 'Ciclos'),
      navItem('/finance/invoices', 'Notas B2B'),
      navItem('/finance/credit-notes', 'Créditos'),
      navItem('/finance/disputes', 'Disputas'),
      navItem('/fiscal/reconcile', 'Reconciliação'),
    ],
  }),
]
