import React, { useState } from "react";
import { Link } from "react-router-dom";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const TIMELINE_TEMPLATE_JSON = `{
  "date": "YYYY-MM-DD",
  "scope": "L-3 D4",
  "title": "Resumo curto da entrega",
  "description": "Descrição breve do valor operacional entregue.",
  "uiRoutesNew": [
    "/ops/nova-rota-ui"
  ],
  "apiRoutesNew": [
    "GET /alguma/rota-nova"
  ],
  "routes": [
    "GET /alguma/rota",
    "POST /alguma/rota"
  ],
  "directLink": "/ops/alguma-pagina",
  "directLinkLabel": "Abrir página operacional"
}`;

const UPDATES = [
  {
    date: "2026-04-29",
    scope: "Fiscal UX - integração com FG-1 wave scope",
    title: "Badge IN WAVE (FG-1) no fiscal/countries sem regra hardcoded",
    description:
      "Conexão do cockpit fiscal/countries ao endpoint `global/fg1-wave-scope`: cada país agora exibe badge IN WAVE/OUT WAVE com base no backend, incluindo campo no export CSV/JSON para rastreabilidade do escopo da onda.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1-wave-scope"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir badge IN WAVE no cockpit fiscal",
  },
  {
    date: "2026-04-29",
    scope: "FG-1 execução - export e scope de onda",
    title: "Export CSV/JSON no fiscal/countries + endpoint FG-1 wave scope",
    description:
      "Microevolução operacional aplicada: o board fiscal/countries agora exporta snapshot em CSV/JSON para anexar no acompanhamento diário. Na sequência do roteiro, foi adicionado endpoint admin com escopo formal da onda FG-1 (países + cenários obrigatórios).",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1-wave-scope"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_global_catalog_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /ops/updates",
    ],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir board com export + avanço FG-1",
  },
  {
    date: "2026-04-29",
    scope: "Fiscal UX - board vivo FG-1/FG-2",
    title: "Status por país (TODO/IN_PROGRESS/DONE) no fiscal/countries",
    description:
      "Evolução do cockpit fiscal/countries para execução diária: adição de status por país com persistência local, filtro por execução e contadores em tempo real para operar a onda FG-1/FG-2 como board vivo.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir board vivo por país no fiscal/countries",
  },
  {
    date: "2026-04-29",
    scope: "Frontend UX - varredura geral de órfãos",
    title: "Checklist de constantes/helpers órfãos fora de OPS (resultado limpo)",
    description:
      "Varredura automática aplicada no restante do frontend (fora do escopo OPS já tratado): nenhuma constante/helper local órfã adicional foi encontrada em arquivos JS/JSX/TS/TSX, confirmando base enxuta após os refactors recentes.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src (scan de JS/JSX/TS/TSX fora de OPS)",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir registro da varredura geral no frontend",
  },
  {
    date: "2026-04-29",
    scope: "Fiscal UX - cockpit de países FG-1/FG-2",
    title: "Nova página fiscal/countries com filtros por região/prioridade/autoridade",
    description:
      "Entrega do cockpit de execução FG-1/FG-2: página fiscal/countries com filtros operacionais sobre o catálogo global, conectada ao menu FISCAL para priorização rápida por região, tier e autoridade.",
    uiRoutesNew: ["/fiscal/countries", "/fiscal", "/fiscal/updates"],
    apiRoutesNew: ["GET /admin/fiscal/global/catalog"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "UI /ops/updates",
    ],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit fiscal/countries",
  },
  {
    date: "2026-04-29",
    scope: "Fiscal UX - menu dedicado",
    title: "Novo menu FISCAL com páginas fiscal/global e fiscal/updates",
    description:
      "Para acompanhar a expansão multipaís, foi criado menu dedicado FISCAL no topo (desktop e mobile), com rotas protegidas para catálogo/matriz global e histórico próprio de updates fiscais, no mesmo padrão operacional já usado em OPS.",
    uiRoutesNew: ["/fiscal", "/fiscal/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/catalog",
      "GET /admin/fiscal/global/scenario-matrix",
    ],
    routes: [
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalUpdatesPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir menu e página FISCAL global",
  },
  {
    date: "2026-04-29",
    scope: "OPS UX - cleanup de helpers órfãos",
    title: "Varredura final de constantes não-style sem uso nas páginas OPS",
    description:
      "Rodada complementar de limpeza técnica executada após a padronização de headers: remoção de helpers e constantes locais legadas sem referência ativa nas páginas OPS/rotas OPS, reduzindo ruído e risco de manutenção futura.",
    uiRoutesNew: ["/ops/updates", "/ops/sp/kiosk"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/RegionPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir registro da varredura de helpers órfãos",
  },
  {
    date: "2026-04-29",
    scope: "OPS UX - dead style cleanup final",
    title: "Rodada final de limpeza de estilos órfãos após header unificado",
    description:
      "Limpeza final de manutenção aplicada nas páginas OPS após extração do OpsPageTitleHeader: remoção de constantes de estilo locais sem uso para reduzir ruído visual no código e manter a base pronta para evolução do padrão de header.",
    uiRoutesNew: ["/ops/audit", "/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsAuditPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir registro da limpeza final de estilos",
  },
  {
    date: "2026-04-29",
    scope: "FG-0 Foundation - catálogo e matriz canônica",
    title: "Endpoints admin para catálogo fiscal global e scenario matrix",
    description:
      "Primeiro sprint codado da trilha global: o billing_fiscal_service agora expõe catálogo fiscal multipaís e matriz canônica de cenários obrigatórios via rotas admin protegidas por token interno, preparando execução de FG-1/FG-2 sem depender só de documentação.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/catalog",
      "GET /admin/fiscal/global/scenario-matrix",
    ],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_global_catalog_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir entrega FG-0 em execução",
  },
  {
    date: "2026-04-29",
    scope: "OPS UX - Header unificado",
    title: "Componente único OpsPageTitleHeader para título, versão e ajuda",
    description:
      "Refinamento visual final aplicado para eliminar divergência de header: criação do componente OpsPageTitleHeader e adoção nas páginas OPS (incluindo rotas compartilhadas de /ops/*), padronizando ordem e espaçamento entre h1, badge de versão e ação de Ajuda.",
    uiRoutesNew: ["/ops/audit", "/ops/health", "/ops/reconciliation", "/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/components/OpsPageTitleHeader.jsx",
      "Frontend: páginas OPS e rotas compartilhadas /ops/*",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir registro do header unificado OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Gate UX - constantes centralizadas de escopo",
    title: "Textos de escopo extraídos para src/constants/fiscalScope.js",
    description:
      "Microajuste de manutenção aplicado: os textos de escopo dos gates fiscais foram centralizados em constantes compartilhadas, reduzindo risco de divergência entre ops/health, ops/fiscal/providers e util de summary.",
    uiRoutesNew: ["/ops/health", "/ops/fiscal/providers"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/constants/fiscalScope.js",
      "Frontend: 01_source/frontend/src/utils/fiscalScopeSummary.js",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir padronização de constantes de escopo",
  },
  {
    date: "2026-04-29",
    scope: "OPS Gate UX - util compartilhado de escopo",
    title: "Helper de summary fiscal extraído para src/utils (fonte única de regra)",
    description:
      "Refatoração para consistência e evolução segura: a regra de prefixo de escopo para summaries genéricos de gates fiscais foi extraída para util compartilhado e passou a ser importada por ops/health e ops/fiscal/providers, eliminando duplicação.",
    uiRoutesNew: ["/ops/health", "/ops/fiscal/providers"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/utils/fiscalScopeSummary.js",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir entregas com util compartilhado de escopo",
  },
  {
    date: "2026-04-29",
    scope: "OPS Gate UX - summary/tooltips com escopo",
    title: "Prefixo de escopo aplicado quando summary do backend é genérico",
    description:
      "Padronização de consistência no ELLAN LAB: os summaries dos gates BR/PT agora recebem prefixo explícito de escopo (Trilha B real BR/PT) quando o payload vier genérico, com o mesmo texto também em tooltip (`title`) nas telas ops/health e ops/fiscal/providers.",
    uiRoutesNew: ["/ops/health", "/ops/fiscal/providers"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir summaries padronizados com escopo",
  },
  {
    date: "2026-04-29",
    scope: "OPS Fiscal Providers - linguagem de escopo explícito",
    title: "Cards BR/PT alinhados ao padrão de escopo atual no ops/health",
    description:
      "Padronização de linguagem aplicada em ops/fiscal/providers: títulos e ações dos cards de gate BR/PT passaram a indicar explicitamente o escopo atual da Trilha B real, evitando interpretação de que sejam os únicos gates fiscais futuros.",
    uiRoutesNew: ["/ops/fiscal/providers", "/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers",
    directLinkLabel: "Abrir cards de gate com escopo explícito",
  },
  {
    date: "2026-04-29",
    scope: "OPS UX - Ajuda no título em todas as rotas OPS",
    title: "Botão Ajuda migrado para o título de todas as páginas /ops/*",
    description:
      "Padronização visual concluída: o botão ?/Ajuda saiu do bloco Contexto Ops e foi movido para o título das páginas OPS, com conteúdo rico por rota centralizado em arquivo dedicado. A experiência ficou consistente entre dashboards, logística, produtos, integrações, partners, políticas, dev, regiões e kiosk.",
    uiRoutesNew: [
      "/ops/health",
      "/ops/audit",
      "/ops/reconciliation",
      "/ops/analytics/pickup",
      "/ops/updates",
    ],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/components/OpsRouteHelpButton.jsx",
      "Frontend: 01_source/frontend/src/constants/opsTutorialContent.js",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: páginas OPS e rotas compartilhadas de /ops/*",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir registro da migração de Ajuda para o título",
  },
  {
    date: "2026-04-29",
    scope: "OPS Health - criticidade e nomenclatura de gates",
    title: "Botões por criticidade (Gate x Rollback) e título com escopo explícito",
    description:
      "Ajuste operacional aplicado: no card de gates fiscais do ops/health, comandos de rollback receberam visual de alerta e comandos de gate visual informativo. O título também foi ajustado para indicar claramente o escopo atual (Trilha B real BR/PT), sem sugerir que estes são os únicos gates fiscais futuros.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card de gates com criticidade e escopo explícito",
  },
  {
    date: "2026-04-29",
    scope: "OPS Health - ações rápidas de plantão",
    title: "Botões de cópia para Gate/Rollback BR/PT no card fiscal",
    description:
      "Sprint de agilidade operacional: o card fiscal no ops/health agora inclui botões para copiar comandos de Gate BR/PT e Rollback BR/PT, reduzindo tempo de resposta durante incidente e evitando erro manual de digitação.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir ações rápidas de plantão no gate fiscal",
  },
  {
    date: "2026-04-29",
    scope: "OPS Fiscal Providers - reforço visual de navegação",
    title: "Rótulo temporário 'Seção alvo' durante highlight por âncora",
    description:
      "Aprimoramento de leitura rápida no plantão: além do auto-scroll suave e highlight, as seções BR/PT agora exibem o rótulo temporário 'Seção alvo' enquanto o foco por âncora está ativo.",
    uiRoutesNew: ["/ops/fiscal/providers"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers#go-no-go-pt",
    directLinkLabel: "Abrir com rótulo temporário de seção alvo",
  },
  {
    date: "2026-04-29",
    scope: "OPS Fiscal Providers - Navegação por âncora",
    title: "Auto-scroll suave + destaque temporário no alvo BR/PT",
    description:
      "Melhoria de velocidade no plantão: ao abrir ops/fiscal/providers com âncora (#go-no-go-br ou #go-no-go-pt), a tela faz scroll suave automático para a seção alvo e aplica destaque visual temporário para facilitar foco imediato.",
    uiRoutesNew: ["/ops/fiscal/providers", "/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers#go-no-go-br",
    directLinkLabel: "Abrir com auto-scroll e highlight no BR",
  },
  {
    date: "2026-04-29",
    scope: "OPS Health -> Fiscal Providers (drill-down)",
    title: "Links diretos BR/PT no card de Gate fiscal para abrir contexto em 1 clique",
    description:
      "Melhoria de fluxo operacional: o card de Gate fiscal BR/PT no ops/health passou a ter links de drill-down por país, abrindo ops/fiscal/providers já na seção correta (âncoras BR/PT) para investigação rápida.",
    uiRoutesNew: ["/ops/health", "/ops/fiscal/providers"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsFiscalProvidersPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card com drill-down BR/PT",
  },
  {
    date: "2026-04-29",
    scope: "OPS Health - Gate fiscal resumido",
    title: "Card GO/NO-GO BR/PT no ops/health para leitura rápida de plantão",
    description:
      "Próximo sprint operacional aplicado: o painel de saúde agora exibe o gate fiscal BR/PT (snapshot atual) com decisão GO/NO-GO por país, resumo e botão de atualização, reduzindo troca de contexto com ops/fiscal/providers durante plantão.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir gate fiscal BR/PT no ops/health",
  },
  {
    date: "2026-04-29",
    scope: "OPS Plantão - Padronização de semáforo",
    title: "Texto de razão do semáforo unificado entre ops/audit e ops/health",
    description:
      "Padronização concluída para plantão: ambos os cards de Última sanidade OPS agora usam a mesma redação operacional de razão para Verde/Amarelo/Vermelho, eliminando divergência de interpretação entre telas.",
    uiRoutesNew: ["/ops/audit", "/ops/health"],
    apiRoutesNew: ["GET /dev-admin/ops-sanity/latest"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsAuditPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir cards padronizados de sanidade OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Health - Semáforo de sanidade",
    title: "Card resumido de plantão com Última sanidade OPS no ops/health",
    description:
      "Entrega concluída no painel de saúde operacional: inclusão do card de sanidade OPS com botão de atualização e semáforo visual (verde/amarelo/vermelho) baseado em report.result e fail_count, no mesmo padrão operacional do ops/audit.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: ["GET /dev-admin/ops-sanity/latest"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir semáforo de sanidade no ops/health",
  },
  {
    date: "2026-04-29",
    scope: "OPS UX - Tutoriais in-page (piloto)",
    title: "Botão ? padronizado em todas as rotas OPS + conteúdo centralizado",
    description:
      "Padronização final aplicada: botão de ajuda consolidado no Contexto Ops para todas as rotas /ops/* (evitando inconsistência entre páginas) e textos movidos para arquivo dedicado por domínio para facilitar manutenção. Preferência por usuário/página em localStorage e reset em /ops/updates permanecem ativos.",
    uiRoutesNew: ["/ops/updates", "/ops/audit", "/ops/health", "/ops/reconciliation"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/components/OpsHelpTutorialModal.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/constants/opsTutorialContent.js",
      "Frontend: 01_source/frontend/src/pages/OpsAuditPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsReconciliationPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir reset e histórico de tutoriais OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Audit - Semáforo visual de sanidade",
    title: "Card Última sanidade OPS com status verde/amarelo/vermelho",
    description:
      "Melhoria visual no ops/audit: o card de última sanidade ganhou semáforo operacional com regras por report.result e fail_count, facilitando decisão rápida de plantão sem abrir o JSON completo.",
    uiRoutesNew: ["/ops/audit"],
    apiRoutesNew: ["GET /dev-admin/ops-sanity/latest"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsAuditPage.jsx",
      "UI /ops/updates",
    ],
    directLink: "/ops/audit",
    directLinkLabel: "Abrir semáforo de sanidade OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Audit - Última sanidade automática",
    title: "Card no ops/audit lendo ops_sanity_latest.json automaticamente",
    description:
      "Conexão concluída entre auditoria e sanidade OPS: o ops/audit agora consulta endpoint dedicado para carregar o último relatório JSON e exibe card com resultado final, falhas e timestamp, com botão de atualização.",
    uiRoutesNew: ["/ops/audit"],
    apiRoutesNew: ["GET /dev-admin/ops-sanity/latest"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsAuditPage.jsx",
      "Backend: 01_source/order_pickup_service/app/routers/dev_admin.py",
      "Infra: 02_docker/docker-compose.yml (volume ../04_logs:/app/ops_logs)",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/audit",
    directLinkLabel: "Abrir card de última sanidade OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Automacao - Relatorio JSON para auditoria",
    title: "run_ops_sanity com --json e trilha estável para ops/audit",
    description:
      "Automação expandida para auditoria: script de sanidade OPS agora exporta relatório estruturado em JSON, mantendo histórico por timestamp e um arquivo latest estável para consumo direto no fluxo ops/audit.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Script: 02_docker/run_ops_sanity.sh (--json, --json-path)",
      "Artefato: 04_logs/ops/ops_sanity_<timestamp>.json",
      "Artefato: 04_logs/ops/ops_sanity_latest.json",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir entrega de JSON para auditoria OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Automacao - Sanidade end-to-end",
    title: "Script run_ops_sanity.sh para checagem única após troca de OPS_TOKEN",
    description:
      "Automação operacional adicionada para plantão: script único executa validações dos endpoints críticos OPS e fiscal em sequência, com leitura de token via .env e resultado final consolidado (OK/FAIL) em um comando.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /partners/ops/settlements/reconciliation/top-divergences",
      "GET /ops/integration/order-events-outbox",
      "GET /ops/integration/order-events-outbox/dead-letter-priority",
      "GET /admin/fiscal/providers/status",
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Script: 02_docker/run_ops_sanity.sh",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir automação de sanidade OPS",
  },
  {
    date: "2026-04-29",
    scope: "OPS Sanidade - novo token + correção endpoint",
    title: "Validação de fluxo OPS com novo OPS_TOKEN e fix em dead-letter-priority",
    description:
      "Checagem de sanidade executada com novo OPS_TOKEN nos endpoints críticos do fluxo OPS. Foi identificado e corrigido um erro 500 no endpoint de priorização de dead letters (ajuste de cast SQLAlchemy), com revalidação em 200 após rebuild do order_pickup_service.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /partners/ops/settlements/reconciliation/top-divergences",
      "GET /ops/integration/order-events-outbox",
      "GET /ops/integration/order-events-outbox/dead-letter-priority",
      "GET /admin/fiscal/providers/status",
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Backend: 01_source/order_pickup_service/app/routers/integration_ops.py",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir sanidade OPS com novo token",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Preflight consolidado",
    title: "Script único de decisão GO/NO-GO (ENV + gates BR/PT)",
    description:
      "Novo passo operacional para reduzir erro manual: script run_f3_preflight.sh valida variáveis de ambiente críticas, executa os gates BR/PT e retorna decisão final GO/NO_GO em uma única execução.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Script: 02_docker/run_f3_preflight.sh",
      "DOC docs/F3_RUNBOOK_GO_LIVE_REAL_BR_PT.md",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir preflight consolidado F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Padronizacao ENV",
    title: "Bloco fiscal real oficializado em .env e arquivos de referência",
    description:
      "Padronização operacional aplicada: as variáveis FISCAL_REAL_PROVIDER_* agora estão documentadas no 02_docker/.env e também nos arquivos de referência (.env.example, .env.development, .env.production), reduzindo inconsistência entre ambientes.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Infra: 02_docker/.env",
      "Infra: 02_docker/.env.example",
      "Infra: 02_docker/.env.development",
      "Infra: 02_docker/.env.production",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir padronização ENV F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Simulacao local GO/NO-GO",
    title: "ENV local de laboratório para treino operacional sem credenciais reais",
    description:
      "Foi adicionado arquivo de ambiente local sem segredos para simulação controlada da trilha real BR/PT, permitindo treinar fluxo de gate, painel OPS e rollback por flag antes do go-live com credenciais oficiais.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Infra: 02_docker/.env.f3-real.local.example",
      "Script: 02_docker/run_f3_go_no_go.sh",
      "DOC docs/F3_RUNBOOK_GO_LIVE_REAL_BR_PT.md",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir template local de simulação F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - ENV template de go-live",
    title: "Arquivo exemplo de ENV real BR/PT com checklist de preenchimento",
    description:
      "Foi criado template operacional para acelerar a virada real quando credenciais estiverem disponíveis: arquivo .env de exemplo com placeholders BR/PT, flags de habilitação, timeout/retries e checklist de pré-go-live.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Infra: 02_docker/.env.f3-real.example",
      "DOC docs/F3_RUNBOOK_GO_LIVE_REAL_BR_PT.md",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir template ENV de go-live F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Hardening de configuracao",
    title: "Compose fiscal por ENV + atalho unico para gates BR/PT",
    description:
      "Próximo sprint de execução técnica focado em desbloquear go-live real com segurança: variáveis de provider real foram parametrizadas no compose com defaults seguros (sem acoplamento fixo) e foi criado script operacional para executar go/no-go BR/PT em 1 comando.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
    ],
    routes: [
      "Infra: 02_docker/docker-compose.yml",
      "Script: 02_docker/run_f3_go_no_go.sh",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir hardening de configuração F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Janela controlada executada",
    title: "Evidência de 30 min sem CRITICAL pós-rollback por flag (BR/PT)",
    description:
      "A janela operacional controlada foi executada: gates BR/PT retornaram NO_GO no ambiente atual, rollback por flag foi validado em ambos os países e a coleta de 30 minutos confirmou ausência de CRITICAL (amostras INFO/SKIPPED).",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/br-go-no-go",
      "GET /admin/fiscal/providers/pt-go-no-go",
      "GET /admin/fiscal/providers/status",
    ],
    routes: [
      "DOC 02_docker/docker-compose.f3-rollback-override.yml",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir evidência da janela controlada F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Go-live real BR/PT",
    title: "Runbook/playbook de virada real com rollback por flag e saida objetiva",
    description:
      "Fechado o pacote operacional da Trilha B com documentação de go-live real BR/PT: runbook e playbook de 1 página com rollback imediato por flag, critérios de saída para mudança de [~] para [x] e evidência de operação/handoff.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "DOC docs/F3_RUNBOOK_GO_LIVE_REAL_BR_PT.md",
      "DOC docs/F3_PLAYBOOK_GO_LIVE_REAL_1PAGINA.md",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir pacote de go-live real BR/PT",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Inicio controlado PT real",
    title: "Gate técnico GO/NO-GO para habilitação PT real",
    description:
      "Sequência operacional da Trilha B ampliada para PT com o mesmo padrão do BR: endpoint de go/no-go e card dedicado no ops/fiscal/providers para decisão de liberação real (snapshot e teste de conectividade PT).",
    uiRoutesNew: ["/ops/fiscal/providers"],
    apiRoutesNew: ["GET /admin/fiscal/providers/pt-go-no-go"],
    routes: [
      "Backend: billing_fiscal_service/app/services/fiscal_provider_ops_service.py",
      "Backend: billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /ops/fiscal/providers",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers",
    directLinkLabel: "Abrir gate GO/NO-GO PT real",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Trilha B - Inicio controlado BR real",
    title: "Gate técnico GO/NO-GO para habilitação BR real",
    description:
      "Foi adicionado checklist técnico de go/no-go para início controlado do provider BR real, com endpoint dedicado e card operacional no ops/fiscal/providers para decisão rápida (snapshot e reavaliação com teste de conectividade). Mantido frontend em JavaScript.",
    uiRoutesNew: ["/ops/fiscal/providers"],
    apiRoutesNew: ["GET /admin/fiscal/providers/br-go-no-go"],
    routes: [
      "Backend: billing_fiscal_service/app/services/fiscal_provider_ops_service.py",
      "Backend: billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /ops/fiscal/providers",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers",
    directLinkLabel: "Abrir gate GO/NO-GO BR real",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Operacao - Handoff concluido",
    title: "Fechamento de turno em 1 minuto com bloco pronto no acompanhamento",
    description:
      "Foi concluído o handoff operacional do F-3 com padronização explícita no acompanhamento: bloco copiar/colar + exemplo preenchido com nome, contato, janela, owner e status BR/PT para fechamento rápido de plantão.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir evidência de handoff F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Operacao - Trilha A consolidada",
    title: "Runbook/Playbook F-3 + decisao de curto prazo em JavaScript",
    description:
      "Continuidade dos sprints com prioridade de velocidade imediata: frontend permanece em JavaScript no curto prazo. No F-3, a trilha A (stub-ready) foi consolidada com runbook e playbook de plantão dedicados, alinhados ao painel ops/fiscal/providers para fallback/rollback por país.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "DOC docs/F3_RUNBOOK_OPERACAO_TRILHA_A.md",
      "DOC docs/F3_PLAYBOOK_PLANTAO_1PAGINA.md",
      "DOC docs/F3_CHECKLIST_EXECUTIVO_OPERACAO.md",
      "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir consolidado operacional F-3",
  },
  {
    date: "2026-04-29",
    scope: "F-3 Hardening Operacional - Providers",
    title: "Painel de providers com critérios de ação e rollback por país",
    description:
      "No fluxo OPS de providers (BR/PT) foi incluída camada de hardening operacional com decisão acionável por país: severidade, resumo do estado, passos imediatos e checklist de rollback no próprio painel, sem depender de consulta externa.",
    uiRoutesNew: ["/ops/fiscal/providers"],
    apiRoutesNew: ["GET /admin/fiscal/providers/status (action_summary/action_steps/rollback_checklist)"],
    routes: [
      "UI /ops/fiscal/providers",
      "Backend: billing_fiscal_service/app/services/fiscal_provider_ops_service.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/fiscal/providers",
    directLinkLabel: "Abrir painel de providers endurecido (F-3)",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Runtime Final Closure",
    title: "Fechamento formal da trilha crítica (CORS dinâmico + sanitização final)",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Rodada curta final em runtime com alinhamento de CORS por ENV no `order_pickup_service` e sanitização dos últimos pontos com `str(exc)` em fluxos internos de confirmação de pagamento e validação de NCM, preservando observabilidade via `error_type`.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "runtime config: CORS_ALLOW_ORIGINS no order_pickup_service",
      "POST /internal/orders/{order_id}/payment/confirm (erro sanitizado)",
      "POST /public/orders (validação NCM sanitizada)",
    ],
    routes: [
      "Backend: order_pickup_service/app/main.py",
      "Backend: order_pickup_service/app/routers/internal.py",
      "Backend: order_pickup_service/app/services/order_creation_service.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir fechamento formal da trilha crítica",
  },
  {
    date: "2026-04-29",
    scope: "Cosmetic Cleanup - Legacy/Dev",
    title: "Limpeza de artefatos legados não usados e comentários históricos",
    description:
      "Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Passada cosmética final removendo helpers legados não referenciados e ajustando comentários/descrições históricas para reduzir ruído operacional sem impacto no fluxo principal.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [],
    routes: [
      "Backend: payment_gateway/app/routers/lockers.py (helper legado removido)",
      "Backend: runtime/app/repositories/runtime_registry_repo.py (função legado removida)",
      "Backend: order_pickup_service/app/routers/public_orders.py (comentário histórico limpo)",
      "Backend: billing_fiscal_service/app/api/routes_invoice.py (comentário legado limpo)",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de limpeza cosmética final",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Legacy/Dev Final Sweep",
    title: "Sanitização final em health interno e retorno de migration",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Ajustes finais em arquivos legados/dev fora da rota principal: sanitização de erro no health interno e padronização para `error_type` no retorno de falha de migrations.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /internal/health",
      "startup migration status payload",
    ],
    routes: [
      "Backend: order_pickup_service/app/health/internal.py",
      "Backend: order_pickup_service/app/core/db_migrations.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de varredura final legacy/dev",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Internal/Dev Sanitization",
    title: "Sanitização adicional em internos/dev com error_type e telemetria estruturada",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Sanitização de respostas e metadados internos/dev para evitar exposição de `str(exc)`, preservando observabilidade com `error_type` e eventos estruturados em runtime, gateway, billing e order_pickup.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST /dev-admin/release-regional-allocations",
      "POST /dev-admin/reset-locker",
      "POST /kiosk/orders (legacy/public)",
      "gateway/payment backend fallback paths",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/dev_admin.py",
      "Backend router legado descontinuado (antes: public_orders_BUGADA-POREM.py)",
      "Backend service: order_pickup_service/app/services/locker_service.py",
      "Backend service: order_pickup_service/app/services/credits_service.py",
      "Backend service: payment_gateway/app/services/payment_service.py",
      "Backend core: payment_gateway/app/core/runtime_client.py",
      "Backend service: backend/runtime/app/services/hardware_command_service.py",
      "Backend services: billing_fiscal_service adapters (AT/SVRS)",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de sanitização interna/dev",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Continuous Pass",
    title: "Remanescentes de SQL dinâmico e erros sensíveis sanitizados",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Remoção de SQL dinâmico residual em serviços de billing/payment e sanitização de detalhes sensíveis de exceção em fluxos de criação KIOSK, integração runtime e registro de deadline no lifecycle.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST/worker recompute utilization snapshots",
      "GET /risk/events (listagem com ORDER BY seguro)",
      "POST /kiosk/orders",
    ],
    routes: [
      "Backend service: billing_fiscal_service/app/services/partner_billing_utilization_service.py",
      "Backend service: payment_gateway/app/services/risk_events_service.py",
      "Backend router: order_pickup_service/app/routers/kiosk.py",
      "Backend service: order_pickup_service/app/services/order_creation_service.py",
      "Backend core: payment_gateway/app/core/runtime_client.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de correções remanescentes",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Error Sanitization + Tracing",
    title: "Sanitização adicional em pricing/lockers e tracing padronizado em lifecycle+billing",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Remoção de detalhes sensíveis em erros de `pricing_fiscal` e `payment_gateway/lockers`, além da padronização de middleware/handler de trace (`X-Trace-Id`) nos serviços `billing_fiscal_service` e `order_lifecycle_service`.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST /products/bundles",
      "POST /promotions",
      "GET /lockers",
      "GET /lockers/{locker_id}",
      "billing_fiscal_service global tracing middleware",
      "order_lifecycle_service global tracing middleware",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/pricing_fiscal.py",
      "Backend router: payment_gateway/app/routers/lockers.py",
      "Backend app: backend/billing_fiscal_service/app/main.py",
      "Backend app: backend/order_lifecycle_service/app/main.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de tracing e sanitização",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Billing/Internal Sanitization",
    title: "Billing fiscal sem SQL dinâmico remanescente + sanitização de erros internos",
    description:
      "Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Remoção dos últimos pontos com SQL dinâmico em billing_fiscal_service e sanitização de respostas de erro em billing_fiscal_service, order_pickup_service/internal e order_lifecycle_service/internal.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /v1/partners/{partner_id}/billing/cycles",
      "GET /v1/partners/{partner_id}/billing/cycles/{cycle_id}/line-items",
      "GET /v1/partners/{partner_id}/invoices",
      "GET /v1/partners/{partner_id}/credit-notes",
      "GET /v1/partners/{partner_id}/billing/disputes",
      "GET /v1/partners/ops/utilization-divergences",
      "GET /admin/fiscal/ledger-compat/audit",
    ],
    routes: [
      "Backend: billing_fiscal_service/app/api/routes_partner_billing.py",
      "Backend: billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Backend: billing_fiscal_service/app/api/routes_invoice.py",
      "Backend: order_pickup_service/app/routers/internal.py",
      "Backend: order_lifecycle_service/app/routers/internal.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de hardening final",
  },
  {
    date: "2026-04-29",
    scope: "Dev Tooling - Internal Errors HTML",
    title: "Nova página ops/dev/errors com filtros por status e rota",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Foi adicionada uma página HTML interna para visualizar `/internal/dev/errors` no navegador com filtros (status/rota), cards de indicadores e integração no OPS menu como NEW.',
    uiRoutesNew: ["/ops/dev/errors"],
    apiRoutesNew: ["GET /internal/dev/errors"],
    routes: [
      "UI /ops/dev/errors",
      "UI OPS menu (Dashboards) com badge NEW",
      "Backend endpoint interno /internal/dev/errors",
      "UI /ops/updates",
    ],
    directLink: "/ops/dev/errors",
    directLinkLabel: "Abrir visualizador interno de erros",
  },
  {
    date: "2026-04-29",
    scope: "Hardening Config + Dev Error Registry",
    title: "CORS por ENV, bloqueio de segredos default e trilha de erros em dev",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Hardening adicional controlado por ENV para CORS/segredos fora de dev e criação de endpoint interno de registro de erros HTTP/500 em desenvolvimento para acelerar diagnóstico sem expor detalhes em respostas públicas.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /internal/dev/errors",
      "CORS_ALLOW_ORIGINS (env)",
    ],
    routes: [
      "Backend app: order_pickup_service/app/main.py",
      "Backend app: billing_fiscal_service/app/main.py",
      "Backend app: order_lifecycle_service/app/main.py",
      "Backend app: runtime/app/main.py",
      "Backend app: payment_gateway/app/main.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de hardening por ENV",
  },
  {
    date: "2026-04-29",
    scope: "Security Review - Public/Auth e Runtime",
    title: "Sanitização de erros públicos e hardening de exceções",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Revisão adicional com correção de vazamento de detalhes internos em /public/auth, padronização de erro 500 no runtime com trace_id e ajuste seguro de ordenação em partner billing.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST /public/auth/register",
      "POST /public/auth/login",
      "PUT /public/auth/me/fiscal-profile",
      "POST /public/auth/change-password",
      "POST /public/auth/reset-password",
      "POST /public/auth/email-verification/resend",
      "GET /public/auth/email-verification/confirm",
      "runtime global exception handler",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/public_auth.py",
      "Backend app: backend/runtime/app/main.py",
      "Backend router: billing_fiscal_service/app/api/routes_partner_billing.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de revisão de segurança",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - SQLAlchemy Core Completo",
    title: "Partners router migrado para select/where/order_by sem text(...)",
    description:
      'Correção de problemas críticos (SQL injection, logging, tracing, rate limiting). Conversão dos blocos de reconciliação e métricas de webhook no partners router para SQLAlchemy Core completo, com consultas estruturadas e sem SQL textual dinâmico.',
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST /partners/ops/settlements/reconciliation/run",
      "GET /partners/ops/settlements/reconciliation/compare",
      "GET /partners/ops/settlements/reconciliation/top-divergences",
      "GET /partners/ops/webhooks/metrics",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/partners.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização SQLAlchemy Core completo",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Partners Router",
    title: "Hardening adicional em /partners com SQL estático parametrizado",
    description:
      "Passada complementar no router de partners para remover composição dinâmica de WHERE em reconciliação de settlements e métricas de webhooks, padronizando uso de filtros opcionais por bind params e reduzindo risco de SQL injection em rotas OPS críticas.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "POST /partners/ops/settlements/reconciliation/run",
      "GET /partners/ops/settlements/reconciliation/compare",
      "GET /partners/ops/settlements/reconciliation/top-divergences",
      "GET /partners/ops/webhooks/metrics",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/partners.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de hardening em partners",
  },
  {
    date: "2026-04-29",
    scope: "Security Hardening - Defense in Depth",
    title: "Queries migradas para SQLAlchemy select/where/order_by",
    description:
      "Passada de hardening focada em defesa em profundidade: listagens com filtros dinâmicos migradas de SQL textual com concatenação para SQLAlchemy Core (select/where/order_by), padronizando construção segura de queries em OPS e reduzindo superfície para SQL injection.",
    uiRoutesNew: ["/ops/updates"],
    apiRoutesNew: [
      "GET /products",
      "GET /products/{product_id}/inventory",
      "GET /ops/inventory/reservations",
      "GET /ops/inventory/low-stock",
      "GET /products/bundles",
      "GET /promotions",
      "GET /fiscal/auto-classification-log",
      "GET /ops/integration/order-events-outbox",
      "GET /ops/integration/order-events-outbox/dead-letter-priority",
      "GET /ops/integration/order-events-outbox/replay-priority-groups/runs",
      "POST /ops/integration/order-events-outbox/replay-batch",
      "GET /ops/integration/order-fulfillment-tracking",
    ],
    routes: [
      "Backend router: order_pickup_service/app/routers/products.py",
      "Backend router: order_pickup_service/app/routers/inventory.py",
      "Backend router: order_pickup_service/app/routers/pricing_fiscal.py",
      "Backend router: order_pickup_service/app/routers/integration_ops.py",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir atualização de hardening de segurança",
  },
  {
    date: "2026-04-28",
    scope: "Sprint FA-5 - Timescale OPS",
    title: "Página dedicada de hypertables/policies no OPS",
    description:
      "Foi adicionada uma rota operacional para visualização organizada das hypertables e jobs Timescale do FA-5, com smoke consolidado em tela para operação e suporte.",
    uiRoutesNew: ["/ops/partners/hypertables"],
    apiRoutesNew: ["GET /admin/fiscal/timescale/status"],
    routes: [
      "UI /ops/partners/hypertables",
      "UI /ops/partners/billing-monitor (atalho para hypertables)",
      "GET /admin/fiscal/timescale/status",
    ],
    directLink: "/ops/partners/hypertables",
    directLinkLabel: "Abrir monitor de hypertables (FA-5)",
  },
  {
    date: "2026-04-28",
    scope: "Sprint FA-1 - Billing Monitor",
    title: "Página simples de acompanhamento de billing para partners",
    description:
      "Foi adicionada a tela operacional com filtros, ordenação e paginação para acompanhar ciclos, invoices, credit notes e disputes do partner em um único fluxo.",
    uiRoutesNew: ["/ops/partners/billing-monitor"],
    apiRoutesNew: [
      "GET /v1/partners/{partner_id}/billing/cycles",
      "GET /v1/partners/{partner_id}/invoices",
      "GET /v1/partners/{partner_id}/credit-notes",
      "GET /v1/partners/{partner_id}/billing/disputes",
    ],
    routes: [
      "UI /ops/partners/billing-monitor",
      "GET /v1/partners/{partner_id}/billing/cycles",
      "GET /v1/partners/{partner_id}/invoices",
      "GET /v1/partners/{partner_id}/credit-notes",
      "GET /v1/partners/{partner_id}/billing/disputes",
    ],
    directLink: "/ops/partners/billing-monitor",
    directLinkLabel: "Abrir monitor de billing de partners",
  },
  {
    date: "2026-04-28",
    scope: "Sprint 12 - Dashboard Operacional",
    title: "Novo dashboard OPS de reconciliação (Partners)",
    description:
      "Foi iniciada a página operacional mínima para reconciliação de settlements, com filtros (partner_id, janela, min_severity, top_n), cards de priorização e consumo dos endpoints executivos de compare + top-divergences.",
    uiRoutesNew: ["/ops/partners/reconciliation-dashboard"],
    apiRoutesNew: [],
    routes: [
      "UI /ops/partners/reconciliation-dashboard",
      "GET /partners/ops/settlements/reconciliation/compare",
      "GET /partners/ops/settlements/reconciliation/top-divergences",
    ],
    directLink: "/ops/partners/reconciliation-dashboard",
    directLinkLabel: "Abrir dashboard OPS de reconciliação",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint Board - Products/Partners/Lockers",
    title: "Board visual com gates de UX/CX, risco operacional e WCAG AA",
    description:
      "Foi publicada uma versão visual do plano de sprint em tabs/kanban com triagem por história (impacto no cliente, risco operacional e conformidade WCAG AA), incluindo governança cruzada com ops/auth/policy, versioning e trilha em ops/updates para manter consistência visual ELLAN LAB.",
    routes: [
      "DOC docs/ellan_lab_sprint_board.html",
      "UI /ops/auth/policy",
      "UI /ops/auth/policy/versioning",
      "UI /ops/updates",
    ],
    directLink: "/ops/updates",
    directLinkLabel: "Abrir trilha de atualizações OPS",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - US-AUDIT-FINAL-VALIDATION",
    title: "Fechamento operacional auditável em 1 clique",
    description:
      "A página ops/audit ganhou seção de validação final com snapshot operacional estruturado (resultado, notas, resumo 24h, top causas e sinais da timeline) com cópia em markdown/texto simples para fechamento do sprint.",
    routes: [
      "UI /ops/audit",
      "UI seção: US-AUDIT-FINAL-VALIDATION",
      "UI ação: Copiar validação final (markdown/texto simples)",
    ],
    directLink: "/ops/audit",
    directLinkLabel: "Abrir validação final do sprint",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - Daily Operacional",
    title: "Botão de daily Slack/Teams em 1 clique",
    description:
      "Ops audit e ops health passaram a ter botão de cópia de daily operacional para Slack/Teams, gerando resumo curto com hoje, bloqueios e decisão.",
    routes: [
      "UI /ops/audit (Copiar daily Slack/Teams)",
      "UI /ops/health (Copiar daily Slack/Teams)",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir OPS Health (daily 1 clique)",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - US-AUDIT-003/005",
    title: "Copia executiva para Slack/Teams no ops/audit",
    description:
      "A seção de evidências do ops/audit ganhou formato curto para comunicação executiva (Slack/Teams), disponível por linha e em lote, mantendo redaction e limites de segurança já existentes.",
    routes: [
      "UI /ops/audit",
      "UI ação: Copiar Slack/Teams",
      "UI ação: Copiar Slack/Teams (lote)",
    ],
    directLink: "/ops/audit",
    directLinkLabel: "Abrir evidências com formato Slack/Teams",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - US-AUDIT-005",
    title: "Timeline investigativa com marcadores de anomalia",
    description:
      "A página ops/audit recebeu timeline investigativa com stream temporal, marcadores de anomalia (ERROR_EVENT, ERROR_SPIKE, SEVERITY_CRITICAL) e atalhos de entidade para investigação rápida por locker, correlation_id, reconciliação e visão de saúde.",
    routes: [
      "UI /ops/audit",
      "UI seção: Timeline investigativa (US-AUDIT-005)",
      "UI atalho: Locker/Correlation/Reconciliação/Ops Health",
    ],
    directLink: "/ops/audit",
    directLinkLabel: "Abrir timeline investigativa (US-AUDIT-005)",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - US-OPS-002",
    title: "Matriz SLA/canal por severidade + evidência auditável",
    description:
      "A página ops/health passou a exibir matriz operacional por severidade (CRITICO/ALTO/MEDIO/BAIXO), com SLA, canal, owner e contagem de alertas ativos por nível. Também foi adicionado bloco de evidência auditável com cópia em 1 clique, incluindo janela from/to e checklist de DoD.",
    routes: [
      "UI /ops/health",
      "UI ação: Copiar evidência US-OPS-002",
      "UI ação: Copiar para seção US-OPS-002",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir OPS Health (US-OPS-002)",
  },
  {
    date: "2026-04-27",
    scope: "OPS Sprint - US-OPS-001",
    title: "Fechamento US-001 assistido na UI",
    description:
      "O card Investigação auditável ganhou ação para copiar fechamento pré-formatado da seção 19, com top 3 causas da janela, distribuição por categoria e checklist de encerramento para evidência operacional.",
    routes: [
      "GET /dev-admin/ops-metrics/error-investigation",
      "GET /dev-admin/ops-metrics/error-investigation/export.csv",
      "UI ação: Copiar fechamento US-001 (seção 19)",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir investigação auditável (US-001)",
  },
  {
    date: "2026-04-27",
    scope: "OPS Governance",
    title: "Política de versionamento da ops/health",
    description:
      "Nova rota dedicada para explicar o padrão major.minor.patch + sprint, com regras de incremento, checklist por release e links de navegação cruzada para governança e auditoria.",
    routes: [
      "UI /ops/auth/policy/versioning",
      "UI /ops/auth/policy",
      "UI /ops/health (badge de versão clicável)",
    ],
    directLink: "/ops/auth/policy/versioning",
    directLinkLabel: "Abrir política de versionamento",
  },
  {
    date: "2026-04-26",
    scope: "L-3 Orders Integration",
    title: "Rota OPS dedicada para partner-lookup",
    description:
      "Nova tela operacional para lookup de pedidos por partner_id + partner_order_ref com presets, consulta técnica e cópia de evidência.",
    routes: [
      "GET /orders/partner-lookup",
      "UI /ops/integration/orders-partner-lookup",
    ],
    directLink: "/ops/integration/orders-partner-lookup",
    directLinkLabel: "Abrir OPS L-3 orders partner-lookup",
  },
  {
    date: "2026-04-26",
    scope: "L-3 D1",
    title: "Fundação de dados/manifests",
    description:
      "Migrações idempotentes, modelos e contratos para manifests/capacidade/rates, com endpoints base e auditoria OPS.",
    routes: [
      "POST /logistics/manifests",
      "POST /logistics/{partner_id}/capacity",
      "GET /logistics/manifests",
      "GET /logistics/{partner_id}/capacity",
    ],
    directLink: "/ops/logistics/manifests",
    directLinkLabel: "Abrir operação de manifests (D1/D2)",
  },
  {
    date: "2026-04-26",
    scope: "L-3 D2",
    title: "Fluxo operacional de manifesto",
    description:
      "Itens de manifesto, fechamento idempotente com reconciliação e endpoint de exception idempotente por item.",
    routes: [
      "GET /logistics/manifests/{manifest_id}/items",
      "POST /logistics/manifests/{manifest_id}/close",
      "POST /logistics/manifests/{manifest_id}/items/{item_id}/exception",
    ],
    directLink: "/ops/logistics/manifests",
    directLinkLabel: "Abrir operação D2 de manifests",
  },
  {
    date: "2026-04-26",
    scope: "L-3 D3",
    title: "Observabilidade de manifestos + painel OPS",
    description:
      "Overview OPS de manifestos com comparação temporal, confidence_badge, alertas e página dedicada para operação.",
    routes: [
      "GET /logistics/ops/manifests/overview",
      "GET /logistics/ops/manifests/view",
      "UI /ops/logistics/manifests-overview",
    ],
    directLink: "/ops/logistics/manifests-overview",
    directLinkLabel: "Abrir painel OPS de manifests",
  },
  {
    date: "2026-04-26",
    scope: "Pr-1 D1",
    title: "Assets de catálogo (media + barcodes)",
    description:
      "Endpoints mínimos para gestão de media e barcodes por produto, com página OPS dedicada para operação rápida.",
    routes: [
      "POST /products/{id}/media",
      "GET /products/{id}/media",
      "POST /products/{id}/barcodes",
      "GET /products/{id}/barcodes",
      "UI /ops/products/assets",
    ],
    directLink: "/ops/products/assets",
    directLinkLabel: "Abrir OPS de assets de produtos",
  },
  {
    date: "2026-04-26",
    scope: "Pr-3 D2/D3",
    title: "Pricing/Fiscal operacional + painel OPS",
    description:
      "Fechamento backend-first de bundles/promotions/fiscal-config/log com operação dedicada no front para monitoramento e mutações rápidas.",
    routes: [
      "GET/POST /products/bundles",
      "POST /products/bundles/{id}/items",
      "GET/POST /promotions",
      "PATCH /promotions/{id}/status",
      "POST /promotions/validate",
      "GET /products/{id}/fiscal-config",
      "PUT /products/{id}/fiscal-config",
      "GET /fiscal/auto-classification-log",
      "GET /ops/products/pricing-fiscal/overview",
      "UI /ops/products/pricing-fiscal",
    ],
    directLink: "/ops/products/pricing-fiscal",
    directLinkLabel: "Abrir OPS de pricing/fiscal (Pr-3)",
  },
  {
    date: "2026-04-26",
    scope: "I-1 Orders/Fiscal",
    title: "Operação dedicada por order_id (I-1)",
    description:
      "Página OPS para consulta/retry do outbox por pedido e reprocessamento fiscal com foco em incidentes de integração.",
    routes: [
      "GET /orders/{id}/fulfillment",
      "GET /orders/{id}/partner-events",
      "POST /orders/{id}/partner-events/retry",
      "GET /fiscal/auto-classification-log/{order_id}",
      "POST /fiscal/auto-classification/{order_id}/reprocess",
      "UI /ops/integration/orders-fiscal",
    ],
    directLink: "/ops/integration/orders-fiscal",
    directLinkLabel: "Abrir OPS I-1 orders/fiscal",
  },
  {
    date: "2026-04-26",
    scope: "L-2 D2",
    title: "Fila OPS de return-requests com quick actions",
    description:
      "Evolução da UI de returns para operação de fila e handoff com filtros ricos, chips por ação, detalhe por ID, patch de status, emissão de label e evidência rápida.",
    routes: [
      "GET /logistics/return-requests",
      "GET /logistics/return-requests/{id}",
      "PATCH /logistics/return-requests/{id}/status",
      "POST /logistics/return-requests/{id}/labels",
      "GET /logistics/sla-breaches",
      "UI /ops/logistics/returns",
    ],
    directLink: "/ops/logistics/returns",
    directLinkLabel: "Abrir OPS L-2 returns queue",
  },
  {
    date: "2026-04-26",
    scope: "P-3 Financials/Areas",
    title: "Operação de settlement e service-area por parceiro",
    description:
      "Página OPS dedicada para geração/aprovação de settlements, leitura de performance e gestão de cobertura por locker em service-areas.",
    routes: [
      "GET /partners/{id}/settlements",
      "POST /partners/{id}/settlements/generate",
      "PATCH /partners/{id}/settlements/{batch_id}/approve",
      "GET /partners/{id}/performance",
      "GET/POST /partners/{id}/service-areas",
      "UI /ops/partners/financials-service-areas",
    ],
    directLink: "/ops/partners/financials-service-areas",
    directLinkLabel: "Abrir OPS P-3 financials/service-areas",
  },
];

export default function OpsUpdatesHistoryPage() {
  const [copyStatus, setCopyStatus] = useState("");
  const [openEntries, setOpenEntries] = useState({});
  const [resetStatus, setResetStatus] = useState("");

  async function handleCopyTemplate() {
    try {
      await navigator.clipboard.writeText(TIMELINE_TEMPLATE_JSON);
      setCopyStatus("Template copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch (_) {
      setCopyStatus("Não foi possível copiar automaticamente. Copie manualmente o bloco JSON.");
    }
  }

  function handleResetTutorialPreferences() {
    try {
      const keysToRemove = [];
      for (let idx = 0; idx < window.localStorage.length; idx += 1) {
        const key = window.localStorage.key(idx);
        if (String(key || "").startsWith("ops:tutorial:hidden:v1:")) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach((key) => window.localStorage.removeItem(key));
      setResetStatus(
        keysToRemove.length > 0
          ? `Preferências de tutorial resetadas (${keysToRemove.length} chave(s)).`
          : "Nenhuma preferência de tutorial encontrada para reset."
      );
      window.setTimeout(() => setResetStatus(""), 2800);
    } catch (_err) {
      setResetStatus("Não foi possível resetar preferências de tutorial neste navegador.");
    }
  }

  function resolveUpdateDateKey(entry) {
    return String(entry?.dateTime || entry?.date || "").trim();
  }

  function formatUpdateDateTime(entry) {
    const raw = resolveUpdateDateKey(entry);
    if (!raw) return "-";
    const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(raw);
    const normalized = isDateOnly ? `${raw}T00:00:00-03:00` : raw;
    const parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) return raw;
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(parsed);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Updates History" />
        <p style={mutedStyle}>
          Histórico de acréscimos OPS com descrição curta de valor e trilha técnica por sprint.
        </p>
        <button type="button" style={copyButtonStyle} onClick={handleResetTutorialPreferences}>
          Resetar preferências de tutoriais
        </button>
        {resetStatus ? <div style={copyStatusStyle}>{resetStatus}</div> : null}

        <details style={templateBoxStyle}>
          <summary style={templateSummaryStyle}>Mini-template JSON (novos itens da timeline)</summary>
          <p style={{ ...mutedStyle, marginTop: 8 }}>
            Campos obrigatórios: <b>scope</b>, <b>description</b>, <b>directLink</b>. Convenção NEW:
            use <b>uiRoutesNew</b> e <b>apiRoutesNew</b> para destacar novidades do sprint.
          </p>
          <button type="button" style={copyButtonStyle} onClick={() => void handleCopyTemplate()}>
            Copiar template
          </button>
          {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}
          <pre style={templateJsonStyle}>{TIMELINE_TEMPLATE_JSON}</pre>
        </details>

        <div style={timelineStyle}>
          {UPDATES.map((entry) => (
            <details
              key={`${resolveUpdateDateKey(entry)}-${entry.scope}-${entry.title}`}
              style={entryStyle}
              onToggle={(event) => {
                const entryKey = `${resolveUpdateDateKey(entry)}-${entry.scope}-${entry.title}`;
                const isOpen = Boolean(event.currentTarget?.open);
                setOpenEntries((prev) => ({ ...prev, [entryKey]: isOpen }));
              }}
            >
              <summary style={entrySummaryStyle}>
                <div style={entrySummaryContentStyle}>
                  <div style={{ display: "grid", gap: 6 }}>
                    <strong>{entry.title}</strong>
                    <span style={{ ...getSeverityBadgeStyle("WARN"), width: "fit-content" }}>{entry.scope}</span>
                  </div>
                  <span style={entryToggleBadgeStyle}>
                    {openEntries[`${resolveUpdateDateKey(entry)}-${entry.scope}-${entry.title}`] ? "Recolher" : "Expandir"}
                  </span>
                </div>
              </summary>
              <div style={entryBodyStyle}>
                <small style={{ color: "#94A3B8" }}>{formatUpdateDateTime(entry)}</small>
                <p style={{ margin: "8px 0", color: "#CBD5E1" }}>{entry.description}</p>
                {(entry.uiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>UI route NEW</small>
                    <ul style={routesListStyle}>
                      {entry.uiRoutesNew.map((route) => (
                        <li key={`ui-${route}`} style={{ color: "#BFDBFE", fontSize: 12 }}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(entry.apiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>API route NEW</small>
                    <ul style={routesListStyle}>
                      {entry.apiRoutesNew.map((route) => (
                        <li key={`api-${route}`} style={{ color: "#BFDBFE", fontSize: 12 }}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <ul style={routesListStyle}>
                  {entry.routes.map((route) => (
                    <li key={route} style={{ color: "#BFDBFE", fontSize: 12 }}>
                      {route}
                    </li>
                  ))}
                </ul>
                {entry.directLink ? (
                  <div style={{ marginTop: 8 }}>
                    <Link to={entry.directLink} style={directLinkStyle}>
                      {entry.directLinkLabel || "Abrir rota relacionada"}
                    </Link>
                  </div>
                ) : null}
                </div>
            </details>
          ))}
        </div>
      </section>

    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8" };
const templateBoxStyle = { marginTop: 10, marginBottom: 12, background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10 };
const templateSummaryStyle = { cursor: "pointer", color: "#BFDBFE", fontWeight: 700 };
const copyButtonStyle = { marginTop: 8, padding: "6px 10px", borderRadius: 999, border: "1px solid rgba(59,130,246,0.45)", background: "rgba(59,130,246,0.12)", color: "#BFDBFE", fontWeight: 700, cursor: "pointer", fontSize: 12 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };
const templateJsonStyle = { marginTop: 8, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 10, overflow: "auto", fontSize: 12 };
const timelineStyle = { display: "grid", gap: 10 };
const entryStyle = { border: "1px solid #334155", borderRadius: 12, padding: "8px 12px", background: "#0B1220" };
const entrySummaryStyle = { cursor: "pointer", display: "flex", alignItems: "center", listStyle: "none", outline: "none", padding: "2px 0" };
const entrySummaryContentStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap", width: "100%" };
const entryToggleBadgeStyle = { border: "1px solid rgba(59,130,246,0.45)", background: "rgba(59,130,246,0.12)", color: "#BFDBFE", borderRadius: 999, padding: "4px 8px", fontSize: 11, fontWeight: 700 };
const entryBodyStyle = { marginTop: 8 };
const newRoutesBlockStyle = { marginBottom: 8 };
const newRoutesTitleStyle = { color: "#93C5FD", fontWeight: 700, fontSize: 11 };
const newInlineBadgeStyle = {
  display: "inline-flex",
  marginLeft: 6,
  padding: "1px 6px",
  borderRadius: 999,
  fontSize: 10,
  fontWeight: 700,
  color: "#ECFEFF",
  border: "1px solid rgba(45,212,191,0.55)",
  background: "rgba(45,212,191,0.16)",
};
const routesListStyle = { margin: 0, paddingLeft: 16, display: "grid", gap: 4 };
const directLinkStyle = {
  display: "inline-flex",
  textDecoration: "none",
  color: "#93C5FD",
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(59,130,246,0.12)",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 700,
};
