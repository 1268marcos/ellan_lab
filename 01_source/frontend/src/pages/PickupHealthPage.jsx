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

const SEVERITY_META = {
  normal: {
    label: "Normal",
    bg: "rgba(31,122,63,0.14)",
    border: "rgba(31,122,63,0.40)",
    accent: "#1f7a3f",
  },
  attention: {
    label: "Atenção",
    bg: "rgba(199,146,0,0.14)",
    border: "rgba(199,146,0,0.40)",
    accent: "#c79200",
  },
  critical: {
    label: "Crítico",
    bg: "rgba(239,108,0,0.14)",
    border: "rgba(239,108,0,0.42)",
    accent: "#ef6c00",
  },
  incident: {
    label: "Incidente",
    bg: "rgba(179,38,30,0.18)",
    border: "rgba(179,38,30,0.46)",
    accent: "#b3261e",
  },
};

function formatScore(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "-";
  return n.toFixed(2);
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

function buildAlertChips(item) {
  const alerts = Array.isArray(item?.alerts) ? item.alerts : [];
  const anomalyAlerts = Array.isArray(item?.anomaly?.alerts) ? item.anomaly.alerts : [];
  return [...alerts, ...anomalyAlerts].filter((v, i, arr) => arr.indexOf(v) === i);
}

function buildAutoRefreshLabel(enabled, secondsLeft) {
  if (!enabled) return "Auto-refresh desligado";
  return `Auto-refresh em ${secondsLeft}s`;
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

  return (
    <div style={pageStyle}>
      <section style={headerCardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0 }}>Pickup Health Dashboard</h1>
            <div style={subtleStyle}>
              Ranking ordenado, severidade, anomalias, auto-refresh e drill-down operacional.
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
            Incluir alerts
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
        <SummaryCard title="Entidades" value={summary.total_entities} />
        <SummaryCard title="Healthy" value={summary.healthy_count} />
        <SummaryCard title="Attention" value={summary.attention_count} />
        <SummaryCard title="Warning" value={summary.warning_count} />
        <SummaryCard title="Critical" value={summary.critical_count} />
        <SummaryCard title="Collapsed" value={summary.collapsed_count} />
      </section>

      <div style={dashboardGridStyle}>
        <section style={cardStyle}>
          <div style={sectionHeaderStyle}>
            <h2 style={h2Style}>Ranking operacional</h2>
            <div style={subtleStyle}>{ranking.length} itens</div>
          </div>

          {!loading && ranking.length === 0 ? (
            <div style={subtleStyle}>Nenhum dado retornado.</div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {ranking.map((item, index) => {
                const severity = buildSeverityMeta(item?.severity_bucket);
                const alertChips = buildAlertChips(item);

                return (
                  <button
                    key={`${item?.entity_type}-${item?.entity_id || index}`}
                    type="button"
                    onClick={() => setSelectedItem(item)}
                    style={{
                      ...rankingItemStyle,
                      background: severity.bg,
                      border: `1px solid ${severity.border}`,
                      borderLeft: `6px solid ${severity.accent}`,
                    }}
                  >
                    <div style={rankingHeaderStyle}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 15 }}>
                          {item?.entity_type || "-"} • {item?.entity_id || "N/D"}
                        </div>
                        <div style={subtleStyle}>
                          tenant: <b>{item?.tenant_id || "-"}</b> • operator: <b>{item?.operator_id || "-"}</b> • region: <b>{item?.region || "-"}</b>
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                        <Badge>{severity.label}</Badge>
                        <Badge>priority {formatScore(item?.priority_score)}</Badge>
                        <Badge>health {formatScore(item?.health_score)}</Badge>
                      </div>
                    </div>

                    <div style={metricRowStyle}>
                      <div><b>playbook:</b> {item?.suggested_playbook || "-"}</div>
                      <div><b>trend:</b> {item?.trend?.direction || item?.signals?.trend_direction || "-"}</div>
                      <div><b>delta:</b> {formatScore(item?.trend?.delta)}</div>
                      <div><b>volume:</b> {item?.metrics?.total_terminal_pickups ?? "-"}</div>
                    </div>

                    <div style={metricRowStyle}>
                      <div><b>expiração:</b> {formatScore(item?.metrics?.expiration_rate)}</div>
                      <div><b>cancelamento:</b> {formatScore(item?.metrics?.cancellation_rate)}</div>
                      <div><b>SLA ready→redeemed:</b> {formatScore(item?.metrics?.avg_minutes_ready_to_redeemed)}</div>
                    </div>

                    {alertChips.length > 0 ? (
                      <div style={chipsRowStyle}>
                        {alertChips.map((alert) => (
                          <Badge key={alert}>{alert}</Badge>
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
                <div><b>entity_type:</b> {selectedItem.entity_type}</div>
                <div><b>entity_id:</b> {selectedItem.entity_id}</div>
                <div><b>priority_score:</b> {formatScore(selectedItem.priority_score)}</div>
                <div><b>health_score:</b> {formatScore(selectedItem.health_score)}</div>
                <div><b>severity_bucket:</b> {selectedItem.severity_bucket || "-"}</div>
                <div><b>suggested_playbook:</b> {selectedItem.suggested_playbook || "-"}</div>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Trend</h3>
                <pre style={preStyle}>{prettyJson(selectedItem.trend || {})}</pre>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Anomaly</h3>
                <pre style={preStyle}>{prettyJson(selectedItem.anomaly || {})}</pre>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Baseline</h3>
                <pre style={preStyle}>{prettyJson(selectedItem.baseline || {})}</pre>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Signals</h3>
                <pre style={preStyle}>{prettyJson(selectedItem.signals || {})}</pre>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>Metrics</h3>
                <pre style={preStyle}>{prettyJson(selectedItem.metrics || {})}</pre>
              </div>

              <div style={detailCardStyle}>
                <h3 style={h3Style}>JSON bruto do item</h3>
                <pre style={preStyle}>{prettyJson(selectedItem)}</pre>
              </div>
            </div>
          )}
        </section>
      </div>

      <section style={cardStyle}>
        <div style={sectionHeaderStyle}>
          <h2 style={h2Style}>Ranking por entidade</h2>
          <div style={subtleStyle}>Drill-down estrutural</div>
        </div>

        <pre style={preStyle}>{prettyJson(rankingByEntity)}</pre>
      </section>
    </div>
  );
}

function SummaryCard({ title, value }) {
  return (
    <div style={summaryCardStyle}>
      <div style={summaryTitleStyle}>{title}</div>
      <div style={summaryValueStyle}>{value ?? "-"}</div>
    </div>
  );
}

function Badge({ children }) {
  return <span style={badgeStyle}>{children}</span>;
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