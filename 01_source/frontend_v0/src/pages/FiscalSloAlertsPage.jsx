
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import {
  fetchAccountingApprovalsDivergenceHealth,
  fetchConsolidatedAccountingApprovals,
} from "../utils/fiscalAccountingApprovalsHistory";
import {
  appendSloPostRecommendationDecision,
  buildSloPostRecommendationDecisionsPayload,
  clearSloPostRecommendationDecisions,
  loadSloPostRecommendationDecisions,
  SPRINT3_SLO_POST_REC_VERSION,
} from "../utils/fiscalSprint3SloPostRecDecisions";
import {
  applySprint3CountryCalibration,
  buildCountrySloScorecardRows,
  buildSloThresholdsExportBundle,
  COUNTRY_CALIBRATION_PROFILES,
  computeSloFiscalOpsReadinessScore,
  resolveSprint3SloBaseThresholds,
  SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA,
  SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION,
} from "../utils/fiscalSprint3SloScorecardRollup";
import {
  FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG,
  SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA,
  SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION,
  SPRINT4_SLO_METRICS_COLLECT_COMMANDS,
} from "../utils/fiscalSprint4SloKpiExitBaseline";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/slo-alerts v1.8.0-sprint4-kpi-exit-baseline-v2-prod-br-pt";

const POST_REC_DECISION_OPTIONS = [
  { value: "FOLLOW_RECOMMENDATION", label: "Seguir recomendação (ação alinhada)" },
  { value: "PARTIAL_APPLY", label: "Aplicar parcialmente / piloto" },
  { value: "DEFER", label: "Adiar (aguardar dados ou janela)" },
  { value: "REJECT", label: "Não aplicar (rejeitar)" },
  { value: "INVESTIGATE_FIRST", label: "Investigar antes de mudar threshold" },
];
const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";

const CALIBRATION_STRATEGY_SEVERITY = Object.freeze({
  TIGHTEN_THRESHOLDS: "MEDIUM",
  INVESTIGATE_FIRST: "HIGH",
  KEEP_BASELINE: "LOW",
});

function median(values) {
  const nums = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (nums.length === 0) return 0;
  const mid = Math.floor(nums.length / 2);
  if (nums.length % 2 === 1) return nums[mid];
  return (nums[mid - 1] + nums[mid]) / 2;
}

function percentileFromSorted(sortedNums, p) {
  if (sortedNums.length === 0) return 0;
  const index = Math.min(sortedNums.length - 1, Math.ceil((p / 100) * sortedNums.length) - 1);
  return sortedNums[Math.max(index, 0)];
}

function buildCountryPartnerStats(rows) {
  /** @type {Map<string, {country: string, partner: string, latencies: number[], errors: number, total: number}>} */
  const map = new Map();
  for (const row of rows) {
    const country = String(row?.country || "").toUpperCase() || "UNKNOWN";
    const partner = String(row?.provider_name || "").trim() || "UNKNOWN";
    const key = `${country}::${partner}`;
    const latency = Number(row?.last_latency_ms || 0);
    const isError = String(row?.last_status || "").toUpperCase() !== "OK";
    const cur = map.get(key) || { country, partner, latencies: [], errors: 0, total: 0 };
    cur.total += 1;
    if (isError) cur.errors += 1;
    if (Number.isFinite(latency) && latency > 0) cur.latencies.push(latency);
    map.set(key, cur);
  }
  return Array.from(map.values());
}

function buildAutoAdjustmentRecommendations({
  rowsAllProviders,
  thresholds,
  countryFilter,
  partnerFilter,
  auditTrail,
}) {
  const stats = buildCountryPartnerStats(rowsAllProviders);
  const recs = [];

  const scopedStats = stats.filter((row) => {
    if (countryFilter !== "ALL" && row.country !== countryFilter) return false;
    if (partnerFilter !== "ALL" && row.partner !== partnerFilter) return false;
    return true;
  });

  for (const slice of scopedStats) {
    if (slice.total <= 0) continue;
    const errorRate = slice.errors / slice.total;
    const latSorted = [...slice.latencies].sort((a, b) => a - b);
    const p95 = percentileFromSorted(latSorted, 95);
    const med = median(slice.latencies);

    const nearMediumShare =
      slice.latencies.length > 0
        ? slice.latencies.filter((v) => v >= thresholds.latencyP95Ms.medium * 0.85).length / slice.latencies.length
        : 0;

    const noisyLatencyCluster =
      p95 >= thresholds.latencyP95Ms.medium * 0.9 &&
      p95 < thresholds.latencyP95Ms.high &&
      nearMediumShare >= 0.45 &&
      slice.latencies.length >= 3;

    if (noisyLatencyCluster) {
      recs.push({
        id: `latency_tighten_${slice.country}_${slice.partner}`,
        severity_hint: "MEDIUM",
        target: { country: slice.country, partner: slice.partner },
        recommendation:
          `Ruído recorrente de latência próximo ao limiar médio (${Math.round(thresholds.latencyP95Ms.medium)} ms). Considere reduzir o threshold de latência (p95) para ${slice.country}${slice.partner !== "UNKNOWN" ? ` / ${slice.partner}` : ""} ou investigar degradação pontual antes de ampliar alertas globais.`,
        evidence: {
          latency_p95_ms: Math.round(p95),
          latency_median_ms: Math.round(med),
          near_medium_share: Number(nearMediumShare.toFixed(2)),
          provider_rows: slice.total,
        },
      });
    }

    const nearErrorMedium =
      errorRate >= thresholds.errorRate.medium * 0.75 && errorRate < thresholds.errorRate.medium;
    if (nearErrorMedium && slice.total >= 3) {
      recs.push({
        id: `error_rate_watch_${slice.country}_${slice.partner}`,
        severity_hint: "MEDIUM",
        target: { country: slice.country, partner: slice.partner },
        recommendation:
          `Taxa de erro fiscal subindo em direção ao limiar médio (${(thresholds.errorRate.medium * 100).toFixed(0)}%). Considere reduzir o threshold médio em ${slice.country}${slice.partner !== "UNKNOWN" ? ` / ${slice.partner}` : ""} ou priorizar triagem de providers com status não-OK.`,
        evidence: {
          error_rate: Number(errorRate.toFixed(4)),
          provider_rows: slice.total,
          provider_rows_error: slice.errors,
        },
      });
    }
  }

  const materializedRate = Number(auditTrail?.coverage?.materialized_rate || 0);
  const targetRate = Number(auditTrail?.coverage?.target_rate || 1);
  const materializedPass = Number(auditTrail?.coverage?.materialized_complete || 0);
  const materializedTotal = Number(auditTrail?.coverage?.total || 0);
  if (materializedTotal > 0 && targetRate > 0 && materializedRate < targetRate && materializedRate >= targetRate * 0.85) {
    recs.push({
      id: "e2e_audit_coverage_near_target",
      severity_hint: "MEDIUM",
      target: { country: countryFilter, partner: partnerFilter },
      recommendation:
        "Cobertura da trilha ponta a ponta (4 chaves) está próxima do alvo, mas ainda abaixo de 100%. Antes de endurecer thresholds globais de SLO, priorize fechar lacunas de materialização e repetir o scorecard.",
      evidence: {
        materialized_rate: Number(materializedRate.toFixed(4)),
        target_rate: Number(targetRate.toFixed(4)),
        materialized_coverage: `${materializedPass}/${materializedTotal}`,
      },
    });
  }

  const rank = (item) => {
    const p95 = Number(item?.evidence?.latency_p95_ms || 0);
    const share = Number(item?.evidence?.near_medium_share || 0);
    const err = Number(item?.evidence?.error_rate || 0);
    return p95 * 2 + share * 500 + err * 2000;
  };

  return recs.sort((a, b) => rank(b) - rank(a)).slice(0, 6);
}

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function toAuditDayStamp(isoString) {
  return String(isoString || "").slice(0, 10).replaceAll("-", "");
}

function downloadJsonFile(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

function downloadZipFile(filename, filesMap) {
  const zipped = zipSync(filesMap, { level: 6 });
  const blob = new Blob([zipped], { type: "application/zip" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

async function computeSha256Hex(content) {
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(String(content || ""));
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function buildSignedPayload(payload) {
  const payloadJson = JSON.stringify(payload, null, 2);
  return {
    integrity: {
      algorithm: "SHA-256",
      content_sha256: await computeSha256Hex(payloadJson),
    },
    payload,
  };
}

function percentile(values, p) {
  const nums = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (nums.length === 0) return 0;
  const index = Math.min(nums.length - 1, Math.ceil((p / 100) * nums.length) - 1);
  return nums[Math.max(index, 0)];
}

function readPeriodDateFrom(period) {
  const now = new Date();
  const days = period === "24H" ? 1 : period === "30D" ? 30 : 7;
  const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
  return from.toISOString().slice(0, 10);
}

function evaluateSloSeverity({
  thresholds,
  errorRate,
  latencyP95,
  hoursSinceLatestApproval,
  prolongedDiff,
}) {
  const reasons = [];
  let severity = "LOW";

  if (Boolean(prolongedDiff) === thresholds.prolongedDiff.critical) {
    severity = "CRITICAL";
    reasons.push("divergencia_prolongada");
  }
  if (errorRate >= thresholds.errorRate.critical) {
    severity = "CRITICAL";
    reasons.push("erro_fiscal_rate_critical");
  } else if (errorRate >= thresholds.errorRate.medium && severity !== "CRITICAL") {
    severity = "MEDIUM";
    reasons.push("erro_fiscal_rate_medium");
  }

  if (latencyP95 >= thresholds.latencyP95Ms.high && severity !== "CRITICAL") {
    severity = "HIGH";
    reasons.push("latency_p95_high");
  } else if (
    latencyP95 >= thresholds.latencyP95Ms.medium &&
    !["CRITICAL", "HIGH"].includes(severity)
  ) {
    severity = "MEDIUM";
    reasons.push("latency_p95_medium");
  }

  if (hoursSinceLatestApproval >= thresholds.hoursSinceLatestApproval.high && severity !== "CRITICAL") {
    severity = "HIGH";
    reasons.push("tempo_tratativa_high");
  }

  return { severity, reasons };
}

function buildCalibrationPlaybook({ sloSeverity, reasons, recommendations }) {
  const hasNearThresholdSignals = recommendations.some((row) =>
    String(row?.id || "").startsWith("latency_tighten_") || String(row?.id || "").startsWith("error_rate_watch_")
  );
  const hasAuditCoverageGap = recommendations.some((row) => String(row?.id || "") === "e2e_audit_coverage_near_target");
  const hasCriticalReasons = reasons.some((r) => String(r || "").includes("critical") || String(r || "").includes("high"));

  if (sloSeverity === "CRITICAL" || sloSeverity === "HIGH" || hasCriticalReasons) {
    return {
      strategy: "INVESTIGATE_FIRST",
      rationale: "Incidente ativo ou sinais de alto impacto: estabilizar antes de endurecer limiares.",
      next_actions: [
        "Abrir tratativa com owner/ETA no turno atual.",
        "Validar 3 maiores fontes de erro/latência por parceiro.",
        "Reavaliar thresholds somente após mitigação e 1 ciclo estável.",
      ],
    };
  }
  if (hasAuditCoverageGap) {
    return {
      strategy: "INVESTIGATE_FIRST",
      rationale: "Cobertura E2E ainda abaixo de 100%; endurecimento agora aumenta risco de falso positivo.",
      next_actions: [
        "Fechar lacunas de materialização das 4 chaves.",
        "Repetir scorecard com trilha completa.",
        "Só então aplicar endurecimento por país/parceiro.",
      ],
    };
  }
  if (hasNearThresholdSignals) {
    return {
      strategy: "TIGHTEN_THRESHOLDS",
      rationale: "Ruído recorrente próximo ao limiar médio com operação estável.",
      next_actions: [
        "Reduzir limiares médios por país/parceiro (mudança incremental).",
        "Acompanhar 24h para validar redução de ruído sem ampliar incidentes.",
        "Registrar decisão no handoff diário.",
      ],
    };
  }
  return {
    strategy: "KEEP_BASELINE",
    rationale: "Sem sinais consistentes para calibragem adicional no snapshot atual.",
    next_actions: [
      "Manter thresholds atuais.",
      "Revisar no próximo ciclo diário com novos dados.",
    ],
  };
}

export default function FiscalSloAlertsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [providers, setProviders] = useState([]);
  const [divergenceHealth, setDivergenceHealth] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [latestApproval, setLatestApproval] = useState(null);
  const [auditTrail, setAuditTrail] = useState(null);
  const [countryFilter, setCountryFilter] = useState("ALL");
  const [partnerFilter, setPartnerFilter] = useState("ALL");
  const [periodFilter, setPeriodFilter] = useState("7D");
  const [calibrationProfile, setCalibrationProfile] = useState("AUTO");
  const [postRecDecisions, setPostRecDecisions] = useState(() => loadSloPostRecommendationDecisions());
  const [postRecSelectedRecId, setPostRecSelectedRecId] = useState("");
  const [postRecOperatorDecision, setPostRecOperatorDecision] = useState("INVESTIGATE_FIRST");
  const [postRecOperatorNotes, setPostRecOperatorNotes] = useState("");
  const effectiveCalibrationProfile = useMemo(() => {
    if (calibrationProfile !== "AUTO") return calibrationProfile;
    if (countryFilter === "BR" || countryFilter === "PT") return countryFilter;
    return "GLOBAL";
  }, [calibrationProfile, countryFilter]);
  const activeThresholds = useMemo(
    () => applySprint3CountryCalibration(resolveSprint3SloBaseThresholds(periodFilter), effectiveCalibrationProfile),
    [periodFilter, effectiveCalibrationProfile]
  );

  useEffect(() => {
    void loadData();
  }, []);

  const filteredProviders = useMemo(() => {
    return providers.filter((row) => {
      const country = String(row?.country || "").toUpperCase();
      const partner = String(row?.provider_name || "");
      if (countryFilter !== "ALL" && country !== countryFilter) return false;
      if (partnerFilter !== "ALL" && partner !== partnerFilter) return false;
      return true;
    });
  }, [providers, countryFilter, partnerFilter]);

  const partnerOptions = useMemo(() => {
    const set = new Set(["ALL"]);
    for (const row of providers) {
      const name = String(row?.provider_name || "").trim();
      if (name) set.add(name);
    }
    return Array.from(set);
  }, [providers]);

  const errorCount = filteredProviders.filter((row) => String(row?.last_status || "").toUpperCase() !== "OK").length;
  const totalCount = filteredProviders.length;
  const errorRate = totalCount > 0 ? errorCount / totalCount : 0;
  const latencies = filteredProviders.map((row) => Number(row?.last_latency_ms || 0)).filter((v) => v > 0);
  const latencyP95 = percentile(latencies, 95);
  const latestCreatedAt = String(latestApproval?.created_at || "");
  const hoursSinceLatestApproval =
    latestCreatedAt && Number.isFinite(new Date(latestCreatedAt).getTime())
      ? Math.max(0, (Date.now() - new Date(latestCreatedAt).getTime()) / (1000 * 60 * 60))
      : 0;
  const prolongedDiff = Boolean(divergenceHealth?.prolonged_identical_diff);
  const prolongedEdges = Number(divergenceHealth?.prolonged_detail?.consecutive_edges_with_same_diff || 0);
  const auditMaterializedRate = Number(auditTrail?.coverage?.materialized_rate || 0);
  const auditMaterializedPass = Number(auditTrail?.coverage?.materialized_complete || 0);
  const auditMaterializedTotal = Number(auditTrail?.coverage?.total || 0);

  const sloAssessment = useMemo(
    () =>
      evaluateSloSeverity({
        thresholds: activeThresholds,
        prolongedDiff,
        errorRate,
        latencyP95,
        hoursSinceLatestApproval,
      }),
    [activeThresholds, prolongedDiff, errorRate, latencyP95, hoursSinceLatestApproval]
  );
  const sloSeverity = sloAssessment.severity;

  const adjustmentRecommendations = useMemo(
    () =>
      buildAutoAdjustmentRecommendations({
        rowsAllProviders: providers,
        thresholds: activeThresholds,
        countryFilter,
        partnerFilter,
        auditTrail,
      }),
    [providers, activeThresholds, countryFilter, partnerFilter, auditTrail]
  );
  const calibrationPlaybook = useMemo(
    () =>
      buildCalibrationPlaybook({
        sloSeverity,
        reasons: sloAssessment.reasons,
        recommendations: adjustmentRecommendations,
      }),
    [sloSeverity, sloAssessment.reasons, adjustmentRecommendations]
  );

  const countryScorecardAll = useMemo(() => buildCountrySloScorecardRows(providers), [providers]);

  const sloReadinessScore = useMemo(
    () =>
      computeSloFiscalOpsReadinessScore({
        sloSeverity,
        errorRate,
        latencyP95,
        thresholds: activeThresholds,
        auditMaterializedRate,
      }),
    [sloSeverity, errorRate, latencyP95, activeThresholds, auditMaterializedRate]
  );

  function buildPostRecScorecardDigest() {
    return {
      export_schema: SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA,
      page_version: PAGE_VERSION,
      threshold_bundle: SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION,
      thresholds_by_country: buildSloThresholdsExportBundle(periodFilter),
      filters: {
        country: countryFilter,
        partner: partnerFilter,
        period: periodFilter,
        calibration_applied: effectiveCalibrationProfile,
      },
      slo_readiness_0_100: sloReadinessScore,
      slo_severity: sloSeverity,
      scorecard_by_country: countryScorecardAll,
      e2e_audit_trail_rollups: auditTrail?.trail_rollups ?? null,
    };
  }

  async function loadData(periodOverride = null) {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido. Configure VITE_INTERNAL_TOKEN.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const effectivePeriod = periodOverride || periodFilter;
      const thresholdsForFetch = resolveSprint3SloBaseThresholds(effectivePeriod);
      const dateFrom = readPeriodDateFrom(effectivePeriod);
      const [providerRes, latestRes, auditRes, divergencePayload, approvalsPayload] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/providers/status`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/accounting-approvals/latest`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=500`, { method: "GET", headers: headersJson() }),
        fetchAccountingApprovalsDivergenceHealth({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          window: thresholdsForFetch.prolongedDiff.divergenceWindow,
          prolongedEdges: thresholdsForFetch.prolongedDiff.prolongedEdges,
        }),
        fetchConsolidatedAccountingApprovals({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          filters: { date_from: dateFrom },
          pageSize: 200,
        }),
      ]);
      const [providerPayload, latestPayload, auditPayload] = await Promise.all([
        providerRes.json().catch(() => ({})),
        latestRes.json().catch(() => ({})),
        auditRes.json().catch(() => ({})),
      ]);
      if (!providerRes.ok || !latestRes.ok || !auditRes.ok) {
        throw new Error(String(providerPayload?.detail || latestPayload?.detail || auditPayload?.detail || "Falha ao carregar SLO fiscal."));
      }
      setProviders(Array.isArray(providerPayload?.items) ? providerPayload.items : []);
      setLatestApproval(latestPayload?.item || null);
      setAuditTrail(auditPayload || null);
      setDivergenceHealth(divergencePayload || null);
      setApprovals(Array.isArray(approvalsPayload?.items) ? approvalsPayload.items : []);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function buildSloPayload(nowIso) {
    return {
      scope: "SPRINT3_SLO_SCORECARD",
      export_schema: SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA,
      generated_at: nowIso,
      filters: {
        country: countryFilter,
        partner: partnerFilter,
        period: periodFilter,
        calibration_profile: calibrationProfile,
        calibration_applied: effectiveCalibrationProfile,
      },
      metrics: {
        erro_fiscal_rate: Number(errorRate.toFixed(4)),
        latency_p95_ms: Number(latencyP95.toFixed(2)),
        divergencia_prolongada: prolongedDiff,
        divergencia_edges: prolongedEdges,
        tempo_tratativa_horas_desde_ultimo_snapshot: Number(hoursSinceLatestApproval.toFixed(2)),
        trilha_e2e_materialized_rate: Number(auditMaterializedRate.toFixed(4)),
      },
      thresholds: {
        version: SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION,
        selected_period: periodFilter,
        error_rate: activeThresholds.errorRate,
        latency_p95_ms: activeThresholds.latencyP95Ms,
        hours_since_latest_approval: activeThresholds.hoursSinceLatestApproval,
        prolonged_diff: activeThresholds.prolongedDiff,
        calibration_profile: {
          key: effectiveCalibrationProfile,
          label: COUNTRY_CALIBRATION_PROFILES[effectiveCalibrationProfile]?.label || "Global baseline",
        },
        by_country: buildSloThresholdsExportBundle(periodFilter),
      },
      totals: {
        provider_rows_filtered: totalCount,
        provider_rows_error: errorCount,
        approvals_in_period: approvals.length,
        e2e_audit_rows: auditMaterializedTotal,
      },
      scorecard_rollups: {
        by_country: countryScorecardAll,
        thresholds_by_country: buildSloThresholdsExportBundle(periodFilter),
        slo_readiness_0_100: sloReadinessScore,
        fiscal_ops_note:
          "Agregado por país sobre `providers/status`; readiness combina severidade SLO, erro, latência p95 vs limiares da janela e cobertura E2E.",
      },
      e2e_audit_trail_rollups: auditTrail?.trail_rollups ?? null,
      alerts: {
        severity: sloSeverity,
        triggered_reasons: sloAssessment.reasons,
        active: sloSeverity !== "LOW",
        auto_adjustment_recommendations: adjustmentRecommendations,
        post_recommendation_decisions: {
          version: SPRINT3_SLO_POST_REC_VERSION,
          count: postRecDecisions.length,
          last_3: postRecDecisions.slice(-3),
          timeline: postRecDecisions.slice(-10),
        },
        calibration_playbook: calibrationPlaybook,
        practical_action:
          sloSeverity === "CRITICAL"
            ? "Escalar incidente fiscal imediatamente e acionar war room."
            : sloSeverity === "HIGH"
              ? "Abrir plano de mitigação com owner e ETA no turno atual."
              : sloSeverity === "MEDIUM"
                ? "Reforçar monitoramento e revisar thresholds no daily."
                : "Operação estável; manter monitoramento passivo.",
      },
      e2e_audit_trail: {
        decision: String(auditTrail?.decision || "NO_GO"),
        evidence_id: String(auditTrail?.handoff_evidence?.evidence_id || "-"),
        materialized_coverage: `${auditMaterializedPass}/${auditMaterializedTotal}`,
        materialized_rate: Number(auditMaterializedRate.toFixed(4)),
        target_rate: Number(auditTrail?.coverage?.target_rate || 1),
      },
    };
  }

  function registerPostRecommendationDecision() {
    const nowIso = new Date().toISOString();
    if (!postRecSelectedRecId) {
      setStatus("Selecione uma recomendação da lista ou “Outra…”.");
      window.setTimeout(() => setStatus(""), 2600);
      return;
    }
    const notesTrim = String(postRecOperatorNotes || "").trim();
    if (notesTrim.length < 8) {
      setStatus("Notas obrigatórias (mín. 8 caracteres) para evidência auditável.");
      window.setTimeout(() => setStatus(""), 2800);
      return;
    }
    const manual = postRecSelectedRecId === "__manual__";
    const rec = !manual ? adjustmentRecommendations.find((r) => r.id === postRecSelectedRecId) : null;
    if (!manual && !rec) {
      setStatus("Recomendação inválida para o snapshot atual. Atualize a página ou escolha “Outra…”.");
      window.setTimeout(() => setStatus(""), 2600);
      return;
    }
    if (!postRecOperatorDecision) {
      setStatus("Escolha a decisão operacional.");
      window.setTimeout(() => setStatus(""), 2200);
      return;
    }
    const entry = {
      id: `p02_${Date.now()}`,
      recorded_at: nowIso,
      recommendation_id: rec ? String(rec.id || "") : null,
      recommendation_summary: rec
        ? String(rec.recommendation || "").slice(0, 500)
        : notesTrim.slice(0, 240) || "-",
      operator_decision: String(postRecOperatorDecision),
      operator_notes: notesTrim,
      filters_snapshot: {
        country: countryFilter,
        partner: partnerFilter,
        period: periodFilter,
        calibration_profile: calibrationProfile,
        calibration_applied: effectiveCalibrationProfile,
      },
      slo_severity_snapshot: sloSeverity,
    };
    const next = appendSloPostRecommendationDecision(entry);
    setPostRecDecisions(next);
    setPostRecOperatorNotes("");
    setPostRecSelectedRecId("");
    setStatus("Decisão pós-recomendação registada (P0-2).");
    window.setTimeout(() => setStatus(""), 2400);
  }

  function clearPostRecommendationDecisions() {
    const ok = window.confirm("Apagar todas as decisões P0-2 guardadas neste browser?");
    if (!ok) return;
    clearSloPostRecommendationDecisions();
    setPostRecDecisions([]);
    setStatus("Histórico P0-2 limpo.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportPostRecDecisionsJson() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const payload = buildSloPostRecommendationDecisionsPayload(
      nowIso,
      postRecDecisions,
      "fiscal/slo-alerts",
      buildPostRecScorecardDigest()
    );
    const signed = await buildSignedPayload(payload);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_P0_2_POST_REC_DECISIONS_${ts}.json`, signed);
    setStatus("Decisões P0-2 exportadas (.json assinado).");
    window.setTimeout(() => setStatus(""), 2400);
  }

  async function exportUniqueHandoffEvidence() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const payload = {
      scope: "SPRINT3_P0_1_E2E_AUDIT_HANDOFF",
      generated_at: nowIso,
      decision: String(auditTrail?.decision || "NO_GO"),
      mandatory_trace_keys: ["order_id", "invoice_id", "partner_id", "batch_id"],
      coverage: auditTrail?.coverage || null,
      evidence: auditTrail?.handoff_evidence || null,
      summary: {
        slo_severity: sloSeverity,
        erro_fiscal_rate: Number(errorRate.toFixed(4)),
        latency_p95_ms: Number(latencyP95.toFixed(2)),
        divergencia_prolongada: prolongedDiff,
        tempo_tratativa_horas_desde_ultimo_snapshot: Number(hoursSinceLatestApproval.toFixed(2)),
      },
      sample_items: Array.isArray(auditTrail?.items) ? auditTrail.items.slice(0, 25) : [],
    };
    const signed = await buildSignedPayload(payload);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_E2E_AUDIT_HANDOFF_${ts}.json`, signed);
    setStatus("Evidência operacional única (P0-1) exportada.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportJson() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signed = await buildSignedPayload(buildSloPayload(nowIso));
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_SLO_SCORECARD_${ts}.json`, signed);
    setStatus("Payload SLO exportado em JSON.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportZip() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signedScorecard = await buildSignedPayload(buildSloPayload(nowIso));
    const signedRaw = await buildSignedPayload({
      scope: "SPRINT3_SLO_SCORECARD_RAW",
      generated_at: nowIso,
      raw: {
        providers_filtered: filteredProviders,
        country_scorecard_all: countryScorecardAll,
        slo_readiness_0_100: sloReadinessScore,
        divergence_health: divergenceHealth,
        latest_approval: latestApproval,
        auto_adjustment_recommendations: adjustmentRecommendations,
        calibration_playbook: calibrationPlaybook,
        calibration_profile: {
          selected: calibrationProfile,
          applied: effectiveCalibrationProfile,
        },
        thresholds_by_country: buildSloThresholdsExportBundle(periodFilter),
        e2e_audit_trail_rollups: auditTrail?.trail_rollups ?? null,
      },
    });
    const signedPostRec = await buildSignedPayload(
      buildSloPostRecommendationDecisionsPayload(nowIso, postRecDecisions, "fiscal/slo-alerts", buildPostRecScorecardDigest())
    );
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_SLO_PACKAGE_${ts}.zip`, {
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_SLO_SCORECARD_${ts}.json`]: strToU8(JSON.stringify(signedScorecard, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_SLO_RAW_${ts}.json`]: strToU8(JSON.stringify(signedRaw, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_P0_2_POST_REC_DECISIONS_${ts}.json`]: strToU8(JSON.stringify(signedPostRec, null, 2)),
    });
    setStatus("Pacote SLO exportado (scorecard + raw + decisões P0-2).");
    window.setTimeout(() => setStatus(""), 2200);
  }

  const maxLatency = Math.max(...filteredProviders.map((row) => Number(row?.last_latency_ms || 0)), 1);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal/department-dashboards" style={shortcutLinkStyle}>Abrir fiscal/department-dashboards</Link>
          <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>Abrir fiscal/sprint3-partner-audit (P0-1)</Link>
          <Link to="/fiscal/sprint4-regression-matrix" style={shortcutLinkStyle}>Abrir fiscal/sprint4-regression-matrix (Sprint 4)</Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>Abrir ops/health</Link>
          <Link to="/fiscal/incident-response" style={shortcutLinkStyle}>Abrir fiscal/incident-response (P0-3)</Link>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>Abrir Swagger FISCAL</a>
        </div>
        <OpsPageTitleHeader title="FISCAL - Sprint 3 SLO Scorecard" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Sprint 3 (P0-2): scorecard SLO v3 + limiares BR/PT explícitos no export + recomendações automáticas + registo local de decisões pós-recomendação (JSON/ZIP; meta **3 decisões reais** BR/PT no daily via ZIP ou ficheiro `SPRINT3_P0_2_POST_REC_DECISIONS_*`).
        </p>

        <section style={{ ...cardStyle, marginTop: 12, padding: 12 }}>
          <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>Sprint 4 — KPI mínimo de saída (baseline)</h3>
          <p style={{ ...mutedTextStyle, marginTop: 0 }}>
            Versão <code>{SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION}</code>. Produção mínima:{" "}
            <code>{FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG.version}</code> — env{" "}
            <code>VITE_BILLING_FISCAL_BASE_URL</code> + <code>VITE_INTERNAL_TOKEN</code>; UI padrão{" "}
            <code>{JSON.stringify(FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG.ui_defaults)}</code>.
          </p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc", padding: 6 }}>Persona</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc", padding: 6 }}>KPI</th>
                  <th style={{ textAlign: "right", borderBottom: "1px solid #ccc", padding: 6 }}>Baseline v1</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc", padding: 6 }}>Fonte</th>
                </tr>
              </thead>
              <tbody>
                {SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA.map((row) => (
                  <tr key={row.persona + row.kpi}>
                    <td style={{ padding: 6, borderBottom: "1px solid #eee" }}>{row.persona}</td>
                    <td style={{ padding: 6, borderBottom: "1px solid #eee" }}>{row.kpi}</td>
                    <td style={{ padding: 6, borderBottom: "1px solid #eee", textAlign: "right" }}>
                      {row.value} {row.unit}
                    </td>
                    <td style={{ padding: 6, borderBottom: "1px solid #eee", color: "var(--fiscal-muted, #666)" }}>{row.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ ...mutedTextStyle, marginBottom: 4 }}>Coleta métricas (shell — mesmo contrato que esta página):</p>
          <pre
            style={{
              margin: 0,
              padding: 8,
              fontSize: 11,
              background: "var(--fiscal-surface-2, #f6f6f6)",
              borderRadius: 6,
              overflowX: "auto",
            }}
          >
            {SPRINT4_SLO_METRICS_COLLECT_COMMANDS.join("\n")}
          </pre>
        </section>

        <div style={filtersRowStyle}>
          <label style={labelStyle}>País
            <select value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="BR">BR</option>
              <option value="PT">PT</option>
            </select>
          </label>
          <label style={labelStyle}>Parceiro
            <select value={partnerFilter} onChange={(e) => setPartnerFilter(e.target.value)} style={inputStyle}>
              {partnerOptions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label style={labelStyle}>Período
            <select
              value={periodFilter}
              onChange={(e) => {
                const next = e.target.value;
                setPeriodFilter(next);
                void loadData(next);
              }}
              style={inputStyle}
            >
              <option value="24H">24H</option>
              <option value="7D">7D</option>
              <option value="30D">30D</option>
            </select>
          </label>
          <label style={labelStyle}>Calibragem
            <select value={calibrationProfile} onChange={(e) => setCalibrationProfile(e.target.value)} style={inputStyle}>
              <option value="AUTO">AUTO (derivar por país)</option>
              <option value="GLOBAL">GLOBAL baseline</option>
              <option value="BR">BR (sensível)</option>
              <option value="PT">PT (moderado)</option>
            </select>
          </label>
        </div>

        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadData()} style={buttonStyle} disabled={loading}>{loading ? "Atualizando..." : "Atualizar"}</button>
          <button type="button" onClick={() => void exportJson()} style={buttonStyle} disabled={loading}>Exportar JSON</button>
          <button type="button" onClick={() => void exportZip()} style={buttonStyle} disabled={loading}>Exportar ZIP auditável</button>
          <button type="button" onClick={() => void exportPostRecDecisionsJson()} style={buttonStyle} disabled={loading}>
            Exportar decisões P0-2 (.json)
          </button>
          <button type="button" onClick={() => void exportUniqueHandoffEvidence()} style={buttonStyle} disabled={loading}>Exportar evidência única P0-1</button>
        </div>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error ? (
          <>
            <div style={gridStyle}>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Scorecard OPS/Fiscal — readiness</h3>
                <div style={kpiRowStyle}>
                  <span style={chipStyle}>Índice 0–100: {sloReadinessScore}</span>
                  <span style={chipStyle}>Países no agregado: {countryScorecardAll.length}</span>
                </div>
                <small style={mutedTextStyle}>
                  Incluído no JSON/ZIP como <code>scorecard_rollups</code> e anexado às decisões P0-2 como{" "}
                  <code>attached_scorecard_digest</code>.
                </small>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Alertas ativos</h3>
                <div style={kpiRowStyle}>
                  <span style={severityBadgeStyle(sloSeverity)}>Severidade: {sloSeverity}</span>
                  <span style={chipStyle}>Erro fiscal: {(errorRate * 100).toFixed(1)}%</span>
                  <span style={chipStyle}>Latência p95: {Math.round(latencyP95)} ms</span>
                  <span style={chipStyle}>Aprovação sem update: {hoursSinceLatestApproval.toFixed(1)}h</span>
                </div>
                <small style={mutedTextStyle}>
                  Thresholds ({SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION}, janela {periodFilter}, perfil {effectiveCalibrationProfile}): erro `{(activeThresholds.errorRate.medium * 100).toFixed(0)}%`/`{(activeThresholds.errorRate.critical * 100).toFixed(0)}%`, latência `{activeThresholds.latencyP95Ms.medium}`/`{activeThresholds.latencyP95Ms.high}` ms, tratativa `{activeThresholds.hoursSinceLatestApproval.high}`h.
                </small>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Divergência e tratativa</h3>
                <div style={kpiRowStyle}>
                  <span style={chipStyle}>Divergência prolongada: {prolongedDiff ? "SIM" : "NÃO"}</span>
                  <span style={chipStyle}>Edges repetidas: {prolongedEdges}</span>
                  <span style={chipStyle}>Último update: {hoursSinceLatestApproval.toFixed(1)}h</span>
                </div>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Auditoria ponta a ponta (P0-1)</h3>
                <div style={kpiRowStyle}>
                  <span style={severityBadgeStyle(String(auditTrail?.decision || "NO_GO"))}>Decisão: {String(auditTrail?.decision || "NO_GO")}</span>
                  <span style={chipStyle}>Trilha 4 chaves: {auditMaterializedPass}/{auditMaterializedTotal}</span>
                  <span style={chipStyle}>Cobertura: {(auditMaterializedRate * 100).toFixed(1)}%</span>
                </div>
                <small style={mutedTextStyle}>Evidência: {String(auditTrail?.handoff_evidence?.evidence_id || "-")}</small>
              </section>
            </div>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>SLO por país (todos os providers carregados)</h3>
              {countryScorecardAll.length === 0 ? (
                <small style={mutedTextStyle}>Sem linhas de provider para agregar.</small>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr>
                      <th style={thStyle}>País</th>
                      <th style={thStyle}>Linhas</th>
                      <th style={thStyle}>Erros</th>
                      <th style={thStyle}>Taxa erro</th>
                      <th style={thStyle}>Latência p95 (ms)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {countryScorecardAll.map((r) => (
                      <tr key={r.country}>
                        <td style={tdStyle}>{r.country}</td>
                        <td style={tdStyle}>{r.rows}</td>
                        <td style={tdStyle}>{r.errors}</td>
                        <td style={tdStyle}>{(r.error_rate * 100).toFixed(1)}%</td>
                        <td style={tdStyle}>{Math.round(r.latency_p95_ms)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Playbook de calibragem (P0-2b)</h3>
              <div style={kpiRowStyle}>
                <span style={severityBadgeStyle(CALIBRATION_STRATEGY_SEVERITY[calibrationPlaybook.strategy] || "LOW")}>
                  Estratégia: {calibrationPlaybook.strategy}
                </span>
                <span style={chipStyle}>Perfil aplicado: {effectiveCalibrationProfile}</span>
              </div>
              <small style={mutedTextStyle}>{calibrationPlaybook.rationale}</small>
              <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "var(--fiscal-text)" }}>
                {calibrationPlaybook.next_actions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Recomendações automáticas de ajuste (thresholds)</h3>
              {adjustmentRecommendations.length === 0 ? (
                <small style={mutedTextStyle}>
                  Sem recomendações automáticas no snapshot atual (ou dados insuficientes para inferir ruído recorrente).
                </small>
              ) : (
                <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "var(--fiscal-text)" }}>
                  {adjustmentRecommendations.map((item) => (
                    <li key={item.id} style={{ marginBottom: 8 }}>
                      <div style={{ fontWeight: 800 }}>{item.recommendation}</div>
                      <small style={mutedTextStyle}>
                        Evidência: {JSON.stringify(item.evidence)}
                      </small>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>P0-2 — Registo de decisões pós-recomendação (meta: 3 no sprint)</h3>
              <div style={kpiRowStyle}>
                <span style={chipStyle}>
                  Registadas: {postRecDecisions.length}
                  {postRecDecisions.length >= 3 ? " (meta ≥3 atingida)" : " (meta sprint: 3)"}
                </span>
              </div>
              <small style={mutedTextStyle}>
                Após alinhar com operação (ex. BR/PT), registe a decisão face à recomendação; entra no JSON/ZIP do scorecard e no ficheiro dedicado{" "}
                <code>SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS</code>.
              </small>
              <div style={{ ...filtersRowStyle, marginTop: 12 }}>
                <label style={labelStyle}>
                  Recomendação
                  <select
                    value={postRecSelectedRecId}
                    onChange={(e) => setPostRecSelectedRecId(e.target.value)}
                    style={inputStyle}
                  >
                    <option value="">— Escolher —</option>
                    <option value="__manual__">Outra (sem ID da lista atual)</option>
                    {adjustmentRecommendations.map((item) => (
                      <option key={item.id} value={item.id}>
                        {String(item.id).slice(0, 48)}
                      </option>
                    ))}
                  </select>
                </label>
                <label style={labelStyle}>
                  Decisão operacional
                  <select
                    value={postRecOperatorDecision}
                    onChange={(e) => setPostRecOperatorDecision(e.target.value)}
                    style={inputStyle}
                  >
                    {POST_REC_DECISION_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label style={{ ...labelStyle, marginTop: 10 }}>
                Notas (ticket, turno, acordo com N2, etc.)
                <textarea
                  value={postRecOperatorNotes}
                  onChange={(e) => setPostRecOperatorNotes(e.target.value)}
                  rows={3}
                  style={{ ...inputStyle, minHeight: 72, resize: "vertical" }}
                  placeholder="Obrigatório para evidência; use “Outra…” se a recomendação não estiver na lista."
                />
              </label>
              <div style={{ ...toolbarStyle, marginTop: 10 }}>
                <button type="button" style={buttonStyle} onClick={() => registerPostRecommendationDecision()}>
                  Registar decisão
                </button>
                <button type="button" style={buttonStyle} onClick={() => clearPostRecommendationDecisions()}>
                  Limpar histórico local
                </button>
              </div>
              {postRecDecisions.length ? (
                <ul style={{ margin: "12px 0 0", paddingLeft: 18, color: "var(--fiscal-text)", fontSize: 13 }}>
                  {[...postRecDecisions].reverse().slice(0, 8).map((d) => (
                    <li key={d.id} style={{ marginBottom: 6 }}>
                      <strong>{d.recorded_at}</strong> — {d.operator_decision}
                      {d.recommendation_id ? ` · rec: ${d.recommendation_id}` : " · rec: (manual)"}
                      {d.operator_notes ? <div style={mutedTextStyle}>{d.operator_notes}</div> : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <small style={{ ...mutedTextStyle, display: "block", marginTop: 10 }}>Ainda sem registos neste browser.</small>
              )}
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Latência operacional por parceiro</h3>
              <div style={{ display: "grid", gap: 8 }}>
                {filteredProviders.map((row, idx) => {
                  const latency = Number(row?.last_latency_ms || 0);
                  const pct = Math.max(Math.min((latency / maxLatency) * 100, 100), 0);
                  return (
                    <article key={`lat-${idx}`} style={barRowStyle}>
                      <strong style={{ width: 120 }}>{String(row?.country || "-")} / {String(row?.provider_name || "-")}</strong>
                      <div style={barTrackStyle}><div style={{ ...barFillStyle, width: `${pct}%` }} /></div>
                      <small style={{ minWidth: 60, textAlign: "right" }}>{latency} ms</small>
                    </article>
                  );
                })}
                {filteredProviders.length === 0 ? <small style={mutedTextStyle}>Sem dados para os filtros atuais.</small> : null}
              </div>
            </section>
          </>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10 };
const shortcutLinkStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", textDecoration: "none", fontWeight: 700, fontSize: 13 };
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const filtersRowStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginTop: 10 };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, fontWeight: 700, color: "var(--fiscal-soft-text)" };
const inputStyle = { borderRadius: 8, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", padding: "8px 10px", fontSize: 13 };
const toolbarStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const buttonStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", cursor: "pointer", fontWeight: 700 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const gridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" };
const boxStyle = { marginTop: 10, border: "1px solid var(--fiscal-box-border)", borderRadius: 12, background: "var(--fiscal-box-bg)", padding: 12 };
const boxTitleStyle = { margin: "0 0 8px", fontSize: 14 };
const kpiRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const chipStyle = { display: "inline-flex", padding: "4px 10px", borderRadius: 999, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", fontSize: 12, fontWeight: 700 };
const severityBadgeStyle = (severity) => {
  const s = String(severity || "").toUpperCase();
  if (s === "NO_GO") return { ...chipStyle, background: "rgba(239,68,68,0.18)", border: "1px solid rgba(239,68,68,0.65)", color: "#fecaca" };
  if (s === "GO") return { ...chipStyle, background: "rgba(34,197,94,0.18)", border: "1px solid rgba(34,197,94,0.65)", color: "#bbf7d0" };
  if (s === "CRITICAL") return { ...chipStyle, background: "rgba(239,68,68,0.18)", border: "1px solid rgba(239,68,68,0.65)", color: "#fecaca" };
  if (s === "HIGH") return { ...chipStyle, background: "rgba(245,158,11,0.2)", border: "1px solid rgba(245,158,11,0.65)", color: "#fde68a" };
  if (s === "MEDIUM") return { ...chipStyle, background: "rgba(59,130,246,0.18)", border: "1px solid rgba(59,130,246,0.65)", color: "#bfdbfe" };
  return { ...chipStyle, background: "rgba(34,197,94,0.18)", border: "1px solid rgba(34,197,94,0.65)", color: "#bbf7d0" };
};
const barRowStyle = { display: "flex", gap: 8, alignItems: "center" };
const barTrackStyle = { flex: 1, height: 10, borderRadius: 999, background: "rgba(148,163,184,0.25)", overflow: "hidden" };
const barFillStyle = { height: "100%", borderRadius: 999, background: "linear-gradient(90deg, rgba(59,130,246,0.85), rgba(239,68,68,0.85))" };
const thStyle = { textAlign: "left", padding: "6px 8px", borderBottom: "1px solid var(--fiscal-link-border)", color: "var(--fiscal-soft-text)" };
const tdStyle = { padding: "6px 8px", borderBottom: "1px solid rgba(148,163,184,0.25)" };

