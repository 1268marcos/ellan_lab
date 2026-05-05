
/**
 * Sprint 4 — KPI mínimo de saída (baseline numérica por persona; séries oficiais produção + calibragem BR/PT).
 * Fonte narrativa: `docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md` (Sprint 4 + Sprint 0 baseline).
 */

export const SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION = "sprint4-slo-kpi-exit-baseline-v2-prod-br-pt";

/**
 * Baseline v2 — médias oficiais janela 7D pós-calibragem regional presencial BR/PT (`fiscal/slo-alerts`).
 * @type {{ persona: string, kpi: string, value: number, unit: string, source: string }[]}
 */
export const SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA = [
  { persona: "Comprador ONLINE", kpi: "taxa_erro_checkout", value: 1.95, unit: "%", source: "série oficial produção 7D (4xx/409 checkout)" },
  { persona: "OPS", kpi: "mttr_incidente_mediana", value: 4.25, unit: "h", source: "série oficial produção 7D (ops/health + dailies)" },
  { persona: "Suporte", kpi: "fcr_primeiro_contacto", value: 64, unit: "%", source: "série oficial produção 7D (macros + tickets)" },
  { persona: "Comprador KIOSK", kpi: "tempo_funil_p95", value: 76, unit: "s", source: "série oficial produção 7D (E2E + totens BR/PT)" },
  { persona: "Parceiros", kpi: "divergencia_settlement_p95", value: 3.05, unit: "dias", source: "série oficial produção 7D (divergence-health D17)" },
  { persona: "Fiscal / OPS", kpi: "share_emissor_nao_ok", value: 1.65, unit: "%", source: "série oficial produção 7D (providers/status)" },
  { persona: "Contábil", kpi: "tempo_medio_pendencia_d18", value: 16.5, unit: "h", source: "série oficial produção 7D (accounting-approvals consolidado)" },
];

/** Template JSON para anexo presencial BR/PT (ZIP daily / acta). */
export const SPRINT4_SLO_CALIBRATION_BR_PT_EVIDENCE = {
  scope: "SPRINT4_SLO_CALIBRATION_BR_PT_PRESENCIAL",
  schema_version: "sprint4-slo-calibration-br-pt-evidence-v1",
  session_id: "",
  signed_at: "",
  operator: "",
  location: "",
  country_targets: { BR: "thresholds_by_country.BR aplicados e assinados", PT: "thresholds_by_country.PT aplicados e assinados" },
  slo_alerts_page_version_ref: "fiscal/slo-alerts",
  export_attachment_refs: ["SPRINT3_SLO_SCORECARD bundle", "ELLAN_FISCAL_DAILY_*"],
};

/**
 * Configuração mínima esperada em produção para `fiscal/slo-alerts` (documental; segredos fora do repo).
 */
export const FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG = {
  version: "fiscal-slo-alerts-prod-min-v2-br-pt",
  env: {
    VITE_BILLING_FISCAL_BASE_URL: "https://<billing-fiscal-host>",
    VITE_INTERNAL_TOKEN: "<set-only-in-deployment-secret>",
  },
  ui_defaults: {
    periodFilter: "7D",
    countryFilter: "ALL",
    partnerFilter: "ALL",
    calibrationProfile: "BR_PT_PRESENCIAL_SIGNED",
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
  'DATE_FROM="${DATE_FROM:?defina DATE_FROM YYYY-MM-DD (início janela 7D)}"',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/providers/status" | tee slo-providers-status.json',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/accounting-approvals/latest" | tee slo-approvals-latest.json',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=500" | tee slo-e2e-audit-trail.json',
  'curl -sS -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/accounting-approvals/divergence-health?window=8&prolonged_edges=3" | tee slo-divergence-health.json',
  'curl -sS -G -H "Accept: application/json" -H "X-Internal-Token: $TOK" "$BASE/admin/fiscal/accounting-approvals" --data-urlencode "date_from=$DATE_FROM" --data-urlencode "limit=200" --data-urlencode "offset=0" | tee slo-accounting-approvals-consolidated.json',
];

