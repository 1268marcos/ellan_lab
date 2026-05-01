import React, { useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import { formatOpsDateTime } from "../utils/opsDateTimeFormat";

const FISCAL_UPDATES_PAGE_VERSION = "fiscal/updates v1.2.1";
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
    dateTime: "2026-04-30T23:45:00-03:00",
    scope: "Sprint 3 (P0-1) — espelho no pacote diário / close",
    title: "Gravar espelho partner-audit → ZIP management-daily e accounting-close",
    description:
      "Botão «Gravar espelho para pacote diário» em fiscal/sprint3-partner-audit persiste slice + metadados em localStorage; fiscal/management-daily e fiscal/accounting-close anexam JSON assinado com scope SPRINT3_PARTNER_AUDIT_MIRROR_ATTACH quando existir. Pré-visualização no management-daily e atalhos adicionais.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/utils/fiscalSprint3PartnerAuditMirror.js",
      "Frontend: 01_source/frontend/src/pages/FiscalSprint3PartnerAuditPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalAccountingClosePage.jsx",
    ],
    directLink: "/fiscal/sprint3-partner-audit",
    directLinkLabel: "Abrir auditoria por parceiro (gravar espelho)",
  },
  {
    dateTime: "2026-04-30T23:05:00-03:00",
    scope: "Sprint 3 (P0-1) — auditoria por parceiro (próximo sprint em código)",
    title: "Nova rota fiscal/sprint3-partner-audit (rollup partner_id + D11 opcional + export assinado)",
    description:
      "Cockpit dedicado à extensão P0-1 do plano Sprint 3: consome `GET /admin/fiscal/global/sprint3/e2e-audit-trail`, agrega por `partner_id` via `buildP01bPartnerReconciliationSlice` (mesmo contrato P0-1b), mostra cobertura materializada/raw, tabela ordenada por volume de gaps, cruzamento opcional com snapshot D11 (`ellan_ops_fiscal_d11_handoff_v1`) e export/cópia JSON com SHA-256. Atalhos para slo-alerts, sprint2-finance-gate e management-daily.",
    uiRoutesNew: ["/fiscal/sprint3-partner-audit"],
    apiRoutesNew: ["GET /admin/fiscal/global/sprint3/e2e-audit-trail"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalSprint3PartnerAuditPage.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalP01bDailyPackage.js",
      "Frontend: 01_source/frontend/src/App.jsx",
      "DOC: docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md",
    ],
    directLink: "/fiscal/sprint3-partner-audit",
    directLinkLabel: "Abrir auditoria por parceiro Sprint 3",
  },
  {
    dateTime: "2026-04-30T22:15:00-03:00",
    scope: "Sprint 2 — gate financeiro v2 + próximo sprint previsto (cockpit)",
    title: "Nova rota fiscal/sprint2-finance-gate (PASS/NO_GO, export JSON assinado, sequência S2→S3→S4)",
    description:
      "Entrega operacional do próximo sprint previsto no plano global: cockpit para o gate financeiro Sprint 2 **v2** (comité 2026-05-01) com limiares Fiscal ≥50%, Contábil ≥40%, consolidado ≥55%, comprovação P0 mínima, persistência local e export/cópia JSON com SHA-256 (scope SPRINT2_FINANCE_GATE_V2). Texto orienta a sequência: Fase A = Sprint 2 dominante; após PASS = Fase B com Sprint 3 como sprint ideal; Sprint 4 na fase C. Atalhos para management-daily, accounting-close e fiscal/updates.",
    uiRoutesNew: ["/fiscal/sprint2-finance-gate"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalSprint2FinanceGatePage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "DOC: docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md",
    ],
    directLink: "/fiscal/sprint2-finance-gate",
    directLinkLabel: "Abrir gate financeiro Sprint 2 (v2)",
  },
  {
    dateTime: "2026-04-30T20:58:00-03:00",
    scope: "Sprint 4 — UAT KIOSK + registro Go/No-Go mínimo",
    title: "fiscal/sprint4-regression-matrix com UAT 4 modelos e bloco formal de decisão",
    description:
      "Priorizado Sprint 4 por readiness: adicionados controles explícitos para UAT dos 4 modelos KIOSK (A/B/C/D) com evidência por item e registro Go/No-Go mínimo (decisão, risco residual, mitigação). Os campos entram no payload assinado da matriz e nos pacotes auditáveis já existentes.",
    uiRoutesNew: ["/fiscal/sprint4-regression-matrix"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalSprint4RegressionMatrixPage.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalSprint4RegressionMatrix.js",
      "DOC: docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/sprint4-regression-matrix",
    directLinkLabel: "Abrir UAT KIOSK + Go/No-Go mínimo",
  },
  {
    dateTime: "2026-04-30T20:35:00-03:00",
    scope: "Sprint 3 — treinamento rápido OPS/Suporte (plano)",
    title: "Nova rota ops/quick-enablement com checklist, export ELLAN_FISCAL_DAILY e handoff Slack",
    description:
      "Fechado o item aberto do plano Sprint 3 «treinamento rápido operacional»: cockpit para OPS e Suporte com roteiro curto, persistência local, evidência JSON/ZIP assinada (scope SPRINT3_OPS_SUPPORT_QUICK_TRAINING) e atalhos desde ops/health e runbook P0-3.",
    uiRoutesNew: ["/ops/quick-enablement"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsQuickEnablementPage.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalSprint3OpsEnablement.ts",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalSprint3IncidentRunbook.js",
      "DOC: docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/quick-enablement",
    directLinkLabel: "Abrir treinamento rápido OPS/Suporte",
  },
  {
    dateTime: "2026-04-30T20:05:00-03:00",
    scope: "Sprint 4 (paralelo) — cópia última rodada + anexo no pacote diário",
    title: "Última rodada piloto copiável (JSON assinado) e anexo Sprint 4 opcional no ZIP management-daily",
    description:
      "Incremento: botão Copiar JSON da última rodada (scope SPRINT4_REGRESSION_PILOT_RUN_LATEST) em fiscal/sprint4-regression-matrix; fiscal/management-daily anexa ao ZIP diário matriz e histórico de pilotos do localStorage quando existentes, com skip documentado se o histórico exceder 120k caracteres no JSON bruto.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/utils/fiscalSprint4RegressionMatrix.js",
      "Frontend: 01_source/frontend/src/pages/FiscalSprint4RegressionMatrixPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/sprint4-regression-matrix",
    directLinkLabel: "Abrir matriz Sprint 4",
  },
  {
    dateTime: "2026-04-30T19:45:00-03:00",
    scope: "Sprint 4 (paralelo seguro) — matriz por persona + rodada piloto",
    title: "fiscal/sprint4-regression-matrix: rollup por persona, registro de pilotos e ZIP ELLAN_FISCAL_DAILY",
    description:
      "Sprint 4 sem bloquear Sprint 3: matriz mínima exporta personas agregadas; rodadas piloto ficam em localStorage com progresso e rollup no momento do registro; pacote ZIP auditável inclui JSON assinado da matriz + histórico SPRINT4_REGRESSION_PILOT_HISTORY; export JSON da matriz alinhado ao prefixo ELLAN_FISCAL_DAILY_YYYYMMDD.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/utils/fiscalSprint4RegressionMatrix.js",
      "Frontend: 01_source/frontend/src/pages/FiscalSprint4RegressionMatrixPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/sprint4-regression-matrix",
    directLinkLabel: "Abrir matriz Sprint 4 e registrar piloto",
  },
  {
    dateTime: "2026-04-30T19:12:00-03:00",
    scope: "Sprint 3 (P0-2b) — calibragem BR/PT + playbook operacional",
    title: "fiscal/slo-alerts com calibragem por país (AUTO/BR/PT) e decisão endurecer vs investigar",
    description:
      "P0-2b concluído no scorecard SLO: thresholds agora suportam perfil de calibragem por país (modo AUTO ou seleção manual), com payload auditável incluindo perfil aplicado e playbook operacional objetivo (TIGHTEN_THRESHOLDS, INVESTIGATE_FIRST, KEEP_BASELINE) para reduzir ruído sem perder sensibilidade.",
    uiRoutesNew: ["/fiscal/slo-alerts"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalSloAlertsPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/slo-alerts",
    directLinkLabel: "Abrir scorecard SLO calibrado",
  },
  {
    dateTime: "2026-04-30T18:10:00-03:00",
    scope: "Sprint 3 (P0-1b) — pacote único pedido→reconciliação→handoff",
    title: "ZIP diário (management-daily + ops/health) com E2E audit trail + slice por parceiro assinados",
    description:
      "P0-1b: o download do pacote ELLAN_FISCAL_DAILY_*_PACKAGE_*.zip passa a incluir, além dos artefatos existentes, dois JSONs com integridade SHA-256: trilha completa do endpoint sprint3/e2e-audit-trail e consolidação por partner_id (batches, contagens de materialização, severidades) com cruzamento opcional ao snapshot D11 do localStorage.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/utils/fiscalP01bDailyPackage.js",
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Abrir gestão diária e baixar pacote .zip",
  },
  {
    dateTime: "2026-04-30T15:48:00-03:00",
    scope: "Sprint 3 (P0-3) follow-up — cópia JSON assinada",
    title: "fiscal/incident-response: botão Copiar checklist (JSON assinado) para automação",
    description:
      "Complemento ao P0-3: além de export .json e pacote .zip auditável, a página fiscal/incident-response passou a oferecer cópia direta do checklist assinado (SHA-256) para área de transferência, alinhando ao padrão de handoff sem arquivo obrigatório.",
    uiRoutesNew: ["/fiscal/incident-response"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalIncidentResponsePage.jsx", "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt"],
    directLink: "/fiscal/incident-response",
    directLinkLabel: "Abrir cockpit de resposta a incidente",
  },
  {
    dateTime: "2026-04-30T15:45:00-03:00",
    scope: "Sprint 3 (P0-3) — runbook e checklist de incidente",
    title: "Nova rota fiscal/incident-response com checklist, runbook e pacote auditável (.zip)",
    description:
      "Entregue o bloco P0-3: checklist operacional persistido, referência de runbook com atalhos OPS/FISCAL, anexos em texto para evidências, handoff Slack/Teams, export JSON assinado e pacote .zip (checklist + runbook + anexos). Menu FISCAL com badge NEW apenas em incident-response; atalho em ops/health e fiscal/slo-alerts.",
    uiRoutesNew: ["/fiscal/incident-response"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalIncidentResponsePage.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalSprint3IncidentRunbook.js",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalSloAlertsPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/incident-response",
    directLinkLabel: "Abrir runbook de resposta a incidente",
  },
  {
    dateTime: "2026-04-30T15:36:00-03:00",
    scope: "Sprint 3 (P0-1) - auditoria ponta a ponta + menu fiscal limpo",
    title: "Trilha E2E 100% materializada e evidência única de handoff no fiscal/slo-alerts",
    description:
      "Menu FISCAL ajustado para manter apenas o último item com badge NEW. Entregue endpoint de auditoria ponta a ponta (`order_id`, `invoice_id`, `partner_id`, `batch_id`) com cobertura materializada e evidência operacional única, consumida na página fiscal/slo-alerts com export JSON assinado para handoff.",
    uiRoutesNew: ["/fiscal/slo-alerts"],
    apiRoutesNew: ["GET /admin/fiscal/global/sprint3/e2e-audit-trail"],
    routes: [
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalSloAlertsPage.jsx",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/slo-alerts",
    directLinkLabel: "Abrir auditoria ponta a ponta e export único de handoff",
  },
  {
    dateTime: "2026-04-30T15:24:00-03:00",
    scope: "Sprint 3 (P0-2) - scorecards e alertas SLO fiscal/ops",
    title: "Nova rota fiscal/slo-alerts com KPIs mínimos, severidade e export auditável",
    description:
      "Entregue a página fiscal/slo-alerts para consolidar scorecards e alertas por severidade com filtros por país/parceiro/período, incluindo KPIs mínimos de erro fiscal, latência p95, divergência prolongada e tempo de tratativa, além de export JSON/ZIP com assinatura SHA-256.",
    uiRoutesNew: ["/fiscal/slo-alerts"],
    apiRoutesNew: [
      "GET /admin/fiscal/providers/status",
      "GET /admin/fiscal/accounting-approvals/latest",
      "GET /admin/fiscal/accounting-approvals/divergence-health",
      "GET /admin/fiscal/accounting-approvals",
    ],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalSloAlertsPage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/utils/fiscalAccountingApprovalsHistory.js",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/slo-alerts",
    directLinkLabel: "Abrir scorecards e alertas SLO Fiscal/OPS",
  },
  {
    dateTime: "2026-04-30T11:27:00-03:00",
    scope: "Sprint prático — dashboards operacionais Fiscal/Contábil",
    title: "Novas páginas fiscal/partner-performance e fiscal/accounting-close com filtros + export auditável",
    description:
      "Entregues duas páginas novas para operação diária do departamento Fiscal/Contábil e parceiros, com gráficos operacionais reais baseados em endpoints de providers/readiness, filtros por país/parceiro/período e exportação JSON/ZIP com assinatura SHA-256 no padrão auditável.",
    uiRoutesNew: ["/fiscal/partner-performance", "/fiscal/accounting-close"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalPartnerPerformancePage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalAccountingClosePage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/partner-performance",
    directLinkLabel: "Abrir dashboards de performance e fechamento contábil",
  },
  {
    dateTime: "2026-04-30T11:18:00-03:00",
    scope: "Próximo sprint — dashboards para Fiscal/Contábil + parceiros",
    title: "Nova rota fiscal/department-dashboards com visão operacional ELLAN e BR/PT",
    description:
      "Entrega prática de dashboard para os departamentos Fiscal e Contábil: página dedicada com decisão consolidada, checks PASS/FAIL, top pendências por país em gráfico de barras, status de aprovação contábil e visão de parceiros BR/PT, com export de snapshot JSON.",
    uiRoutesNew: ["/fiscal/department-dashboards"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalDepartmentDashboardsPage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/department-dashboards",
    directLinkLabel: "Abrir dashboards departamentais Fiscal/Contábil",
  },
  {
    dateTime: "2026-04-30T11:05:00-03:00",
    scope: "Auditoria — assinatura de integridade dos anexos",
    title: "Pacotes diários com hash SHA-256 em cada JSON (ops + fiscal + approval)",
    description:
      "Reforço da trilha auditável: cada JSON dentro do pacote diário .zip agora inclui bloco de integridade com algoritmo SHA-256 e hash do conteúdo, aplicado nas telas ops/health e fiscal/management-daily.",
    uiRoutesNew: ["/ops/health", "/fiscal/management-daily"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Baixar pacote com assinatura SHA-256",
  },
  {
    dateTime: "2026-04-30T10:59:00-03:00",
    scope: "Simetria total do pacote diário entre telas",
    title: "ops/health pacote .zip alinhado com 3 arquivos (OPS + FISCAL + APPROVAL)",
    description:
      "Aplicada simetria completa com fiscal/management-daily: o botão de pacote diário em ops/health agora também exporta três JSONs (operacional, gestão fiscal e aprovação contábil), mantendo padrão único de anexação para auditoria.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Baixar pacote diário com 3 arquivos no ops/health",
  },
  {
    dateTime: "2026-04-30T10:44:00-03:00",
    scope: "Rastreabilidade de auditoria — naming padronizado",
    title: "Prefixo ELLAN_FISCAL_DAILY_YYYYMMDD aplicado nos arquivos JSON/ZIP diários",
    description:
      "Padronizado o nome interno dos artefatos diários com prefixo auditável (ELLAN_FISCAL_DAILY_YYYYMMDD_...) nos downloads JSON e no pacote .zip das telas ops/health e fiscal/management-daily, facilitando trilha e organização de evidências.",
    uiRoutesNew: ["/ops/health", "/fiscal/management-daily"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Baixar artefatos com naming auditável",
  },
  {
    dateTime: "2026-04-30T10:42:00-03:00",
    scope: "Pacote diário auditável — 3 arquivos",
    title: "ZIP diário da fiscal/management-daily agora inclui OPS + FISCAL + APPROVAL",
    description:
      "O pacote diário (.zip) da página fiscal/management-daily foi ampliado para conter três JSONs: payload operacional OPS, payload de gestão fiscal e aprovação contábil do dia, consolidando a trilha auditável formal em um único anexo.",
    uiRoutesNew: ["/fiscal/management-daily"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Baixar pacote diário com 3 JSONs",
  },
  {
    dateTime: "2026-04-30T10:39:00-03:00",
    scope: "Trilha auditável formal — aprovação contábil diária",
    title: "Bloco 'Aprovação Contábil do Dia' com export JSON na fiscal/management-daily",
    description:
      "Nova seção formal para o Departamento Contábil/Fiscal com responsável, status, observações e timestamp, incluindo salvamento de rascunho local e export JSON da aprovação diária para trilha auditável.",
    uiRoutesNew: ["/fiscal/management-daily"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Abrir aprovação contábil do dia",
  },
  {
    dateTime: "2026-04-30T10:36:00-03:00",
    scope: "Departamento Contábil/Fiscal — página dedicada",
    title: "Nova rota fiscal/management-daily plugada no menu FISCAL",
    description:
      "Criada página dedicada de interação para o time Contábil/Fiscal com foco em gestão diária: decisão consolidada, risco, ações recomendadas e atalhos de evidência (copiar/baixar JSON e pacote diário .zip). A rota foi integrada ao menu FISCAL.",
    uiRoutesNew: ["/fiscal/management-daily"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalManagementDailyPage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/management-daily",
    directLinkLabel: "Abrir página de gestão diária contábil/fiscal",
  },
  {
    dateTime: "2026-04-30T10:34:00-03:00",
    scope: "Gestão FISCAL — autonomia do pacote diário",
    title: "fiscal/global agora gera pacote diário (.zip) com payload OPS + FISCAL",
    description:
      "Adicionado botão de pacote diário no fiscal/global para eliminar dependência da tela ops/health: download único (.zip) com os dois JSONs de handoff (ops_health_daily_payload e fiscal_management_daily_payload) para anexação direta no rito de gestão.",
    uiRoutesNew: ["/fiscal/global"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/global",
    directLinkLabel: "Baixar pacote diário no fiscal/global",
  },
  {
    dateTime: "2026-04-30T10:30:00-03:00",
    scope: "Gestão diária — pacote único de anexos",
    title: "Novo botão: baixar pacote diário (.zip) com JSON OPS + FISCAL",
    description:
      "Entrega prática para o rito de gestão: ops/health agora gera um pacote .zip com dois payloads JSON (ops_health_daily_payload e fiscal_management_daily_payload) para anexar em lote sem montagem manual.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/package.json",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Baixar pacote diário OPS+FISCAL (.zip)",
  },
  {
    dateTime: "2026-04-30T10:28:00-03:00",
    scope: "Automação de rito diário — copy + download JSON",
    title: "Payloads diários agora copiam para clipboard e baixam arquivo .json automaticamente",
    description:
      "Evolução prática para o rito de gestão: os botões de payload JSON em ops/health e fiscal/global passaram a executar cópia para clipboard e download automático de arquivo .json com timestamp, facilitando anexos e automação sem parsing manual.",
    uiRoutesNew: ["/ops/health", "/fiscal/global"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir payload JSON com download automático",
  },
  {
    dateTime: "2026-04-30T10:25:00-03:00",
    scope: "Entregas práticas — automação de handoff + gestão FISCAL",
    title: "Payload diário JSON no ops/health e payload executivo JSON no fiscal/global",
    description:
      "Implementados dois artefatos práticos para operação e gestão: botão de cópia do payload diário padronizado em JSON no ops/health (sem parsing manual) e botão de cópia do payload executivo FISCAL em JSON no fiscal/global com decisão, nível de risco e ações recomendadas para rotina gerencial.",
    uiRoutesNew: ["/ops/health", "/fiscal/global"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/global",
    directLinkLabel: "Abrir payloads JSON de operação e gestão",
  },
  {
    dateTime: "2026-04-30T10:23:00-03:00",
    scope: "Ops/health — daily geral com formato operacional",
    title: "copyOpsHealthDailySlack padronizado com decisão/checks/referência + ação prática",
    description:
      "O payload do daily geral em ops/health deixou o formato narrativo e passou a seguir o padrão operacional de handoff (Decisão consolidada, Checks PASS, Checks com falha, Referência), incluindo ação prática explícita para o plantão.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir daily geral padronizado",
  },
  {
    dateTime: "2026-04-30T10:21:00-03:00",
    scope: "Handoff escrito — payloads Slack/Teams padronizados",
    title: "Estrutura textual unificada nos payloads de cópia das telas FG-1",
    description:
      "Padronização aplicada nos payloads de cópia para handoff diário com a mesma semântica base (Decisão consolidada, Checks PASS, Checks com falha, Referência), alinhando escrita e visual entre ops/health e readiness-execution.",
    uiRoutesNew: ["/ops/health", "/fiscal/readiness-execution"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalReadinessExecutionPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir payloads padronizados de handoff",
  },
  {
    dateTime: "2026-04-30T09:03:00-03:00",
    scope: "Handoff visual diário — padronização cross-page",
    title: "Texto e ordem dos indicadores unificados em ops/health, fg1-gate e fiscal/global",
    description:
      "Padronização aplicada para leitura operacional consistente no handoff: mesma ordem e semântica dos indicadores principais (Decisão consolidada, X/Y checks PASS, checks com falha e referência temporal/versão) nas três páginas de acompanhamento FG-1.",
    uiRoutesNew: ["/ops/health", "/fiscal/fg1-gate", "/fiscal/global"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir handoff visual padronizado",
  },
  {
    dateTime: "2026-04-30T09:01:00-03:00",
    scope: "FG-1 gate — paridade com ops/health",
    title: "Observabilidade técnica com contador explícito X/Y checks PASS",
    description:
      "A página fiscal/fg1-gate passou a consumir o endpoint stub-wave-readiness e agora exibe no bloco técnico o contador explícito de conformidade de checks (X/Y checks PASS), mantendo paridade visual com o card consolidado de ops/health.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/stub-wave-readiness"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir fg1-gate com X/Y checks PASS",
  },
  {
    dateTime: "2026-04-30T08:48:00-03:00",
    scope: "Ops/health — handoff consolidado FG-1 (4 checks PASS)",
    title: "Card consolidado exibe contador explícito de conformidade de checks",
    description:
      "Ajuste no card de handoff consolidado FG-1 para exibir contador explícito de conformidade no formato 4/4 checks PASS, além de incluir a mesma métrica no payload de cópia para Slack/Teams.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card consolidado com 4/4 checks PASS",
  },
  {
    dateTime: "2026-04-30T08:16:00-03:00",
    scope: "FG-1-SPRINT-09 — Stub readiness + regionalidade inicial",
    title: "Endpoint de readiness da onda + region explícita no simulate (US/CA)",
    description:
      "Novo checkpoint técnico da onda FG-1 com GET /admin/fiscal/global/fg1/stub-wave-readiness, smoke operacional dedicado e evolução de regionalidade no simulate via query region (US-CA/US-TX/US-NY e CA-QC), mantendo contrato canônico e correlação telemetry/raw.",
    uiRoutesNew: ["/fiscal/global"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/fg1/stub-wave-readiness",
      "POST /admin/fiscal/global/fg1/simulate?region=<...>",
    ],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_stub_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Script: 02_docker/run_fg1_stub_wave_readiness_smoke.sh",
      "Script: 02_docker/run_fg1_simulate_trace_smoke.sh",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/global",
    directLinkLabel: "Abrir fiscal/global com stub readiness",
  },
  {
    dateTime: "2026-04-30T08:09:00-03:00",
    scope: "Ops/health — handoff consolidado FG-1 (microevolução)",
    title: "Card consolidado com copiar payload Slack/Teams + copiar comando do orquestrador",
    description:
      "Microajuste operacional no card de handoff consolidado FG-1: adicionados botões de cópia em 1 clique para payload de comunicação (Slack/Teams) e para comando run_fg1_handoff_orchestrator.sh --json, reduzindo atrito no plantão.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card consolidado FG-1 com cópia 1 clique",
  },
  {
    dateTime: "2026-04-30T07:08:00-03:00",
    scope: "Ops/health — handoff consolidado FG-1",
    title: "Card único no ops/health consumindo fg1_handoff_orchestrator_latest.json",
    description:
      "Integração fim-a-fim do handoff diário FG-1: backend ganhou GET /dev-admin/fiscal-fg1-handoff/latest e o ops/health agora mostra card consolidado com decisão GO/NO_GO, resultado, número de checks com falha, timestamp e links rápidos para fiscal/fg1-gate e fiscal/readiness-execution.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: ["GET /dev-admin/fiscal-fg1-handoff/latest"],
    routes: [
      "Backend: 01_source/order_pickup_service/app/routers/dev_admin.py",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card consolidado FG-1 no ops/health",
  },
  {
    dateTime: "2026-04-30T06:59:00-03:00",
    scope: "Automação diária FG-1",
    title: "Orquestrador único dos 3 smokes com decisão consolidada GO/NO_GO",
    description:
      "Implementado run_fg1_handoff_orchestrator.sh para executar fixture-inventory + envelope-check + simulate-trace, consolidar resultado diário (decision GO/NO_GO) e gerar artefato latest para handoff operacional.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: [
      "Script: 02_docker/run_fg1_handoff_orchestrator.sh",
      "Script: 02_docker/run_fg1_fixture_inventory_smoke.sh",
      "Script: 02_docker/run_fg1_envelope_check_smoke.sh",
      "Script: 02_docker/run_fg1_simulate_trace_smoke.sh",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/updates",
    directLinkLabel: "Histórico FISCAL (orquestrador diário FG-1)",
  },
  {
    dateTime: "2026-04-30T06:55:00-03:00",
    scope: "Próximo sprint previsto executado — FG-1-SPRINT-08",
    title: "Correlação provider/region/scenario/trace no simulate + smoke diário dedicado",
    description:
      "Sprint aplicado no eixo BE/SRE: simulate agora propaga region no telemetry e government_response.raw, envelope-check reforçado com esse campo, fixtures canônicas regeneradas com region e novo script run_fg1_simulate_trace_smoke.sh para validar correlação entre telemetry/raw em cenários FG-1.",
    uiRoutesNew: [],
    apiRoutesNew: ["POST /admin/fiscal/global/fg1/simulate"],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_stub_service.py",
      "Script: 01_source/backend/billing_fiscal_service/scripts/write_fg1_fixtures.py",
      "Script: 02_docker/run_fg1_simulate_trace_smoke.sh",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/updates",
    directLinkLabel: "Histórico FISCAL (sprint FG-1-SPRINT-08)",
  },
  {
    dateTime: "2026-04-30T06:32:00-03:00",
    scope: "Sprint curto 1-clique FG-1",
    title: "fg1-gate abre readiness-execution já focado nos países com pending_actions > 0",
    description:
      "Implementado fluxo de ação 1 clique: fiscal/fg1-gate calcula países com pending_actions e abre fiscal/readiness-execution com country_focus na URL; readiness aplica o filtro automaticamente, mostra foco ativo e permite limpar foco em um clique.",
    uiRoutesNew: ["/fiscal/fg1-gate", "/fiscal/readiness-execution"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalReadinessExecutionPage.jsx",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir FG-1 gate com ação 1 clique",
  },
  {
    dateTime: "2026-04-30T06:27:00-03:00",
    scope: "Próximo sprint previsto executado — FE-OPS FG-1",
    title: "fiscal/fg1-gate com observabilidade técnica de envelope/fixtures",
    description:
      "Fechamento do próximo sprint previsto: a página fiscal/fg1-gate passou a consumir envelope-check + fixture-inventory e exibir card técnico com status operacional (error_count, checked_pairs, complete/count/expected_count), indicação de fixture_source padrão e atalhos de diagnóstico direto no Swagger.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/fg1/envelope-check",
      "GET /admin/fiscal/global/fg1/fixture-inventory",
    ],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir FG-1 gate com observabilidade técnica",
  },
  {
    dateTime: "2026-04-30T06:19:00-03:00",
    scope: "FG-1-SPRINT-07 executado (envelope + observabilidade)",
    title: "Envelope-check backend + log estruturado simulate + smoke dedicado",
    description:
      "Execução do sprint FG-1-SPRINT-07 no eixo BE/SRE: nova validação canônica de envelope (45 pares), endpoint GET /admin/fiscal/global/fg1/envelope-check, log INFO estruturado no simulate (trace_id/country/operation/scenario/provider_adapter/fixture_source/canonical_status), script run_fg1_envelope_check_smoke.sh e catálogo de APIs FISCAL atualizado.",
    uiRoutesNew: [],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/envelope-check"],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_stub_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Script: 02_docker/run_fg1_envelope_check_smoke.sh",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
      "DOC: docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir hub FISCAL (endpoint envelope-check)",
  },
  {
    dateTime: "2026-04-29T21:00:00-03:00",
    scope: "Planeamento — próximo sprint FG-1",
    title: "Sprint FG-1-SPRINT-07 preparado: envelope universal + logs estruturados (DoD + tarefas)",
    description:
      "No acompanhamento foi adicionado o bloco «Próximo sprint PREPARADO» (FG-1 envelope + observabilidade): matriz de conformidade fixture/simulate, logs INFO com trace_id/cenário, smoke SRE, FE opcional em fg1-gate/global. Postgres de fixtures fora de escopo até pedido explícito.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: ["DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt"],
    directLink: "/fiscal/updates",
    directLinkLabel: "Histórico FISCAL (planeamento)",
  },
  {
    dateTime: "2026-04-29T20:30:00-03:00",
    scope: "FG-1 fixtures — decisão disco vs BD",
    title: "Registro no acompanhamento: canónico em repo; futuro BD sobrepõe ou só metadados",
    description:
      "Decisão arquitetural documentada em docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt: manter fixtures FG-1 canónicas em disco/repositório; evolução opcional com overrides na BD sobre ficheiro ou apenas metadados (hash, ativo, origem). Backlog explícito: sprint Postgres (modelo + migração + seed + API com fallback) apenas se solicitado.",
    uiRoutesNew: [],
    apiRoutesNew: [],
    routes: ["DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt"],
    directLink: "/fiscal/updates",
    directLinkLabel: "Ver histórico FISCAL (entrada de decisão)",
  },
  {
    dateTime: "2026-04-29T20:05:00-03:00",
    scope: "FG-1 G+2 — fixtures on-disk + inventário",
    title: "Árvore fixtures/fiscal/fg1 + GET fixture-inventory/fixture-document + simulate lê disco",
    description:
      "Sprint Kanban G+2: 45 JSON versionados no serviço fiscal (onda US/AU/PL/CA/FR), endpoints de inventário e documento, simulate com telemetry fixture_source disk|synthetic, script run_fg1_fixture_inventory_smoke.sh e catálogo Swagger FISCAL atualizado.",
    uiRoutesNew: [],
    apiRoutesNew: [
      "GET /admin/fiscal/global/fg1/fixture-inventory",
      "GET /admin/fiscal/global/fg1/fixture-document",
    ],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_stub_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Script: 01_source/backend/billing_fiscal_service/scripts/write_fg1_fixtures.py",
      "Script: 02_docker/run_fg1_fixture_inventory_smoke.sh",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir hub FISCAL (APIs novas no catálogo)",
  },
  {
    dateTime: "2026-04-29T19:18:00-03:00",
    scope: "FG-1 readiness execution - handoff export + Trilha B BR/PT",
    title: "Export CSV/JSON latest (mesmo sufixo de sessão do fg1-gate) + bloco BR/PT bloqueados",
    description:
      "Board fiscal/readiness-execution: exportação do estado completo do plano + execução local com arquivos fg1_readiness_execution_latest_<sessão>.json/.csv, botão copiar nomes latest, duas linhas BR_SNAPSHOT/PT_SNAPSHOT no CSV e objeto trilha_b_br_pt no JSON. Card fixo Trilha B com links para ops/fiscal/providers (#go-no-go-br / #go-no-go-pt), destaque de linhas BR/PT bloqueadas na tabela e resumo BR/PT no copiar handoff.",
    uiRoutesNew: ["/fiscal/readiness-execution"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalReadinessExecutionPage.jsx"],
    directLink: "/fiscal/readiness-execution",
    directLinkLabel: "Abrir board com export e BR/PT",
  },
  {
    dateTime: "2026-04-29T19:10:00-03:00",
    scope: "FG-1 Fase 6 - execução operacional de readiness",
    title: "Nova página fiscal/readiness-execution para fechar bloqueios por país com owner/ETA/status",
    description:
      "Próximo sprint macro codado: criada página dedicada de execução para o readiness-action-plan com board por país, status TODO/IN_PROGRESS/DONE, owner, ETA, notas e cópia de resumo para handoff diário. Menu FISCAL atualizado com novo item e destaque NEW nessa rota.",
    uiRoutesNew: ["/fiscal/readiness-execution"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/readiness-action-plan"],
    routes: [
      "Frontend: 01_source/frontend/src/pages/FiscalReadinessExecutionPage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
    ],
    directLink: "/fiscal/readiness-execution",
    directLinkLabel: "Abrir board de execução de readiness FG-1",
  },
  {
    dateTime: "2026-04-29T19:02:00-03:00",
    scope: "FG-1 plantão - ticket imediato",
    title: "Botão no ops/health para copiar ticket imediato do país mais bloqueado",
    description:
      "Próximo sprint executado com foco em ação rápida: o card FG-1 final no ops/health ganhou botão para copiar ticket imediato do país crítico (maior pending_actions), reduzindo tempo de resposta em incidente e priorização operacional.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx"],
    directLink: "/ops/health",
    directLinkLabel: "Abrir ops/health com ticket imediato FG-1",
  },
  {
    dateTime: "2026-04-29T18:56:00-03:00",
    scope: "FG-1 handoff em 1 clique no plantão",
    title: "Botão no ops/health para copiar payload resumido Slack/Teams do handoff final FG-1",
    description:
      "Fechamento do ciclo operacional: card de decisão final FG-1 no ops/health agora possui ação de cópia em 1 clique para Slack/Teams, reduzindo fricção no plantão e padronizando a comunicação de go/no-go.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx"],
    directLink: "/ops/health",
    directLinkLabel: "Abrir ops/health com cópia 1-clique do handoff FG-1",
  },
  {
    dateTime: "2026-04-29T18:47:00-03:00",
    scope: "FG-1 x OPS - handoff server-side",
    title: "Snapshot final FG-1 via script + endpoint OPS + card no ops/health",
    description:
      "Sprint de integração concluído para reduzir esforço operacional: criado script server-side que gera fg1_final_decision_latest.json, endpoint dev-admin autenticado por OPS_TOKEN para leitura segura e card no ops/health para consumo direto da decisão global no plantão.",
    uiRoutesNew: ["/ops/health"],
    apiRoutesNew: ["GET /dev-admin/fiscal-fg1-final/latest"],
    routes: [
      "Script: 02_docker/run_fg1_final_handoff_snapshot.sh",
      "Backend: 01_source/order_pickup_service/app/routers/dev_admin.py",
      "Frontend: 01_source/frontend/src/pages/OpsHealthPage.jsx",
    ],
    directLink: "/ops/health",
    directLinkLabel: "Abrir card FG-1 final no ops/health",
  },
  {
    dateTime: "2026-04-29T18:38:00-03:00",
    scope: "FG-1 handoff pipeline - redução de esforço",
    title: "Botão 'Copiar nome latest atual' no fiscal/fg1-gate",
    description:
      "Para reduzir esforço operacional no rito diário, foi adicionado botão que copia automaticamente os nomes latest atuais (JSON/CSV) da sessão, pronto para plugar no pipeline de upload sem digitação manual.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx"],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir painel com cópia de nomes latest",
  },
  {
    dateTime: "2026-04-29T18:33:00-03:00",
    scope: "FG-1 handoff automático - naming estável",
    title: "Export do painel final com nome latest estável por sessão (CSV/JSON)",
    description:
      "Sprint de padronização concluído: os arquivos exportados do fiscal/fg1-gate agora usam nomenclatura latest com sufixo estável por sessão, facilitando integração com upload automático no rito de handoff.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx"],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir export latest por sessão",
  },
  {
    dateTime: "2026-04-29T18:31:00-03:00",
    scope: "FG-1 handoff de governança fiscal",
    title: "Export do painel final em CSV/JSON no fiscal/fg1-gate",
    description:
      "Sprint de operacionalização concluído: o painel de decisão final passou a exportar CSV/JSON com decisão global e por país (coverage/readiness/pendências/critério de saída), pronto para anexar diretamente no handoff diário.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx"],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir painel final com export CSV/JSON",
  },
  {
    dateTime: "2026-04-29T18:28:00-03:00",
    scope: "FG-1 decisão executiva de go-live",
    title: "Painel de decisão final adicionado em fiscal/fg1-gate (global + por país + saída para [x])",
    description:
      "Último passo do sprint macro implementado: o cockpit fiscal/fg1-gate agora consolida decisão final por país e global com critério de saída para [x], unificando coverage, readiness e pendências do action plan em uma única camada de decisão operacional.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx"],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir painel de decisão final FG-1",
  },
  {
    dateTime: "2026-04-29T18:18:00-03:00",
    scope: "FG-1 Fase 5 - plano executável de remediação",
    title: "Readiness Action Plan API + seção operacional no fiscal/fg1-gate",
    description:
      "Próximo sprint macro codado: backend publica plano de ação por país com ENVs obrigatórias e ações recomendadas por blocking reason. O fiscal/fg1-gate agora expõe esse plano para execução diária e fechamento objetivo dos bloqueios NO_GO.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/readiness-action-plan"],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_readiness_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir plano de remediação FG-1",
  },
  {
    dateTime: "2026-04-29T18:07:00-03:00",
    scope: "FG-1 Fase 4 - readiness regulatório/operacional",
    title: "Readiness Gate por país com blocking reasons + decisão consolidada no cockpit FG-1",
    description:
      "Sprint macro concluído com gate de prontidão por país: backend agora avalia auth/homologação/certificado/SLA e expõe blocking reasons objetivos. A página fiscal/fg1-gate passou a consolidar Coverage+Readiness em GO/NO_GO único e o fiscal/countries mostra readiness por país para priorização operacional.",
    uiRoutesNew: ["/fiscal/fg1-gate", "/fiscal/countries"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/readiness-gate"],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_readiness_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir gate macro FG-1 (coverage + readiness)",
  },
  {
    dateTime: "2026-04-29T18:05:00-03:00",
    scope: "FG-1 operação diária - smoke + cockpit",
    title: "Script run_fg1_coverage_gate_smoke.sh + integração do gate no fiscal/countries",
    description:
      "Evolução de operação diária da trilha global: criado script curto de smoke do Coverage Gate com JSON/latest em 04_logs/ops e o cockpit fiscal/countries passou a exibir resumo GO/NO_GO do gate em tempo real com link direto para o detalhe técnico.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/coverage-gate"],
    routes: [
      "Script: 02_docker/run_fg1_coverage_gate_smoke.sh",
      "Log: 04_logs/ops/fg1_coverage_gate_smoke_latest.json",
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
    ],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit com resumo do coverage gate",
  },
  {
    dateTime: "2026-04-29T17:51:00-03:00",
    scope: "FISCAL menu - destaque de novidade operacional",
    title: "Badge NEW aplicado somente em fiscal/fg1-gate (removendo destaque anterior)",
    description:
      "Padronização de navegação do sprint: no menu FISCAL, a rota nova fiscal/fg1-gate passou a exibir selo NEW em desktop/mobile, com remoção de destaque de itens anteriores para evitar ambiguidade.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/App.jsx"],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir rota NEW do sprint atual",
  },
  {
    dateTime: "2026-04-29T17:47:00-03:00",
    scope: "FG-1 Fase 3 - Coverage Gate técnico",
    title: "Novo endpoint de cobertura FG-1 + página fiscal/fg1-gate para decisão GO/NO_GO",
    description:
      "Entrega de sprint focada em execução: backend agora expõe gate objetivo de cobertura por país/operação/cenário (missing explícito) e frontend ganhou cockpit técnico dedicado em /fiscal/fg1-gate para decisão de onda com atualização em tempo real.",
    uiRoutesNew: ["/fiscal/fg1-gate"],
    apiRoutesNew: ["GET /admin/fiscal/global/fg1/coverage-gate"],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_fg1_stub_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "Frontend: 01_source/frontend/src/pages/FiscalFg1GatePage.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
    ],
    directLink: "/fiscal/fg1-gate",
    directLinkLabel: "Abrir cockpit de gate FG-1",
  },
  {
    dateTime: "2026-04-29T17:44:00-03:00",
    scope: "Fiscal Countries - onboarding imediato",
    title: "Botão Modo inicial recomendado no cockpit fiscal/countries",
    description:
      "Sincronizado no histórico FISCAL: adicionado botão único de onboarding para reset rápido do cockpit (Execução=ALL e Somente IN WAVE=false), reduzindo ambiguidade para novos operadores.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "DOC docs/Sprint_Fiscal_and_Invoices_ACOMPANHAMENTO.txt"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit com modo inicial recomendado",
  },
  {
    dateTime: "2026-04-29T17:36:00-03:00",
    scope: "Fiscal Countries - correção de uso e visualização",
    title: "fiscal/countries robusto contra backend parcial + guia de uso rápido",
    description:
      "Corrigido cenário em que o cockpit parecia vazio: a tela agora carrega catálogo mesmo quando o endpoint de escopo FG-1 falha, exibe aviso claro, adiciona guia de uso rápido e estado vazio com ação direta para limpar filtros.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit com correção de visualização",
  },
  {
    dateTime: "2026-04-29T17:33:00-03:00",
    scope: "Fiscal API Hub - navegação técnica acelerada",
    title: "Filtro rápido por método (GET/POST) e grupo no fiscal/global",
    description:
      "Evolução operacional no hub de APIs FISCAL: adição de filtros rápidos por método e por grupo de API para reduzir tempo de busca técnica durante operação e integração.",
    uiRoutesNew: ["/fiscal"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal",
    directLinkLabel: "Abrir filtros de método/grupo no catálogo FISCAL",
  },
  {
    dateTime: "2026-04-29T17:30:00-03:00",
    scope: "Fiscal API Hub - integração com Swagger",
    title: "Páginas FISCAL conectadas ao conjunto completo de endpoints",
    description:
      "Integração do domínio FISCAL com catálogo de APIs: fiscal/global agora exibe endpoints agrupados por responsabilidade e todas as páginas fiscais receberam atalho direto para Swagger, reduzindo fricção para operação e integração.",
    uiRoutesNew: ["/fiscal", "/fiscal/countries", "/fiscal/updates"],
    apiRoutesNew: ["Catálogo unificado de endpoints FISCAL (admin/invoice/partner/fiscal)"],
    routes: [
      "Frontend: 01_source/frontend/src/constants/fiscalApiCatalog.ts",
      "Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx",
      "Frontend: 01_source/frontend/src/pages/FiscalUpdatesPage.jsx",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir hub de APIs FISCAL",
  },
  {
    dateTime: "2026-04-29T17:26:00-03:00",
    scope: "Fiscal Global - robustez contra backend parcial",
    title: "fiscal/global com degradação graciosa quando APIs FG-1 não estão disponíveis",
    description:
      "Correção de regressão de visualização: catálogo e matriz (FG-0) agora carregam mesmo se endpoints FG-1 retornarem Not Found no backend atual, exibindo apenas aviso informativo e evitando quebra total da página.",
    uiRoutesNew: ["/fiscal"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global com fallback robusto",
  },
  {
    dateTime: "2026-04-29T17:22:00-03:00",
    scope: "Fiscal QA - prevenção de regressão de rotas",
    title: "Script de smoke para /fiscal, /fiscal/updates e /fiscal/countries",
    description:
      "Criado health-check simples de rotas fiscais para execução recorrente em sprints: valida HTTP 200, bloqueia resposta com Not Found e confirma marcador esperado de cada página fiscal.",
    uiRoutesNew: ["/fiscal", "/fiscal/updates", "/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Script: 02_docker/run_fiscal_routes_smoke.sh", "Log: 04_logs/ops/fiscal_routes_smoke_latest.json"],
    directLink: "/fiscal/updates",
    directLinkLabel: "Abrir histórico da proteção de rotas fiscais",
  },
  {
    dateTime: "2026-04-29T17:20:00-03:00",
    scope: "Fiscal Router - robustez de navegação",
    title: "Recuperação automática para aliases /fiscal/* (global, updates, countries)",
    description:
      "Correção aplicada para eliminar Not Found intermitente em navegação fiscal: a rota de fallback agora recupera caminhos malformados/aliases de todo o namespace /fiscal/*, redirecionando para /fiscal, /fiscal/updates ou /fiscal/countries conforme o contexto.",
    uiRoutesNew: ["/fiscal", "/fiscal/updates", "/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/App.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global com fallback robusto",
  },
  {
    dateTime: "2026-04-29T17:14:00-03:00",
    scope: "FG-1 Stub Global - fase 2 (catálogo conectado)",
    title: "fiscal/global integrado com stub-adapters e fixtures-matrix",
    description:
      "A página fiscal/global passou a consumir e exibir as novas APIs FG-1 no próprio catálogo técnico, consolidando visão de países, cenário canônico, adapters stub e matriz de fixtures em uma única tela operacional.",
    uiRoutesNew: ["/fiscal"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/fg1/stub-adapters",
      "GET /admin/fiscal/global/fg1/fixtures-matrix",
    ],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global com visão FG-1 conectada",
  },
  {
    dateTime: "2026-04-29T17:08:00-03:00",
    scope: "FG-1 Stub Global - execução técnica",
    title: "APIs FG-1 para adapters, fixtures e simulação canônica (US/AU/PL/CA/FR)",
    description:
      "Início do sprint macro FG-1 no billing_fiscal_service com APIs admin para inventário de adapters stub, matriz de fixtures canônicos e simulação por país/operação/cenário com telemetria padronizada.",
    links: [
      { to: "/fiscal", label: "Abrir fiscal/global" },
      { to: "/fiscal/updates", label: "Histórico FISCAL" },
    ],
  },
  {
    dateTime: "2026-04-29T17:00:00-03:00",
    scope: "Fiscal UX - handoff operacional",
    title: "Botão Copiar contexto do filtro no fiscal/countries",
    description:
      "Adicionado botão de handoff para copiar texto completo dos filtros ativos (incluindo preset, recorte da onda e contagens), facilitando passagem de turno diária sem digitação manual.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit e copiar contexto",
  },
  {
    dateTime: "2026-04-29T16:58:00-03:00",
    scope: "Fiscal UX - continuidade de plantão",
    title: "Filtros/preset persistentes + ação Limpar filtros no fiscal/countries",
    description:
      "Evolução de operação aplicada para reduzir retrabalho durante plantão: os filtros do cockpit fiscal/countries agora persistem no navegador após refresh e um botão Limpar filtros permite voltar ao estado neutro em 1 clique.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit com persistência de filtros",
  },
  {
    dateTime: "2026-04-29T16:56:00-03:00",
    scope: "Fiscal UX - identidade visual de domínio",
    title: "Tema visual FISCAL aplicado em /fiscal/* com tokens de página",
    description:
      "Foram definidos tokens visuais específicos de página FISCAL (background, cards, badges e links), aplicado wrapper de layout para rotas /fiscal/* e aderência completa em fiscal/global, fiscal/countries e fiscal/updates.",
    uiRoutesNew: ["/fiscal", "/fiscal/countries", "/fiscal/updates"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/index.css",
      "Frontend: 01_source/frontend/src/components/FiscalPageLayout.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: páginas fiscal/global, fiscal/countries, fiscal/updates",
    ],
    directLink: "/fiscal/updates",
    directLinkLabel: "Abrir histórico FISCAL com novo tema",
  },
  {
    dateTime: "2026-04-29T16:48:00-03:00",
    scope: "Fiscal UX - cockpit FG-1",
    title: "Preset Fechamento FG-1 adicionado (Somente IN WAVE + DONE)",
    description:
      "O cockpit fiscal/countries recebeu preset de fechamento para revisão rápida de conclusão da onda FG-1, aplicando em 1 clique os filtros Somente IN WAVE e DONE.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir fiscal/countries (preset fechamento)",
  },
  {
    dateTime: "2026-04-29T16:45:00-03:00",
    scope: "Fiscal UX - governança de domínio",
    title: "Registro de updates fiscais consolidado em fiscal/updates",
    description:
      "A trilha de mudanças do domínio FISCAL foi consolidada no histórico próprio fiscal/updates, evitando registro cruzado no ops/updates.",
    uiRoutesNew: ["/fiscal/updates"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalUpdatesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/updates",
    directLinkLabel: "Abrir atualizações FISCAL",
  },
  {
    dateTime: "2026-04-29T16:40:00-03:00",
    scope: "Fiscal UX - recuperação de rota + preset de foco",
    title: "Correção de Not Found em fiscal/countries e preset FG-1 de foco",
    description:
      "Aplicada proteção de navegação para recuperar caminhos malformados que contenham fiscal/countries (redirecionando para /fiscal/countries) e adicionado preset de foco FG-1 para ativar Somente IN WAVE + IN_PROGRESS em um clique.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/App.jsx", "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir fiscal/countries com foco FG-1",
  },
  {
    dateTime: "2026-04-29T16:36:00-03:00",
    scope: "Fiscal UX - foco de onda + lote operacional",
    title: "Toggle Somente IN WAVE + ações em lote por filtro no fiscal/countries",
    description:
      "Microevolução aplicada com foco de execução: filtro rápido Somente IN WAVE para reduzir ruído visual e bloco de ação em lote para marcar itens filtrados como TODO/IN_PROGRESS/DONE.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir foco IN WAVE + ações em lote",
  },
  {
    dateTime: "2026-04-29T16:35:00-03:00",
    scope: "FG-0 Foundation",
    title: "Catálogo fiscal global e matriz canônica publicados via API admin",
    description:
      "Foi iniciado o ciclo de fiscalidade global com artefato executável no backend: endpoints para catálogo multipaís e scenario matrix canônica, servindo de base para execução FG-1/FG-2.",
    uiRoutesNew: ["/fiscal", "/fiscal/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/catalog",
      "GET /admin/fiscal/global/scenario-matrix",
    ],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_global_catalog_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /fiscal",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global",
  },
];

export default function FiscalUpdatesPage() {
  const [copyStatus, setCopyStatus] = useState("");
  const [openEntries, setOpenEntries] = useState({});

  async function handleCopyTemplate() {
    try {
      await navigator.clipboard.writeText(TIMELINE_TEMPLATE_JSON);
      setCopyStatus("Template copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch (_) {
      setCopyStatus("Não foi possível copiar automaticamente. Copie manualmente o bloco JSON.");
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020")} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/fiscal" style={shortcutLinkStyle}>
            Abrir fiscal/global
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Updates" versionLabel={FISCAL_UPDATES_PAGE_VERSION} />
        <p style={mutedTextStyle}>Histórico dedicado das entregas da trilha fiscal global.</p>

        <details style={templateBoxStyle}>
          <summary style={templateSummaryStyle}>Mini-template JSON (novos itens da timeline)</summary>
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
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
          {UPDATES.map((item) => (
            <details
              key={`${item.dateTime || item.date}-${item.scope}-${item.title}`}
              style={entryStyle}
              onToggle={(event) => {
                const entryKey = `${item.dateTime || item.date}-${item.scope}-${item.title}`;
                const isOpen = Boolean(event.currentTarget?.open);
                setOpenEntries((prev) => ({ ...prev, [entryKey]: isOpen }));
              }}
            >
              <summary style={entrySummaryStyle}>
                <div style={entrySummaryContentStyle}>
                  <div style={{ display: "grid", gap: 6 }}>
                    <strong>{item.title}</strong>
                    <span style={scopeBadgeStyle}>{item.scope}</span>
                  </div>
                  <span style={entryToggleBadgeStyle}>
                    {openEntries[`${item.dateTime || item.date}-${item.scope}-${item.title}`] ? "Recolher" : "Expandir"}
                  </span>
                </div>
              </summary>
              <div style={entryBodyStyle}>
                <small style={dateStyle}>{formatFiscalUpdateDateTime(item)}</small>
                <p style={descStyle}>
                  <b>{item.scope}:</b> {item.description}
                </p>
                {(item.uiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>UI route NEW</small>
                    <ul style={routesListStyle}>
                      {item.uiRoutesNew.map((route) => (
                        <li key={`ui-${route}`} style={routesListItemStyle}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(item.apiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>API route NEW</small>
                    <ul style={routesListStyle}>
                      {item.apiRoutesNew.map((route) => (
                        <li key={`api-${route}`} style={routesListItemStyle}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(item.routes || []).length ? (
                  <ul style={routesListStyle}>
                    {item.routes.map((route) => (
                      <li key={route} style={routesListItemStyle}>
                        {route}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {item.directLink ? (
                  <div style={linksWrapStyle}>
                    <Link to={item.directLink} style={linkStyle}>
                      {item.directLinkLabel || "Abrir rota relacionada"}
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

function formatFiscalUpdateDateTime(item) {
  const raw = String(item?.dateTime || item?.date || "").trim();
  if (!raw) return "-";
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return formatOpsDateTime(parsed, { dateStyle: "short", timeStyle: "short" });
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", justifyContent: "flex-end", marginBottom: 10 };
const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const templateBoxStyle = {
  marginTop: 10,
  marginBottom: 12,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 10,
  background: "var(--fiscal-box-bg)",
  padding: 10,
};
const templateSummaryStyle = { cursor: "pointer", color: "var(--fiscal-accent-2)", fontWeight: 700 };
const copyButtonStyle = {
  marginTop: 8,
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 12,
};
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "var(--fiscal-accent-2)" };
const templateJsonStyle = {
  marginTop: 8,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 10,
  padding: 10,
  overflow: "auto",
  fontSize: 12,
  background: "var(--fiscal-surface)",
  color: "var(--fiscal-text)",
};
const timelineStyle = { marginTop: 12, display: "grid", gap: 10 };
const entryStyle = {
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 12,
  padding: "8px 12px",
  background: "var(--fiscal-box-bg)",
};
const entrySummaryStyle = { cursor: "pointer", display: "flex", alignItems: "center", listStyle: "none", outline: "none", padding: "2px 0" };
const entrySummaryContentStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap", width: "100%" };
const scopeBadgeStyle = {
  width: "fit-content",
  display: "inline-flex",
  alignItems: "center",
  padding: "2px 8px",
  borderRadius: 999,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-soft-text)",
  fontSize: 11,
  fontWeight: 700,
};
const entryToggleBadgeStyle = {
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  borderRadius: 999,
  padding: "4px 8px",
  fontSize: 11,
  fontWeight: 700,
};
const entryBodyStyle = { marginTop: 8 };
const dateStyle = { color: "var(--fiscal-accent-2)", fontWeight: 700 };
const descStyle = { margin: "8px 0 0", color: "var(--fiscal-soft-text)" };
const linksWrapStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const newRoutesBlockStyle = { marginTop: 8 };
const newRoutesTitleStyle = { color: "var(--fiscal-accent-2)", fontWeight: 700, fontSize: 11 };
const newInlineBadgeStyle = {
  display: "inline-flex",
  marginLeft: 6,
  padding: "1px 6px",
  borderRadius: 999,
  fontSize: 10,
  fontWeight: 700,
  color: "#ecfeff",
  border: "1px solid rgba(45, 212, 191, 0.55)",
  background: "rgba(45, 212, 191, 0.16)",
};
const routesListStyle = { margin: "8px 0 0", paddingLeft: 16, display: "grid", gap: 4 };
const routesListItemStyle = { color: "var(--fiscal-soft-text)", fontSize: 12 };
const linkStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  textDecoration: "none",
  fontSize: 12,
  fontWeight: 600,
};
