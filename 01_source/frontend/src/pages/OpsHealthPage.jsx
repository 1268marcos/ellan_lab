import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const OPS_HEALTH_WINDOW_PREF_KEY = "ops_health:window_hours";
const OPS_HEALTH_WINDOW_PRESETS = [1, 6, 12, 24, 48, 72, 168];

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

export default function OpsHealthPage() {
  const { token } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    void loadMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, lookbackHours]);

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
              Métricas e alertas de reconciliação para prevenção de incidentes.
            </p>
          </div>
          <div style={toolbarStyle}>
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

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {!error && loading ? (
          <p style={{ marginBottom: 0 }}>Carregando métricas...</p>
        ) : null}

        {!error && !loading && metrics ? (
          <>
            <div style={kpiGridStyle}>
              <OpsTrendKpiCard label="Ações OPS" value={metrics?.kpis?.total_ops_actions ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard
                label="Taxa de erro"
                value={`${(Number(metrics?.kpis?.error_rate || 0) * 100).toFixed(1)}%`}
                baseStyle={kpiBoxStyle}
                showTrend={false}
              />
              <OpsTrendKpiCard label="Reconciliações" value={metrics?.kpis?.reconciliation_actions ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard label="Pendências abertas" value={metrics?.kpis?.pending_open_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard label="Retry pronto" value={metrics?.kpis?.pending_due_retry_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard label="PROCESSING stale" value={metrics?.kpis?.pending_processing_stale_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard label="FAILED_FINAL" value={metrics?.kpis?.pending_failed_final_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard
                label="Idade média pendência (min)"
                value={metrics?.kpis?.avg_open_pending_age_min ?? 0}
                baseStyle={kpiBoxStyle}
                showTrend={false}
              />
            </div>

            <div style={{ marginTop: 10, color: "rgba(245,247,250,0.78)", fontSize: 13 }}>
              Janela: {metrics?.window?.from ? new Date(metrics.window.from).toLocaleString("pt-BR") : "-"} até{" "}
              {metrics?.window?.to ? new Date(metrics.window.to).toLocaleString("pt-BR") : "-"}
            </div>

            <div style={alertsWrapStyle}>
              {(metrics?.alerts || []).length === 0 ? (
                <span style={getSeverityBadgeStyle("OK")}>Sem alertas ativos</span>
              ) : (
                (metrics?.alerts || []).map((alert, index) => (
                  <span key={`${alert.code}-${index}`} style={getSeverityBadgeStyle(alert.severity)}>
                    {alert.code}: {alert.message}
                  </span>
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

const kpiGridStyle = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
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
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

