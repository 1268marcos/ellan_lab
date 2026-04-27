import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import { getDataQualityFlagStyle, getSeverityBadgeStyle, getConfidenceBadgeStyle } from "../components/opsVisualTokens";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const OPS_HEALTH_WINDOW_PREF_KEY = "ops_health:window_hours";
const OPS_HEALTH_PERSONA_PREF_KEY = "ops_health:persona";
const OPS_HEALTH_WINDOW_PRESETS = [1, 6, 12, 24, 48, 72, 168];
const OPS_HEALTH_PERSONAS = [
  { value: "ops", label: "Ops" },
  { value: "dev", label: "Dev" },
  { value: "gestao", label: "Gestão" },
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

function OpsLineChart({ title, points, valueKey, stroke = "#93C5FD", formatter = (v) => String(v) }) {
  const width = 460;
  const height = 160;
  const padding = 20;
  const values = (Array.isArray(points) ? points : []).map((point) => Number(point?.[valueKey] || 0));
  const labels = (Array.isArray(points) ? points : []).map((point) => String(point?.bucket_start || ""));
  const path = buildSparklinePath(values, width, height, padding);
  const noData = values.length === 0;
  const allZero = values.length > 0 && values.every((value) => value === 0);
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
        {path ? <path d={path} fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" /> : null}
        {(noData || allZero) ? <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="rgba(148,163,184,0.55)" strokeDasharray="6 4" /> : null}
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [predictiveMinVolume, setPredictiveMinVolume] = useState(5);
  const [predictiveErrorMinRate, setPredictiveErrorMinRate] = useState(0.05);
  const [predictiveErrorAccelFactor, setPredictiveErrorAccelFactor] = useState(1.5);
  const [predictiveLatencyMinMs, setPredictiveLatencyMinMs] = useState(100);
  const [predictiveLatencyAccelFactor, setPredictiveLatencyAccelFactor] = useState(1.4);
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
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    void loadMetrics();
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

  const previousKpis = metrics?.comparison?.kpis || {};
  const currentErrorRate = Number(metrics?.kpis?.error_rate || 0);
  const previousErrorRate = Number(previousKpis?.error_rate || 0);
  const currentP50 = Number(metrics?.kpis?.latency_p50_ms || 0);
  const currentP95 = Number(metrics?.kpis?.latency_p95_ms || 0);
  const previousP50 = Number(previousKpis?.latency_p50_ms || 0);
  const previousP95 = Number(previousKpis?.latency_p95_ms || 0);
  const currentLatencySamples = Number(metrics?.kpis?.latency_samples || 0);
  const trendPoints = Array.isArray(metrics?.trends?.points) ? metrics.trends.points : [];
  const trendPoints24h = Array.isArray(metrics24h?.trends?.points) ? metrics24h.trends.points : [];
  const drilldownLinks = buildDrilldownLinks(metrics, lookbackHours);
  const errorRateSeries = trendPoints.map((point) => Number(point?.error_rate || 0) * 100);
  const volumeSeries = trendPoints.map((point) => Number(point?.total_ops_actions || 0));
  const latencySeries = trendPoints.map((point) => Number(point?.latency_p95_ms || 0));
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

  const kpiCardMap = {
    totalActions: (
      <OpsTrendKpiCard label="Ações OPS" value={metrics?.kpis?.total_ops_actions ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
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
        hint: domainHintByPersona[personaView]?.[domain] || "",
        cards,
      };
    })
    .filter((group) => group.cards.length > 0);

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
            <h1 style={{ margin: 0 }}>OPS - Saúde Operacional</h1>
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
          </div>
        </div>

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

        <section style={predictiveTuningSectionStyle}>
          <h3 style={{ margin: 0, fontSize: 14 }}>Rotina semanal - calibração preditiva</h3>
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
          <small style={predictiveReviewHintStyle}>
            Revisão semanal sugerida: comparar falso positivo (7d), ajustar thresholds e validar ruído por volume.
          </small>
          {metrics?.predictive_monitoring ? (
            <small style={predictiveReviewStatusStyle}>
              Recomendação automática (7d): {metrics.predictive_monitoring.recommendation || "KEEP"}
            </small>
          ) : null}
        </section>

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
              <h3 style={{ margin: 0, fontSize: 15 }}>Linha temporal fixa de 24h</h3>
              <div style={lineChartGridStyle}>
                <OpsLineChart
                  title="Erro (%)"
                  points={trendPoints24h}
                  valueKey="error_rate"
                  stroke="#FCA5A5"
                  formatter={(v) => `${(Number(v || 0) * 100).toFixed(1)}%`}
                />
                <OpsLineChart
                  title="Volume (ações)"
                  points={trendPoints24h}
                  valueKey="total_ops_actions"
                  stroke="#93C5FD"
                  formatter={(v) => `${Number(v || 0).toFixed(0)}`}
                />
                <OpsLineChart
                  title="Latência p95 (ms)"
                  points={trendPoints24h}
                  valueKey="latency_p95_ms"
                  stroke="#FDE68A"
                  formatter={(v) => `${Number(v || 0).toFixed(0)}ms`}
                />
              </div>
            </section>
            ) : null}

            {(isOpsPersona || isDevPersona) ? (
            <section style={drilldownSectionStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Drill-down operacional</h3>
              <p style={drilldownHelpTextStyle}>
                Nível 1: visão geral (esta tela) -> Nível 2: componente/processo -> Nível 3: evidência operacional.
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

            <div style={alertsWrapStyle}>
              {(metrics?.alerts || []).length === 0 ? (
                <span style={getSeverityBadgeStyle("OK")}>Sem alertas ativos</span>
              ) : (
                (metrics?.alerts || []).map((alert, index) => (
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
                ))
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

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
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

