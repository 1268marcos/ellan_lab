// 01_source/frontend/src/pages/PickupHealthPage.jsx
import React, { useEffect, useMemo, useState } from "react";

const ORDER_LIFECYCLE_BASE =
  import.meta.env.VITE_ORDER_LIFECYCLE_BASE_URL || "http://localhost:8010";

const INTERNAL_TOKEN =
  import.meta.env.VITE_INTERNAL_TOKEN || "";

const ENTITY_OPTIONS = [
  { value: "all", label: "Todos" },
  { value: "locker", label: "Lockers" },
  { value: "machine", label: "Máquinas" },
  { value: "site", label: "Sites" },
  { value: "region", label: "Regiões" },
  { value: "channel", label: "Canal" }, // novo
  { value: "slot", label: "Slot de Entrega" }, // novo
  { value: "operator", label: "Operador Logístico" }, // novo
  { value: "tenant", label: "Inquilino" }, // novo
];

const REGION_OPTIONS = [
  { value: "", label: "Todas" },
  { value: "SP", label: "SP" },
  { value: "PT", label: "PT" },
];

/** Cores do bucket derivado (menos prioritario que `classification` na UI). */
const SEVERITY_META = {
  normal: {
    label: "Bucket: normal",
    bg: "rgba(39, 174, 96, 0.18)",
    border: "rgba(39, 174, 96, 0.55)",
    accent: "#27ae60",
  },
  attention: {
    label: "Bucket: atencao",
    bg: "rgba(241, 196, 15, 0.22)",
    border: "rgba(241, 196, 15, 0.70)",
    accent: "#f39c12",
  },
  critical: {
    label: "Bucket: critico",
    bg: "rgba(230, 126, 34, 0.28)",
    border: "rgba(230, 126, 34, 0.85)",
    accent: "#e67e22",
  },
  incident: {
    label: "Bucket: incidente",
    bg: "rgba(192, 57, 43, 0.32)",
    border: "rgba(192, 57, 43, 0.92)",
    accent: "#c0392b",
  },
};

/** Classificacao operacional — define cor “agressiva” do card (alinha ao resumo Healthy/Attention/Warning). */
const CLASSIFICATION_VISUAL = {
  healthy: {
    label: "Saudavel",
    bg: "rgba(46, 204, 113, 0.26)",
    border: "rgba(39, 174, 96, 0.85)",
    accent: "#2ecc71",
  },
  attention: {
    label: "Atencao",
    bg: "rgba(241, 196, 15, 0.34)",
    border: "rgba(243, 156, 18, 0.95)",
    accent: "#f1c40f",
  },
  warning: {
    label: "Alerta",
    bg: "rgba(230, 126, 34, 0.40)",
    border: "rgba(211, 84, 0, 0.98)",
    accent: "#d35400",
  },
  critical: {
    label: "Critico",
    bg: "rgba(231, 76, 60, 0.42)",
    border: "rgba(192, 57, 43, 1)",
    accent: "#e74c3c",
  },
  collapsed: {
    label: "Colapsado",
    bg: "rgba(142, 68, 173, 0.38)",
    border: "rgba(155, 89, 182, 0.95)",
    accent: "#9b59b6",
  },
};

const RANKING_SORT_OPTIONS = [
  { value: "api", label: "Ordem da API (backend)" },
  { value: "priority_desc", label: "Prioridade (maior primeiro)" },
  { value: "priority_asc", label: "Prioridade (menor primeiro)" },
  { value: "health_asc", label: "Saude (pior primeiro)" },
  { value: "health_desc", label: "Saude (melhor primeiro)" },
  { value: "classification", label: "Classificacao + prioridade" },
];

const CLASSIFICATION_SORT_ORDER = {
  collapsed: 0,
  critical: 1,
  warning: 2,
  attention: 3,
  healthy: 4,
};

const ALERT_LABELS = {
  baixa_confiabilidade_amostral: "Amostra pequena (baixa confiabilidade)",
  expiracao_acima_do_normal: "Expiração acima do normal",
  cancelamento_acima_do_normal: "Cancelamento acima do normal",
  expiracao_alta: "Risco de expiração alta",
};

function formatScore(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(2);
}

function formatPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `${n.toFixed(2)}%`;
}

function formatMinutes(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return `${n.toFixed(2)} min`;
}

function formatDelta(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  const signal = n > 0 ? "+" : "";
  return `${signal}${n.toFixed(2)} pp`;
}

function prettyJson(value) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function buildHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function buildSeverityMeta(severity) {
  return SEVERITY_META[severity] || SEVERITY_META.normal;
}

function buildClassificationVisual(classification) {
  const key = String(classification || "").toLowerCase();
  return CLASSIFICATION_VISUAL[key] || null;
}

/** Visual do card: classificacao operacional primeiro; fallback no bucket derivado. */
function buildRowVisual(item) {
  const byClass = buildClassificationVisual(item?.classification);
  if (byClass) {
    return {
      source: "classification",
      label: byClass.label,
      bg: byClass.bg,
      border: byClass.border,
      accent: byClass.accent,
    };
  }
  const sev = buildSeverityMeta(item?.severity_bucket);
  return {
    source: "severity_bucket",
    label: sev.label,
    bg: sev.bg,
    border: sev.border,
    accent: sev.accent,
  };
}

function sortRankingCopy(items, sortKey) {
  const list = Array.isArray(items) ? [...items] : [];
  const num = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  switch (sortKey) {
    case "priority_desc":
      return list.sort((a, b) => num(b?.priority_score) - num(a?.priority_score));
    case "priority_asc":
      return list.sort((a, b) => num(a?.priority_score) - num(b?.priority_score));
    case "health_asc":
      return list.sort((a, b) => num(a?.health_score) - num(b?.health_score));
    case "health_desc":
      return list.sort((a, b) => num(b?.health_score) - num(a?.health_score));
    case "classification": {
      return list.sort((a, b) => {
        const oa = CLASSIFICATION_SORT_ORDER[String(a?.classification || "").toLowerCase()] ?? 99;
        const ob = CLASSIFICATION_SORT_ORDER[String(b?.classification || "").toLowerCase()] ?? 99;
        if (oa !== ob) return oa - ob;
        return num(b?.priority_score) - num(a?.priority_score);
      });
    }
    default:
      return list;
  }
}

/** "Alerta+": classificacao warning/critical/collapsed; fallback por bucket quando classificacao ausente. */
const CLASSIFICATION_ALERTA_PLUS = new Set(["warning", "critical", "collapsed"]);
const SEVERITY_ALERTA_PLUS_FALLBACK = new Set(["attention", "critical", "incident"]);

function matchesAlertaPlus(item) {
  const c = String(item?.classification || "").toLowerCase();
  if (CLASSIFICATION_ALERTA_PLUS.has(c)) return true;
  if (!c || c === "healthy") {
    const b = String(item?.severity_bucket || "").toLowerCase();
    if (SEVERITY_ALERTA_PLUS_FALLBACK.has(b)) return true;
  }
  return false;
}

function matchesWithAlerts(item) {
  return buildAlertChips(item).length > 0;
}

function escapeCsvCell(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function buildPickupHealthRankingCsv(rows) {
  const headers = [
    "entity_type",
    "entity_id",
    "slot_id",
    "locker_id",
    "machine_id",
    "site_id",
    "region",
    "tenant_id",
    "operator_id",
    "classification",
    "severity_bucket",
    "priority_score",
    "health_score",
    "recommended_action",
    "suggested_playbook",
    "trend_direction",
    "trend_delta_pp",
    "volume_terminal_pickups",
    "expiration_rate_pct",
    "cancellation_rate_pct",
    "avg_minutes_ready_to_redeemed",
    "alerts_pt",
    "alerts_codes",
  ];

  const lines = [headers.join(",")];

  for (const item of rows) {
    const alerts = buildAlertChips(item);
    const alertsPt = alerts.map((code) => toAlertLabel(code)).join(" | ");
    const trendDir = item?.trend?.direction || item?.signals?.trend_direction || "";
    const trendDelta = item?.trend?.delta ?? item?.signals?.trend_delta;
    const line = [
      escapeCsvCell(item?.entity_type),
      escapeCsvCell(item?.entity_id),
      escapeCsvCell(item?.slot_id ?? (String(item?.entity_type || "").toLowerCase() === "slot" ? item?.entity_id : "")),
      escapeCsvCell(item?.locker_id),
      escapeCsvCell(item?.machine_id),
      escapeCsvCell(item?.site_id),
      escapeCsvCell(item?.region),
      escapeCsvCell(item?.tenant_id),
      escapeCsvCell(item?.operator_id),
      escapeCsvCell(item?.classification),
      escapeCsvCell(item?.severity_bucket),
      escapeCsvCell(formatScore(item?.priority_score)),
      escapeCsvCell(formatScore(item?.health_score)),
      escapeCsvCell(item?.recommended_action),
      escapeCsvCell(item?.suggested_playbook),
      escapeCsvCell(trendDir),
      escapeCsvCell(formatDelta(trendDelta)),
      escapeCsvCell(item?.metrics?.total_terminal_pickups),
      escapeCsvCell(formatPercent(item?.metrics?.expiration_rate)),
      escapeCsvCell(formatPercent(item?.metrics?.cancellation_rate)),
      escapeCsvCell(formatMinutes(item?.metrics?.avg_minutes_ready_to_redeemed)),
      escapeCsvCell(alertsPt),
      escapeCsvCell(alerts.join("|")),
    ].join(",");

    lines.push(line);
  }

  return `\uFEFF${lines.join("\n")}\n`;
}

function triggerDownloadTextFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function buildAlertChips(item) {
  const alerts = Array.isArray(item?.alerts) ? item.alerts : [];
  const anomalyAlerts = Array.isArray(item?.anomaly?.alerts) ? item.anomaly.alerts : [];
  const predictionSignals = Array.isArray(item?.anomaly?.prediction_signals)
    ? item.anomaly.prediction_signals
    : [];
  return [...alerts, ...anomalyAlerts, ...predictionSignals].filter((v, i, arr) => arr.indexOf(v) === i);
}

function toAlertLabel(code) {
  return ALERT_LABELS[code] || String(code || "-").replaceAll("_", " ");
}

/** Slot de entrega: exibe armario/maquina/site (preenchidos pelo backend a partir dos fatos). */
function formatSlotEquipmentLine(item) {
  if (String(item?.entity_type || "").toLowerCase() !== "slot") return "";
  const locker = item?.locker_id;
  const machine = item?.machine_id;
  const site = item?.site_id;
  const bits = [];
  if (locker) bits.push(`armario ${locker}`);
  if (machine) bits.push(`maquina ${machine}`);
  if (site) bits.push(`site ${site}`);
  if (!bits.length) {
    return "sem vínculo nos fatos deste periodo (locker/maquina ausentes)";
  }
  return bits.join(" · ");
}

function buildAutoRefreshLabel(enabled, secondsLeft) {
  if (!enabled) return "Auto-refresh desligado";
  return `Auto-refresh em ${secondsLeft}s`;
}

function buildFilterChipStyle(active, accent) {
  return {
    padding: "10px 14px",
    borderRadius: 12,
    border: active ? `2px solid ${accent}` : "1px solid rgba(255,255,255,0.14)",
    background: active ? `${accent}2a` : "rgba(255,255,255,0.05)",
    color: "#f5f7fa",
    fontWeight: 800,
    cursor: "pointer",
    boxShadow: active ? `0 0 0 1px ${accent}55, 0 10px 22px rgba(0,0,0,0.22)` : "none",
  };
}

export default function PickupHealthPage() {
  const [entityType, setEntityType] = useState("locker");
  const [region, setRegion] = useState("SP");
  const [rankingLimit, setRankingLimit] = useState(20);
  const [trendDaysWindow, setTrendDaysWindow] = useState(7);
  const [includeAlerts, setIncludeAlerts] = useState(true);

  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshIntervalSec, setRefreshIntervalSec] = useState(15);
  const [refreshCountdown, setRefreshCountdown] = useState(15);

  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState(null);
  const [err, setErr] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);
  const [showSelectedItemJson, setShowSelectedItemJson] = useState(false);
  const [showRankingByEntityJson, setShowRankingByEntityJson] = useState(false);
  const [rankingSort, setRankingSort] = useState("priority_desc");
  /** null | "alerta_plus" | "with_alerts" — filtro client-side sobre o ranking ja ordenado */
  const [rankingFilter, setRankingFilter] = useState(null);

  const endpointUrl = useMemo(() => {
    const params = new URLSearchParams();
    params.set("entity_type", entityType);
    params.set("ranking_limit", String(rankingLimit));
    params.set("trend_days_window", String(trendDaysWindow));
    params.set("include_alerts", includeAlerts ? "true" : "false");
    if (region) params.set("region", region);

    return `${ORDER_LIFECYCLE_BASE}/internal/analytics/pickup-health?${params.toString()}`;
  }, [entityType, rankingLimit, trendDaysWindow, includeAlerts, region]);

  async function fetchPickupHealth() {
    setLoading(true);
    setErr("");

    try {
      const res = await fetch(endpointUrl, {
        method: "GET",
        headers: buildHeaders(),
      });

      const text = await res.text();
      let parsed;

      try {
        parsed = text ? JSON.parse(text) : {};
      } catch {
        parsed = { raw: text };
      }

      if (!res.ok) {
        throw new Error(
          prettyJson({
            type: "PICKUP_HEALTH_FETCH_FAILED",
            status: res.status,
            url: endpointUrl,
            response: parsed,
          })
        );
      }

      setPayload(parsed);

      if (selectedItem?.entity_id) {
        const updated = (Array.isArray(parsed?.ranking) ? parsed.ranking : []).find(
          (item) =>
            item?.entity_id === selectedItem.entity_id &&
            item?.entity_type === selectedItem.entity_type
        );
        setSelectedItem(updated || null);
      }
    } catch (e) {
      setErr(String(e?.message || e));
      setPayload(null);
    } finally {
      setLoading(false);
      setRefreshCountdown(refreshIntervalSec);
    }
  }

  useEffect(() => {
    fetchPickupHealth();
  }, [endpointUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!autoRefresh) return;

    const timer = setInterval(() => {
      setRefreshCountdown((prev) => {
        if (prev <= 1) {
          fetchPickupHealth();
          return refreshIntervalSec;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [autoRefresh, refreshIntervalSec, endpointUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  const ranking = Array.isArray(payload?.ranking) ? payload.ranking : [];
  const summary = payload?.summary || {};
  const rankingByEntity = payload?.ranking_by_entity || {};

  const sortedRanking = useMemo(
    () => sortRankingCopy(ranking, rankingSort),
    [ranking, rankingSort]
  );

  const filteredRanking = useMemo(() => {
    if (!rankingFilter) return sortedRanking;
    if (rankingFilter === "alerta_plus") return sortedRanking.filter(matchesAlertaPlus);
    if (rankingFilter === "with_alerts") return sortedRanking.filter(matchesWithAlerts);
    return sortedRanking;
  }, [sortedRanking, rankingFilter]);

  const topThree = useMemo(() => filteredRanking.slice(0, 3), [filteredRanking]);

  useEffect(() => {
    setSelectedItem((prev) => {
      if (!prev?.entity_id) return prev;
      const still = filteredRanking.some(
        (i) => i?.entity_id === prev.entity_id && i?.entity_type === prev.entity_type
      );
      return still ? prev : null;
    });
  }, [filteredRanking]);

  function toggleRankingFilter(next) {
    setRankingFilter((current) => (current === next ? null : next));
  }

  function handleExportRankingCsv() {
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const regionTag = region ? String(region) : "todas";
    const filterTag = rankingFilter || "sem-filtro";
    const filename = `pickup-health-ranking_${entityType}_${regionTag}_${filterTag}_${ts}.csv`;
    const csv = buildPickupHealthRankingCsv(filteredRanking);
    triggerDownloadTextFile(filename, csv, "text/csv;charset=utf-8;");
  }

  return (
    <div style={pageStyle}>
      <section style={headerCardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0 }}>Pickup Health Dashboard</h1>
            <div style={subtleStyle}>
              Priorizacao de risco por entidade, com sinais operacionais e acao recomendada.
            </div>
          </div>

          <div style={{ display: "grid", gap: 6, textAlign: "right" }}>
            <div style={subtleStyle}>
              <b>Base:</b> {ORDER_LIFECYCLE_BASE}
            </div>
            <div style={subtleStyle}>
              <b>Endpoint:</b> /internal/analytics/pickup-health
            </div>
            <div style={subtleStyle}>
              <b>Status:</b> {loading ? "atualizando..." : "pronto"}
            </div>
          </div>
        </div>
      </section>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>Filtros operacionais</h2>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <button onClick={fetchPickupHealth} disabled={loading} style={buttonSecondaryStyle}>
              {loading ? "Atualizando..." : "Atualizar agora"}
            </button>

            <label style={checkboxLabelStyle}>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => {
                  setAutoRefresh(e.target.checked);
                  setRefreshCountdown(refreshIntervalSec);
                }}
              />
              {buildAutoRefreshLabel(autoRefresh, refreshCountdown)}
            </label>
          </div>
        </div>

        <div style={fieldGridStyle}>
          <label style={labelStyle}>
            Entidade
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              style={inputStyle}
            >
              {ENTITY_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label style={labelStyle}>
            Região
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              style={inputStyle}
            >
              {REGION_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label style={labelStyle}>
            Limite do ranking
            <input
              type="number"
              min={1}
              max={100}
              value={rankingLimit}
              onChange={(e) => setRankingLimit(Number(e.target.value || 20))}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Janela de tendência (dias)
            <input
              type="number"
              min={1}
              max={90}
              value={trendDaysWindow}
              onChange={(e) => setTrendDaysWindow(Number(e.target.value || 7))}
              style={inputStyle}
            />
          </label>

          <label style={labelStyle}>
            Intervalo auto-refresh (seg)
            <input
              type="number"
              min={5}
              max={120}
              value={refreshIntervalSec}
              onChange={(e) => {
                const value = Number(e.target.value || 15);
                setRefreshIntervalSec(value);
                setRefreshCountdown(value);
              }}
              style={inputStyle}
            />
          </label>

          <label style={checkboxLabelStyle}>
            <input
              type="checkbox"
              checked={includeAlerts}
              onChange={(e) => setIncludeAlerts(e.target.checked)}
            />
            Incluir alertas
          </label>
        </div>
      </section>

      {err ? (
        <section style={cardStyle}>
          <h2 style={h2Style}>Erro rico</h2>
          <pre style={errorBoxStyle}>{err}</pre>
        </section>
      ) : null}

      <section style={summaryGridStyle}>
        <SummaryCard title="Entidades" value={summary.total_entities} accent="#64748b" />
        <SummaryCard title="Saudavel" value={summary.healthy_count} accent={CLASSIFICATION_VISUAL.healthy.accent} />
        <SummaryCard title="Atencao" value={summary.attention_count} accent={CLASSIFICATION_VISUAL.attention.accent} />
        <SummaryCard title="Alerta" value={summary.warning_count} accent={CLASSIFICATION_VISUAL.warning.accent} />
        <SummaryCard title="Critico" value={summary.critical_count} accent={CLASSIFICATION_VISUAL.critical.accent} />
        <SummaryCard title="Colapsado" value={summary.collapsed_count} accent={CLASSIFICATION_VISUAL.collapsed.accent} />
      </section>

      <section style={queueCardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>Fila e ordenacao</h2>
          <div style={subtleStyle}>Ordena o ranking e o destaque abaixo</div>
        </div>
        <div style={queueControlsStyle}>
          <label style={labelStyle}>
            Ordenar ranking por
            <select
              value={rankingSort}
              onChange={(e) => setRankingSort(e.target.value)}
              style={inputStyle}
            >
              {RANKING_SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={filterToolbarStyle}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <button
              type="button"
              onClick={() => toggleRankingFilter("alerta_plus")}
              style={buildFilterChipStyle(rankingFilter === "alerta_plus", CLASSIFICATION_VISUAL.warning.accent)}
              title="Classificacao warning/critical/collapsed (e buckets equivalentes quando classificacao nao veio)"
            >
              So alerta+
            </button>
            <button
              type="button"
              onClick={() => toggleRankingFilter("with_alerts")}
              style={buildFilterChipStyle(rankingFilter === "with_alerts", "#38bdf8")}
              title="Itens com alertas operacionais ou sinais preditivos (chips na lista)"
            >
              So com alertas
            </button>
            {rankingFilter ? (
              <button type="button" onClick={() => setRankingFilter(null)} style={filterClearButtonStyle}>
                Limpar filtro
              </button>
            ) : null}
          </div>

          <button
            type="button"
            onClick={handleExportRankingCsv}
            disabled={filteredRanking.length === 0}
            style={{
              ...exportCsvButtonStyle,
              opacity: filteredRanking.length === 0 ? 0.45 : 1,
              cursor: filteredRanking.length === 0 ? "not-allowed" : "pointer",
            }}
            title="Exporta o ranking visivel (ordenacao + filtro) em CSV com BOM para Excel"
          >
            Exportar CSV
          </button>
        </div>

        {rankingFilter ? (
          <div style={{ ...subtleStyle, marginTop: 10 }}>
            Filtro ativo:{" "}
            <b>
              {rankingFilter === "alerta_plus"
                ? "So alerta+ (warning/critical/collapsed + fallback de bucket)"
                : "So com alertas (chips nao vazios)"}
            </b>
            {" · "}
            mostrando <b>{filteredRanking.length}</b> de <b>{sortedRanking.length}</b>
          </div>
        ) : null}

        {sortedRanking.length > 0 ? (
          <div style={{ marginTop: 14 }}>
            <div style={{ fontWeight: 800, marginBottom: 8 }}>
              Destaque (3 primeiros na ordenacao{rankingFilter ? " e filtro" : ""})
            </div>
            <div style={priorityStripStyle}>
              {topThree.map((item, idx) => {
                const v = buildRowVisual(item);
                return (
                  <button
                    key={`top-${item?.entity_type}-${item?.entity_id}-${idx}`}
                    type="button"
                    onClick={() => setSelectedItem(item)}
                    style={{
                      ...priorityPillStyle,
                      borderColor: v.border,
                      background: v.bg,
                      boxShadow: `0 0 0 1px ${v.accent}33`,
                    }}
                  >
                    <span style={{ fontWeight: 900, color: v.accent }}>#{idx + 1}</span>
                    <span style={{ fontWeight: 800 }}>{item?.entity_id || "N/D"}</span>
                    <span style={subtleStyle}>
                      P {formatScore(item?.priority_score)} · S {formatScore(item?.health_score)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </section>

      <div style={dashboardGridStyle}>
        <section style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <h2 style={h2Style}>Ranking operacional</h2>
            <div style={subtleStyle}>
              {rankingFilter
                ? `${filteredRanking.length} exibidos de ${sortedRanking.length} (filtro ativo)`
                : `${filteredRanking.length} itens`}
              {rankingSort !== "api" ? ` · ordenado: ${RANKING_SORT_OPTIONS.find((o) => o.value === rankingSort)?.label || rankingSort}` : null}
            </div>
          </div>

          {!loading && sortedRanking.length === 0 ? (
            <div style={subtleStyle}>Nenhum dado retornado.</div>
          ) : !loading && filteredRanking.length === 0 ? (
            <div style={subtleStyle}>Nenhum item corresponde ao filtro rapido.</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {filteredRanking.map((item, index) => {
                const rowVisual = buildRowVisual(item);
                const alertChips = buildAlertChips(item);
                const isSelected =
                  Boolean(selectedItem?.entity_id) &&
                  selectedItem?.entity_id === item?.entity_id &&
                  selectedItem?.entity_type === item?.entity_type;

                return (
                  <button
                    key={`${item?.entity_type}-${item?.entity_id || index}`}
                    type="button"
                    onClick={() => setSelectedItem(item)}
                    style={{
                      ...rankingItemStyle,
                      background: rowVisual.bg,
                      border: `2px solid ${rowVisual.border}`,
                      borderLeft: `8px solid ${rowVisual.accent}`,
                      boxShadow: isSelected
                        ? `0 0 0 2px #f8fafc, 0 0 0 6px ${rowVisual.accent}, 0 12px 28px rgba(0,0,0,0.35)`
                        : `0 10px 22px rgba(0,0,0,0.22)`,
                      outline: "none",
                    }}
                  >
                    <div style={rankingHeaderStyle}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 15 }}>
                          {item?.entity_type || "-"} • {item?.entity_id || "N/D"}
                        </div>
                        {String(item?.entity_type || "").toLowerCase() === "slot" ? (
                          <div
                            style={{
                              marginTop: 6,
                              fontSize: 12,
                              fontWeight: 700,
                              color: "#bae6fd",
                              lineHeight: 1.35,
                            }}
                          >
                            Equipamento:{" "}
                            <span style={{ fontWeight: 600, color: "#e0f2fe" }}>{formatSlotEquipmentLine(item)}</span>
                          </div>
                        ) : null}
                        <div style={subtleStyle}>
                          tenant: <b>{item?.tenant_id || "-"}</b> • operador: <b>{item?.operator_id || "-"}</b> • regiao: <b>{item?.region || "-"}</b>
                        </div>
                        {buildClassificationVisual(item?.classification) ? (
                          <div style={{ ...subtleStyle, marginTop: 4, fontSize: 11 }}>
                            Bucket derivado: <b>{item?.severity_bucket || "-"}</b>
                          </div>
                        ) : null}
                      </div>

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                        <ClassificationChip label={rowVisual.label} accent={rowVisual.accent} />
                        {buildClassificationVisual(item?.classification) ? (
                          <Badge variant="muted">{buildSeverityMeta(item?.severity_bucket).label}</Badge>
                        ) : null}
                        <Badge>prioridade {formatScore(item?.priority_score)}</Badge>
                        <Badge>saude {formatScore(item?.health_score)}</Badge>
                      </div>
                    </div>

                    <div style={metricRowStyle}>
                      <div><b>acao sugerida:</b> {item?.recommended_action || "-"}</div>
                      <div><b>playbook:</b> {item?.suggested_playbook || "-"}</div>
                      <div><b>tendencia:</b> {item?.trend?.direction || item?.signals?.trend_direction || "-"}</div>
                      <div><b>delta tendencia:</b> {formatDelta(item?.trend?.delta)}</div>
                    </div>

                    <div style={metricRowStyle}>
                      <div><b>volume:</b> {item?.metrics?.total_terminal_pickups ?? "-"}</div>
                      <div><b>expiracao:</b> {formatPercent(item?.metrics?.expiration_rate)}</div>
                      <div><b>cancelamento:</b> {formatPercent(item?.metrics?.cancellation_rate)}</div>
                      <div><b>SLA ready→redeemed:</b> {formatMinutes(item?.metrics?.avg_minutes_ready_to_redeemed)}</div>
                    </div>

                    {alertChips.length > 0 ? (
                      <div style={chipsRowStyle}>
                        {alertChips.map((alert) => (
                          <Badge key={alert}>{toAlertLabel(alert)}</Badge>
                        ))}
                      </div>
                    ) : null}
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <section style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <h2 style={h2Style}>Drill-down da entidade</h2>
            <div style={subtleStyle}>
              {selectedItem ? `${selectedItem.entity_type} • ${selectedItem.entity_id}` : "Selecione um item"}
            </div>
          </div>

          {!selectedItem ? (
            <div style={subtleStyle}>
              Clique em um item do ranking para abrir detalhes operacionais, sinais, baseline e anomalias.
            </div>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              <div style={detailCardStyle}>
                <h3 style={h3Style}>Resumo operacional</h3>
                <div><b>entidade:</b> {selectedItem.entity_type} • {selectedItem.entity_id}</div>
                {String(selectedItem.entity_type || "").toLowerCase() === "slot" ? (
                  <>
                    <div><b>slot (id):</b> {selectedItem.slot_id || selectedItem.entity_id}</div>
                    <div>
                      <b>equipamento (dominante no periodo):</b> {formatSlotEquipmentLine(selectedItem)}
                    </div>
                    <div><b>armario:</b> {selectedItem.locker_id || "-"}</div>
                    <div><b>maquina:</b> {selectedItem.machine_id || "-"}</div>
                    <div><b>site:</b> {selectedItem.site_id || "-"}</div>
                  </>
                ) : null}
                <div><b>regiao:</b> {selectedItem.region || "-"}</div>
                <div><b>classificacao:</b> {selectedItem.classification || "-"}</div>
                <div><b>bucket derivado:</b> {selectedItem.severity_bucket || "-"}</div>
                <div><b>saude:</b> {formatScore(selectedItem.health_score)}</div>
                <div><b>prioridade:</b> {formatScore(selectedItem.priority_score)}</div>
                <div><b>acao recomendada:</b> {selectedItem.recommended_action || "-"}</div>
                <div><b>playbook:</b> {selectedItem.suggested_playbook || "-"}</div>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Sinais chave</h3>
                <div><b>taxa sucesso pickup:</b> {formatPercent((selectedItem?.signals?.pickup_success_rate ?? 0) * 100)}</div>
                <div><b>expiracao:</b> {formatPercent((selectedItem?.signals?.expiration_rate ?? 0) * 100)}</div>
                <div><b>cancelamento:</b> {formatPercent((selectedItem?.signals?.cancel_rate ?? 0) * 100)}</div>
                <div><b>tempo medio pickup:</b> {formatMinutes(selectedItem?.signals?.avg_pickup_minutes)}</div>
                <div><b>tamanho da amostra:</b> {selectedItem?.signals?.sample_size ?? "-"}</div>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Anomalias e baseline</h3>
                <div><b>queda abrupta:</b> {selectedItem?.anomaly?.abrupt_drop ? "sim" : "nao"}</div>
                <div><b>fora do padrao:</b> {selectedItem?.anomaly?.out_of_pattern ? "sim" : "nao"}</div>
                <div><b>risco preditivo:</b> {selectedItem?.anomaly?.predictive_risk ? "sim" : "nao"}</div>
                <div><b>media baseline:</b> {formatPercent(selectedItem?.baseline?.mean_rate)}</div>
                <div><b>desvio baseline:</b> {formatScore(selectedItem?.baseline?.stddev_rate)}</div>
                <div><b>historico baseline:</b> {selectedItem?.baseline?.history_count ?? "-"}</div>
              </div>

              <div style={detailCardStyle}>
                <button
                  type="button"
                  onClick={() => setShowSelectedItemJson((v) => !v)}
                  style={buttonSecondaryStyle}
                >
                  {showSelectedItemJson ? "Ocultar JSON tecnico do item" : "Mostrar JSON tecnico do item"}
                </button>
                {showSelectedItemJson ? <pre style={preStyle}>{prettyJson(selectedItem)}</pre> : null}
              </div>
            </div>
          )}
        </section>
      </div>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>Ranking por entidade</h2>
          <div style={subtleStyle}>Visao tecnica consolidada</div>
        </div>
        <button
          type="button"
          onClick={() => setShowRankingByEntityJson((v) => !v)}
          style={buttonSecondaryStyle}
        >
          {showRankingByEntityJson ? "Ocultar JSON estrutural" : "Mostrar JSON estrutural"}
        </button>
        {showRankingByEntityJson ? <pre style={{ ...preStyle, marginTop: 12 }}>{prettyJson(rankingByEntity)}</pre> : null}
      </section>
    </div>
  );
}

function SummaryCard({ title, value, accent }) {
  return (
    <div
      style={{
        ...summaryCardStyle,
        ...(accent
          ? {
              borderLeft: `6px solid ${accent}`,
            }
          : {}),
      }}
    >
      <div style={summaryTitleStyle}>{title}</div>
      <div style={summaryValueStyle}>{value ?? "-"}</div>
    </div>
  );
}

function Badge({ children, variant = "default" }) {
  if (variant === "muted") {
    return <span style={{ ...badgeStyle, ...badgeMutedStyle }}>{children}</span>;
  }
  return <span style={badgeStyle}>{children}</span>;
}

function ClassificationChip({ label, accent }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "6px 12px",
        borderRadius: 999,
        border: `2px solid ${accent}`,
        background: `linear-gradient(180deg, ${accent} 0%, ${accent}cc 100%)`,
        color: "#0b0f14",
        fontSize: 11,
        fontWeight: 900,
        letterSpacing: 0.35,
        textTransform: "uppercase",
        boxShadow: `0 8px 18px ${accent}55`,
      }}
    >
      {label}
    </span>
  );
}

const pageStyle = {
  padding: 24,
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const headerCardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxShadow: "0 8px 24px rgba(0,0,0,0.22)",
  marginBottom: 16,
};

const cardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxShadow: "0 8px 24px rgba(0,0,0,0.22)",
  marginBottom: 16,
};

const sectionHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
};

const h2Style = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: 18,
};

const h3Style = {
  marginTop: 0,
  marginBottom: 8,
  fontSize: 15,
};

const subtleStyle = {
  opacity: 0.78,
  fontSize: 12,
};

const fieldGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
  marginTop: 12,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const checkboxLabelStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  fontSize: 14,
  paddingTop: 26,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const buttonSecondaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "white",
  fontWeight: 600,
};

const queueCardStyle = {
  ...cardStyle,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "linear-gradient(180deg, rgba(17,22,28,0.98), rgba(11,15,20,0.98))",
};

const queueControlsStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  gap: 12,
  marginTop: 4,
};

const filterToolbarStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 12,
  flexWrap: "wrap",
  marginTop: 12,
  paddingTop: 12,
  borderTop: "1px solid rgba(255,255,255,0.10)",
};

const filterClearButtonStyle = {
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.55)",
  color: "rgba(226,232,240,0.95)",
  fontWeight: 700,
  cursor: "pointer",
};

const exportCsvButtonStyle = {
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid rgba(56, 189, 248, 0.45)",
  background: "rgba(14, 165, 233, 0.22)",
  color: "#e0f2fe",
  fontWeight: 800,
  cursor: "pointer",
};

const priorityStripStyle = {
  display: "flex",
  gap: 10,
  flexWrap: "wrap",
};

const priorityPillStyle = {
  display: "grid",
  gap: 4,
  padding: "10px 12px",
  borderRadius: 14,
  border: "2px solid rgba(255,255,255,0.18)",
  cursor: "pointer",
  textAlign: "left",
  color: "#f5f7fa",
  minWidth: 200,
};

const summaryGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
  gap: 12,
  marginBottom: 16,
};

const summaryCardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
};

const summaryTitleStyle = {
  fontSize: 12,
  opacity: 0.72,
};

const summaryValueStyle = {
  fontSize: 24,
  fontWeight: 800,
  marginTop: 6,
};

const dashboardGridStyle = {
  display: "grid",
  gridTemplateColumns: "1.2fr 0.9fr",
  gap: 16,
  alignItems: "start",
};

const rankingItemStyle = {
  borderRadius: 14,
  padding: 12,
  textAlign: "left",
  color: "#f5f7fa",
  cursor: "pointer",
  display: "grid",
  gap: 8,
};

const rankingHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "start",
  gap: 10,
  flexWrap: "wrap",
};

const metricRowStyle = {
  display: "grid",
  gap: 6,
  fontSize: 13,
};

const chipsRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const badgeStyle = {
  display: "inline-flex",
  padding: "4px 8px",
  borderRadius: 999,
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.14)",
  fontSize: 11,
  fontWeight: 700,
};

const badgeMutedStyle = {
  background: "rgba(15,23,42,0.55)",
  border: "1px solid rgba(148,163,184,0.35)",
  color: "rgba(226,232,240,0.92)",
  fontWeight: 600,
};

const detailCardStyle = {
  padding: 12,
  borderRadius: 12,
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.08)",
  display: "grid",
  gap: 6,
  fontSize: 13,
};

const preStyle = {
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12,
  padding: 12,
  overflow: "auto",
  margin: 0,
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};

const errorBoxStyle = {
  margin: 0,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
};