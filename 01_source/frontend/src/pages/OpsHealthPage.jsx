import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import { getDataQualityFlagStyle, getSeverityBadgeStyle, getConfidenceBadgeStyle } from "../components/opsVisualTokens";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { withScopePrefixIfGenericSummary } from "../utils/fiscalScopeSummary";
import { FISCAL_SCOPE_GATE_PANEL_TITLE, FISCAL_SCOPE_QUICK_ACTIONS_TITLE } from "../constants/fiscalScope";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const BILLING_BASE =
  import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN =
  import.meta.env.VITE_INTERNAL_TOKEN || "";
const OPS_HEALTH_WINDOW_PREF_KEY = "ops_health:window_hours";
const OPS_HEALTH_PERSONA_PREF_KEY = "ops_health:persona";
const OPS_HEALTH_COLLAPSE_PREF_KEY = "ops_health:collapse_state:v1";
const OPS_HEALTH_LINE_CHART_GRID_MODE_PREF_KEY = "ops_health:line_chart_grid_mode:v1";
const OPS_HEALTH_WINDOW_PRESETS = [1, 6, 12, 24, 48, 72, 168];
const OPS_HEALTH_PAGE_VERSION = "ops/health v1.4.5-sprint5";
const OPS_HEALTH_PERSONAS = [
  { value: "ops", label: "Ops" },
  { value: "dev", label: "Dev" },
  { value: "gestao", label: "Gestão" },
];
const PREDICTIVE_THRESHOLD_PROFILES = {
  dev: {
    predictiveMinVolume: 20,
    predictiveErrorMinRate: 0.12,
    predictiveErrorAccelFactor: 1.8,
    predictiveLatencyMinMs: 220,
    predictiveLatencyAccelFactor: 1.7,
  },
  hml: {
    predictiveMinVolume: 12,
    predictiveErrorMinRate: 0.08,
    predictiveErrorAccelFactor: 1.6,
    predictiveLatencyMinMs: 160,
    predictiveLatencyAccelFactor: 1.5,
  },
  prod: {
    predictiveMinVolume: 8,
    predictiveErrorMinRate: 0.05,
    predictiveErrorAccelFactor: 1.4,
    predictiveLatencyMinMs: 120,
    predictiveLatencyAccelFactor: 1.35,
  },
};
const OPS_SEVERITY_SLA_MATRIX = [
  {
    severityKey: "CRITICAL",
    severityLabel: "CRITICO",
    responseSla: "Ate 5 min",
    channel: "Pager + #ops-critical + incidente formal",
    owner: "Plantao SRE",
  },
  {
    severityKey: "HIGH",
    severityLabel: "ALTO",
    responseSla: "Ate 15 min",
    channel: "#ops-alerts + owner de dominio",
    owner: "Ops + Engenharia",
  },
  {
    severityKey: "MEDIUM",
    severityLabel: "MEDIO",
    responseSla: "Ate 60 min",
    channel: "#ops-alerts (fila priorizada)",
    owner: "Ops",
  },
  {
    severityKey: "LOW",
    severityLabel: "BAIXO",
    responseSla: "Ate 4h",
    channel: "Backlog operacional + revisao diaria",
    owner: "Ops/Produto",
  },
];

function extractErrorMessage(payload, fallback = "Não foi possível carregar métricas operacionais.") {
  if (!payload) return fallback;
  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim();
  }
  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message.trim();
  }
  return fallback;
}

function toPercent(value) {
  return Number(value || 0) * 100;
}

function formatPercent(value) {
  return `${toPercent(value).toFixed(1)}%`;
}

function formatDeltaPercentagePoints(currentRate, previousRate) {
  const delta = toPercent(currentRate) - toPercent(previousRate);
  const signal = delta >= 0 ? "+" : "";
  return `${signal}${delta.toFixed(1)} p.p.`;
}

function resolveErrorRateTrend(currentRate, previousRate) {
  const delta = Number(currentRate || 0) - Number(previousRate || 0);
  if (delta > 0) return "down";
  if (delta < 0) return "up";
  return "stable";
}

function resolveLatencyTrend(currentP95, previousP95) {
  const current = Number(currentP95 || 0);
  const previous = Number(previousP95 || 0);
  if (current < previous) return "up";
  if (current > previous) return "down";
  return "stable";
}

function formatLatencySampleQuality(sampleCount) {
  const samples = Number(sampleCount || 0);
  if (samples >= 50) return `Qualidade da amostra: alta (${samples})`;
  if (samples >= 15) return `Qualidade da amostra: média (${samples})`;
  if (samples > 0) return `Qualidade da amostra: baixa (${samples})`;
  return "Qualidade da amostra: sem dados (0)";
}

function getCriticalityCardStyle(baseStyle, criticality) {
  if (criticality === "critical") {
    return {
      ...baseStyle,
      border: "1px solid rgba(248,113,113,0.9)",
      background: "linear-gradient(180deg, rgba(127,29,29,0.48) 0%, rgba(127,29,29,0.22) 100%)",
      boxShadow: "0 0 0 1px rgba(248,113,113,0.18), 0 10px 24px rgba(127,29,29,0.28)",
    };
  }
  if (criticality === "high") {
    return {
      ...baseStyle,
      border: "1px solid rgba(250,204,21,0.72)",
      background: "linear-gradient(180deg, rgba(120,53,15,0.36) 0%, rgba(120,53,15,0.16) 100%)",
    };
  }
  return baseStyle;
}

function formatPendingAgeBuckets(kpis) {
  const b0_1 = Number(kpis?.pending_age_0_1h || 0);
  const b1_4 = Number(kpis?.pending_age_1_4h || 0);
  const b4_24 = Number(kpis?.pending_age_4_24h || 0);
  const b24 = Number(kpis?.pending_age_24h_plus || 0);
  return `0-1h:${b0_1} | 1-4h:${b1_4} | 4-24h:${b4_24} | >24h:${b24}`;
}

function resolveSeverityFromRate(errorRate) {
  const rate = Number(errorRate || 0);
  if (rate > 0.5) return "CRITICAL";
  if (rate >= 0.2) return "HIGH";
  if (rate >= 0.05) return "MEDIUM";
  return "LOW";
}

function severityEmoji(severity) {
  const normalized = String(severity || "").toUpperCase();
  if (normalized === "CRITICAL") return "🔴";
  if (normalized === "HIGH" || normalized === "ERROR") return "🟠";
  if (normalized === "MEDIUM" || normalized === "WARN") return "🟡";
  return "🟢";
}

function resolveOpsSanitySemaphore(report) {
  const result = String(report?.result || "").toUpperCase();
  const failCount = Number(report?.fail_count || 0);
  if (result === "OPS_SANITY_OK" && failCount === 0) {
    return {
      label: "Verde",
      reason: "Plantão estável: sanidade OPS OK sem falhas.",
      style: {
        border: "1px solid rgba(34,197,94,0.65)",
        background: "rgba(34,197,94,0.2)",
        color: "#bbf7d0",
      },
    };
  }
  if (result === "OPS_SANITY_FAIL" && failCount > 0 && failCount <= 2) {
    return {
      label: "Amarelo",
      reason: `Plantão em atenção: ${failCount} falha(s) parcial(is) com possível degradação localizada.`,
      style: {
        border: "1px solid rgba(245,158,11,0.65)",
        background: "rgba(245,158,11,0.2)",
        color: "#fde68a",
      },
    };
  }
  return {
    label: "Vermelho",
    reason:
      failCount > 0
        ? `Plantão crítico: ${failCount} falha(s) no checklist de sanidade.`
        : "Plantão crítico: sanidade sem resultado válido.",
    style: {
      border: "1px solid rgba(239,68,68,0.65)",
      background: "rgba(239,68,68,0.22)",
      color: "#fecaca",
    },
  };
}

function resolveGateBadgeStyle(decision) {
  const normalized = String(decision || "").toUpperCase();
  if (normalized === "GO") {
    return {
      border: "1px solid rgba(34,197,94,0.65)",
      background: "rgba(34,197,94,0.2)",
      color: "#bbf7d0",
    };
  }
  return {
    border: "1px solid rgba(239,68,68,0.65)",
    background: "rgba(239,68,68,0.22)",
    color: "#fecaca",
  };
}

function getCheckStats(report) {
  const checks = Array.isArray(report?.checks) ? report.checks : [];
  const failed = checks.filter((check) => Number(check?.exit_code || 1) !== 0).length;
  const passed = Math.max(checks.length - failed, 0);
  return {
    checks,
    failed,
    passed,
    total: checks.length,
  };
}

function getSeveritySurfaceStyle(severity) {
  const badge = getSeverityBadgeStyle(severity);
  return {
    border: badge.border,
    background: `${badge.background}CC`,
  };
}

function loadCollapsedStatePreference() {
  try {
    const raw = window.localStorage.getItem(OPS_HEALTH_COLLAPSE_PREF_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function loadLineChartGridModePreference() {
  try {
    const raw = window.localStorage.getItem(OPS_HEALTH_LINE_CHART_GRID_MODE_PREF_KEY);
    if (raw === "simple" || raw === "full") return raw;
  } catch {
    // no-op
  }
  return "full";
}

function appendWindowParamsToPath(path, metrics, lookbackHours) {
  const [basePath, queryString = ""] = String(path || "").split("?");
  const params = new URLSearchParams(queryString);
  const from = String(metrics?.window?.from || "").trim();
  const to = String(metrics?.window?.to || "").trim();
  const lookback = Math.max(Number(lookbackHours || metrics?.window?.lookback_hours || 24), 1);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  params.set("lookback_hours", String(lookback));
  const encoded = params.toString();
  return encoded ? `${basePath}?${encoded}` : basePath;
}

function resolveAlertInvestigateLink(alert, metrics, lookbackHours) {
  const raw = String(alert?.investigate_url || "").trim();
  if (raw.startsWith("/")) return appendWindowParamsToPath(raw, metrics, lookbackHours);
  if (String(alert?.code || "").toUpperCase().includes("PENDING")) {
    return appendWindowParamsToPath("/ops/reconciliation", metrics, lookbackHours);
  }
  return appendWindowParamsToPath("/ops/audit?action=OPS_METRICS_VIEW&limit=50", metrics, lookbackHours);
}

function getRunbookByAlertCode(code) {
  const normalized = String(code || "").toUpperCase().trim();
  const runbooks = {
    OPS_ERROR_RATE_HIGH: {
      title: "Runbook: Taxa de erro operacional alta",
      owner: "SRE + Backend",
      steps: [
        "Validar volume total e percentual de erro na janela atual e anterior.",
        "Abrir OPS Audit filtrando ERROR e identificar top 3 causas por mensagem.",
        "Usar classificação assistida por tipo (timeout/validacao/integracao/infra) para priorizar mitigação.",
        "Checar timeout/rede/integracao com lockers e saúde dos workers.",
        "Aplicar mitigação rápida (retry com backoff / reduzir carga / rollback controlado).",
        "Registrar incidente com impacto e plano de correção definitiva.",
      ],
    },
    PENDING_BACKLOG_HIGH: {
      title: "Runbook: Backlog de pendências alto",
      owner: "Ops + Plataforma",
      steps: [
        "Abrir reconciliação pendente e segmentar por idade e status.",
        "Executar processamento manual em lote para reduzir fila crítica.",
        "Priorizar itens mais antigos e com maior impacto de cliente.",
        "Identificar gargalo de origem (worker, lock, integração, validação).",
        "Ajustar capacidade/threshold e acompanhar queda do backlog.",
      ],
    },
    PENDING_FAILED_FINAL: {
      title: "Runbook: Pendências em FAILED_FINAL",
      owner: "Ops + Engenharia",
      steps: [
        "Listar todos os itens FAILED_FINAL e categorizar motivo dominante.",
        "Executar reconciliação manual para itens recuperáveis.",
        "Escalar para engenharia os casos não recuperáveis com evidência.",
        "Aplicar correção na causa raiz e acompanhar reincidência.",
        "Atualizar documentação operacional com o novo aprendizado.",
      ],
    },
    PENDING_PROCESSING_STALE: {
      title: "Runbook: Pendências travadas em PROCESSING",
      owner: "Plataforma + SRE",
      steps: [
        "Verificar workers/jobs ativos e filas de processamento.",
        "Identificar lock/concorrência ou timeout em chamadas externas.",
        "Destravar itens estagnados e reprocessar lote afetado.",
        "Confirmar normalização da fila e da latência de processamento.",
        "Registrar ação corretiva preventiva para evitar novo travamento.",
      ],
    },
  };
  return (
    runbooks[normalized] || {
      title: `Runbook: ${normalized || "ALERTA_OPERACIONAL"}`,
      owner: "Ops",
      steps: [
        "Validar impacto real na janela atual.",
        "Investigar logs e trilha de auditoria relacionados ao alerta.",
        "Executar mitigação segura para reduzir risco imediato.",
        "Escalar para o time responsável se persistir após mitigação.",
        "Documentar causa e ação tomada no registro de incidente.",
      ],
    }
  );
}

function toBrDateTime(value) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("pt-BR");
}

function buildRunbookClipboardText(alert, metrics) {
  const code = String(alert?.code || "");
  const runbook = getRunbookByAlertCode(code);
  const investigateUrl = resolveAlertInvestigateLink(alert, metrics, metrics?.window?.lookback_hours);
  const windowFrom = metrics?.window?.from;
  const windowTo = metrics?.window?.to;
  const severity = String(alert?.severity || "INFO").toUpperCase();
  const value = alert?.value ?? "-";
  const threshold = alert?.threshold ?? "-";
  const source = "ELLAN LAB > Contexto Ops > OPS - Saúde Operacional";
  const generatedAt = new Date().toLocaleString("pt-BR");
  const alertCode = code || "ALERTA_OPERACIONAL";
  const alertMessage = alert?.message || "Alerta operacional detectado.";
  const impact = alert?.impact || "Impacto ainda não detalhado.";
  const mitigationHint = alert?.mitigation_hint || "Executar mitigação operacional padrão.";
  const investigateHint = alert?.investigate_hint || "Investigar trilha de auditoria relacionada.";
  const topCategory = Array.isArray(metrics?.error_classification?.categories)
    ? metrics.error_classification.categories[0]
    : null;

  const nextSteps = runbook.steps.map((step, idx) => `${idx + 1}. ${step}`).join("\n");
  return [
    "## Título",
    `[${severity}] ${alertCode} - ${alertMessage}`,
    "",
    "## Impacto",
    `${impact}`,
    "",
    "## Evidências",
    `- Origem: ${source}`,
    `- Gerado em: ${generatedAt}`,
    `- Alerta: [${severity}] ${alertCode}`,
    `- Valor / Threshold: ${value} / ${threshold}`,
    `- Janela analisada: ${toBrDateTime(windowFrom)} até ${toBrDateTime(windowTo)}`,
    `- Onde investigar: ${investigateUrl}`,
    `- Dica de investigação: ${investigateHint}`,
    `- Classificação dominante: ${topCategory ? `${topCategory.category} (${Number(topCategory.percentage || 0).toFixed(1)}%)` : "-"}`,
    "",
    "## Mitigação",
    `${mitigationHint}`,
    "",
    "## Próximos passos",
    nextSteps,
    "",
    "## Owner sugerido",
    runbook.owner,
  ].join("\n");
}

function buildRunbookPlainClipboardText(alert, metrics) {
  const code = String(alert?.code || "");
  const runbook = getRunbookByAlertCode(code);
  const investigateUrl = resolveAlertInvestigateLink(alert, metrics, metrics?.window?.lookback_hours);
  const windowFrom = metrics?.window?.from;
  const windowTo = metrics?.window?.to;
  const severity = String(alert?.severity || "INFO").toUpperCase();
  const value = alert?.value ?? "-";
  const threshold = alert?.threshold ?? "-";
  const source = "ELLAN LAB > Contexto Ops > OPS - Saúde Operacional";
  const generatedAt = new Date().toLocaleString("pt-BR");
  const alertCode = code || "ALERTA_OPERACIONAL";
  const alertMessage = alert?.message || "Alerta operacional detectado.";
  const impact = alert?.impact || "Impacto ainda não detalhado.";
  const mitigationHint = alert?.mitigation_hint || "Executar mitigação operacional padrão.";
  const investigateHint = alert?.investigate_hint || "Investigar trilha de auditoria relacionada.";
  const topCategory = Array.isArray(metrics?.error_classification?.categories)
    ? metrics.error_classification.categories[0]
    : null;
  const nextSteps = runbook.steps.map((step, idx) => `${idx + 1}. ${step}`).join("\n");

  return [
    "TITULO",
    `[${severity}] ${alertCode} - ${alertMessage}`,
    "",
    "IMPACTO",
    impact,
    "",
    "EVIDENCIAS",
    `- Origem: ${source}`,
    `- Gerado em: ${generatedAt}`,
    `- Alerta: [${severity}] ${alertCode}`,
    `- Valor / Threshold: ${value} / ${threshold}`,
    `- Janela analisada: ${toBrDateTime(windowFrom)} até ${toBrDateTime(windowTo)}`,
    `- Onde investigar: ${investigateUrl}`,
    `- Dica de investigação: ${investigateHint}`,
    `- Classificação dominante: ${topCategory ? `${topCategory.category} (${Number(topCategory.percentage || 0).toFixed(1)}%)` : "-"}`,
    "",
    "MITIGACAO",
    mitigationHint,
    "",
    "PROXIMOS PASSOS",
    nextSteps,
    "",
    "OWNER SUGERIDO",
    runbook.owner,
  ].join("\n");
}

function buildDrilldownLinks(metrics, lookbackHours) {
  const params = new URLSearchParams();
  const from = String(metrics?.window?.from || "").trim();
  const to = String(metrics?.window?.to || "").trim();
  const lookback = Math.max(Number(lookbackHours || metrics?.window?.lookback_hours || 24), 1);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  params.set("lookback_hours", String(lookback));

  const auditErrorsParams = new URLSearchParams(params);
  auditErrorsParams.set("result", "ERROR");
  auditErrorsParams.set("limit", "100");

  const reconParams = new URLSearchParams(params);

  const evidenceParams = new URLSearchParams(params);
  evidenceParams.set("action", "OPS_RECON_PENDING_RUN_ONCE");
  evidenceParams.set("limit", "100");

  return {
    auditErrors: `/ops/audit?${auditErrorsParams.toString()}`,
    reconciliation: `/ops/reconciliation?${reconParams.toString()}`,
    evidence: `/ops/audit?${evidenceParams.toString()}`,
  };
}

function buildSparklinePath(values, width, height, padding = 4) {
  if (!Array.isArray(values) || values.length === 0) return "";
  const validValues = values.map((v) => Number(v || 0));
  const min = Math.min(...validValues);
  const max = Math.max(...validValues);
  const range = max - min || 1;
  return validValues
    .map((value, index) => {
      const x = padding + (index * (width - padding * 2)) / Math.max(validValues.length - 1, 1);
      const y = height - padding - ((value - min) / range) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function OpsSparkline({ values, stroke = "#93C5FD" }) {
  const width = 220;
  const height = 52;
  const path = buildSparklinePath(values, width, height);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Sparkline">
      <rect x="0" y="0" width={width} height={height} rx="8" fill="rgba(15,23,42,0.45)" />
      {path ? <path d={path} fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" /> : null}
    </svg>
  );
}

function OpsLineChart({ title, points, valueKey, stroke = "#93C5FD", formatter = (v) => String(v), showDetailedGrid = true }) {
  const width = 460;
  const height = 160;
  const padding = 20;
  const chartLeft = 44;
  const chartRight = width - 16;
  const chartTop = 14;
  const chartBottom = height - 28;
  const chartWidth = chartRight - chartLeft;
  const chartHeight = chartBottom - chartTop;
  const values = (Array.isArray(points) ? points : []).map((point) => Number(point?.[valueKey] || 0));
  const labels = (Array.isArray(points) ? points : []).map((point) => String(point?.bucket_start || ""));
  const noData = values.length === 0;
  const allZero = values.length > 0 && values.every((value) => value === 0);
  const minValue = values.length > 0 ? Math.min(...values) : 0;
  const maxValue = values.length > 0 ? Math.max(...values) : 0;
  const range = maxValue - minValue || 1;
  const path = values
    .map((value, index) => {
      const x = chartLeft + (index * chartWidth) / Math.max(values.length - 1, 1);
      const y = chartBottom - ((value - minValue) / range) * chartHeight;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  const yTicks = [maxValue, minValue + range / 2, minValue];
  const xTickIndexes = [0, Math.floor(Math.max(labels.length - 1, 0) / 2), Math.max(labels.length - 1, 0)];
  const latest = values.length ? values[values.length - 1] : 0;
  const first = values.length ? values[0] : 0;
  const delta = latest - first;
  return (
    <article style={lineChartCardStyle}>
      <small style={trendLabelStyle}>{title}</small>
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Linha temporal 24h - ${title || "métrica"}`}
        preserveAspectRatio="none"
      >
        <rect x="0" y="0" width={width} height={height} rx="10" fill="rgba(30,41,59,0.40)" />
        {!noData && showDetailedGrid ? (
          <>
            {yTicks.map((tickValue, idx) => {
              const y = chartBottom - ((tickValue - minValue) / range) * chartHeight;
              return (
                <g key={`y-tick-${idx}`}>
                  <line x1={chartLeft} y1={y} x2={chartRight} y2={y} stroke="rgba(148,163,184,0.20)" strokeDasharray="3 3" />
                  <text x={chartLeft - 6} y={y + 4} textAnchor="end" fill="rgba(203,213,225,0.95)" fontSize="10">
                    {formatter(tickValue)}
                  </text>
                </g>
              );
            })}
            {xTickIndexes
              .filter((idx, pos, arr) => arr.indexOf(idx) === pos)
              .map((idx) => {
                const x = chartLeft + (idx * chartWidth) / Math.max(values.length - 1, 1);
                const raw = labels[idx] ? new Date(labels[idx]) : null;
                const label = raw && !Number.isNaN(raw.getTime())
                  ? raw.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
                  : "-";
                return (
                  <g key={`x-tick-${idx}`}>
                    <line x1={x} y1={chartTop} x2={x} y2={chartBottom} stroke="rgba(148,163,184,0.15)" />
                    <text x={x} y={height - 8} textAnchor="middle" fill="rgba(203,213,225,0.95)" fontSize="10">
                      {label}
                    </text>
                  </g>
                );
              })}
          </>
        ) : null}
        {path ? <path d={path} fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" /> : null}
        {(noData || allZero) ? <line x1={chartLeft} y1={height / 2} x2={chartRight} y2={height / 2} stroke="rgba(148,163,184,0.55)" strokeDasharray="6 4" /> : null}
        {(noData || allZero) ? (
          <text x={width / 2} y={height / 2 - 8} textAnchor="middle" fill="rgba(191,219,254,0.96)" fontSize="12" fontWeight="700">
            Sem variação relevante em 24h
          </text>
        ) : null}
      </svg>
      <div style={lineChartMetaStyle}>
        <small style={lineChartValueStyle}>Atual: {formatter(latest)}</small>
        <small style={lineChartValueStyle}>Delta 24h: {formatter(delta)}</small>
      </div>
      <div style={lineChartLabelsStyle}>
        <small>{labels[0] ? new Date(labels[0]).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "-"}</small>
        <small>
          {labels[labels.length - 1]
            ? new Date(labels[labels.length - 1]).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
            : "-"}
        </small>
      </div>
    </article>
  );
}

export default function OpsHealthPage() {
  const { token } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [metrics24h, setMetrics24h] = useState(null);
  const [errorInvestigationReport, setErrorInvestigationReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [predictiveMinVolume, setPredictiveMinVolume] = useState(5);
  const [predictiveErrorMinRate, setPredictiveErrorMinRate] = useState(0.05);
  const [predictiveErrorAccelFactor, setPredictiveErrorAccelFactor] = useState(1.5);
  const [predictiveLatencyMinMs, setPredictiveLatencyMinMs] = useState(100);
  const [predictiveLatencyAccelFactor, setPredictiveLatencyAccelFactor] = useState(1.4);
  const [thresholdProfile, setThresholdProfile] = useState("prod");
  const [snapshotDecision, setSnapshotDecision] = useState("KEEP");
  const [snapshotRationale, setSnapshotRationale] = useState("");
  const [snapshotSaving, setSnapshotSaving] = useState(false);
  const [snapshotStatus, setSnapshotStatus] = useState("");
  const [snapshotEvidenceCopied, setSnapshotEvidenceCopied] = useState(false);
  const [snapshotEvidencePlainCopied, setSnapshotEvidencePlainCopied] = useState(false);
  const [snapshotClosureCopied, setSnapshotClosureCopied] = useState(false);
  const [us002EvidenceCopied, setUs002EvidenceCopied] = useState(false);
  const [us002DocCopied, setUs002DocCopied] = useState(false);
  const [us002TopTicketCopied, setUs002TopTicketCopied] = useState(false);
  const [us002EvidenceStatus, setUs002EvidenceStatus] = useState("");
  const [lockerSeverityRows, setLockerSeverityRows] = useState([]);
  const [lockerDataStatus, setLockerDataStatus] = useState("idle");
  const [us001ClosureCopied, setUs001ClosureCopied] = useState(false);
  const [errorInvestigationStatus, setErrorInvestigationStatus] = useState("");
  const [dailySlackStatus, setDailySlackStatus] = useState("");
  const [topErrorsOpen, setTopErrorsOpen] = useState(() => {
    const prefs = loadCollapsedStatePreference();
    return Boolean(prefs.topErrorsOpen);
  });
  const [topErrorsCategoryFilter, setTopErrorsCategoryFilter] = useState("");
  const [topErrorsLimit, setTopErrorsLimit] = useState(5);
  const [classificationOpen, setClassificationOpen] = useState(() => {
    const prefs = loadCollapsedStatePreference();
    return Boolean(prefs.classificationOpen);
  });
  const [classificationCategoryFilter, setClassificationCategoryFilter] = useState("");
  const [classificationLimit, setClassificationLimit] = useState(6);
  const [alertsOpen, setAlertsOpen] = useState(() => {
    const prefs = loadCollapsedStatePreference();
    return Boolean(prefs.alertsOpen);
  });
  const [alertsSeverityFilter, setAlertsSeverityFilter] = useState("");
  const [alertsCodeFilter, setAlertsCodeFilter] = useState("");
  const [alertsLimit, setAlertsLimit] = useState(20);
  const [lineChartGridMode, setLineChartGridMode] = useState(() => loadLineChartGridModePreference());
  const [showAdminConfig, setShowAdminConfig] = useState(false);
  const [opsSanityReport, setOpsSanityReport] = useState(null);
  const [opsSanityLoading, setOpsSanityLoading] = useState(false);
  const [opsSanityError, setOpsSanityError] = useState("");
  const [fg1FinalDecisionReport, setFg1FinalDecisionReport] = useState(null);
  const [fg1FinalDecisionLoading, setFg1FinalDecisionLoading] = useState(false);
  const [fg1FinalDecisionError, setFg1FinalDecisionError] = useState("");
  const [fg1FinalDecisionCopyStatus, setFg1FinalDecisionCopyStatus] = useState("");
  const [fg1HandoffReport, setFg1HandoffReport] = useState(null);
  const [fg1HandoffLoading, setFg1HandoffLoading] = useState(false);
  const [fg1HandoffError, setFg1HandoffError] = useState("");
  const [fg1HandoffCopyStatus, setFg1HandoffCopyStatus] = useState("");
  const [fiscalGoNoGo, setFiscalGoNoGo] = useState({ br: null, pt: null });
  const [fiscalGoNoGoLoading, setFiscalGoNoGoLoading] = useState(false);
  const [fiscalGoNoGoError, setFiscalGoNoGoError] = useState("");
  const [fiscalQuickActionStatus, setFiscalQuickActionStatus] = useState("");
  const [personaView, setPersonaView] = useState(() => {
    try {
      const stored = window.localStorage.getItem(OPS_HEALTH_PERSONA_PREF_KEY);
      if (stored === "ops" || stored === "dev" || stored === "gestao") return stored;
    } catch {
      // no-op
    }
    return "ops";
  });
  const { windowValue: lookbackHours, setWindowValue: setLookbackHours, applyPreset: applyWindowPreset } = useOpsWindowPreset({
    storageKey: OPS_HEALTH_WINDOW_PREF_KEY,
    defaultValue: 24,
    minValue: 1,
    maxValue: 168,
    presetValues: OPS_HEALTH_WINDOW_PRESETS,
  });

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  function applyThresholdProfile(profileKey) {
    const profile = PREDICTIVE_THRESHOLD_PROFILES[profileKey];
    if (!profile) return;
    setPredictiveMinVolume(profile.predictiveMinVolume);
    setPredictiveErrorMinRate(profile.predictiveErrorMinRate);
    setPredictiveErrorAccelFactor(profile.predictiveErrorAccelFactor);
    setPredictiveLatencyMinMs(profile.predictiveLatencyMinMs);
    setPredictiveLatencyAccelFactor(profile.predictiveLatencyAccelFactor);
  }

  async function loadMetrics({ silent = false } = {}) {
    if (!token) return;
    if (!silent) {
      setLoading(true);
      setError("");
    }
    try {
      const params = new URLSearchParams();
      params.set("lookback_hours", String(Math.max(Number(lookbackHours || 24), 1)));
      params.set("predictive_min_volume", String(Math.max(Number(predictiveMinVolume || 5), 1)));
      params.set("predictive_error_min_rate", String(Math.max(Number(predictiveErrorMinRate || 0.05), 0)));
      params.set("predictive_error_accel_factor", String(Math.max(Number(predictiveErrorAccelFactor || 1.5), 1)));
      params.set("predictive_latency_min_ms", String(Math.max(Number(predictiveLatencyMinMs || 100), 0)));
      params.set("predictive_latency_accel_factor", String(Math.max(Number(predictiveLatencyAccelFactor || 1.4), 1)));
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-metrics?${params.toString()}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
      }
      setMetrics(payload || null);
      const params24h = new URLSearchParams();
      params24h.set("lookback_hours", "24");
      params24h.set("predictive_min_volume", String(Math.max(Number(predictiveMinVolume || 5), 1)));
      params24h.set("predictive_error_min_rate", String(Math.max(Number(predictiveErrorMinRate || 0.05), 0)));
      params24h.set("predictive_error_accel_factor", String(Math.max(Number(predictiveErrorAccelFactor || 1.5), 1)));
      params24h.set("predictive_latency_min_ms", String(Math.max(Number(predictiveLatencyMinMs || 100), 0)));
      params24h.set("predictive_latency_accel_factor", String(Math.max(Number(predictiveLatencyAccelFactor || 1.4), 1)));
      const response24h = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-metrics?${params24h.toString()}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload24h = await response24h.json().catch(() => ({}));
      if (response24h.ok) {
        setMetrics24h(payload24h || null);
      }
      const reportParams = new URLSearchParams();
      reportParams.set("lookback_hours", String(Math.max(Number(lookbackHours || 24), 1)));
      reportParams.set("top_causes_limit", "3");
      reportParams.set("evidence_per_cause_limit", "3");
      const reportResponse = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/ops-metrics/error-investigation?${reportParams.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
            ...authHeaders,
          },
        }
      );
      const reportPayload = await reportResponse.json().catch(() => ({}));
      if (reportResponse.ok) {
        setErrorInvestigationReport(reportPayload || null);
      }

      const nowTs = Date.now();
      const dayAgoTs = nowTs - 24 * 60 * 60 * 1000;
      const auditHeaders = {
        Accept: "application/json",
        ...authHeaders,
      };
      const auditParams0 = new URLSearchParams();
      auditParams0.set("limit", "200");
      auditParams0.set("offset", "0");
      const auditParams1 = new URLSearchParams();
      auditParams1.set("limit", "200");
      auditParams1.set("offset", "200");
      const [auditResponse0, auditResponse1] = await Promise.all([
        fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-audit?${auditParams0.toString()}`, { method: "GET", headers: auditHeaders }),
        fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-audit?${auditParams1.toString()}`, { method: "GET", headers: auditHeaders }),
      ]);
      const auditPayload0 = await auditResponse0.json().catch(() => ({}));
      const auditPayload1 = await auditResponse1.json().catch(() => ({}));
      if (auditResponse0.ok || auditResponse1.ok) {
        const auditItems = [
          ...(Array.isArray(auditPayload0?.items) ? auditPayload0.items : []),
          ...(Array.isArray(auditPayload1?.items) ? auditPayload1.items : []),
        ];
        const aggregateByLocker = {};
        for (const item of auditItems) {
          const details = item?.details && typeof item.details === "object" ? item.details : {};
          const lockerId = String(details?.locker_id || "").trim();
          const createdAtRaw = String(item?.created_at || "");
          const createdTs = Date.parse(createdAtRaw);
          if (!lockerId || Number.isNaN(createdTs) || createdTs < dayAgoTs || createdTs > nowTs) continue;
          const row = aggregateByLocker[lockerId] || { lockerId, total: 0, errors: 0 };
          row.total += 1;
          if (String(item?.result || "").toUpperCase() === "ERROR") row.errors += 1;
          aggregateByLocker[lockerId] = row;
        }
        const rows = Object.values(aggregateByLocker);
        const globalTotal = rows.reduce((acc, row) => acc + Number(row.total || 0), 0);
        const globalErrors = rows.reduce((acc, row) => acc + Number(row.errors || 0), 0);
        const globalRate = globalTotal > 0 ? globalErrors / globalTotal : 0;
        const normalizedRows = rows
          .map((row) => {
            const total = Number(row.total || 0);
            const errors = Number(row.errors || 0);
            const rate = total > 0 ? errors / total : 0;
            return {
              lockerId: row.lockerId,
              totalActions24h: total,
              errorActions24h: errors,
              errorRate24h: rate,
              expectedSeverity24h: resolveSeverityFromRate(rate),
              globalRate24h: globalRate,
              deltaVsGlobalPp: (rate - globalRate) * 100,
            };
          })
          .sort((a, b) => {
            const rank = { CRITICAL: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
            const rankDiff = (rank[a.expectedSeverity24h] || 99) - (rank[b.expectedSeverity24h] || 99);
            if (rankDiff !== 0) return rankDiff;
            if (b.deltaVsGlobalPp !== a.deltaVsGlobalPp) return b.deltaVsGlobalPp - a.deltaVsGlobalPp;
            return b.errorActions24h - a.errorActions24h;
          });
        setLockerSeverityRows(normalizedRows);
        setLockerDataStatus(normalizedRows.length > 0 ? "ok" : "empty");
      } else {
        setLockerSeverityRows([]);
        setLockerDataStatus("unavailable");
      }
    } catch (err) {
      setError(String(err?.message || err));
      setLockerSeverityRows([]);
      setLockerDataStatus("unavailable");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  async function loadOpsSanityLatest({ silent = false } = {}) {
    if (!token) return;
    if (!silent) setOpsSanityLoading(true);
    setOpsSanityError("");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-sanity/latest`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar última sanidade OPS."));
      }
      setOpsSanityReport(payload?.report || null);
    } catch (err) {
      setOpsSanityReport(null);
      setOpsSanityError(String(err?.message || err));
    } finally {
      if (!silent) setOpsSanityLoading(false);
    }
  }

  async function loadFg1FinalDecisionLatest({ silent = false } = {}) {
    if (!token) return;
    if (!silent) setFg1FinalDecisionLoading(true);
    setFg1FinalDecisionError("");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/fiscal-fg1-final/latest`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar snapshot final FG-1."));
      }
      setFg1FinalDecisionReport(payload?.report || null);
    } catch (err) {
      setFg1FinalDecisionReport(null);
      setFg1FinalDecisionError(String(err?.message || err));
    } finally {
      if (!silent) setFg1FinalDecisionLoading(false);
    }
  }

  async function loadFg1HandoffLatest({ silent = false } = {}) {
    if (!token) return;
    if (!silent) setFg1HandoffLoading(true);
    setFg1HandoffError("");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/fiscal-fg1-handoff/latest`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar handoff consolidado FG-1."));
      }
      setFg1HandoffReport(payload?.report || null);
    } catch (err) {
      setFg1HandoffReport(null);
      setFg1HandoffError(String(err?.message || err));
    } finally {
      if (!silent) setFg1HandoffLoading(false);
    }
  }

  async function copyFg1HandoffSlackSummary() {
    if (!fg1HandoffReport) {
      setFg1HandoffCopyStatus("Snapshot consolidado FG-1 indisponível para cópia.");
      window.setTimeout(() => setFg1HandoffCopyStatus(""), 2200);
      return;
    }
    const checkStats = getCheckStats(fg1HandoffReport);
    const failedChecks = checkStats.checks.filter((check) => Number(check?.exit_code || 1) !== 0);
    const lines = [
      "🎯 [FG-1 Handoff consolidado]",
      `Decisão: ${String(fg1HandoffReport.decision || "-")} | Resultado: ${String(fg1HandoffReport.result || "-")}`,
      `Checks PASS: ${checkStats.passed}/${checkStats.total}`,
      `Checks com falha: ${checkStats.failed} / ${checkStats.total}`,
      ...failedChecks.slice(0, 3).map((check) => `- ${String(check?.name || "-")}: exit_code=${Number(check?.exit_code || 0)}`),
      `Gerado UTC: ${String(fg1HandoffReport.generated_at || "-")}`,
    ];
    const payload = lines.join("\n");
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(payload);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = payload;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setFg1HandoffCopyStatus("Payload consolidado FG-1 copiado para Slack/Teams.");
      window.setTimeout(() => setFg1HandoffCopyStatus(""), 2400);
    } catch (err) {
      setFg1HandoffCopyStatus(`Falha ao copiar payload consolidado FG-1: ${String(err?.message || err)}`);
    }
  }

  async function copyFg1HandoffCommand() {
    const command = "02_docker/run_fg1_handoff_orchestrator.sh --json";
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(command);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = command;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setFg1HandoffCopyStatus("Comando do orquestrador FG-1 copiado.");
      window.setTimeout(() => setFg1HandoffCopyStatus(""), 2200);
    } catch (err) {
      setFg1HandoffCopyStatus(`Falha ao copiar comando do orquestrador: ${String(err?.message || err)}`);
    }
  }

  async function loadFiscalGoNoGoSummary({ silent = false } = {}) {
    if (!INTERNAL_TOKEN) {
      setFiscalGoNoGo({ br: null, pt: null });
      setFiscalGoNoGoError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      return;
    }
    if (!silent) setFiscalGoNoGoLoading(true);
    setFiscalGoNoGoError("");
    try {
      const headers = {
        Accept: "application/json",
        "X-Internal-Token": INTERNAL_TOKEN,
      };
      const [brRes, ptRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/providers/br-go-no-go?run_connectivity=false`, { method: "GET", headers }),
        fetch(`${BILLING_BASE}/admin/fiscal/providers/pt-go-no-go?run_connectivity=false`, { method: "GET", headers }),
      ]);
      const [brPayload, ptPayload] = await Promise.all([brRes.json().catch(() => ({})), ptRes.json().catch(() => ({}))]);
      if (!brRes.ok || !ptRes.ok) {
        const firstError = !brRes.ok ? brPayload : ptPayload;
        throw new Error(extractErrorMessage(firstError, "Não foi possível carregar Gate GO/NO-GO BR/PT."));
      }
      setFiscalGoNoGo({
        br: brPayload || null,
        pt: ptPayload || null,
      });
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setFiscalGoNoGoError(
          `Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`
        );
      } else {
        setFiscalGoNoGoError(raw);
      }
    } finally {
      if (!silent) setFiscalGoNoGoLoading(false);
    }
  }

  async function copyFiscalQuickActionCommand(actionKey) {
    const internalTokenRef = "${INTERNAL_TOKEN:-<token-interno>}";
    const billingBaseRef = BILLING_BASE || "http://localhost:8020";
    const commands = {
      gate_br: `curl -sS -H "X-Internal-Token: ${internalTokenRef}" "${billingBaseRef}/admin/fiscal/providers/br-go-no-go?run_connectivity=false"`,
      gate_pt: `curl -sS -H "X-Internal-Token: ${internalTokenRef}" "${billingBaseRef}/admin/fiscal/providers/pt-go-no-go?run_connectivity=false"`,
      rollback_br:
        "cd 02_docker && export FISCAL_REAL_PROVIDER_BR_ENABLED=false && docker compose up -d billing_fiscal_service billing_fiscal_worker",
      rollback_pt:
        "cd 02_docker && export FISCAL_REAL_PROVIDER_PT_ENABLED=false && docker compose up -d billing_fiscal_service billing_fiscal_worker",
    };
    const selected = commands[actionKey];
    if (!selected) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(selected);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = selected;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setFiscalQuickActionStatus("Comando de plantão copiado.");
      window.setTimeout(() => setFiscalQuickActionStatus(""), 2000);
    } catch (err) {
      setFiscalQuickActionStatus(`Falha ao copiar comando: ${String(err?.message || err)}`);
    }
  }

  async function exportErrorInvestigationCsv() {
    if (!token) return;
    setErrorInvestigationStatus("");
    try {
      const csvParams = new URLSearchParams();
      csvParams.set("lookback_hours", String(Math.max(Number(lookbackHours || 24), 1)));
      csvParams.set("top_causes_limit", "3");
      csvParams.set("evidence_per_cause_limit", "3");
      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/ops-metrics/error-investigation/export.csv?${csvParams.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "text/csv",
            ...authHeaders,
          },
        }
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(extractErrorMessage(payload, "Falha ao exportar CSV de investigação."));
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ops_error_investigation_${Math.max(Number(lookbackHours || 24), 1)}h.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setErrorInvestigationStatus("CSV de investigação exportado.");
    } catch (err) {
      setErrorInvestigationStatus(`Falha no export CSV: ${String(err?.message || err)}`);
    }
  }

  function buildUs001ClosureText(reportPayload) {
    const report = reportPayload || {};
    const causes = Array.isArray(report?.top_causes) ? report.top_causes.slice(0, 3) : [];
    const categories = Array.isArray(report?.categories) ? report.categories : [];
    const categorySummary = categories
      .map((item) => `${String(item?.category || "OUTROS").toUpperCase()}:${Number(item?.count || 0)} (${Number(item?.percentage || 0).toFixed(1)}%)`)
      .join(" | ");
    const lookback = Math.max(Number(lookbackHours || report?.lookback_hours || 24), 1);
    const from = String(metrics?.window?.from || "");
    const to = String(metrics?.window?.to || "");
    const causeLines = [0, 1, 2].map((idx) => {
      const item = causes[idx] || {};
      const rank = idx + 1;
      return [
        `${rank}. **Causa #${rank}**: ${String(item?.message || "____________________")}  `,
        `   - Categoria: ${String(item?.category || "OUTROS").toUpperCase()}  `,
        `   - Volume / %: ${Number(item?.count || 0)} / ${Number(item?.percentage || 0).toFixed(1)}%  `,
        "   - **Owner**: ____________________  ",
        "   - **Acao corretiva**: ______________________________________________  ",
        "   - Evidencia (audit_id/correlation_id/link): __________________________",
      ].join("\n");
    });
    return [
      "## 19) Fechamento US-001 (pre-formatado)",
      "",
      "Objetivo: concluir formalmente a US-OPS-001 com evidencias operacionais e trilha auditavel.",
      "",
      `- Janela consolidada: ${lookback}h`,
      `- Faixa from/to: ${from || "-"} -> ${to || "-"}`,
      `- Total de erros na janela: ${Number(report?.total_error_actions || 0)}`,
      `- Distribuicao por categoria: ${categorySummary || "Sem dados na janela"}`,
      "",
      "### 1) Top 3 causas (preencher owner/acao)",
      causeLines.join("\n\n"),
      "",
      "### 2) Hipoteses e evidencias operacionais",
      "- [ ] Hipotese principal validada com evidencia de log/traces.",
      "- [ ] Hipoteses secundarias registradas com status (validada/descartada).",
      "- [ ] Links de evidencias anexados (dashboard/audit/export CSV).",
      "",
      "### 3) Plano de mitigacao emergencial",
      "- [ ] Mitigacao imediata definida e executada.",
      "- [ ] Risco residual descrito.",
      "- [ ] Responsavel por monitoramento pos-mitigacao definido.",
      "- Plano resumido (1-3 linhas): __________________________________________",
      "",
      "### 4) Gate de encerramento (DoD US-001)",
      "- [ ] 100% dos erros da janela classificados por categoria.",
      "- [ ] Top 3 causas com owner e acao corretiva documentados.",
      "- [ ] Evidencias operacionais anexadas e auditaveis.",
      "- [ ] Plano de mitigacao emergencial registrado.",
      "- [ ] Status da **US-OPS-001** alterado para **Concluido (implementado em codigo + evidencias operacionais)**.",
    ].join("\n");
  }

  async function copyUs001ClosureBlock() {
    const text = buildUs001ClosureText(errorInvestigationReport);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setUs001ClosureCopied(true);
      setErrorInvestigationStatus("Bloco de fechamento US-001 copiado para a seção 19.");
      window.setTimeout(() => setUs001ClosureCopied(false), 1800);
    } catch (err) {
      setErrorInvestigationStatus(`Falha ao copiar fechamento US-001: ${String(err?.message || err)}`);
    }
  }

  async function savePredictiveSnapshot() {
    if (!token || snapshotSaving) return;
    setSnapshotSaving(true);
    setSnapshotStatus("");
    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-metrics/predictive-snapshots`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          environment: thresholdProfile,
          decision: snapshotDecision,
          rationale: snapshotRationale || null,
          predictive_min_volume: predictiveMinVolume,
          predictive_error_min_rate: predictiveErrorMinRate,
          predictive_error_accel_factor: predictiveErrorAccelFactor,
          predictive_latency_min_ms: predictiveLatencyMinMs,
          predictive_latency_accel_factor: predictiveLatencyAccelFactor,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(extractErrorMessage(payload));
      setSnapshotStatus("Snapshot semanal salvo.");
      await loadMetrics({ silent: true });
    } catch (err) {
      setSnapshotStatus(`Falha ao salvar snapshot: ${String(err?.message || err)}`);
    } finally {
      setSnapshotSaving(false);
    }
  }

  function buildWeeklyExecutionEvidenceText(snapshot, currentMetrics) {
    const source = snapshot || {};
    const thresholds = source?.thresholds || {};
    const monitoring = {
      emitted_alerts: Number(source?.emitted_alerts ?? currentMetrics?.predictive_monitoring?.emitted_alerts ?? 0),
      confirmed_alerts: Number(source?.confirmed_alerts ?? currentMetrics?.predictive_monitoring?.confirmed_alerts ?? 0),
      false_positive_alerts: Number(source?.false_positive_alerts ?? currentMetrics?.predictive_monitoring?.false_positive_alerts ?? 0),
      false_positive_rate: Number(source?.false_positive_rate ?? currentMetrics?.predictive_monitoring?.false_positive_rate ?? 0),
      recommendation: String(currentMetrics?.predictive_monitoring?.recommendation || "KEEP"),
    };
    const from = String(currentMetrics?.window?.from || "");
    const to = String(currentMetrics?.window?.to || "");
    const env = String(source?.environment || thresholdProfile || "hml").toUpperCase();
    const decision = String(source?.decision || snapshotDecision || "KEEP").toUpperCase();
    const rationale = String(source?.rationale || snapshotRationale || "Sem observação adicional.");
    const createdAt = source?.created_at ? new Date(source.created_at).toLocaleString("pt-BR") : new Date().toLocaleString("pt-BR");

    return [
      "## 18) US-OPS-011 - Execucao semanal #1 (auditavel)",
      "",
      "**Semana de referencia**: 27/04/2026 a 03/05/2026",
      "**Owner do ciclo**: SRE/Plataforma + Dados + Ops",
      `**Ambiente avaliado**: ${env}`,
      "",
      "### 1) Baseline (7d)",
      `- emitted_alerts: ${monitoring.emitted_alerts}`,
      `- confirmed_alerts: ${monitoring.confirmed_alerts}`,
      `- false_positive_alerts: ${monitoring.false_positive_alerts}`,
      `- false_positive_rate: ${monitoring.false_positive_rate.toFixed(4)} (${(monitoring.false_positive_rate * 100).toFixed(1)}%)`,
      `- recommendation retornada: ${monitoring.recommendation}`,
      `- Janela usada (from/to): ${from || "-"} -> ${to || "-"}`,
      `- Evidencia: Snapshot ${source?.id || "(não persistido)"} gerado em ${createdAt}`,
      "",
      "### 2) Decisao semanal",
      `- Decisao tomada: ${decision}`,
      `- Resumo da decisao: ${rationale}`,
      "",
      "### 3) Ajuste aplicado",
      `- predictive_min_volume: ${Number(thresholds?.predictive_min_volume ?? predictiveMinVolume)}`,
      `- predictive_error_min_rate: ${Number(thresholds?.predictive_error_min_rate ?? predictiveErrorMinRate)}`,
      `- predictive_error_accel_factor: ${Number(thresholds?.predictive_error_accel_factor ?? predictiveErrorAccelFactor)}`,
      `- predictive_latency_min_ms: ${Number(thresholds?.predictive_latency_min_ms ?? predictiveLatencyMinMs)}`,
      `- predictive_latency_accel_factor: ${Number(thresholds?.predictive_latency_accel_factor ?? predictiveLatencyAccelFactor)}`,
      "",
      "### 4) Resultado esperado para semana seguinte",
      "- Meta de controle de ruido: false_positive_rate <= 40%",
      "- Critério de sucesso: >= 60% dos alertas confirmados",
    ].join("\n");
  }

  function buildWeeklyExecutionEvidencePlainText(snapshot, currentMetrics) {
    const source = snapshot || {};
    const thresholds = source?.thresholds || {};
    const monitoring = {
      emitted_alerts: Number(source?.emitted_alerts ?? currentMetrics?.predictive_monitoring?.emitted_alerts ?? 0),
      confirmed_alerts: Number(source?.confirmed_alerts ?? currentMetrics?.predictive_monitoring?.confirmed_alerts ?? 0),
      false_positive_alerts: Number(source?.false_positive_alerts ?? currentMetrics?.predictive_monitoring?.false_positive_alerts ?? 0),
      false_positive_rate: Number(source?.false_positive_rate ?? currentMetrics?.predictive_monitoring?.false_positive_rate ?? 0),
      recommendation: String(currentMetrics?.predictive_monitoring?.recommendation || "KEEP"),
    };
    const from = String(currentMetrics?.window?.from || "");
    const to = String(currentMetrics?.window?.to || "");
    const env = String(source?.environment || thresholdProfile || "hml").toUpperCase();
    const decision = String(source?.decision || snapshotDecision || "KEEP").toUpperCase();
    const rationale = String(source?.rationale || snapshotRationale || "Sem observação adicional.");
    const createdAt = source?.created_at ? new Date(source.created_at).toLocaleString("pt-BR") : new Date().toLocaleString("pt-BR");

    return [
      "US-OPS-011 - EXECUCAO SEMANAL #1",
      "",
      `Semana de referencia: 27/04/2026 a 03/05/2026`,
      `Owner do ciclo: SRE/Plataforma + Dados + Ops`,
      `Ambiente avaliado: ${env}`,
      "",
      "BASELINE (7d)",
      `- emitted_alerts: ${monitoring.emitted_alerts}`,
      `- confirmed_alerts: ${monitoring.confirmed_alerts}`,
      `- false_positive_alerts: ${monitoring.false_positive_alerts}`,
      `- false_positive_rate: ${monitoring.false_positive_rate.toFixed(4)} (${(monitoring.false_positive_rate * 100).toFixed(1)}%)`,
      `- recommendation retornada: ${monitoring.recommendation}`,
      `- Janela usada (from/to): ${from || "-"} -> ${to || "-"}`,
      `- Evidencia: Snapshot ${source?.id || "(não persistido)"} gerado em ${createdAt}`,
      "",
      "DECISAO SEMANAL",
      `- Decisao tomada: ${decision}`,
      `- Resumo da decisao: ${rationale}`,
      "",
      "AJUSTE APLICADO",
      `- predictive_min_volume: ${Number(thresholds?.predictive_min_volume ?? predictiveMinVolume)}`,
      `- predictive_error_min_rate: ${Number(thresholds?.predictive_error_min_rate ?? predictiveErrorMinRate)}`,
      `- predictive_error_accel_factor: ${Number(thresholds?.predictive_error_accel_factor ?? predictiveErrorAccelFactor)}`,
      `- predictive_latency_min_ms: ${Number(thresholds?.predictive_latency_min_ms ?? predictiveLatencyMinMs)}`,
      `- predictive_latency_accel_factor: ${Number(thresholds?.predictive_latency_accel_factor ?? predictiveLatencyAccelFactor)}`,
      "",
      "RESULTADO ESPERADO",
      "- Meta de controle de ruido: false_positive_rate <= 40%",
      "- Criterio de sucesso: >= 60% dos alertas confirmados",
    ].join("\n");
  }

  async function copyWeeklyExecutionEvidence() {
    const latestSnapshot = Array.isArray(metrics?.predictive_snapshots) ? metrics.predictive_snapshots[0] : null;
    const text = buildWeeklyExecutionEvidenceText(latestSnapshot, metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setSnapshotEvidenceCopied(true);
      setSnapshotStatus("Evidência semanal copiada para seção 18.");
      window.setTimeout(() => setSnapshotEvidenceCopied(false), 1800);
    } catch (err) {
      setSnapshotStatus(`Falha ao copiar evidência: ${String(err?.message || err)}`);
    }
  }

  async function copyWeeklyExecutionEvidencePlain() {
    const latestSnapshot = Array.isArray(metrics?.predictive_snapshots) ? metrics.predictive_snapshots[0] : null;
    const text = buildWeeklyExecutionEvidencePlainText(latestSnapshot, metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setSnapshotEvidencePlainCopied(true);
      setSnapshotStatus("Evidência semanal (texto simples) copiada.");
      window.setTimeout(() => setSnapshotEvidencePlainCopied(false), 1800);
    } catch (err) {
      setSnapshotStatus(`Falha ao copiar evidência simples: ${String(err?.message || err)}`);
    }
  }

  function buildUs011ClosureText(snapshot, currentMetrics) {
    const source = snapshot || {};
    const monitoring = {
      emitted_alerts: Number(source?.emitted_alerts ?? currentMetrics?.predictive_monitoring?.emitted_alerts ?? 0),
      confirmed_alerts: Number(source?.confirmed_alerts ?? currentMetrics?.predictive_monitoring?.confirmed_alerts ?? 0),
      false_positive_alerts: Number(source?.false_positive_alerts ?? currentMetrics?.predictive_monitoring?.false_positive_alerts ?? 0),
      false_positive_rate: Number(source?.false_positive_rate ?? currentMetrics?.predictive_monitoring?.false_positive_rate ?? 0),
      recommendation: String(currentMetrics?.predictive_monitoring?.recommendation || "KEEP"),
    };
    const thresholds = source?.thresholds || currentMetrics?.predictive_thresholds || {};
    const from = String(currentMetrics?.window?.from || "");
    const to = String(currentMetrics?.window?.to || "");
    return [
      "### US-OPS-011 - Alertas preditivos (Status: Em andamento)",
      "**Owner sugerido**: SRE/Plataforma + Dados + Ops  ",
      "**Data alvo**: 02/05/2026",
      `- [x] Executar 1 ciclo semanal de revisao com baseline de falso positivo (7d): FP ${(monitoring.false_positive_rate * 100).toFixed(1)}%`,
      `- [x] Validar thresholds por ambiente (dev/hml/prod) com evidencias: min_volume=${Number(thresholds?.predictive_min_volume || 0)}, err_min=${Number(
        thresholds?.predictive_error_min_rate || 0
      )}, err_accel=${Number(thresholds?.predictive_error_accel_factor || 0)}, lat_min_ms=${Number(
        thresholds?.predictive_latency_min_ms || 0
      )}, lat_accel=${Number(thresholds?.predictive_latency_accel_factor || 0)}`,
      `- [x] Registrar ajuste aplicado e motivo (ruido, confirmacao, volume): recommendation=${monitoring.recommendation}`,
      `- [x] Confirmar DoD final (taxa de falso positivo monitorada + rotina semanal ativa): janela ${from || "-"} -> ${to || "-"}`,
      "- [ ] Marcar status da US-OPS-011 como concluido no backlog.",
      "",
      `Evidencia: emitted=${monitoring.emitted_alerts}, confirmed=${monitoring.confirmed_alerts}, false_positive=${monitoring.false_positive_alerts}.`,
    ].join("\n");
  }

  async function copyUs011ClosureBlock() {
    const latestSnapshot = Array.isArray(metrics?.predictive_snapshots) ? metrics.predictive_snapshots[0] : null;
    const text = buildUs011ClosureText(latestSnapshot, metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setSnapshotClosureCopied(true);
      setSnapshotStatus("Bloco de fechamento US-OPS-011 copiado.");
      window.setTimeout(() => setSnapshotClosureCopied(false), 1800);
    } catch (err) {
      setSnapshotStatus(`Falha ao copiar fechamento US-OPS-011: ${String(err?.message || err)}`);
    }
  }

  function buildUs002EvidenceText(currentMetrics, lookbackWindowHours) {
    const from = String(currentMetrics?.window?.from || "");
    const to = String(currentMetrics?.window?.to || "");
    const activeAlerts = Array.isArray(currentMetrics?.alerts) ? currentMetrics.alerts : [];
    const countBySeverity = activeAlerts.reduce((acc, item) => {
      const key = String(item?.severity || "INFO").toUpperCase();
      return {
        ...acc,
        [key]: Number(acc[key] || 0) + 1,
      };
    }, {});
    const trackedAlerts = activeAlerts.map((item) => {
      const severity = String(item?.severity || "INFO").toUpperCase();
      const code = String(item?.code || "SEM_CODIGO");
      return `- [${severity}] ${code}`;
    });
    const matrixLines = OPS_SEVERITY_SLA_MATRIX.map((item) => {
      return `- ${item.severityLabel}: SLA ${item.responseSla} | Canal: ${item.channel} | Owner: ${item.owner} | Ativos: ${Number(
        countBySeverity[item.severityKey] || 0
      )}`;
    });
    return [
      "## US-OPS-002 - Evidencia auditavel de severidade (ops/health)",
      "",
      `- Data/hora da coleta: ${new Date().toLocaleString("pt-BR")}`,
      `- Janela monitorada: ${Math.max(Number(lookbackWindowHours || 24), 1)}h`,
      `- Faixa from/to: ${from || "-"} -> ${to || "-"}`,
      `- Total de alertas ativos: ${activeAlerts.length}`,
      "",
      "### Matriz SLA/canal por severidade",
      ...matrixLines,
      "",
      "### Alertas ativos na janela",
      ...(trackedAlerts.length > 0 ? trackedAlerts : ["- Sem alertas ativos"]),
      "",
      "### Checklist operacional (auditoria)",
      "- [ ] Testes de disparo por severidade executados e registrados.",
      "- [ ] Canal critico validado com evidencias (print/log/ticket).",
      "- [ ] SLA de resposta por severidade validado no turno.",
    ].join("\n");
  }

  function buildUs002SprintDocBlockText(currentMetrics) {
    const activeAlerts = Array.isArray(currentMetrics?.alerts) ? currentMetrics.alerts : [];
    const countBySeverity = activeAlerts.reduce((acc, item) => {
      const key = String(item?.severity || "INFO").toUpperCase();
      return {
        ...acc,
        [key]: Number(acc[key] || 0) + 1,
      };
    }, {});
    const from = String(currentMetrics?.window?.from || "");
    const to = String(currentMetrics?.window?.to || "");
    const lookback = Math.max(Number(currentMetrics?.window?.lookback_hours || lookbackHours || 24), 1);
    return [
      "- Matriz SLA/canal por severidade (US-OPS-002) adicionada no dashboard:",
      "  - card dedicado com CRITICO/ALTO/MEDIO/BAIXO",
      "  - SLA de resposta por nivel exibido na UI",
      "  - canal operacional por severidade exibido na UI",
      "  - owner sugerido por severidade exibido na UI",
      `  - contagem de alertas ativos por severidade na janela (${lookback}h)`,
      "- Bloco de evidencia auditavel do US-OPS-002 habilitado via copia em 1 clique:",
      "  - inclui data/hora da coleta",
      `  - inclui janela from/to (${from || "-"} -> ${to || "-"})`,
      "  - inclui total de alertas ativos na janela",
      "  - inclui checklist operacional para DoD (SLA/canal/testes)",
      `  - snapshot atual: CRITICO=${Number(countBySeverity.CRITICAL || 0)}, ALTO=${Number(countBySeverity.HIGH || 0)}, MEDIO=${Number(
        countBySeverity.MEDIUM || 0
      )}, BAIXO=${Number(countBySeverity.LOW || 0)}`,
      "- Validacao apos matriz SLA/canal + evidencia auditavel (US-OPS-002): lint sem erros.",
    ].join("\n");
  }

  async function copyUs002Evidence() {
    const text = buildUs002EvidenceText(metrics, lookbackHours);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setUs002EvidenceCopied(true);
      setUs002EvidenceStatus("Bloco auditavel do US-OPS-002 copiado.");
      window.setTimeout(() => setUs002EvidenceCopied(false), 1800);
    } catch (err) {
      setUs002EvidenceStatus(`Falha ao copiar evidencia do US-OPS-002: ${String(err?.message || err)}`);
    }
  }

  async function copyUs002SprintDocBlock() {
    const text = buildUs002SprintDocBlockText(metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setUs002DocCopied(true);
      setUs002EvidenceStatus("Bloco no formato do documento de sprint copiado.");
      window.setTimeout(() => setUs002DocCopied(false), 1800);
    } catch (err) {
      setUs002EvidenceStatus(`Falha ao copiar bloco para sprint: ${String(err?.message || err)}`);
    }
  }

  function buildTopLockerImmediateTicket(topLocker) {
    if (!topLocker) return "";
    return [
      `# [US-OPS-002] Acao imediata - locker critico 24h`,
      ``,
      `- Locker: ${topLocker.lockerId}`,
      `- Severidade esperada: ${topLocker.expectedSeverity24h}`,
      `- Erros/Total (24h): ${topLocker.errorActions24h}/${topLocker.totalActions24h} (${(topLocker.errorRate24h * 100).toFixed(2)}%)`,
      `- Taxa global (24h): ${(topLocker.globalRate24h * 100).toFixed(2)}%`,
      `- Delta vs global: ${topLocker.deltaVsGlobalPp >= 0 ? "+" : ""}${topLocker.deltaVsGlobalPp.toFixed(2)} p.p.`,
      ``,
      `## Acoes imediatas`,
      `1. Abrir OPS Audit e filtrar por locker + result=ERROR nas ultimas 24h.`,
      `2. Classificar top causas (timeout/validacao/integracao/infra).`,
      `3. Aplicar mitigacao rapida (retry/backoff/fallback) e registrar evidencia no ticket.`,
    ].join("\n");
  }

  async function copyTopLockerImmediateTicket(topLocker) {
    const text = buildTopLockerImmediateTicket(topLocker);
    if (!text) {
      setUs002EvidenceStatus("Sem dados de locker para gerar ticket imediato.");
      return;
    }
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setUs002TopTicketCopied(true);
      setUs002EvidenceStatus("Ticket de acao imediata (Top 1 locker) copiado.");
      window.setTimeout(() => setUs002TopTicketCopied(false), 1800);
    } catch (err) {
      setUs002EvidenceStatus(`Falha ao copiar ticket imediato: ${String(err?.message || err)}`);
    }
  }

  useEffect(() => {
    void loadMetrics();
    void loadOpsSanityLatest({ silent: true });
    void loadFg1FinalDecisionLatest({ silent: true });
    void loadFg1HandoffLatest({ silent: true });
    void loadFiscalGoNoGoSummary({ silent: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    token,
    lookbackHours,
    predictiveMinVolume,
    predictiveErrorMinRate,
    predictiveErrorAccelFactor,
    predictiveLatencyMinMs,
    predictiveLatencyAccelFactor,
  ]);

  useEffect(() => {
    try {
      window.localStorage.setItem(OPS_HEALTH_PERSONA_PREF_KEY, personaView);
    } catch {
      // no-op
    }
  }, [personaView]);

  useEffect(() => {
    try {
      const payload = {
        topErrorsOpen,
        classificationOpen,
        alertsOpen,
      };
      window.localStorage.setItem(OPS_HEALTH_COLLAPSE_PREF_KEY, JSON.stringify(payload));
    } catch {
      // no-op
    }
  }, [topErrorsOpen, classificationOpen, alertsOpen]);

  useEffect(() => {
    try {
      window.localStorage.setItem(OPS_HEALTH_LINE_CHART_GRID_MODE_PREF_KEY, lineChartGridMode);
    } catch {
      // no-op
    }
  }, [lineChartGridMode]);

  const previousKpis = metrics?.comparison?.kpis || {};
  const currentErrorRate = Number(metrics?.kpis?.error_rate || 0);
  const previousErrorRate = Number(previousKpis?.error_rate || 0);
  const currentP50 = Number(metrics?.kpis?.latency_p50_ms || 0);
  const currentP95 = Number(metrics?.kpis?.latency_p95_ms || 0);
  const previousP50 = Number(previousKpis?.latency_p50_ms || 0);
  const previousP95 = Number(previousKpis?.latency_p95_ms || 0);
  const currentLatencySamples = Number(metrics?.kpis?.latency_samples || 0);
  const totalActions = Number(metrics?.kpis?.total_ops_actions || 0);
  const errorActions = Number(metrics?.kpis?.error_actions || 0);
  const redCoverage = {
    rate: totalActions >= 0,
    errors: totalActions > 0 || errorActions === 0,
    duration: currentLatencySamples > 0,
  };
  const redCoverageOk = redCoverage.rate && redCoverage.errors && redCoverage.duration;
  const collectorHealth = totalActions === 0
    ? { label: "Sem dados do coletor na janela", tone: "warn" }
    : currentLatencySamples === 0
      ? { label: "Dados parciais: sem amostra de latência", tone: "warn" }
      : { label: "Coletor ativo (dados recebidos)", tone: "ok" };
  const trendPoints = Array.isArray(metrics?.trends?.points) ? metrics.trends.points : [];
  const trendPoints24h = Array.isArray(metrics24h?.trends?.points) ? metrics24h.trends.points : [];
  const predictiveSnapshots = Array.isArray(metrics?.predictive_snapshots) ? metrics.predictive_snapshots : [];
  const activeAlerts = Array.isArray(metrics?.alerts) ? metrics.alerts : [];
  const topLockerCritical24h = lockerSeverityRows.length > 0 ? lockerSeverityRows[0] : null;
  const alertCountBySeverity = activeAlerts.reduce((acc, item) => {
    const key = String(item?.severity || "INFO").toUpperCase();
    return {
      ...acc,
      [key]: Number(acc[key] || 0) + 1,
    };
  }, {});
  const latestPredictiveSnapshot = predictiveSnapshots.length > 0 ? predictiveSnapshots[0] : null;
  const previousPredictiveSnapshot = predictiveSnapshots.length > 1 ? predictiveSnapshots[1] : null;
  const drilldownLinks = buildDrilldownLinks(metrics, lookbackHours);
  const errorRateSeries = trendPoints.map((point) => Number(point?.error_rate || 0) * 100);
  const volumeSeries = trendPoints.map((point) => Number(point?.total_ops_actions || 0));
  const latencySeries = trendPoints.map((point) => Number(point?.latency_p95_ms || 0));
  const topInvestigatedCauses = Array.isArray(errorInvestigationReport?.top_causes) ? errorInvestigationReport.top_causes : [];
  const investigatedCategories = Array.isArray(errorInvestigationReport?.categories) ? errorInvestigationReport.categories : [];
  const topErrors = Array.isArray(metrics?.top_errors) ? metrics.top_errors : [];
  const filteredTopErrors = topErrors
    .filter((item) =>
      topErrorsCategoryFilter
        ? String(item?.category || "OUTROS").toUpperCase().includes(topErrorsCategoryFilter.toUpperCase())
        : true
    )
    .slice(0, Math.max(Number(topErrorsLimit || 5), 1));
  const classificationCategories = Array.isArray(metrics?.error_classification?.categories) ? metrics.error_classification.categories : [];
  const filteredClassificationCategories = classificationCategories
    .filter((item) =>
      classificationCategoryFilter
        ? String(item?.category || "OUTROS").toUpperCase().includes(classificationCategoryFilter.toUpperCase())
        : true
    )
    .slice(0, Math.max(Number(classificationLimit || 6), 1));
  const filteredActiveAlerts = activeAlerts
    .filter((item) => (alertsSeverityFilter ? String(item?.severity || "").toUpperCase() === alertsSeverityFilter : true))
    .filter((item) =>
      alertsCodeFilter
        ? String(item?.code || "")
            .toUpperCase()
            .includes(alertsCodeFilter.toUpperCase())
        : true
    )
    .slice(0, Math.max(Number(alertsLimit || 20), 1));
  const [openRunbookCode, setOpenRunbookCode] = useState(null);
  const [copiedRunbookCode, setCopiedRunbookCode] = useState(null);
  const [copiedPlainRunbookCode, setCopiedPlainRunbookCode] = useState(null);
  const isOpsPersona = personaView === "ops";
  const isDevPersona = personaView === "dev";
  const isGestaoPersona = personaView === "gestao";
  const personaSubtitleByView = {
    ops: "Foco em operação diária, risco imediato e ação rápida.",
    dev: "Foco em estabilidade técnica, tendência de erro e diagnóstico.",
    gestao: "Foco em saúde do serviço, eficiência e impacto consolidado.",
  };

  function formatSignedNumber(value, digits = 1) {
    const numeric = Number(value || 0);
    const signal = numeric >= 0 ? "+" : "";
    return `${signal}${numeric.toFixed(digits)}`;
  }

  async function copyOpsHealthDailySlack() {
    try {
      const nowIso = new Date().toISOString();
      const dominantSeverity = resolveSeverityFromRate(currentErrorRate);
      const dominantEmoji = severityEmoji(dominantSeverity);
      const topCauses = topInvestigatedCauses
        .slice(0, 3)
        .map((item) => `${String(item?.category || "OUTROS").toUpperCase()}:${Number(item?.count || 0)}`)
        .join(" | ") || "-";
      const predictiveRate = Number(metrics?.predictive_monitoring?.false_positive_rate || 0);
      const text = [
        `${dominantEmoji} *OPS Daily (Health) | ${nowIso}*`,
        `Hoje: erro=${(currentErrorRate * 100).toFixed(1)}% (${errorActions}/${totalActions}) | severidade=${dominantSeverity} ${dominantEmoji} | alertas_ativos=${activeAlerts.length}`,
        `Bloqueios: ${error ? `falha_coleta=${error}` : "sem bloqueios técnicos de coleta"}`,
        `Decisão: manter foco em mitigação de severidade ${dominantSeverity} e seguir triagem das top causas`,
        `Sinais: top_causas=${topCauses} | preditivo_fp_7d=${(predictiveRate * 100).toFixed(1)}% | coletor=${collectorHealth.label}`,
      ].join("\n");
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setDailySlackStatus("Daily Slack/Teams (ops/health) copiado.");
      window.setTimeout(() => setDailySlackStatus(""), 2500);
    } catch (err) {
      setDailySlackStatus(`Falha ao copiar daily: ${String(err?.message || err)}`);
    }
  }

  async function copyFg1FinalDecisionSlack() {
    if (!fg1FinalDecisionReport) {
      setFg1FinalDecisionCopyStatus("Snapshot FG-1 indisponível para cópia.");
      window.setTimeout(() => setFg1FinalDecisionCopyStatus(""), 2200);
      return;
    }
    try {
      const nowIso = new Date().toISOString();
      const text = [
        `📌 *FG-1 Handoff Final | ${nowIso}*`,
        `Decisão global: ${String(fg1FinalDecisionReport.final_global_decision || "-")}`,
        `Países aptos: ${Number(fg1FinalDecisionReport.countries_ready || 0)} | Países bloqueados: ${Number(fg1FinalDecisionReport.countries_blocked || 0)} | Total: ${Number(fg1FinalDecisionReport.country_count || 0)}`,
        `Versões: coverage=${String(fg1FinalDecisionReport?.sources?.coverage_gate_version || "-")} | readiness=${String(fg1FinalDecisionReport?.sources?.readiness_gate_version || "-")} | action_plan=${String(fg1FinalDecisionReport?.sources?.action_plan_version || "-")}`,
        `Gerado em UTC: ${String(fg1FinalDecisionReport.generated_at || "-")}`,
      ].join("\n");
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setFg1FinalDecisionCopyStatus("Payload resumido FG-1 copiado para Slack/Teams.");
      window.setTimeout(() => setFg1FinalDecisionCopyStatus(""), 2400);
    } catch (err) {
      setFg1FinalDecisionCopyStatus(`Falha ao copiar payload FG-1: ${String(err?.message || err)}`);
    }
  }

  async function copyFg1TopBlockedTicket() {
    if (!fg1FinalDecisionReport) {
      setFg1FinalDecisionCopyStatus("Snapshot FG-1 indisponível para ticket imediato.");
      window.setTimeout(() => setFg1FinalDecisionCopyStatus(""), 2200);
      return;
    }
    const countries = Array.isArray(fg1FinalDecisionReport.countries) ? fg1FinalDecisionReport.countries : [];
    const blocked = countries
      .filter((row) => String(row?.final_decision || "").toUpperCase() !== "GO")
      .sort((a, b) => Number(b?.pending_actions || 0) - Number(a?.pending_actions || 0));
    if (blocked.length === 0) {
      setFg1FinalDecisionCopyStatus("Sem país bloqueado no snapshot atual (todos GO).");
      window.setTimeout(() => setFg1FinalDecisionCopyStatus(""), 2200);
      return;
    }
    const top = blocked[0];
    const country = String(top?.country_code || "-").toUpperCase();
    const pending = Number(top?.pending_actions || 0);
    const text = [
      `🎯 [FG-1 Ticket imediato] País crítico: ${country}`,
      `Bloqueios pendentes: ${pending}`,
      `Coverage: ${String(top?.coverage_status || "-")} | Readiness: ${String(top?.readiness_status || "-")}`,
      "Ação recomendada: executar readiness-action-plan do país e fechar primeiro auth/homologação/certificado/SLA.",
      `Snapshot UTC: ${String(fg1FinalDecisionReport.generated_at || "-")}`,
    ].join("\n");
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setFg1FinalDecisionCopyStatus(`Ticket imediato FG-1 copiado (${country}).`);
      window.setTimeout(() => setFg1FinalDecisionCopyStatus(""), 2400);
    } catch (err) {
      setFg1FinalDecisionCopyStatus(`Falha ao copiar ticket imediato FG-1: ${String(err?.message || err)}`);
    }
  }

  const kpiCardMap = {
    totalActions: (
      <OpsTrendKpiCard label="Ações OPS" value={metrics?.kpis?.total_ops_actions ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
    ),
    absoluteImpact: (
      <OpsTrendKpiCard
        label="Impacto absoluto (falhas/total)"
        value={`${errorActions}/${totalActions}`}
        previousValue="-"
        trend={null}
        deltaLabel={`${totalActions > 0 ? ((errorActions / totalActions) * 100).toFixed(1) : "0.0"}% de falhas`}
        baseStyle={getCriticalityCardStyle(
          kpiBoxStyle,
          totalActions > 0 && errorActions / totalActions >= 0.2 ? "critical" : totalActions > 0 && errorActions / totalActions >= 0.05 ? "high" : "normal"
        )}
        linkTo={errorActions > 0 ? drilldownLinks.auditErrors : null}
        linkTitle="Abrir Nível 2: Auditoria de erros"
        showTrend={false}
      />
    ),
    errorRate: (
      <OpsTrendKpiCard
        label="Taxa de erro"
        value={formatPercent(currentErrorRate)}
        previousValue={formatPercent(previousErrorRate)}
        trend={resolveErrorRateTrend(currentErrorRate, previousErrorRate)}
        deltaLabel={formatDeltaPercentagePoints(currentErrorRate, previousErrorRate)}
        baseStyle={getCriticalityCardStyle(
          kpiBoxStyle,
          currentErrorRate >= 0.2 ? "critical" : currentErrorRate >= 0.05 ? "high" : "normal"
        )}
        linkTo={currentErrorRate >= 0.05 ? drilldownLinks.auditErrors : null}
        linkTitle="Abrir Nível 2: Auditoria de erros"
        showTrend
      />
    ),
    reconciliationActions: (
      <OpsTrendKpiCard
        label="Reconciliações"
        value={metrics?.kpis?.reconciliation_actions ?? 0}
        previousValue={previousKpis?.reconciliation_actions ?? 0}
        trend={
          Number(metrics?.kpis?.reconciliation_actions || 0) - Number(previousKpis?.reconciliation_actions || 0) > 0
            ? "up"
            : Number(metrics?.kpis?.reconciliation_actions || 0) - Number(previousKpis?.reconciliation_actions || 0) < 0
              ? "down"
              : "stable"
        }
        deltaLabel={`${
          Number(metrics?.kpis?.reconciliation_actions || 0) - Number(previousKpis?.reconciliation_actions || 0) >= 0 ? "+" : ""
        }${Number(metrics?.kpis?.reconciliation_actions || 0) - Number(previousKpis?.reconciliation_actions || 0)}`}
        baseStyle={kpiBoxStyle}
        showTrend
      />
    ),
    latency: (
      <OpsTrendKpiCard
        label="Latência p50/p95 (ms)"
        value={`${currentP50.toFixed(0)} / ${currentP95.toFixed(0)}`}
        previousValue={`${previousP50.toFixed(0)} / ${previousP95.toFixed(0)}`}
        trend={resolveLatencyTrend(currentP95, previousP95)}
        deltaLabel={`p95 ${currentP95 - previousP95 >= 0 ? "+" : ""}${(currentP95 - previousP95).toFixed(0)}ms`}
        auxiliaryLabel={formatLatencySampleQuality(currentLatencySamples)}
        baseStyle={kpiBoxStyle}
        showTrend
      />
    ),
    autoReconciliationRate: (
      <OpsTrendKpiCard
        label="% reconciliação automática"
        value={`${(Number(metrics?.kpis?.reconciliation_auto_rate || 0) * 100).toFixed(1)}%`}
        previousValue="-"
        trend={null}
        deltaLabel={`total:${Number(metrics?.kpis?.reconciliation_total_completed || 0)}`}
        auxiliaryLabel={`done:${Number(metrics?.kpis?.reconciliation_done_count || 0)} | failed_final:${
          Number(metrics?.kpis?.reconciliation_failed_final_count_window || 0)
        }`}
        baseStyle={kpiBoxStyle}
        showTrend={false}
      />
    ),
    avgReconciliationTime: (
      <OpsTrendKpiCard
        label="Tempo médio reconciliação (min)"
        value={Number(metrics?.kpis?.avg_reconciliation_time_min || 0).toFixed(1)}
        previousValue="-"
        trend={null}
        deltaLabel="média da janela"
        baseStyle={kpiBoxStyle}
        showTrend={false}
      />
    ),
    pendingOpen: (
      <OpsTrendKpiCard
        label="Pendências abertas"
        value={metrics?.kpis?.pending_open_count ?? 0}
        baseStyle={kpiBoxStyle}
        linkTo={Number(metrics?.kpis?.pending_open_count || 0) > 0 ? drilldownLinks.reconciliation : null}
        linkTitle="Abrir Nível 2: Reconciliação"
        showTrend={false}
      />
    ),
    pendingAge: (
      <OpsTrendKpiCard
        label="Pendências por idade"
        value={metrics?.kpis?.pending_open_count ?? 0}
        previousValue="-"
        trend={null}
        deltaLabel="distribuição"
        auxiliaryLabel={formatPendingAgeBuckets(metrics?.kpis)}
        baseStyle={kpiBoxStyle}
        showTrend={false}
      />
    ),
    retryReady: (
      <OpsTrendKpiCard label="Retry pronto" value={metrics?.kpis?.pending_due_retry_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
    ),
    processingStale: (
      <OpsTrendKpiCard
        label="PROCESSING stale"
        value={metrics?.kpis?.pending_processing_stale_count ?? 0}
        baseStyle={kpiBoxStyle}
        linkTo={Number(metrics?.kpis?.pending_processing_stale_count || 0) > 0 ? drilldownLinks.reconciliation : null}
        linkTitle="Abrir Nível 2: Reconciliação"
        showTrend={false}
      />
    ),
    failedFinal: (
      <OpsTrendKpiCard
        label="FAILED_FINAL"
        value={metrics?.kpis?.pending_failed_final_count ?? 0}
        baseStyle={getCriticalityCardStyle(
          kpiBoxStyle,
          Number(metrics?.kpis?.pending_failed_final_count || 0) > 0 ? "high" : "normal"
        )}
        linkTo={Number(metrics?.kpis?.pending_failed_final_count || 0) > 0 ? drilldownLinks.reconciliation : null}
        linkTitle="Abrir Nível 2: Reconciliação"
        showTrend={false}
      />
    ),
    unresolvedExceptions: (
      <OpsTrendKpiCard
        label="Exceções não resolvidas"
        value={metrics?.kpis?.unresolved_exceptions_count ?? 0}
        baseStyle={getCriticalityCardStyle(
          kpiBoxStyle,
          Number(metrics?.kpis?.unresolved_exceptions_count || 0) > 0 ? "critical" : "normal"
        )}
        linkTo={Number(metrics?.kpis?.unresolved_exceptions_count || 0) > 0 ? drilldownLinks.evidence : null}
        linkTitle="Abrir Nível 3: Evidências de execução"
        showTrend={false}
      />
    ),
    avgPendingAge: (
      <OpsTrendKpiCard
        label="Idade média pendência (min)"
        value={metrics?.kpis?.avg_open_pending_age_min ?? 0}
        baseStyle={kpiBoxStyle}
        showTrend={false}
      />
    ),
    predictiveFalsePositive: (
      <OpsTrendKpiCard
        label="Falso positivo preditivo (7d)"
        value={`${(Number(metrics?.predictive_monitoring?.false_positive_rate || 0) * 100).toFixed(1)}%`}
        previousValue="-"
        trend={null}
        deltaLabel={`emitidos:${Number(metrics?.predictive_monitoring?.emitted_alerts || 0)}`}
        auxiliaryLabel={`confirmados:${Number(metrics?.predictive_monitoring?.confirmed_alerts || 0)} | falsos:${
          Number(metrics?.predictive_monitoring?.false_positive_alerts || 0)
        }`}
        baseStyle={kpiBoxStyle}
        showTrend={false}
      />
    ),
  };

  const kpiOrderByPersona = {
    ops: [
      "errorRate",
      "absoluteImpact",
      "predictiveFalsePositive",
      "unresolvedExceptions",
      "failedFinal",
      "pendingOpen",
      "pendingAge",
      "retryReady",
      "processingStale",
      "reconciliationActions",
      "autoReconciliationRate",
      "avgReconciliationTime",
      "latency",
      "avgPendingAge",
      "totalActions",
    ],
    dev: [
      "errorRate",
      "absoluteImpact",
      "predictiveFalsePositive",
      "latency",
      "processingStale",
      "retryReady",
      "failedFinal",
      "unresolvedExceptions",
      "reconciliationActions",
      "pendingOpen",
      "avgPendingAge",
      "totalActions",
      "autoReconciliationRate",
      "avgReconciliationTime",
    ],
    gestao: [
      "errorRate",
      "absoluteImpact",
      "predictiveFalsePositive",
      "autoReconciliationRate",
      "avgReconciliationTime",
      "unresolvedExceptions",
      "failedFinal",
      "reconciliationActions",
      "totalActions",
    ],
  };

  const kpiDomainByKey = {
    errorRate: "confiabilidade",
    absoluteImpact: "confiabilidade",
    predictiveFalsePositive: "confiabilidade",
    unresolvedExceptions: "confiabilidade",
    failedFinal: "confiabilidade",
    processingStale: "confiabilidade",
    retryReady: "confiabilidade",
    latency: "confiabilidade",
    reconciliationActions: "reconciliacao",
    autoReconciliationRate: "reconciliacao",
    avgReconciliationTime: "reconciliacao",
    pendingOpen: "reconciliacao",
    pendingAge: "reconciliacao",
    avgPendingAge: "reconciliacao",
    totalActions: "disponibilidade",
  };

  const domainLabels = {
    confiabilidade: "Confiabilidade",
    reconciliacao: "Reconciliação",
    disponibilidade: "Disponibilidade",
  };
  const domainMicroTitles = {
    confiabilidade: "Saúde - erros, risco e qualidade de execução",
    reconciliacao: "Recuperação - tratamento de pendências e exceções",
    disponibilidade: "Tráfego - volume e capacidade operacional",
  };

  const domainHintByPersona = {
    ops: {
      confiabilidade: "Priorização de risco imediato, erro e exceções ativas.",
      reconciliacao: "Foco no backlog operacional e pendências críticas da janela.",
      disponibilidade: "Volume para leitura de carga e estabilidade de operação.",
    },
    dev: {
      confiabilidade: "Diagnóstico técnico de degradação e comportamento da latência.",
      reconciliacao: "Saúde de processamento para investigar gargalos e reprocessos.",
      disponibilidade: "Base de volume para correlação com erro e throughput.",
    },
    gestao: {
      confiabilidade: "Sinal executivo de risco e confiabilidade do serviço.",
      reconciliacao: "Eficiência operacional e automação de reconciliação.",
      disponibilidade: "Capacidade entregue e impacto consolidado da operação.",
    },
  };

  const domainOrder = ["confiabilidade", "reconciliacao", "disponibilidade"];
  const orderedKeys = kpiOrderByPersona[personaView] || kpiOrderByPersona.ops;
  const groupedKpis = domainOrder
    .map((domain) => {
      const keys = orderedKeys.filter((key) => kpiDomainByKey[key] === domain);
      const cards = keys.map((key) => ({ key, card: kpiCardMap[key] })).filter((entry) => Boolean(entry.card));
      return {
        domain,
        label: domainLabels[domain] || domain,
        microTitle: domainMicroTitles[domain] || "",
        hint: domainHintByPersona[personaView]?.[domain] || "",
        cards,
      };
    })
    .filter((group) => group.cards.length > 0);
  const opsSanitySemaphore = resolveOpsSanitySemaphore(opsSanityReport);
  const brScopedSummary = withScopePrefixIfGenericSummary(fiscalGoNoGo?.br?.summary, "BR");
  const ptScopedSummary = withScopePrefixIfGenericSummary(fiscalGoNoGo?.pt?.summary, "PT");

  async function copyRunbook(alertPayload) {
    const text = buildRunbookClipboardText(alertPayload, metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      const normalized = String(alertPayload?.code || "");
      setCopiedRunbookCode(normalized);
      window.setTimeout(() => {
        setCopiedRunbookCode((current) => (current === normalized ? null : current));
      }, 1600);
    } catch (_err) {
      setCopiedRunbookCode(null);
    }
  }

  async function copyRunbookPlain(alertPayload) {
    const text = buildRunbookPlainClipboardText(alertPayload, metrics);
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      const normalized = String(alertPayload?.code || "");
      setCopiedPlainRunbookCode(normalized);
      window.setTimeout(() => {
        setCopiedPlainRunbookCode((current) => (current === normalized ? null : current));
      }, 1600);
    } catch (_err) {
      setCopiedPlainRunbookCode(null);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/reconciliation" style={crossShortcutLinkStyle}>
            Ir para reconciliação
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS - Saúde Operacional"
              versionLabel={OPS_HEALTH_PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              {personaSubtitleByView[personaView]}
            </p>
          </div>
          <div style={toolbarStyle}>
            <label style={labelStyle}>
              Persona
              <select value={personaView} onChange={(event) => setPersonaView(event.target.value)} style={inputStyle}>
                {OPS_HEALTH_PERSONAS.map((persona) => (
                  <option key={persona.value} value={persona.value}>
                    {persona.label}
                  </option>
                ))}
              </select>
            </label>
            <label style={labelStyle}>
              Janela (h)
              <input
                type="number"
                min={1}
                max={168}
                value={lookbackHours}
                onChange={(event) => setLookbackHours(Number(event.target.value || 24))}
                style={inputStyle}
              />
            </label>
            <button type="button" onClick={() => void loadMetrics()} style={buttonGhostStyle} disabled={loading}>
              {loading ? "Atualizando..." : "Atualizar"}
            </button>
            <button type="button" onClick={() => void copyOpsHealthDailySlack()} style={buttonGhostStyle}>
              Copiar daily Slack/Teams
            </button>
          </div>
        </div>
        {dailySlackStatus ? <small style={predictiveReviewStatusStyle}>{dailySlackStatus}</small> : null}

        <div style={presetRowStyle}>
          <span style={presetLabelStyle}>Presets de janela</span>
          {OPS_HEALTH_WINDOW_PRESETS.map((hours) => (
            <button
              key={hours}
              type="button"
              onClick={() => applyWindowPreset(hours)}
              style={presetButtonStyle(lookbackHours === hours)}
            >
              {hours < 24 ? `${hours}h` : hours === 24 ? "24h" : hours === 168 ? "7d" : `${Math.floor(hours / 24)}d`}
            </button>
          ))}
        </div>

        <div style={collectorHealthWrapStyle}>
          <span style={collectorHealthBadgeStyle(collectorHealth.tone)}>{collectorHealth.label}</span>
          {currentErrorRate >= 0.2 ? (
            <div style={criticalBannerStyle}>
              <strong>Alerta crítico no topo:</strong> taxa de erro em {(currentErrorRate * 100).toFixed(1)}% na janela atual (
              {errorActions}/{totalActions}).
            </div>
          ) : null}
        </div>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Última sanidade OPS</h3>
            <button type="button" onClick={() => void loadOpsSanityLatest()} style={buttonGhostStyle} disabled={opsSanityLoading}>
              {opsSanityLoading ? "Atualizando..." : "Atualizar sanidade"}
            </button>
          </div>
          {opsSanityError ? <small style={{ color: "#fecaca" }}>{opsSanityError}</small> : null}
          {opsSanityReport ? (
            <div style={summary24hGridStyle}>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(opsSanityReport.result || "-")}</strong>
                <small style={summary24hLabelStyle}>Resultado</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{Number(opsSanityReport.fail_count || 0)}</strong>
                <small style={summary24hLabelStyle}>Falhas</small>
              </article>
              <article style={{ ...summary24hItemStyle, ...opsSanitySemaphore.style }}>
                <strong style={{ ...summary24hValueStyle, fontSize: 15 }}>{opsSanitySemaphore.label}</strong>
                <small style={{ ...summary24hLabelStyle, color: "inherit" }}>{opsSanitySemaphore.reason}</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(opsSanityReport.generated_at || "-")}</strong>
                <small style={summary24hLabelStyle}>Gerado em (UTC)</small>
              </article>
            </div>
          ) : (
            <small style={summary24hHintStyle}>
              Execute `02_docker/run_ops_sanity.sh --json` para gerar `ops_sanity_latest.json`.
            </small>
          )}
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>FG-1 handoff consolidado (orchestrator latest)</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={() => void loadFg1HandoffLatest()} style={buttonGhostStyle} disabled={fg1HandoffLoading}>
                {fg1HandoffLoading ? "Atualizando..." : "Atualizar handoff consolidado"}
              </button>
              <button type="button" onClick={() => void copyFg1HandoffSlackSummary()} style={buttonGhostStyle} disabled={!fg1HandoffReport}>
                Copiar payload Slack/Teams
              </button>
              <button type="button" onClick={() => void copyFg1HandoffCommand()} style={buttonGhostStyle}>
                Copiar comando orquestrador
              </button>
              <Link to="/fiscal/fg1-gate" style={buttonGhostLinkStyle}>
                Abrir fiscal/fg1-gate
              </Link>
              <Link to="/fiscal/readiness-execution" style={buttonGhostLinkStyle}>
                Abrir fiscal/readiness-execution
              </Link>
            </div>
          </div>
          {fg1HandoffError ? <small style={{ color: "#fecaca" }}>{fg1HandoffError}</small> : null}
          {fg1HandoffCopyStatus ? <small style={summary24hHintStyle}>{fg1HandoffCopyStatus}</small> : null}
          {fg1HandoffReport ? (
            <div style={summary24hGridStyle}>
              <article style={{ ...summary24hItemStyle, ...resolveGateBadgeStyle(fg1HandoffReport.decision) }}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(fg1HandoffReport.decision || "-")}</strong>
                <small style={summary24hLabelStyle}>Decisão consolidada</small>
              </article>
              <article style={{ ...summary24hItemStyle, ...resolveGateBadgeStyle(getCheckStats(fg1HandoffReport).failed === 0 ? "GO" : "NO_GO") }}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>
                  {`${getCheckStats(fg1HandoffReport).passed}/${getCheckStats(fg1HandoffReport).total} checks PASS`}
                </strong>
                <small style={{ ...summary24hLabelStyle, color: "inherit" }}>Checks PASS</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{getCheckStats(fg1HandoffReport).failed}</strong>
                <small style={summary24hLabelStyle}>Checks com falha</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(fg1HandoffReport.generated_at || "-")}</strong>
                <small style={summary24hLabelStyle}>Gerado em (UTC)</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(fg1HandoffReport.result || "-")}</strong>
                <small style={summary24hLabelStyle}>Resultado técnico</small>
              </article>
            </div>
          ) : (
            <small style={summary24hHintStyle}>
              Execute `02_docker/run_fg1_handoff_orchestrator.sh --json` para gerar `fg1_handoff_orchestrator_latest.json`.
            </small>
          )}
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>FG-1 decisão final (handoff latest)</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={() => void loadFg1FinalDecisionLatest()} style={buttonGhostStyle} disabled={fg1FinalDecisionLoading}>
                {fg1FinalDecisionLoading ? "Atualizando..." : "Atualizar handoff FG-1"}
              </button>
              <button type="button" onClick={() => void copyFg1FinalDecisionSlack()} style={buttonGhostStyle} disabled={!fg1FinalDecisionReport}>
                Copiar payload Slack/Teams
              </button>
              <button type="button" onClick={() => void copyFg1TopBlockedTicket()} style={buttonGhostStyle} disabled={!fg1FinalDecisionReport}>
                Copiar ticket imediato FG-1
              </button>
            </div>
          </div>
          {fg1FinalDecisionError ? <small style={{ color: "#fecaca" }}>{fg1FinalDecisionError}</small> : null}
          {fg1FinalDecisionCopyStatus ? <small style={summary24hHintStyle}>{fg1FinalDecisionCopyStatus}</small> : null}
          {fg1FinalDecisionReport ? (
            <div style={summary24hGridStyle}>
              <article style={{ ...summary24hItemStyle, ...resolveGateBadgeStyle(fg1FinalDecisionReport.final_global_decision) }}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(fg1FinalDecisionReport.final_global_decision || "-")}</strong>
                <small style={summary24hLabelStyle}>Decisão global</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{Number(fg1FinalDecisionReport.countries_ready || 0)}</strong>
                <small style={summary24hLabelStyle}>Países aptos</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{Number(fg1FinalDecisionReport.countries_blocked || 0)}</strong>
                <small style={summary24hLabelStyle}>Países bloqueados</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>{String(fg1FinalDecisionReport.generated_at || "-")}</strong>
                <small style={summary24hLabelStyle}>Gerado em (UTC)</small>
              </article>
            </div>
          ) : (
            <small style={summary24hHintStyle}>
              Execute `02_docker/run_fg1_final_handoff_snapshot.sh` para gerar `fg1_final_decision_latest.json`.
            </small>
          )}
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>{FISCAL_SCOPE_GATE_PANEL_TITLE}</h3>
            <button type="button" onClick={() => void loadFiscalGoNoGoSummary()} style={buttonGhostStyle} disabled={fiscalGoNoGoLoading}>
              {fiscalGoNoGoLoading ? "Atualizando..." : "Atualizar gate"}
            </button>
          </div>
          {fiscalGoNoGoError ? <small style={{ color: "#fecaca" }}>{fiscalGoNoGoError}</small> : null}
          {fiscalGoNoGo?.br || fiscalGoNoGo?.pt ? (
            <>
              <div style={summary24hGridStyle}>
              <article style={summary24hItemStyle}>
                <div style={gateTitleRowStyle}>
                  <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>BR</strong>
                  <span style={{ ...gateBadgeStyle, ...resolveGateBadgeStyle(fiscalGoNoGo?.br?.go_no_go) }}>
                    {String(fiscalGoNoGo?.br?.go_no_go || "NO_GO")}
                  </span>
                </div>
                <small style={summary24hLabelStyle} title={brScopedSummary}>
                  {brScopedSummary}
                </small>
                <Link to="/ops/fiscal/providers#go-no-go-br" style={gateDrilldownLinkStyle}>
                  Drill-down BR em 1 clique
                </Link>
              </article>
              <article style={summary24hItemStyle}>
                <div style={gateTitleRowStyle}>
                  <strong style={{ ...summary24hValueStyle, fontSize: 13 }}>PT</strong>
                  <span style={{ ...gateBadgeStyle, ...resolveGateBadgeStyle(fiscalGoNoGo?.pt?.go_no_go) }}>
                    {String(fiscalGoNoGo?.pt?.go_no_go || "NO_GO")}
                  </span>
                </div>
                <small style={summary24hLabelStyle} title={ptScopedSummary}>
                  {ptScopedSummary}
                </small>
                <Link to="/ops/fiscal/providers#go-no-go-pt" style={gateDrilldownLinkStyle}>
                  Drill-down PT em 1 clique
                </Link>
              </article>
              </div>
              <div style={fiscalQuickActionsWrapStyle}>
                <strong style={{ fontSize: 12, color: "#cbd5e1" }}>{FISCAL_SCOPE_QUICK_ACTIONS_TITLE}</strong>
                <div style={fiscalQuickActionsRowStyle}>
                  <button type="button" style={quickActionInfoButtonStyle} onClick={() => void copyFiscalQuickActionCommand("gate_br")}>
                    Copiar comando Gate BR
                  </button>
                  <button type="button" style={quickActionInfoButtonStyle} onClick={() => void copyFiscalQuickActionCommand("gate_pt")}>
                    Copiar comando Gate PT
                  </button>
                  <button type="button" style={quickActionAlertButtonStyle} onClick={() => void copyFiscalQuickActionCommand("rollback_br")}>
                    Copiar rollback BR
                  </button>
                  <button type="button" style={quickActionAlertButtonStyle} onClick={() => void copyFiscalQuickActionCommand("rollback_pt")}>
                    Copiar rollback PT
                  </button>
                </div>
                {fiscalQuickActionStatus ? <small style={summary24hHintStyle}>{fiscalQuickActionStatus}</small> : null}
              </div>
            </>
          ) : (
            <small style={summary24hHintStyle}>Sem snapshot carregado do gate BR/PT.</small>
          )}
        </section>

        <details style={adminConfigDetailsStyle} open={showAdminConfig} onToggle={(event) => setShowAdminConfig(event.currentTarget.open)}>
          <summary style={adminConfigSummaryStyle}>Configurações avançadas (Admin) - calibração preditiva</summary>
          <section style={predictiveTuningSectionStyle}>
          <h3 style={{ margin: 0, fontSize: 14 }}>Rotina semanal - calibração preditiva</h3>
          <div style={predictiveProfileRowStyle}>
            <label style={labelStyle}>
              Perfil de ambiente
              <select value={thresholdProfile} onChange={(event) => setThresholdProfile(event.target.value)} style={inputStyle}>
                <option value="dev">DEV</option>
                <option value="hml">HML</option>
                <option value="prod">PROD</option>
              </select>
            </label>
            <button
              type="button"
              onClick={() => applyThresholdProfile(thresholdProfile)}
              style={buttonGhostStyle}
            >
              Aplicar perfil
            </button>
          </div>
          <div style={predictiveTuningGridStyle}>
            <label style={labelStyle}>
              Volume mínimo
              <input
                type="number"
                min={1}
                max={500}
                value={predictiveMinVolume}
                onChange={(event) => setPredictiveMinVolume(Number(event.target.value || 5))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Erro mínimo (0-1)
              <input
                type="number"
                min={0}
                max={1}
                step={0.01}
                value={predictiveErrorMinRate}
                onChange={(event) => setPredictiveErrorMinRate(Number(event.target.value || 0.05))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Fator aceleração erro
              <input
                type="number"
                min={1}
                max={10}
                step={0.1}
                value={predictiveErrorAccelFactor}
                onChange={(event) => setPredictiveErrorAccelFactor(Number(event.target.value || 1.5))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Latência mínima (ms)
              <input
                type="number"
                min={0}
                max={60000}
                step={10}
                value={predictiveLatencyMinMs}
                onChange={(event) => setPredictiveLatencyMinMs(Number(event.target.value || 100))}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Fator aceleração latência
              <input
                type="number"
                min={1}
                max={10}
                step={0.1}
                value={predictiveLatencyAccelFactor}
                onChange={(event) => setPredictiveLatencyAccelFactor(Number(event.target.value || 1.4))}
                style={inputStyle}
              />
            </label>
          </div>
          <div style={predictiveSnapshotFormStyle}>
            <label style={labelStyle}>
              Decisão semanal
              <select value={snapshotDecision} onChange={(event) => setSnapshotDecision(event.target.value)} style={inputStyle}>
                <option value="KEEP">KEEP</option>
                <option value="INCREASE_SENSITIVITY_GUARDRAILS">INCREASE_SENSITIVITY_GUARDRAILS</option>
                <option value="CAN_INCREASE_SENSITIVITY">CAN_INCREASE_SENSITIVITY</option>
              </select>
            </label>
            <label style={labelStyle}>
              Racional (opcional)
              <input
                type="text"
                value={snapshotRationale}
                onChange={(event) => setSnapshotRationale(event.target.value)}
                placeholder="Resumo da decisão semanal"
                style={longInputStyle}
              />
            </label>
            <button type="button" onClick={() => void savePredictiveSnapshot()} style={buttonGhostStyle} disabled={snapshotSaving}>
              {snapshotSaving ? "Salvando..." : "Salvar snapshot semanal"}
            </button>
            <button type="button" onClick={() => void copyWeeklyExecutionEvidence()} style={copyEvidenceButtonStyle}>
              {snapshotEvidenceCopied ? "Evidência copiada" : "Copiar evidência da execução semanal"}
            </button>
            <button type="button" onClick={() => void copyWeeklyExecutionEvidencePlain()} style={copyEvidencePlainButtonStyle}>
              {snapshotEvidencePlainCopied ? "Texto simples copiado" : "Copiar evidência (texto simples)"}
            </button>
            <button type="button" onClick={() => void copyUs011ClosureBlock()} style={copyEvidencePlainButtonStyle}>
              {snapshotClosureCopied ? "Fechamento copiado" : "Copiar fechamento US-OPS-011"}
            </button>
          </div>
          {snapshotStatus ? <small style={predictiveReviewStatusStyle}>{snapshotStatus}</small> : null}
          <small style={predictiveReviewHintStyle}>
            Revisão semanal sugerida: comparar falso positivo (7d), ajustar thresholds e validar ruído por volume.
          </small>
          {metrics?.predictive_monitoring ? (
            <small style={predictiveReviewStatusStyle}>
              Recomendação automática (7d): {metrics.predictive_monitoring.recommendation || "KEEP"}
            </small>
          ) : null}
          </section>
        </details>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {!error && loading ? (
          <p style={{ marginBottom: 0 }}>Carregando métricas...</p>
        ) : null}

        {!error && !loading && metrics ? (
          <>
            <div style={kpiDomainWrapStyle}>
              {groupedKpis.map((group) => (
                <section key={`kpi-domain-${group.domain}`} style={kpiDomainSectionStyle}>
                  <div style={kpiDomainHeaderStyle}>
                    <h3 style={kpiDomainTitleStyle}>{group.label}</h3>
                    {group.microTitle ? <small style={kpiDomainMicroTitleStyle}>{group.microTitle}</small> : null}
                    {group.hint ? <small style={kpiDomainHintStyle}>{group.hint}</small> : null}
                  </div>
                  <div style={kpiGridStyle}>
                    {group.cards.map((entry) => (
                      <React.Fragment key={`persona-kpi-${personaView}-${entry.key}`}>{entry.card}</React.Fragment>
                    ))}
                  </div>
                </section>
              ))}
            </div>

            <div style={{ marginTop: 10, color: "rgba(245,247,250,0.78)", fontSize: 13 }}>
              Janela: {metrics?.window?.from ? new Date(metrics.window.from).toLocaleString("pt-BR") : "-"} até{" "}
              {metrics?.window?.to ? new Date(metrics.window.to).toLocaleString("pt-BR") : "-"}
            </div>

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Histórico de snapshots semanais (US-OPS-011)</h3>
              {latestPredictiveSnapshot && previousPredictiveSnapshot ? (
                <article style={snapshotComparisonCardStyle}>
                  <strong style={snapshotHistoryTitleStyle}>Comparativo semanal (snapshot atual vs anterior)</strong>
                  <small style={snapshotHistoryMetaStyle}>
                    FP rate: {formatSignedNumber(
                      (Number(latestPredictiveSnapshot.false_positive_rate || 0) - Number(previousPredictiveSnapshot.false_positive_rate || 0)) * 100,
                      1
                    )}
                    p.p. · emitidos:{" "}
                    {formatSignedNumber(
                      Number(latestPredictiveSnapshot.emitted_alerts || 0) - Number(previousPredictiveSnapshot.emitted_alerts || 0),
                      0
                    )}{" "}
                    · confirmados:{" "}
                    {formatSignedNumber(
                      Number(latestPredictiveSnapshot.confirmed_alerts || 0) - Number(previousPredictiveSnapshot.confirmed_alerts || 0),
                      0
                    )}
                  </small>
                </article>
              ) : null}
              {Array.isArray(metrics?.predictive_snapshots) && metrics.predictive_snapshots.length > 0 ? (
                <div style={snapshotHistoryGridStyle}>
                  {metrics.predictive_snapshots.map((item) => (
                    <article key={item.id} style={snapshotHistoryItemStyle}>
                      <strong style={snapshotHistoryTitleStyle}>
                        {String(item.environment || "unknown").toUpperCase()} · {String(item.decision || "KEEP")}
                      </strong>
                      <small style={snapshotHistoryMetaStyle}>
                        {item.created_at ? new Date(item.created_at).toLocaleString("pt-BR") : "-"}
                      </small>
                      <small style={snapshotHistoryMetaStyle}>
                        FP: {(Number(item.false_positive_rate || 0) * 100).toFixed(1)}% · emitidos:{Number(item.emitted_alerts || 0)} · confirmados:
                        {Number(item.confirmed_alerts || 0)}
                      </small>
                    </article>
                  ))}
                </div>
              ) : (
                <small style={predictiveReviewHintStyle}>Nenhum snapshot semanal persistido ainda.</small>
              )}
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Checagem RED (visual/funcional)</h3>
              <div style={redCheckGridStyle}>
                <article style={redCheckItemStyle(redCoverage.rate)}>
                  <strong>Rate</strong>
                  <small>Volume por janela: {totalActions}</small>
                </article>
                <article style={redCheckItemStyle(redCoverage.errors)}>
                  <strong>Errors</strong>
                  <small>Falhas/total: {errorActions}/{totalActions}</small>
                </article>
                <article style={redCheckItemStyle(redCoverage.duration)}>
                  <strong>Duration</strong>
                  <small>Latência p50/p95 ativa (amostras: {currentLatencySamples})</small>
                </article>
              </div>
              <small style={redCheckFooterStyle}>
                Estado RED da janela: {redCoverageOk ? "completo" : "parcial"}.
              </small>
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Tendências da janela ({metrics?.trends?.bucket_minutes || 60}min por ponto)</h3>
              <small style={predictiveHintStyle}>
                Alertas preditivos atuais usam heurística de tendência (sem ML pesado).
              </small>
              <div style={trendGridStyle}>
                <article style={trendCardStyle}>
                  <small style={trendLabelStyle}>Erro (%)</small>
                  <OpsSparkline values={errorRateSeries} stroke="#FCA5A5" />
                </article>
                <article style={trendCardStyle}>
                  <small style={trendLabelStyle}>Volume (ações)</small>
                  <OpsSparkline values={volumeSeries} stroke="#93C5FD" />
                </article>
                <article style={trendCardStyle}>
                  <small style={trendLabelStyle}>Latência p95 (ms)</small>
                  <OpsSparkline values={latencySeries} stroke="#FDE68A" />
                </article>
              </div>
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <div style={lineChartHeaderStyle}>
                <h3 style={{ margin: 0, fontSize: 15 }}>Linha temporal fixa de 24h</h3>
                <div style={lineChartToggleRowStyle}>
                  <small style={lineChartToggleLabelStyle}>Grade:</small>
                  <button
                    type="button"
                    onClick={() => setLineChartGridMode("simple")}
                    style={lineChartToggleButtonStyle(lineChartGridMode === "simple")}
                  >
                    Simplificada
                  </button>
                  <button
                    type="button"
                    onClick={() => setLineChartGridMode("full")}
                    style={lineChartToggleButtonStyle(lineChartGridMode === "full")}
                  >
                    Completa
                  </button>
                </div>
              </div>
              <div style={lineChartGridStyle}>
                <OpsLineChart
                  title="Erro (%)"
                  points={trendPoints24h}
                  valueKey="error_rate"
                  stroke="#FCA5A5"
                  formatter={(v) => `${(Number(v || 0) * 100).toFixed(1)}%`}
                  showDetailedGrid={lineChartGridMode === "full"}
                />
                <OpsLineChart
                  title="Volume (ações)"
                  points={trendPoints24h}
                  valueKey="total_ops_actions"
                  stroke="#93C5FD"
                  formatter={(v) => `${Number(v || 0).toFixed(0)}`}
                  showDetailedGrid={lineChartGridMode === "full"}
                />
                <OpsLineChart
                  title="Latência p95 (ms)"
                  points={trendPoints24h}
                  valueKey="latency_p95_ms"
                  stroke="#FDE68A"
                  formatter={(v) => `${Number(v || 0).toFixed(0)}ms`}
                  showDetailedGrid={lineChartGridMode === "full"}
                />
              </div>
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={drilldownSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Drill-down operacional</h3>
              <p style={drilldownHelpTextStyle}>
                Nível 1: visão geral (esta tela) -&gt; Nível 2: componente/processo -&gt; Nível 3: evidência operacional.
              </p>
              <div style={drilldownActionsStyle}>
                <Link to={drilldownLinks.auditErrors} style={drilldownLinkStyle}>
                  Nível 2: Auditoria de erros
                </Link>
                <Link to={drilldownLinks.reconciliation} style={drilldownLinkStyle}>
                  Nível 2: Reconciliação
                </Link>
                <Link to={drilldownLinks.evidence} style={drilldownLinkStyle}>
                  Nível 3: Evidências de execução
                </Link>
              </div>
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Top 5 erros da janela</h3>
              {topErrors.length === 0 ? (
                <small style={predictiveReviewHintStyle}>
                  {currentErrorRate >= 0.05
                    ? "Sem erros classificados na janela, apesar de taxa de erro relevante. Verifique endpoint de investigação e fallback por mensagens brutas."
                    : "Sem erros classificados na janela selecionada."}
                </small>
              ) : (
                <details open={topErrorsOpen} onToggle={(event) => setTopErrorsOpen(event.currentTarget.open)} style={healthCollapsibleStyle}>
                  <summary style={healthCollapsibleSummaryStyle}>
                    Lista de erros · exibindo {filteredTopErrors.length}/{topErrors.length}
                  </summary>
                  <div style={healthLocalFilterRowStyle}>
                    <label style={healthLocalFilterFieldStyle}>
                      Categoria
                      <input
                        type="text"
                        value={topErrorsCategoryFilter}
                        onChange={(event) => setTopErrorsCategoryFilter(event.target.value)}
                        placeholder="timeout, integracao..."
                        style={healthLocalFilterInputStyle}
                      />
                    </label>
                    <label style={healthLocalFilterFieldStyle}>
                      Limite
                      <input
                        type="number"
                        min={1}
                        max={20}
                        value={topErrorsLimit}
                        onChange={(event) => setTopErrorsLimit(Number(event.target.value || 5))}
                        style={healthLocalFilterNumberStyle}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setTopErrorsCategoryFilter("");
                        setTopErrorsLimit(5);
                      }}
                      style={healthLocalFilterButtonStyle}
                    >
                      Limpar seção
                    </button>
                  </div>
                  <div style={topErrorsListStyle}>
                    {filteredTopErrors.map((item, idx) => (
                      <article key={`top-error-${idx}`} style={topErrorItemStyle}>
                        <strong style={topErrorRankStyle}>#{idx + 1}</strong>
                        <div style={{ display: "grid", gap: 2 }}>
                          <small style={topErrorMessageStyle}>{item?.message || "Erro não classificado"}</small>
                          <small style={topErrorMetaStyle}>
                            {Number(item?.count || 0)} ocorrências ({Number(item?.percentage || 0).toFixed(1)}% dos erros){" "}
                            {item?.category ? `· ${String(item.category).toUpperCase()}` : ""}
                          </small>
                        </div>
                      </article>
                    ))}
                  </div>
                </details>
              )}
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Investigação auditável (US-001)</h3>
              <div style={auditInvestigationHeaderStyle}>
                <small style={predictiveReviewHintStyle}>
                  Total de erros na janela: {Number(errorInvestigationReport?.total_error_actions || 0)}
                </small>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button type="button" onClick={() => void exportErrorInvestigationCsv()} style={copyEvidenceButtonStyle}>
                    Exportar CSV (1 clique)
                  </button>
                  <button type="button" onClick={() => void copyUs001ClosureBlock()} style={copyEvidencePlainButtonStyle}>
                    {us001ClosureCopied ? "Fechamento copiado" : "Copiar fechamento US-001 (seção 19)"}
                  </button>
                </div>
              </div>
              {errorInvestigationStatus ? <small style={predictiveReviewStatusStyle}>{errorInvestigationStatus}</small> : null}
              {investigatedCategories.length > 0 ? (
                <div style={errorCategoryGridStyle}>
                  {investigatedCategories.map((item, idx) => (
                    <article key={`audit-category-${idx}`} style={errorCategoryItemStyle}>
                      <strong style={errorCategoryNameStyle}>{String(item?.category || "OUTROS").toUpperCase()}</strong>
                      <small style={errorCategoryMetaStyle}>
                        {Number(item?.count || 0)} itens · {Number(item?.percentage || 0).toFixed(1)}%
                      </small>
                    </article>
                  ))}
                </div>
              ) : (
                <small style={predictiveReviewHintStyle}>Sem categorias de erro para a janela selecionada.</small>
              )}
              {topInvestigatedCauses.length > 0 ? (
                <div style={topErrorsListStyle}>
                  {topInvestigatedCauses.map((item, idx) => (
                    <article key={`audit-cause-${idx}`} style={topErrorItemStyle}>
                      <strong style={topErrorRankStyle}>#{idx + 1}</strong>
                      <div style={{ display: "grid", gap: 2 }}>
                        <small style={topErrorMessageStyle}>{item?.message || "Erro não classificado"}</small>
                        <small style={topErrorMetaStyle}>
                          {String(item?.category || "OUTROS").toUpperCase()} · {Number(item?.count || 0)} ocorrências ·{" "}
                          {Number(item?.percentage || 0).toFixed(1)}%
                        </small>
                      </div>
                    </article>
                  ))}
                </div>
              ) : null}
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={trendSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Classificação assistida por tipo</h3>
              {classificationCategories.length > 0 ? (
                <details
                  open={classificationOpen}
                  onToggle={(event) => setClassificationOpen(event.currentTarget.open)}
                  style={healthCollapsibleStyle}
                >
                  <summary style={healthCollapsibleSummaryStyle}>
                    Categorias classificadas · exibindo {filteredClassificationCategories.length}/{classificationCategories.length}
                  </summary>
                  <div style={healthLocalFilterRowStyle}>
                    <label style={healthLocalFilterFieldStyle}>
                      Categoria
                      <input
                        type="text"
                        value={classificationCategoryFilter}
                        onChange={(event) => setClassificationCategoryFilter(event.target.value)}
                        placeholder="timeout, validacao..."
                        style={healthLocalFilterInputStyle}
                      />
                    </label>
                    <label style={healthLocalFilterFieldStyle}>
                      Limite
                      <input
                        type="number"
                        min={1}
                        max={20}
                        value={classificationLimit}
                        onChange={(event) => setClassificationLimit(Number(event.target.value || 6))}
                        style={healthLocalFilterNumberStyle}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setClassificationCategoryFilter("");
                        setClassificationLimit(6);
                      }}
                      style={healthLocalFilterButtonStyle}
                    >
                      Limpar seção
                    </button>
                  </div>
                  <div style={errorCategoryGridStyle}>
                    {filteredClassificationCategories.map((item, idx) => (
                      <article key={`error-category-${idx}`} style={errorCategoryItemStyle}>
                        <strong style={errorCategoryNameStyle}>{String(item?.category || "OUTROS").toUpperCase()}</strong>
                        <small style={errorCategoryMetaStyle}>
                          {Number(item?.count || 0)} itens · {Number(item?.percentage || 0).toFixed(1)}%
                        </small>
                      </article>
                    ))}
                  </div>
                </details>
              ) : (
                <small style={predictiveReviewHintStyle}>Sem erros na janela para classificação assistida.</small>
              )}
            </section>
            ) : null}

            <section style={severityMatrixSectionStyle}>
              <div style={auditInvestigationHeaderStyle}>
                <h3 style={{ margin: 0, fontSize: 15 }}>Matriz SLA/canal por severidade (US-OPS-002)</h3>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button type="button" onClick={() => void copyUs002Evidence()} style={copyEvidenceButtonStyle}>
                    {us002EvidenceCopied ? "Evidência copiada" : "Copiar evidência US-OPS-002"}
                  </button>
                  <button type="button" onClick={() => void copyUs002SprintDocBlock()} style={copyEvidencePlainButtonStyle}>
                    {us002DocCopied ? "Bloco de sprint copiado" : "Copiar para seção US-OPS-002"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void copyTopLockerImmediateTicket(topLockerCritical24h)}
                    style={copyEvidencePlainButtonStyle}
                  >
                    {us002TopTicketCopied ? "Ticket copiado" : "Copiar ticket de ação imediata"}
                  </button>
                </div>
              </div>
              {us002EvidenceStatus ? <small style={predictiveReviewStatusStyle}>{us002EvidenceStatus}</small> : null}
              {topLockerCritical24h ? (
                <article style={topLockerCardStyle}>
                  <div style={severityMatrixHeaderStyle}>
                    <strong style={{ fontSize: 13 }}>Top 1 locker crítico (24h)</strong>
                    <span style={getSeverityBadgeStyle(topLockerCritical24h.expectedSeverity24h)}>
                      {topLockerCritical24h.expectedSeverity24h}
                    </span>
                  </div>
                  <small style={severityMatrixMetaStyle}>
                    {topLockerCritical24h.lockerId} · erros/total: {topLockerCritical24h.errorActions24h}/{topLockerCritical24h.totalActions24h} (
                    {(topLockerCritical24h.errorRate24h * 100).toFixed(2)}%)
                  </small>
                  <small style={severityMatrixMetaStyle}>
                    Taxa global 24h: {(topLockerCritical24h.globalRate24h * 100).toFixed(2)}% · delta:{" "}
                    {topLockerCritical24h.deltaVsGlobalPp >= 0 ? "+" : ""}
                    {topLockerCritical24h.deltaVsGlobalPp.toFixed(2)} p.p.
                  </small>
                </article>
              ) : (
                <div style={lockerFallbackStyle}>
                  <small style={predictiveReviewHintStyle}>
                    {lockerDataStatus === "unavailable"
                      ? "Dados de locker indisponíveis. Verifique endpoint /dev-admin/ops-audit e autenticação da sessão."
                      : "Sem dados por locker nas últimas 24h para cálculo de criticidade."}
                  </small>
                  <small style={predictiveReviewHintStyle}>
                    Referência rápida: valide também a trilha em <Link to="/ops/audit" style={lockerFallbackLinkStyle}>ops/audit</Link>.
                  </small>
                </div>
              )}
              <div style={severityMatrixGridStyle}>
                {OPS_SEVERITY_SLA_MATRIX.map((row) => (
                  <article key={row.severityKey} style={severityMatrixItemStyle(row.severityKey)}>
                    <div style={severityMatrixHeaderStyle}>
                      <span style={getSeverityBadgeStyle(row.severityKey)}>{row.severityLabel}</span>
                      <small style={severityMatrixCountStyle(row.severityKey)}>
                        Ativos: {Number(alertCountBySeverity[row.severityKey] || 0)}
                      </small>
                    </div>
                    <small style={severityMatrixMetaStyle}>SLA: {row.responseSla}</small>
                    <small style={severityMatrixMetaStyle}>Canal: {row.channel}</small>
                    <small style={severityMatrixMetaStyle}>Owner sugerido: {row.owner}</small>
                  </article>
                ))}
              </div>
              {lockerSeverityRows.length > 0 ? (
                <div style={lockerSeverityTableWrapStyle}>
                  <table style={lockerSeverityTableStyle}>
                    <thead>
                      <tr>
                        <th style={lockerSeverityThStyle}>Locker</th>
                        <th style={lockerSeverityThStyle}>Severidade 24h</th>
                        <th style={lockerSeverityThStyle}>Erros/Total</th>
                        <th style={lockerSeverityThStyle}>Taxa locker</th>
                        <th style={lockerSeverityThStyle}>Taxa global</th>
                        <th style={lockerSeverityThStyle}>Delta vs global</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lockerSeverityRows.map((row) => (
                        <tr key={row.lockerId}>
                          <td style={lockerSeverityTdStyle}>{row.lockerId}</td>
                          <td style={lockerSeverityTdStyle}>
                            <span style={getSeverityBadgeStyle(row.expectedSeverity24h)}>{row.expectedSeverity24h}</span>
                          </td>
                          <td style={lockerSeverityTdStyle}>
                            {row.errorActions24h}/{row.totalActions24h}
                          </td>
                          <td style={lockerSeverityTdStyle}>{(row.errorRate24h * 100).toFixed(2)}%</td>
                          <td style={lockerSeverityTdStyle}>{(row.globalRate24h * 100).toFixed(2)}%</td>
                          <td style={lockerSeverityTdStyle}>
                            {row.deltaVsGlobalPp >= 0 ? "+" : ""}
                            {row.deltaVsGlobalPp.toFixed(2)} p.p.
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={lockerFallbackStyle}>
                  <small style={predictiveReviewHintStyle}>
                    {lockerDataStatus === "unavailable"
                      ? "Tabela por locker indisponível: endpoint ops-audit sem payload utilizável."
                      : "Tabela por locker sem linhas na janela atual (24h)."}
                  </small>
                </div>
              )}
              <small style={predictiveReviewHintStyle}>
                Evidência pronta para anexar em auditoria/DoD do US-OPS-002 com snapshot da janela atual.
              </small>
            </section>

            <div style={alertsWrapStyle}>
              {activeAlerts.length === 0 ? (
                <span style={getSeverityBadgeStyle("OK")}>Sem alertas ativos</span>
              ) : (
                <details open={alertsOpen} onToggle={(event) => setAlertsOpen(event.currentTarget.open)} style={healthCollapsibleStyle}>
                  <summary style={healthCollapsibleSummaryStyle}>
                    Alertas ativos · exibindo {filteredActiveAlerts.length}/{activeAlerts.length}
                  </summary>
                  <div style={healthLocalFilterRowStyle}>
                    <label style={healthLocalFilterFieldStyle}>
                      Severidade
                      <select
                        value={alertsSeverityFilter}
                        onChange={(event) => setAlertsSeverityFilter(event.target.value)}
                        style={healthLocalFilterInputStyle}
                      >
                        <option value="">Todas</option>
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                    </label>
                    <label style={healthLocalFilterFieldStyle}>
                      Código
                      <input
                        type="text"
                        value={alertsCodeFilter}
                        onChange={(event) => setAlertsCodeFilter(event.target.value)}
                        placeholder="OPS_, PENDING..."
                        style={healthLocalFilterInputStyle}
                      />
                    </label>
                    <label style={healthLocalFilterFieldStyle}>
                      Limite
                      <input
                        type="number"
                        min={1}
                        max={100}
                        value={alertsLimit}
                        onChange={(event) => setAlertsLimit(Number(event.target.value || 20))}
                        style={healthLocalFilterNumberStyle}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setAlertsSeverityFilter("");
                        setAlertsCodeFilter("");
                        setAlertsLimit(20);
                      }}
                      style={healthLocalFilterButtonStyle}
                    >
                      Limpar seção
                    </button>
                  </div>
                {filteredActiveAlerts.map((alert, index) => (
                  <article key={`${alert.code}-${index}`} style={alertCardStyle}>
                    {(() => {
                      const alertCode = String(alert.code || "");
                      const isRunbookOpen = openRunbookCode === alertCode;
                      const isRunbookCopied = copiedRunbookCode === alertCode;
                      const isPlainRunbookCopied = copiedPlainRunbookCode === alertCode;
                      return (
                        <>
                    <div style={alertHeaderStyle}>
                      <span style={getSeverityBadgeStyle(alert.severity)}>
                        {String(alert.severity || "INFO").toUpperCase()}
                      </span>
                      <strong style={{ fontSize: 13 }}>{alert.code}</strong>
                    </div>
                    <p style={alertMessageStyle}>{alert.message}</p>
                    {alert.impact ? <p style={alertSubLineStyle}>Impacto: {alert.impact}</p> : null}
                    {alert.mitigation_hint ? (
                      <p style={alertSubLineStyle}>Ação recomendada: {alert.mitigation_hint}</p>
                    ) : null}
                    {(alert.confidence_level || alert.data_quality_flag) ? (
                      <div style={alertMetaBadgesStyle}>
                        {alert.confidence_level ? (
                          <span style={getConfidenceBadgeStyle(alert.confidence_level)}>
                            confiança: {String(alert.confidence_level).toUpperCase()}
                          </span>
                        ) : null}
                        {alert.data_quality_flag ? (
                          <span style={getDataQualityFlagStyle(alert.data_quality_flag)}>
                            dados: {String(alert.data_quality_flag).toUpperCase()}
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                    <div style={alertActionsRowStyle}>
                      <small style={alertHintStyle}>
                        {alert.investigate_hint || "Abrir trilha de auditoria para análise detalhada."}
                      </small>
                      <div style={alertButtonsRowStyle}>
                        <button
                          type="button"
                          onClick={() => setOpenRunbookCode((current) => (current === alertCode ? null : alertCode))}
                          style={runbookButtonStyle}
                        >
                          {isRunbookOpen ? "Fechar Runbook" : "Abrir Runbook"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void copyRunbook({ ...alert, code: alertCode })}
                          style={copyRunbookButtonStyle}
                        >
                          {isRunbookCopied ? "Runbook copiado" : "Copiar runbook"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void copyRunbookPlain({ ...alert, code: alertCode })}
                          style={copyRunbookPlainButtonStyle}
                        >
                          {isPlainRunbookCopied ? "Ticket simples copiado" : "Copiar ticket (texto simples)"}
                        </button>
                        <Link to={resolveAlertInvestigateLink(alert, metrics, lookbackHours)} style={investigateLinkStyle}>
                          Investigar
                        </Link>
                      </div>
                    </div>
                    {isRunbookOpen ? (
                      <section style={runbookPanelStyle}>
                        <strong style={{ fontSize: 12 }}>{getRunbookByAlertCode(alert.code).title}</strong>
                        <small style={runbookOwnerStyle}>Owner sugerido: {getRunbookByAlertCode(alert.code).owner}</small>
                        <ol style={runbookListStyle}>
                          {getRunbookByAlertCode(alert.code).steps.map((step, idx) => (
                            <li key={`${alert.code}-runbook-step-${idx}`}>{step}</li>
                          ))}
                        </ol>
                      </section>
                    ) : null}
                        </>
                      );
                    })()}
                  </article>
                ))}
                </details>
              )}
            </div>
          </>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const longInputStyle = {
  width: 280,
  maxWidth: "100%",
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const buttonGhostLinkStyle = {
  ...buttonGhostStyle,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  textDecoration: "none",
};

const healthCollapsibleStyle = {
  marginTop: 8,
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(2,6,23,0.24)",
  padding: 8,
};

const healthCollapsibleSummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 13,
  fontWeight: 700,
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const healthLocalFilterNumberStyle = {
  ...healthLocalFilterInputStyle,
};

const healthLocalFilterButtonStyle = {
  ...buttonGhostStyle,
  height: 36,
  fontSize: 12,
  border: "1px solid rgba(248,113,113,0.55)",
  color: "#fecaca",
  background: "rgba(127,29,29,0.2)",
};

const presetRowStyle = {
  marginTop: 10,
  display: "flex",
  flexWrap: "wrap",
  alignItems: "center",
  gap: 8,
};

const presetLabelStyle = {
  color: "rgba(245,247,250,0.72)",
  fontSize: 12,
  marginRight: 2,
};

const collectorHealthWrapStyle = {
  marginTop: 10,
  display: "grid",
  gap: 8,
};

const collectorHealthBadgeStyle = (tone) => ({
  display: "inline-flex",
  width: "fit-content",
  padding: "6px 10px",
  borderRadius: 999,
  border:
    tone === "ok"
      ? "1px solid rgba(74,222,128,0.55)"
      : "1px solid rgba(251,191,36,0.55)",
  background:
    tone === "ok"
      ? "rgba(22,101,52,0.22)"
      : "rgba(120,53,15,0.26)",
  color: tone === "ok" ? "#bbf7d0" : "#fde68a",
  fontSize: 12,
  fontWeight: 700,
});

const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
};

const summary24hItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const summary24hValueStyle = {
  color: "#f8fafc",
  fontSize: 18,
  fontWeight: 800,
};

const summary24hLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const gateTitleRowStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 8,
};

const gateBadgeStyle = {
  borderRadius: 999,
  padding: "3px 9px",
  fontSize: 11,
  fontWeight: 700,
};

const gateDrilldownLinkStyle = {
  marginTop: 8,
  width: "fit-content",
  color: "#93c5fd",
  textDecoration: "underline",
  fontSize: 12,
  fontWeight: 600,
};

const fiscalQuickActionsWrapStyle = {
  marginTop: 10,
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(2,6,23,0.24)",
  padding: 10,
  display: "grid",
  gap: 8,
};

const fiscalQuickActionsRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const quickActionInfoButtonStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(30,64,175,0.2)",
  color: "#bfdbfe",
};

const quickActionAlertButtonStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(248,113,113,0.65)",
  background: "rgba(127,29,29,0.28)",
  color: "#fecaca",
};

const adminConfigDetailsStyle = {
  marginTop: 8,
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.28)",
  padding: 8,
};

const adminConfigSummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 13,
  fontWeight: 700,
};

const presetButtonStyle = (active) => ({
  padding: "6px 10px",
  borderRadius: 999,
  border: active ? "1px solid rgba(29,78,216,0.95)" : "1px solid rgba(255,255,255,0.14)",
  background: active ? "rgba(29,78,216,0.22)" : "#0b0f14",
  color: active ? "#bfdbfe" : "#e2e8f0",
  fontWeight: 700,
  cursor: "pointer",
});

const predictiveTuningSectionStyle = {
  marginTop: 12,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
  display: "grid",
  gap: 8,
};

const predictiveTuningGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 8,
};

const predictiveProfileRowStyle = {
  display: "flex",
  gap: 8,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const predictiveSnapshotFormStyle = {
  display: "flex",
  gap: 8,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const copyEvidenceButtonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(134,239,172,0.55)",
  background: "rgba(22,101,52,0.18)",
  color: "#dcfce7",
  cursor: "pointer",
  fontWeight: 700,
};

const copyEvidencePlainButtonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(125,211,252,0.55)",
  background: "rgba(14,116,144,0.16)",
  color: "#bae6fd",
  cursor: "pointer",
  fontWeight: 700,
};

const predictiveReviewHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const predictiveReviewStatusStyle = {
  color: "#e2e8f0",
  fontSize: 12,
  fontWeight: 700,
};

const kpiGridStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
};

const kpiDomainWrapStyle = {
  marginTop: 14,
  display: "grid",
  gap: 12,
};

const kpiDomainSectionStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 10,
  display: "grid",
  gap: 8,
};

const kpiDomainHeaderStyle = {
  display: "grid",
  gap: 2,
};

const kpiDomainTitleStyle = {
  margin: 0,
  fontSize: 13,
  fontWeight: 800,
  color: "#BFDBFE",
  letterSpacing: 0.2,
  textTransform: "uppercase",
};

const kpiDomainMicroTitleStyle = {
  color: "rgba(226,232,240,0.95)",
  fontSize: 11,
  fontWeight: 700,
  textTransform: "none",
};

const kpiDomainHintStyle = {
  color: "rgba(203,213,225,0.9)",
  fontSize: 11,
  fontWeight: 600,
};

const kpiBoxStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: "10px 12px",
  display: "grid",
  gap: 4,
};

const alertsWrapStyle = {
  marginTop: 12,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
};

const trendSectionStyle = {
  marginTop: 14,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const severityMatrixSectionStyle = {
  marginTop: 14,
  borderRadius: 12,
  border: "1px solid rgba(186,230,253,0.42)",
  background: "rgba(14,116,144,0.11)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const severityMatrixGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
};

const severityMatrixItemStyle = (severity) => {
  const surface = getSeveritySurfaceStyle(severity);
  return {
    borderRadius: 10,
    border: surface.border,
    background: surface.background,
    padding: 10,
    display: "grid",
    gap: 4,
  };
};

const topLockerCardStyle = {
  borderRadius: 10,
  border: "1px solid rgba(251,191,36,0.45)",
  background: "rgba(120,53,15,0.2)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const severityMatrixHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
};

const severityMatrixCountStyle = (severity) => {
  const token = getSeverityBadgeStyle(severity);
  return {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "4px 10px",
    borderRadius: 999,
    border: token.border,
    background: "rgba(2,6,23,0.45)",
    color: "#ffffff",
    fontSize: 11,
    fontWeight: 800,
    minWidth: 90,
  };
};

const severityMatrixMetaStyle = {
  color: "#e2e8f0",
  fontSize: 12,
};

const lockerSeverityTableWrapStyle = {
  overflowX: "auto",
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.35)",
};

const lockerSeverityTableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  minWidth: 760,
  background: "rgba(15,23,42,0.28)",
};

const lockerSeverityThStyle = {
  textAlign: "left",
  fontSize: 12,
  color: "#bfdbfe",
  padding: "8px 10px",
  borderBottom: "1px solid rgba(148,163,184,0.35)",
  whiteSpace: "nowrap",
};

const lockerSeverityTdStyle = {
  fontSize: 12,
  color: "#e2e8f0",
  padding: "8px 10px",
  borderBottom: "1px solid rgba(148,163,184,0.2)",
  whiteSpace: "nowrap",
};

const lockerFallbackStyle = {
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.24)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const lockerFallbackLinkStyle = {
  color: "#93c5fd",
  fontWeight: 700,
  textDecoration: "none",
};

const trendGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 10,
};

const lineChartGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  gap: 10,
};

const lineChartHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const lineChartToggleRowStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  flexWrap: "wrap",
};

const lineChartToggleLabelStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 12,
  fontWeight: 700,
};

const lineChartToggleButtonStyle = (active) => ({
  padding: "4px 10px",
  borderRadius: 999,
  border: active ? "1px solid rgba(147,197,253,0.95)" : "1px solid rgba(148,163,184,0.45)",
  background: active ? "rgba(30,64,175,0.45)" : "rgba(15,23,42,0.34)",
  color: active ? "#dbeafe" : "#cbd5e1",
  fontSize: 12,
  fontWeight: 700,
  cursor: "pointer",
});

const lineChartCardStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.26)",
  background: "linear-gradient(180deg, rgba(15,23,42,0.44) 0%, rgba(15,23,42,0.24) 100%)",
  padding: 10,
  display: "grid",
  gap: 8,
  minHeight: 222,
};

const lineChartMetaStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 8,
  flexWrap: "wrap",
};

const lineChartValueStyle = {
  color: "#F8FAFC",
  fontSize: 12,
  fontWeight: 700,
};

const lineChartLabelsStyle = {
  display: "flex",
  justifyContent: "space-between",
  color: "rgba(203,213,225,0.92)",
  fontSize: 11,
};

const topErrorsListStyle = {
  display: "grid",
  gap: 8,
};

const topErrorItemStyle = {
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(15,23,42,0.32)",
  padding: "8px 10px",
  display: "grid",
  gridTemplateColumns: "28px 1fr",
  gap: 8,
  alignItems: "start",
};

const topErrorRankStyle = {
  color: "#FCA5A5",
  fontSize: 12,
};

const topErrorMessageStyle = {
  color: "#E2E8F0",
  fontSize: 12,
  fontWeight: 700,
  lineHeight: 1.3,
};

const topErrorMetaStyle = {
  color: "#CBD5E1",
  fontSize: 11,
};

const redCheckGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: 8,
};

const redCheckItemStyle = (ok) => ({
  borderRadius: 10,
  border: ok ? "1px solid rgba(74,222,128,0.55)" : "1px solid rgba(248,113,113,0.65)",
  background: ok ? "rgba(22,101,52,0.20)" : "rgba(127,29,29,0.24)",
  padding: "8px 10px",
  display: "grid",
  gap: 3,
  color: "#E2E8F0",
});

const redCheckFooterStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
  fontWeight: 700,
};

const errorCategoryGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
  gap: 8,
};

const errorCategoryItemStyle = {
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.28)",
  padding: "8px 10px",
  display: "grid",
  gap: 3,
};

const errorCategoryNameStyle = {
  fontSize: 12,
  color: "#F8FAFC",
};

const errorCategoryMetaStyle = {
  fontSize: 11,
  color: "#CBD5E1",
};

const auditInvestigationHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const snapshotHistoryGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
};

const snapshotHistoryItemStyle = {
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.28)",
  padding: "8px 10px",
  display: "grid",
  gap: 3,
};

const snapshotComparisonCardStyle = {
  borderRadius: 8,
  border: "1px solid rgba(96,165,250,0.45)",
  background: "rgba(30,58,138,0.18)",
  padding: "8px 10px",
  display: "grid",
  gap: 3,
};

const snapshotHistoryTitleStyle = {
  fontSize: 12,
  color: "#E2E8F0",
};

const snapshotHistoryMetaStyle = {
  fontSize: 11,
  color: "#CBD5E1",
};

const trendCardStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(15,23,42,0.2)",
  padding: 8,
  display: "grid",
  gap: 6,
};

const trendLabelStyle = {
  color: "#CBD5E1",
  fontSize: 12,
  fontWeight: 700,
};

const predictiveHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
  fontWeight: 600,
  display: "inline-block",
  padding: "4px 8px",
  borderRadius: 999,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(30,58,138,0.24)",
};

const drilldownSectionStyle = {
  marginTop: 12,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
  display: "grid",
  gap: 8,
};

const drilldownHelpTextStyle = {
  margin: 0,
  color: "rgba(203,213,225,0.95)",
  fontSize: 12,
};

const drilldownActionsStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const drilldownLinkStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 12,
};

const alertCardStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(255,255,255,0.03)",
  padding: 12,
  display: "grid",
  gap: 8,
};

const alertHeaderStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 8,
};

const alertMessageStyle = {
  margin: 0,
  fontSize: 13,
  color: "#e2e8f0",
};

const alertSubLineStyle = {
  margin: 0,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const alertMetaBadgesStyle = {
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
};

const alertActionsRowStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 10,
  flexWrap: "wrap",
};

const alertButtonsRowStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
};

const alertHintStyle = {
  fontSize: 11,
  color: "rgba(148,163,184,1)",
};

const runbookButtonStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(245,158,11,0.55)",
  background: "rgba(245,158,11,0.12)",
  color: "#fde68a",
  cursor: "pointer",
  fontWeight: 700,
  fontSize: 12,
};

const copyRunbookButtonStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(125,211,252,0.55)",
  background: "rgba(14,116,144,0.16)",
  color: "#bae6fd",
  cursor: "pointer",
  fontWeight: 700,
  fontSize: 12,
};

const copyRunbookPlainButtonStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(134,239,172,0.55)",
  background: "rgba(22,101,52,0.18)",
  color: "#dcfce7",
  cursor: "pointer",
  fontWeight: 700,
  fontSize: 12,
};

const investigateLinkStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 12,
};

const runbookPanelStyle = {
  marginTop: 4,
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.55)",
  padding: "10px 12px",
  display: "grid",
  gap: 6,
};

const runbookOwnerStyle = {
  fontSize: 11,
  color: "rgba(148,163,184,1)",
};

const runbookListStyle = {
  margin: 0,
  paddingLeft: 18,
  color: "#e2e8f0",
  fontSize: 12,
  display: "grid",
  gap: 4,
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

