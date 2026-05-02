/**
 * Sprint 4 — KPI mínimo de saída (baseline numérica por persona, lab / handoff).
 * Fonte narrativa: `docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md` (Sprint 4 + Sprint 0 baseline).
 */

export const SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION = "sprint4-slo-kpi-exit-baseline-v1";

/**
 * Baseline v1 (valores congelados para comparação em revisões Sprint 4; não substitui séries oficiais em prod).
 * @type {{ persona: string, kpi: string, value: number, unit: string, source: string }[]}
 */
export const SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA = [
  { persona: "Comprador ONLINE", kpi: "taxa_erro_checkout", value: 2.1, unit: "%", source: "funil checkout + erros 4xx/409 (lab)" },
  { persona: "OPS", kpi: "mttr_incidente_mediana", value: 4.5, unit: "h", source: "ops/health + pacotes diários (amostra lab)" },
  { persona: "Suporte", kpi: "fcr_primeiro_contacto", value: 62, unit: "%", source: "console jornada + macros (amostra lab)" },
  { persona: "Comprador KIOSK", kpi: "tempo_funil_p95", value: 78, unit: "s", source: "E2E kiosk A–D + totem PT mock (lab)" },
  { persona: "Parceiros", kpi: "divergencia_settlement_p95", value: 3.2, unit: "dias", source: "reconciliação amostra piloto" },
  { persona: "Fiscal / OPS", kpi: "share_emissor_nao_ok", value: 1.8, unit: "%", source: "GET providers/status agregado" },
  { persona: "Contábil", kpi: "tempo_medio_pendencia_d18", value: 18, unit: "h", source: "accounting-approvals/latest + janela 7D" },
];

/**
 * Configuração mínima esperada em produção para `fiscal/slo-alerts` (documental; segredos fora do repo).
 */
export const FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG = {
  version: "fiscal-slo-alerts-prod-min-v1",
  env: {
    VITE_BILLING_FISCAL_BASE_URL: "https://<billing-fiscal-host>",
    VITE_INTERNAL_TOKEN: "<set-only-in-deployment-secret>",
  },
  ui_defaults: {
    periodFilter: "7D",
    countryFilter: "ALL",
    partnerFilter: "ALL",
    calibrationProfile: "AUTO",
  },
  required_headers: {
    Accept: "application/json",
    "X-Internal-Token": "from VITE_INTERNAL_TOKEN",
  },
  api_endpoints: [
    "GET {BILLING}/admin/fiscal/providers/status",
    "GET {BILLING}/admin/fiscal/accounting-approvals/latest",
    "GET {BILLING}/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=500",
    "GET {BILLING}/admin/fiscal/accounting-approvals/divergence-health (parâmetros conforme rollup)",
    "GET {BILLING}/admin/fiscal/accounting-approvals (consolidado date_from)",
  ],
};

/**
 * Linhas de shell para colar métricas SLO (mesmas fontes que `FiscalSloAlertsPage.loadData`).
 * Substituir BASE e TOK antes de executar.
 */
export const SPRINT4_SLO_METRICS_COLLECT_COMMANDS = [
  'BASE="${VITE_BILLING_FISCAL_BASE_URL:-http://127.0.0.1:8020}"',
  'TOK="${VITE_INTERNAL_TOKEN:?defina VITE_INTERNAL_TOKEN}"',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/providers/status" | tee slo-providers-status.json',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/accounting-approvals/latest" | tee slo-approvals-latest.json',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=500" | tee slo-e2e-audit-trail.json',
];
