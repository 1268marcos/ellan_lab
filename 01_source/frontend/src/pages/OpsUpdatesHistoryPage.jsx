import React, { useState } from "react";
import { Link } from "react-router-dom";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";

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
        <h1 style={{ marginTop: 0 }}>OPS - Updates History</h1>
        <p style={mutedStyle}>
          Histórico de acréscimos OPS com descrição curta de valor e trilha técnica por sprint.
        </p>

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
              key={`${entry.date}-${entry.scope}-${entry.title}`}
              style={entryStyle}
              onToggle={(event) => {
                const entryKey = `${entry.date}-${entry.scope}-${entry.title}`;
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
                    {openEntries[`${entry.date}-${entry.scope}-${entry.title}`] ? "Recolher" : "Expandir"}
                  </span>
                </div>
              </summary>
              <div style={entryBodyStyle}>
                <small style={{ color: "#94A3B8" }}>{entry.date}</small>
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
