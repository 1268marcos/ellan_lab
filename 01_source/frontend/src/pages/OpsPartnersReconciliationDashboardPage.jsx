import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsActionButton from "../components/OpsActionButton";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const OPS_RECON_DASHBOARD_VERSION = "ops/partners/reconciliation-dashboard v1.0.0-sprint12";
const WINDOW_PRESETS = [
  { id: "1h", label: "1h", hours: 1 },
  { id: "6h", label: "6h", hours: 6 },
  { id: "24h", label: "24h", hours: 24 },
  { id: "7d", label: "7d", hours: 24 * 7 },
  { id: "30d", label: "30d", hours: 24 * 30 },
];

function toDateTimeLocalInputValue(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${d}T${hh}:${mm}`;
}

function toIsoOrNull(localDateTimeValue) {
  const raw = String(localDateTimeValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function parseError(payload, fallback = "Falha ao consultar dashboard de reconciliação.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsPartnersReconciliationDashboardPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [partnerId, setPartnerId] = useState("");
  const [topN, setTopN] = useState("10");
  const [minSeverity, setMinSeverity] = useState("MEDIUM");
  const now = new Date();
  const defaultFrom = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const [fromDateTime, setFromDateTime] = useState(toDateTimeLocalInputValue(defaultFrom));
  const [toDateTime, setToDateTime] = useState(toDateTimeLocalInputValue(now));
  const [selectedPreset, setSelectedPreset] = useState("24h");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [compare, setCompare] = useState(null);
  const [top, setTop] = useState(null);
  const [copyStatus, setCopyStatus] = useState("");
  const [inboundExpanded, setInboundExpanded] = useState(false);
  const [runbookOpen, setRunbookOpen] = useState(false);
  const [runbookCopied, setRunbookCopied] = useState(false);
  const [runbookPlainCopied, setRunbookPlainCopied] = useState(false);
  const [timeSeries, setTimeSeries] = useState([]);
  const [chartGrade, setChartGrade] = useState("complete");
  const [selectedHeatmapWindowKey, setSelectedHeatmapWindowKey] = useState("");

  async function loadDashboard(overrides = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const commonParams = new URLSearchParams();
      const pid = String(partnerId || "").trim();
      const effectiveFrom = overrides?.fromDateTime ?? fromDateTime;
      const effectiveTo = overrides?.toDateTime ?? toDateTime;
      const fromIso = toIsoOrNull(effectiveFrom);
      const toIso = toIsoOrNull(effectiveTo);
      if (!fromIso || !toIso) throw new Error("Preencha from/to com data e hora válidas.");
      if (pid) commonParams.set("partner_id", pid);
      commonParams.set("from", fromIso);
      commonParams.set("to", toIso);

      const compareResp = await fetch(
        `${ORDER_PICKUP_BASE}/partners/ops/settlements/reconciliation/compare?${commonParams.toString()}`,
        { headers: { Accept: "application/json", ...authHeaders } }
      );
      const compareJson = await compareResp.json().catch(() => ({}));
      if (!compareResp.ok) throw new Error(parseError(compareJson));

      const topParams = new URLSearchParams(commonParams);
      topParams.set("top_n", String(Number(topN || 10) || 10));
      if (String(minSeverity || "").trim()) topParams.set("min_severity", String(minSeverity).trim().toUpperCase());

      const topResp = await fetch(
        `${ORDER_PICKUP_BASE}/partners/ops/settlements/reconciliation/top-divergences?${topParams.toString()}`,
        { headers: { Accept: "application/json", ...authHeaders } }
      );
      const topJson = await topResp.json().catch(() => ({}));
      if (!topResp.ok) throw new Error(parseError(topJson));

      const slices = buildWindowSlices(fromIso, toIso);
      const series = await Promise.all(
        slices.map(async (slice) => {
          const sliceParams = new URLSearchParams();
          if (pid) sliceParams.set("partner_id", pid);
          sliceParams.set("from", slice.fromIso);
          sliceParams.set("to", slice.toIso);

          const sliceCompareResp = await fetch(
            `${ORDER_PICKUP_BASE}/partners/ops/settlements/reconciliation/compare?${sliceParams.toString()}`,
            { headers: { Accept: "application/json", ...authHeaders } }
          );
          const sliceCompareJson = await sliceCompareResp.json().catch(() => ({}));
          if (!sliceCompareResp.ok) throw new Error(parseError(sliceCompareJson));

          const sliceTopParams = new URLSearchParams(sliceParams);
          sliceTopParams.set("top_n", "200");
          sliceTopParams.set("min_severity", "LOW");
          const sliceTopResp = await fetch(
            `${ORDER_PICKUP_BASE}/partners/ops/settlements/reconciliation/top-divergences?${sliceTopParams.toString()}`,
            { headers: { Accept: "application/json", ...authHeaders } }
          );
          const sliceTopJson = await sliceTopResp.json().catch(() => ({}));
          if (!sliceTopResp.ok) throw new Error(parseError(sliceTopJson));

          return {
            label: formatSliceLabel(slice.fromIso, slice.toIso),
            fromIso: slice.fromIso,
            toIso: slice.toIso,
            divergenceRatePct: Number(sliceCompareJson?.current?.divergence_rate_pct || 0),
            divergentBatches: Number(sliceTopJson?.total_divergent_batches || 0),
            severityCounts: {
              HIGH: Number(sliceTopJson?.severity_counts?.HIGH || 0),
              MEDIUM: Number(sliceTopJson?.severity_counts?.MEDIUM || 0),
              LOW: Number(sliceTopJson?.severity_counts?.LOW || 0),
            },
          };
        })
      );

      setCompare(compareJson);
      setTop(topJson);
      setTimeSeries(series);
    } catch (err) {
      setError(String(err?.message || err || "erro desconhecido"));
      setTimeSeries([]);
    } finally {
      setLoading(false);
    }
  }

  function applyRangePreset(presetId) {
    const referenceNow = new Date();
    const preset = WINDOW_PRESETS.find((item) => item.id === presetId);
    const hours = preset ? preset.hours : 24;
    const start = new Date(referenceNow.getTime() - hours * 60 * 60 * 1000);
    const nextFrom = toDateTimeLocalInputValue(start);
    const nextTo = toDateTimeLocalInputValue(referenceNow);
    setFromDateTime(nextFrom);
    setToDateTime(nextTo);
    setSelectedPreset(presetId);
    void loadDashboard({ fromDateTime: nextFrom, toDateTime: nextTo });
  }

  function buildEvidenceSummary() {
    const counts = top?.severity_counts || {};
    const topItems = Array.isArray(top?.items) ? top.items.slice(0, 5) : [];
    const lines = [
      "Sprint 12 - Reconciliation Dashboard Evidence",
      `timestamp: ${new Date().toISOString()}`,
      `version: ${OPS_RECON_DASHBOARD_VERSION}`,
      `partner_id: ${String(partnerId || "").trim() || "-"}`,
      `from: ${toIsoOrNull(fromDateTime) || "-"}`,
      `to: ${toIsoOrNull(toDateTime) || "-"}`,
      `min_severity: ${String(minSeverity || "").trim().toUpperCase() || "-"}`,
      `top_n: ${String(topN || "").trim() || "-"}`,
      `current_divergence_rate_pct: ${compare?.current?.divergence_rate_pct ?? "-"}`,
      `delta_divergence_rate_pct: ${compare?.delta_divergence_rate_pct ?? "-"}`,
      `total_divergent_batches_filtered: ${top?.total_divergent_batches ?? "-"}`,
      `severity_counts: HIGH=${counts.HIGH ?? "-"} MEDIUM=${counts.MEDIUM ?? "-"} LOW=${counts.LOW ?? "-"}`,
      "",
      "top5_batches:",
      ...(topItems.length
        ? topItems.map(
            (item, idx) =>
              `${idx + 1}. ${item.batch_id} | ${item.partner_id} | severity=${item.severity} | impact=${item.impact_score}`
          )
        : ["- sem dados"]),
    ];
    return lines.join("\n");
  }

  function buildInboundInsight() {
    const currentRate = Number(compare?.current?.divergence_rate_pct || 0);
    const deltaRate = Number(compare?.delta_divergence_rate_pct || 0);
    const filteredTotal = Number(top?.total_divergent_batches || 0);
    const counts = top?.severity_counts || {};
    const high = Number(counts.HIGH || 0);
    const medium = Number(counts.MEDIUM || 0);
    const low = Number(counts.LOW || 0);
    const totalBySeverity = high + medium + low;
    const highShare = totalBySeverity > 0 ? (high / totalBySeverity) * 100 : 0;
    const trend = deltaRate > 0 ? "piorando" : deltaRate < 0 ? "melhorando" : "estável";
    const severity = high > 0 || currentRate >= 20 ? "CRITICAL" : currentRate >= 10 ? "HIGH" : currentRate >= 5 ? "MEDIUM" : "LOW";
    const emoji = severity === "CRITICAL" ? "🔴" : severity === "HIGH" ? "🟠" : severity === "MEDIUM" ? "🟡" : "🟢";
    const headline = `${emoji} Inbound: divergência ${trend} | taxa atual ${currentRate.toFixed(2)}% | delta ${deltaRate >= 0 ? "+" : ""}${deltaRate.toFixed(2)} p.p.`;
    const impact = `Batches em foco (filtro): ${filteredTotal}. Distribuição: HIGH=${high}, MEDIUM=${medium}, LOW=${low} (HIGH ${highShare.toFixed(1)}%).`;
    const next = high > 0
      ? "Ação imediata: priorizar HIGH por impacto_score, validar origem da divergência em gross/orders/share e abrir tratativa com financeiro/operação."
      : "Ação imediata: manter monitoramento de MEDIUM/LOW, validar tendência e prevenir escalada para HIGH.";
    return { severity, headline, impact, next };
  }

  function buildRunbookMarkdown() {
    const insight = buildInboundInsight();
    const first = (top?.items || [])[0];
    const investigateLink = "/ops/partners/financials-service-areas";
    return [
      "## Runbook - Inbound de Reconciliacao (Partners)",
      "",
      `- Versao painel: ${OPS_RECON_DASHBOARD_VERSION}`,
      `- Timestamp: ${new Date().toISOString()}`,
      `- Severidade sugerida: ${insight.severity}`,
      "",
      "### Leitura rapida",
      `- ${insight.headline}`,
      `- ${insight.impact}`,
      `- ${insight.next}`,
      "",
      "### Proximos passos (plantao)",
      "1. Priorizar lotes no topo de impacto e confirmar se ha divergencia em gross (HIGH).",
      "2. Cruzar com o endpoint de compare para validar tendencia da janela.",
      "3. Registrar incidente com lote principal, impacto e owner da acao.",
      "4. Executar mitigacao operacional e monitorar queda de divergencias.",
      "",
      "### Evidencia principal",
      `- top_batch: ${first?.batch_id || "-"}`,
      `- partner: ${first?.partner_id || "-"}`,
      `- impact_score: ${first?.impact_score ?? "-"}`,
      `- severity_counts: H=${top?.severity_counts?.HIGH ?? "-"} M=${top?.severity_counts?.MEDIUM ?? "-"} L=${top?.severity_counts?.LOW ?? "-"}`,
      `- link investigacao: ${investigateLink}`,
    ].join("\n");
  }

  function buildRunbookPlainTicket() {
    const insight = buildInboundInsight();
    const first = (top?.items || [])[0];
    return [
      "INBOUND RECONCILIACAO (PARTNERS)",
      `timestamp=${new Date().toISOString()}`,
      `severity=${insight.severity}`,
      `headline=${insight.headline}`,
      `impact=${insight.impact}`,
      `next=${insight.next}`,
      `top_batch=${first?.batch_id || "-"}`,
      `top_partner=${first?.partner_id || "-"}`,
      `top_impact=${first?.impact_score ?? "-"}`,
      "investigate=/ops/partners/financials-service-areas",
    ].join("\n");
  }

  async function handleCopyEvidence() {
    try {
      await navigator.clipboard.writeText(buildEvidenceSummary());
      setCopyStatus("Resumo de evidência copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2200);
    } catch (_) {
      setCopyStatus("Falha ao copiar automaticamente. Copie manualmente do painel técnico.");
    }
  }

  async function handleCopyRunbookMarkdown() {
    try {
      await navigator.clipboard.writeText(buildRunbookMarkdown());
      setRunbookCopied(true);
      window.setTimeout(() => setRunbookCopied(false), 2200);
    } catch (_) {
      setCopyStatus("Falha ao copiar runbook. Copie manualmente.");
      window.setTimeout(() => setCopyStatus(""), 2200);
    }
  }

  async function handleCopyRunbookPlain() {
    try {
      await navigator.clipboard.writeText(buildRunbookPlainTicket());
      setRunbookPlainCopied(true);
      window.setTimeout(() => setRunbookPlainCopied(false), 2200);
    } catch (_) {
      setCopyStatus("Falha ao copiar ticket simples. Copie manualmente.");
      window.setTimeout(() => setCopyStatus(""), 2200);
    }
  }

  function handleSelectHeatmapWindow(windowPoint) {
    if (!windowPoint?.fromIso || !windowPoint?.toIso) return;
    const nextFrom = toDateTimeLocalInputValue(new Date(windowPoint.fromIso));
    const nextTo = toDateTimeLocalInputValue(new Date(windowPoint.toIso));
    setFromDateTime(nextFrom);
    setToDateTime(nextTo);
    setSelectedPreset("");
    setSelectedHeatmapWindowKey(`${windowPoint.fromIso}|${windowPoint.toIso}`);
    void loadDashboard({ fromDateTime: nextFrom, toDateTime: nextTo });
  }

  function handleClearHeatmapWindowFilter() {
    setSelectedHeatmapWindowKey("");
  }

  const inboundInsight = buildInboundInsight();
  const severityCounts = {
    HIGH: Number(top?.severity_counts?.HIGH || 0),
    MEDIUM: Number(top?.severity_counts?.MEDIUM || 0),
    LOW: Number(top?.severity_counts?.LOW || 0),
  };
  const severityTotal = severityCounts.HIGH + severityCounts.MEDIUM + severityCounts.LOW;
  const severityPercent = {
    HIGH: severityTotal > 0 ? (severityCounts.HIGH / severityTotal) * 100 : 0,
    MEDIUM: severityTotal > 0 ? (severityCounts.MEDIUM / severityTotal) * 100 : 0,
    LOW: severityTotal > 0 ? (severityCounts.LOW / severityTotal) * 100 : 0,
  };
  const trendRatePoints = timeSeries.map((point) => point.divergenceRatePct);
  const displayedSeries = chartGrade === "simplified" ? simplifyTimeSeries(timeSeries) : timeSeries;
  const displayedTrendRatePoints = displayedSeries.map((point) => point.divergenceRatePct);
  const trendMax = Math.max(...displayedTrendRatePoints, 0);
  const trendMin = Math.min(...displayedTrendRatePoints, 0);
  const trendSpan = Math.max(trendMax - trendMin, 1);
  const trendPolylinePoints = displayedSeries
    .map((point, index) => {
      const x = displayedSeries.length > 1 ? (index / (displayedSeries.length - 1)) * 100 : 50;
      const y = 100 - ((point.divergenceRatePct - trendMin) / trendSpan) * 100;
      return `${x},${y}`;
    })
    .join(" ");
  const scatterXMax = Math.max(...displayedSeries.map((point) => point.divergenceRatePct), 1);
  const scatterYMax = Math.max(...displayedSeries.map((point) => point.divergentBatches || 0), 1);
  const scatterPoints = displayedSeries.map((point) => {
    const x = (Math.max(0, point.divergenceRatePct) / scatterXMax) * 100;
    const y = 100 - ((Math.max(0, point.divergentBatches || 0) / scatterYMax) * 100);
    const sev = point.severityCounts || {};
    const dominant =
      sev.HIGH >= sev.MEDIUM && sev.HIGH >= sev.LOW ? "HIGH" : sev.MEDIUM >= sev.LOW ? "MEDIUM" : "LOW";
    const fill = dominant === "HIGH" ? "#ef4444" : dominant === "MEDIUM" ? "#f59e0b" : "#22c55e";
    return { x, y, fill, label: point.label, rate: point.divergenceRatePct, batches: point.divergentBatches || 0 };
  });
  const selectedHeatmapWindowLabel =
    displayedSeries.find((point) => `${point.fromIso}|${point.toIso}` === selectedHeatmapWindowKey)?.label || "";

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={headerRowStyle}>
          <OpsPageTitleHeader
            title="OPS - Partners Reconciliation Dashboard"
            versionLabel={OPS_RECON_DASHBOARD_VERSION}
            versionTo="/ops/auth/policy/versioning"
            containerStyle={{ marginBottom: 0 }}
            titleStyle={{ margin: 0 }}
          />
        </div>
        <p style={mutedStyle}>
          Painel executivo para comitê operacional: tendência de divergência (`compare`) + priorização por impacto (`top-divergences`).
        </p>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            partner_id (opcional)
            <input style={inputStyle} value={partnerId} onChange={(e) => setPartnerId(e.target.value)} placeholder="OP-ELLAN-001" />
          </label>
          <label style={labelStyle}>
            min_severity
            <select style={inputStyle} value={minSeverity} onChange={(e) => setMinSeverity(e.target.value)}>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </label>
          <label style={labelStyle}>
            top_n
            <input style={inputStyle} value={topN} onChange={(e) => setTopN(e.target.value)} />
          </label>
          <label style={labelStyle}>
            from
            <input type="datetime-local" style={inputStyle} value={fromDateTime} onChange={(e) => setFromDateTime(e.target.value)} />
          </label>
          <label style={labelStyle}>
            to
            <input type="datetime-local" style={inputStyle} value={toDateTime} onChange={(e) => setToDateTime(e.target.value)} />
          </label>
        </div>
        <div style={presetSectionStyle}>
          <small style={presetLabelStyle}>Presets de janela</small>
          <div style={presetRowStyle}>
          {WINDOW_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              style={selectedPreset === preset.id ? presetButtonActiveStyle : presetButtonStyle}
              onClick={() => applyRangePreset(preset.id)}
            >
              {preset.label}
            </button>
          ))}
          </div>
        </div>

        <div style={actionsRowStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void loadDashboard()} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar dashboard"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="copy" onClick={() => void handleCopyEvidence()} disabled={loading || !top}>
            Copiar evidência
          </OpsActionButton>
          <Link to="/ops/partners/financials-service-areas" style={drilldownLinkStyle}>
            Abrir operação financeira de parceiros
          </Link>
        </div>
        {copyStatus ? <small style={copyStatusStyle}>{copyStatus}</small> : null}

        {error ? <p style={errorStyle}>Erro: {error}</p> : null}

        <div style={kpiGridStyle}>
          <article style={kpiCardStyle}>
            <small style={kpiLabelStyle}>Current divergence rate</small>
            <strong style={kpiValueStyle}>{compare?.current?.divergence_rate_pct ?? "-"}</strong>
          </article>
          <article style={kpiCardStyle}>
            <small style={kpiLabelStyle}>Delta divergence rate</small>
            <strong style={kpiValueStyle}>{compare?.delta_divergence_rate_pct ?? "-"}</strong>
          </article>
          <article style={kpiCardStyle}>
            <small style={kpiLabelStyle}>Batches divergentes (filtro)</small>
            <strong style={kpiValueStyle}>{top?.total_divergent_batches ?? "-"}</strong>
          </article>
          <article style={kpiCardStyle}>
            <small style={kpiLabelStyle}>Severity counts</small>
            {top?.severity_counts ? (
              <div style={severityCountsStackStyle}>
                <div style={severityChipsRowStyle}>
                  <span style={severityChipCriticalStyle}>H {severityCounts.HIGH}</span>
                  <span style={severityChipHighStyle}>M {severityCounts.MEDIUM}</span>
                  <span style={severityChipMediumStyle}>L {severityCounts.LOW}</span>
                </div>
                <div style={severityBarTrackStyle} aria-label="Distribuição por severidade">
                  <span style={{ ...severityBarHighStyle, width: `${severityPercent.HIGH}%` }} />
                  <span style={{ ...severityBarMediumStyle, width: `${severityPercent.MEDIUM}%` }} />
                  <span style={{ ...severityBarLowStyle, width: `${severityPercent.LOW}%` }} />
                </div>
              </div>
            ) : (
              <strong style={kpiValueStyle}>-</strong>
            )}
          </article>
        </div>

        <section style={chartsGridStyle}>
          <div style={chartGradeRowStyle}>
            <small style={chartGradeLabelStyle}>Grade:</small>
            <div style={chartGradeToggleStyle}>
              <button
                type="button"
                style={chartGrade === "simplified" ? chartGradeButtonActiveStyle : chartGradeButtonStyle}
                onClick={() => setChartGrade("simplified")}
              >
                Simplificada
              </button>
              <button
                type="button"
                style={chartGrade === "complete" ? chartGradeButtonActiveStyle : chartGradeButtonStyle}
                onClick={() => setChartGrade("complete")}
              >
                Completa
              </button>
            </div>
          </div>
          <article style={chartCardStyle}>
            <div style={chartHeaderStyle}>
              <strong style={{ fontSize: 13 }}>Tendência da taxa</strong>
              <small style={chartHelpStyle}>Série por sub-janelas no período selecionado</small>
            </div>
            {displayedSeries.length ? (
              <div style={trendChartWrapStyle}>
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={trendSvgStyle} aria-label="Tendência da taxa de divergência">
                  <polyline points={trendPolylinePoints} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
                </svg>
                <div style={trendLegendRowStyle}>
                  {displayedSeries.map((point) => (
                    <div key={point.label} style={trendLegendItemStyle}>
                      <small style={trendLegendLabelStyle}>{point.label}</small>
                      <strong style={trendLegendValueStyle}>{point.divergenceRatePct.toFixed(2)}%</strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <small style={chartEmptyStyle}>Execute "Atualizar dashboard" para montar a tendência.</small>
            )}
          </article>

          <article style={chartCardStyle}>
            <div style={chartHeaderStyle}>
              <strong style={{ fontSize: 13 }}>Severidade H/M/L no tempo</strong>
              <small style={chartHelpStyle}>Distribuição por sub-janela (HIGH, MEDIUM, LOW)</small>
            </div>
            {displayedSeries.length ? (
              <div style={severityTimelineStackStyle}>
                {displayedSeries.map((point) => {
                  const h = point.severityCounts.HIGH;
                  const m = point.severityCounts.MEDIUM;
                  const l = point.severityCounts.LOW;
                  const total = h + m + l;
                  const hp = total > 0 ? (h / total) * 100 : 0;
                  const mp = total > 0 ? (m / total) * 100 : 0;
                  const lp = total > 0 ? (l / total) * 100 : 0;
                  return (
                    <div key={`sev-${point.label}`} style={severityTimelineRowStyle}>
                      <small style={severityTimelineLabelStyle}>{point.label}</small>
                      <div style={severityTimelineTrackStyle} aria-label={`Severidade na janela ${point.label}`}>
                        <span style={{ ...severityBarHighStyle, width: `${hp}%` }} />
                        <span style={{ ...severityBarMediumStyle, width: `${mp}%` }} />
                        <span style={{ ...severityBarLowStyle, width: `${lp}%` }} />
                      </div>
                      <small style={severityTimelineCountStyle}>H:{h} M:{m} L:{l}</small>
                    </div>
                  );
                })}
              </div>
            ) : (
              <small style={chartEmptyStyle}>Execute "Atualizar dashboard" para montar a série de severidade.</small>
            )}
          </article>

          <article style={chartCardStyle}>
            <div style={chartHeaderStyle}>
              <strong style={{ fontSize: 13 }}>Correlação: taxa vs batches</strong>
              <small style={chartHelpStyle}>Scatter 2D por janela (sem bolha no Sprint 12.5)</small>
            </div>
            {displayedSeries.length ? (
              <div style={scatterWrapStyle}>
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={scatterSvgStyle} aria-label="Correlação entre taxa de divergência e batches divergentes">
                  <line x1="0" y1="100" x2="100" y2="100" stroke="#334155" strokeWidth="0.8" />
                  <line x1="0" y1="0" x2="0" y2="100" stroke="#334155" strokeWidth="0.8" />
                  {scatterPoints.map((point) => (
                    <circle key={`scatter-${point.label}`} cx={point.x} cy={point.y} r="2.2" fill={point.fill} />
                  ))}
                </svg>
                <div style={scatterAxisLegendStyle}>
                  <small style={chartHelpStyle}>X: taxa de divergência (%)</small>
                  <small style={chartHelpStyle}>Y: batches divergentes</small>
                </div>
                <div style={trendLegendRowStyle}>
                  {scatterPoints.map((point) => (
                    <div key={`scatter-legend-${point.label}`} style={trendLegendItemStyle}>
                      <small style={trendLegendLabelStyle}>{point.label}</small>
                      <strong style={trendLegendValueStyle}>
                        {point.rate.toFixed(2)}% / {point.batches}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <small style={chartEmptyStyle}>Execute "Atualizar dashboard" para calcular a correlação.</small>
            )}
          </article>

          <article style={chartCardStyle}>
            <div style={chartHeaderStyle}>
              <strong style={{ fontSize: 13 }}>Heatmap horário de HIGH</strong>
              <small style={chartHelpStyle}>Intensidade de ocorrências HIGH por sub-janela</small>
            </div>
            <div style={chartHintRowStyle}>
              <small style={chartHintTextStyle}>Clique em uma célula para filtrar automaticamente a janela do dashboard.</small>
              {selectedHeatmapWindowKey ? (
                <div style={chartHintActionsStyle}>
                  <small style={chartActiveWindowStyle}>Janela ativa: {selectedHeatmapWindowLabel || "custom"}</small>
                  <button type="button" style={chartClearFilterButtonStyle} onClick={handleClearHeatmapWindowFilter}>
                    Limpar seleção
                  </button>
                </div>
              ) : null}
            </div>
            {displayedSeries.length ? (
              <div style={heatmapWrapStyle}>
                <div style={heatmapRowStyle}>
                  {buildHighHeatmapCells(displayedSeries).map((cell) => (
                    <button
                      type="button"
                      key={`heat-${cell.label}`}
                      style={{
                        ...heatmapCellStyle,
                        background: cell.color,
                        outline: selectedHeatmapWindowKey === `${cell.fromIso}|${cell.toIso}` ? "2px solid #93c5fd" : "none",
                      }}
                      title={`${cell.label} | HIGH: ${cell.high}`}
                      aria-label={`Janela ${cell.label} com ${cell.high} ocorrências HIGH`}
                      onClick={() => handleSelectHeatmapWindow(cell)}
                    />
                  ))}
                </div>
                <div style={heatmapLegendStyle}>
                  <small style={chartHelpStyle}>Menor intensidade</small>
                  <div style={heatmapLegendBarStyle} />
                  <small style={chartHelpStyle}>Maior intensidade</small>
                </div>
              </div>
            ) : (
              <small style={chartEmptyStyle}>Execute "Atualizar dashboard" para montar o heatmap.</small>
            )}
          </article>
        </section>

        <details
          style={inboundSectionStyle}
          open={inboundExpanded}
          onToggle={(event) => setInboundExpanded(event.currentTarget.open)}
        >
          <summary style={inboundSummaryStyle}>
            <span style={{ fontSize: 14, fontWeight: 700 }}>Inbound de priorização</span>
            <span style={inboundSummaryRightStyle}>
              <span style={inboundSeverityBadgeStyle(inboundInsight.severity)}>{inboundInsight.severity}</span>
              <span style={inboundChevronStyle}>{inboundExpanded ? "▾" : "▸"}</span>
            </span>
          </summary>
          <div style={inboundBodyStyle}>
            <small style={inboundLineStyle}>{inboundInsight.headline}</small>
            <small style={inboundLineStyle}>{inboundInsight.impact}</small>
            <small style={inboundLineStyle}>{inboundInsight.next}</small>
            <div style={runbookActionsStyle}>
              <button type="button" style={runbookButtonStyle} onClick={() => setRunbookOpen((v) => !v)}>
                {runbookOpen ? "Fechar Runbook" : "Abrir Runbook"}
              </button>
              <button type="button" style={runbookCopyButtonStyle} onClick={() => void handleCopyRunbookMarkdown()}>
                {runbookCopied ? "Runbook copiado" : "Copiar runbook"}
              </button>
              <button type="button" style={runbookPlainButtonStyle} onClick={() => void handleCopyRunbookPlain()}>
                {runbookPlainCopied ? "Ticket simples copiado" : "Copiar ticket (texto simples)"}
              </button>
              <Link to="/ops/partners/financials-service-areas" style={drilldownLinkStyle}>
                Investigar
              </Link>
            </div>
            {runbookOpen ? (
              <pre style={runbookPanelStyle}>{buildRunbookMarkdown()}</pre>
            ) : null}
          </div>
        </details>

        <section style={tableSectionStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8, fontSize: 15 }}>Top divergências por impacto</h3>
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Batch</th>
                  <th style={thStyle}>Partner</th>
                  <th style={thStyle}>Severity</th>
                  <th style={thStyle}>Impact</th>
                  <th style={thStyle}>Δ Orders</th>
                  <th style={thStyle}>Δ Gross</th>
                  <th style={thStyle}>Δ Share</th>
                </tr>
              </thead>
              <tbody>
                {(top?.items || []).length ? (
                  top.items.map((item) => (
                    <tr key={item.batch_id}>
                      <td style={tdStyle}>{item.batch_id}</td>
                      <td style={tdStyle}>{item.partner_id}</td>
                      <td style={tdStyle}>{item.severity}</td>
                      <td style={tdStyle}>{item.impact_score}</td>
                      <td style={tdStyle}>{item.delta_total_orders}</td>
                      <td style={tdStyle}>{item.delta_gross_revenue_cents}</td>
                      <td style={tdStyle}>{item.delta_revenue_share_cents}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td style={tdStyle} colSpan={7}>
                      Execute "Atualizar dashboard" para carregar os batches.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <details style={rawDetailsStyle}>
          <summary style={rawSummaryStyle}>Payload técnico (top-divergences)</summary>
          <pre style={resultStyle}>{top ? JSON.stringify(top, null, 2) : "Sem payload carregado."}</pre>
        </details>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const headerRowStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" };
const mutedStyle = { color: "#94A3B8" };
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const presetSectionStyle = { marginTop: -2, marginBottom: 10, display: "grid", gap: 6 };
const presetLabelStyle = { color: "#94A3B8", fontSize: 12 };
const presetRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const presetButtonStyle = {
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid #334155",
  background: "#0f172a",
  color: "#cbd5e1",
  cursor: "pointer",
  fontSize: 12,
};
const presetButtonActiveStyle = {
  ...presetButtonStyle,
  border: "1px solid rgba(59,130,246,0.55)",
  background: "rgba(59,130,246,0.18)",
  color: "#dbeafe",
};
const errorStyle = { color: "#FCA5A5", fontSize: 13 };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" };
const copyStatusStyle = { marginTop: 6, color: "#93C5FD", fontSize: 12 };
const drilldownLinkStyle = {
  color: "#93C5FD",
  textDecoration: "none",
  border: "1px solid #334155",
  borderRadius: 8,
  padding: "8px 10px",
  fontSize: 12,
  background: "#0f172a",
};
const kpiGridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" };
const kpiCardStyle = { background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 10, display: "grid", gap: 4 };
const kpiLabelStyle = { color: "#94A3B8", fontSize: 11 };
const kpiValueStyle = { fontSize: 18 };
const chartsGridStyle = { marginTop: 14, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" };
const chartCardStyle = { background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, display: "grid", gap: 10 };
const chartHeaderStyle = { display: "grid", gap: 2 };
const chartHelpStyle = { color: "#94A3B8", fontSize: 11 };
const chartEmptyStyle = { color: "#94A3B8", fontSize: 12 };
const chartGradeRowStyle = { gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 8 };
const chartGradeLabelStyle = { color: "#94A3B8", fontSize: 12 };
const chartGradeToggleStyle = { display: "inline-flex", border: "1px solid #334155", borderRadius: 999, padding: 2, background: "rgba(15,23,42,0.65)" };
const chartGradeButtonStyle = {
  border: "none",
  background: "transparent",
  color: "#94A3B8",
  padding: "4px 10px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 700,
  cursor: "pointer",
};
const chartGradeButtonActiveStyle = {
  ...chartGradeButtonStyle,
  background: "rgba(59,130,246,0.28)",
  color: "#dbeafe",
};
const chartHintRowStyle = { display: "grid", gap: 6 };
const chartHintTextStyle = { color: "#bfdbfe", fontSize: 11 };
const chartHintActionsStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" };
const chartActiveWindowStyle = {
  display: "inline-flex",
  borderRadius: 999,
  border: "1px solid rgba(147,197,253,0.55)",
  background: "rgba(30,64,175,0.25)",
  color: "#dbeafe",
  padding: "3px 8px",
  fontSize: 11,
};
const chartClearFilterButtonStyle = {
  border: "1px solid #334155",
  background: "rgba(15,23,42,0.7)",
  color: "#cbd5e1",
  borderRadius: 999,
  padding: "3px 9px",
  fontSize: 11,
  cursor: "pointer",
};
const trendChartWrapStyle = { display: "grid", gap: 8 };
const trendSvgStyle = { width: "100%", height: 100, background: "rgba(15,23,42,0.45)", border: "1px solid #1e293b", borderRadius: 8 };
const trendLegendRowStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(88px, 1fr))", gap: 6 };
const trendLegendItemStyle = { background: "rgba(15,23,42,0.45)", border: "1px solid #1e293b", borderRadius: 8, padding: "6px 8px", display: "grid", gap: 2 };
const trendLegendLabelStyle = { color: "#94A3B8", fontSize: 10 };
const trendLegendValueStyle = { fontSize: 12, color: "#e2e8f0" };
const scatterWrapStyle = { display: "grid", gap: 8 };
const scatterSvgStyle = { width: "100%", height: 120, background: "rgba(15,23,42,0.45)", border: "1px solid #1e293b", borderRadius: 8 };
const scatterAxisLegendStyle = { display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" };
const heatmapWrapStyle = { display: "grid", gap: 10 };
const heatmapRowStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(20px, 1fr))", gap: 6 };
const heatmapCellStyle = {
  height: 22,
  borderRadius: 6,
  border: "1px solid rgba(148,163,184,0.35)",
  cursor: "pointer",
  padding: 0,
};
const heatmapLegendStyle = { display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 8, alignItems: "center" };
const heatmapLegendBarStyle = { height: 8, borderRadius: 999, background: "linear-gradient(90deg, rgba(30,41,59,0.95), rgba(239,68,68,0.95))", border: "1px solid #334155" };
const severityTimelineStackStyle = { display: "grid", gap: 8 };
const severityTimelineRowStyle = { display: "grid", gridTemplateColumns: "74px 1fr auto", gap: 8, alignItems: "center" };
const severityTimelineLabelStyle = { color: "#94A3B8", fontSize: 11 };
const severityTimelineTrackStyle = { height: 10, borderRadius: 999, overflow: "hidden", display: "flex", border: "1px solid #334155", background: "rgba(15,23,42,0.7)" };
const severityTimelineCountStyle = { color: "#CBD5E1", fontSize: 11, whiteSpace: "nowrap" };
const severityCountsStackStyle = { display: "grid", gap: 8, marginTop: 2 };
const severityChipsRowStyle = { display: "flex", gap: 6, flexWrap: "wrap" };
const severityChipBaseStyle = { display: "inline-flex", borderRadius: 999, padding: "3px 8px", fontSize: 11, fontWeight: 700 };
const severityChipCriticalStyle = { ...severityChipBaseStyle, background: "rgba(220,38,38,0.22)", color: "#fecaca", border: "1px solid rgba(248,113,113,0.6)" };
const severityChipHighStyle = { ...severityChipBaseStyle, background: "rgba(245,158,11,0.22)", color: "#fde68a", border: "1px solid rgba(251,191,36,0.6)" };
const severityChipMediumStyle = { ...severityChipBaseStyle, background: "rgba(34,197,94,0.18)", color: "#bbf7d0", border: "1px solid rgba(74,222,128,0.55)" };
const severityBarTrackStyle = {
  width: "100%",
  height: 8,
  borderRadius: 999,
  overflow: "hidden",
  border: "1px solid #334155",
  background: "rgba(15,23,42,0.7)",
  display: "flex",
};
const severityBarBaseStyle = { height: "100%" };
const severityBarHighStyle = { ...severityBarBaseStyle, background: "linear-gradient(90deg, #ef4444, #dc2626)" };
const severityBarMediumStyle = { ...severityBarBaseStyle, background: "linear-gradient(90deg, #f59e0b, #d97706)" };
const severityBarLowStyle = { ...severityBarBaseStyle, background: "linear-gradient(90deg, #22c55e, #16a34a)" };
const inboundSectionStyle = {
  marginTop: 14,
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
  display: "grid",
  gap: 6,
};
const inboundSummaryStyle = { listStyle: "none", display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" };
const inboundSummaryRightStyle = { display: "inline-flex", alignItems: "center", gap: 8 };
const inboundChevronStyle = { color: "#94A3B8", fontSize: 13, fontWeight: 700, width: 12, textAlign: "center" };
const inboundBodyStyle = { marginTop: 6, display: "grid", gap: 6 };
const inboundSeverityBadgeStyle = (severity) => ({
  display: "inline-flex",
  borderRadius: 999,
  padding: "3px 10px",
  fontSize: 11,
  fontWeight: 700,
  color: "#fff",
  border: severity === "CRITICAL" ? "1px solid #fecaca" : severity === "HIGH" ? "1px solid #fdba74" : "1px solid #fcd34d",
  background: severity === "CRITICAL" ? "#7f1d1d" : severity === "HIGH" ? "#9a3412" : "#78350f",
});
const inboundLineStyle = { color: "#CBD5E1", fontSize: 12 };
const runbookActionsStyle = { marginTop: 6, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" };
const runbookButtonStyle = {
  padding: "7px 10px",
  borderRadius: 10,
  border: "1px solid rgba(245,158,11,0.55)",
  background: "rgba(245,158,11,0.12)",
  color: "#fde68a",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 12,
};
const runbookCopyButtonStyle = {
  padding: "7px 10px",
  borderRadius: 10,
  border: "1px solid rgba(14,116,144,0.55)",
  background: "rgba(14,116,144,0.16)",
  color: "#bae6fd",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 12,
};
const runbookPlainButtonStyle = {
  padding: "7px 10px",
  borderRadius: 10,
  border: "1px solid rgba(22,101,52,0.55)",
  background: "rgba(22,101,52,0.18)",
  color: "#dcfce7",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 12,
};
const runbookPanelStyle = {
  marginTop: 6,
  background: "rgba(15,23,42,0.55)",
  border: "1px solid rgba(148,163,184,0.35)",
  borderRadius: 10,
  padding: 10,
  overflow: "auto",
  fontSize: 12,
  whiteSpace: "pre-wrap",
};
const tableSectionStyle = { marginTop: 14, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12 };
const tableWrapStyle = { overflow: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };
const thStyle = { textAlign: "left", borderBottom: "1px solid #334155", padding: "8px 6px", color: "#94A3B8", whiteSpace: "nowrap" };
const tdStyle = { borderBottom: "1px solid #1e293b", padding: "8px 6px", verticalAlign: "top" };
const rawDetailsStyle = { marginTop: 10 };
const rawSummaryStyle = { cursor: "pointer", color: "#94A3B8", fontSize: 12 };
const resultStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" };

function buildWindowSlices(fromIso, toIso) {
  const fromMs = new Date(fromIso).getTime();
  const toMs = new Date(toIso).getTime();
  if (Number.isNaN(fromMs) || Number.isNaN(toMs) || toMs <= fromMs) return [];
  const totalHours = (toMs - fromMs) / (1000 * 60 * 60);
  let slices = 6;
  if (totalHours > 36 && totalHours <= 24 * 10) {
    slices = Math.min(10, Math.max(5, Math.round(totalHours / 24)));
  } else if (totalHours > 24 * 10) {
    slices = 10;
  }
  const step = Math.max(1, Math.floor((toMs - fromMs) / slices));
  const windows = [];
  for (let i = 0; i < slices; i += 1) {
    const start = fromMs + i * step;
    const end = i === slices - 1 ? toMs : Math.min(toMs, start + step);
    windows.push({ fromIso: new Date(start).toISOString(), toIso: new Date(end).toISOString() });
  }
  return windows;
}

function formatSliceLabel(fromIso, toIso) {
  const start = new Date(fromIso);
  const end = new Date(toIso);
  const sameDay =
    start.getFullYear() === end.getFullYear()
    && start.getMonth() === end.getMonth()
    && start.getDate() === end.getDate();
  const sh = String(start.getHours()).padStart(2, "0");
  const sm = String(start.getMinutes()).padStart(2, "0");
  const eh = String(end.getHours()).padStart(2, "0");
  const em = String(end.getMinutes()).padStart(2, "0");
  const sd = String(start.getDate()).padStart(2, "0");
  const smon = String(start.getMonth() + 1).padStart(2, "0");
  const ed = String(end.getDate()).padStart(2, "0");
  const emon = String(end.getMonth() + 1).padStart(2, "0");
  if (sameDay) return `${sd}/${smon} ${sh}:${sm}-${eh}:${em}`;
  return `${sd}/${smon} ${sh}:${sm} -> ${ed}/${emon} ${eh}:${em}`;
}

function simplifyTimeSeries(series) {
  if (!Array.isArray(series) || series.length <= 6) return series;
  const step = Math.max(1, Math.ceil(series.length / 6));
  const simplified = [];
  for (let i = 0; i < series.length; i += step) {
    simplified.push(series[i]);
  }
  const last = series[series.length - 1];
  if (simplified[simplified.length - 1] !== last) simplified.push(last);
  return simplified.slice(0, 6);
}

function buildHighHeatmapCells(series) {
  const highs = series.map((point) => Number(point?.severityCounts?.HIGH || 0));
  const maxHigh = Math.max(...highs, 1);
  return series.map((point) => {
    const high = Number(point?.severityCounts?.HIGH || 0);
    const ratio = Math.max(0, Math.min(1, high / maxHigh));
    const alpha = 0.15 + ratio * 0.8;
    return {
      label: point.label,
      high,
      fromIso: point.fromIso,
      toIso: point.toIso,
      color: `rgba(239,68,68,${alpha.toFixed(3)})`,
    };
  });
}
