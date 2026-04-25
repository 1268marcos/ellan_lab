import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const SESSION_HISTORY_KEY = "ops_reconciliation_history_v1";
const OPS_RECON_HEALTH_WINDOW_PREF_KEY = "ops_reconciliation:health_window_hours";
const OPS_RECON_HEALTH_WINDOW_PRESETS = [6, 12, 24, 48, 72, 168];
const MAX_HISTORY_ITEMS = 10;

function extractErrorMessage(payload, fallback = "Não foi possível reconciliar o pedido.") {
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

export default function OpsReconciliationPage() {
  const { token } = useAuth();
  const [orderId, setOrderId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [historyFilter, setHistoryFilter] = useState("ALL");
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState("");
  const {
    windowValue: healthLookbackHours,
    applyPreset: applyHealthWindowPreset,
  } = useOpsWindowPreset({
    storageKey: OPS_RECON_HEALTH_WINDOW_PREF_KEY,
    defaultValue: 24,
    minValue: 1,
    maxValue: 168,
    presetValues: OPS_RECON_HEALTH_WINDOW_PRESETS,
  });

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem(SESSION_HISTORY_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setHistory(parsed);
      }
    } catch {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      window.sessionStorage.setItem(SESSION_HISTORY_KEY, JSON.stringify(history));
    } catch {
      // no-op
    }
  }, [history]);

  const filteredHistory = useMemo(() => {
    if (historyFilter === "ALL") return history;
    if (historyFilter === "OK") return history.filter((item) => Boolean(item.ok));
    return history.filter((item) => !item.ok);
  }, [history, historyFilter]);

  const historyCounts = useMemo(() => {
    const ok = history.filter((item) => Boolean(item.ok)).length;
    const error = history.length - ok;
    return {
      all: history.length,
      ok,
      error,
    };
  }, [history]);

  async function loadOpsHealth({ silent = false } = {}) {
    if (!token) return;
    if (!silent) {
      setHealthLoading(true);
      setHealthError("");
    }
    try {
      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/ops-metrics?lookback_hours=${Math.max(Number(healthLookbackHours || 24), 1)}`,
        {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
        }
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar saúde operacional."));
      }
      setHealth(payload || null);
    } catch (err) {
      setHealthError(String(err?.message || err));
    } finally {
      if (!silent) setHealthLoading(false);
    }
  }

  useEffect(() => {
    void loadOpsHealth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, healthLookbackHours]);

  async function handleReconcile() {
    const normalizedOrderId = String(orderId || "").trim();
    if (!normalizedOrderId) {
      setError("Informe um order_id válido antes de executar a reconciliação.");
      return;
    }

    setRunning(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/reconcile-order`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          order_id: normalizedOrderId,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
      }

      setResult(payload);
      void loadOpsHealth({ silent: true });
      setHistory((previous) => {
        const item = {
          key: `${Date.now()}-${payload.order_id || normalizedOrderId}`,
          executedAt: new Date().toISOString(),
          order_id: payload.order_id || normalizedOrderId,
          ok: Boolean(payload.ok),
          status: payload.status || "-",
          message: payload.message || "",
          compensation: payload.compensation || {},
        };
        return [item, ...previous].slice(0, MAX_HISTORY_ITEMS);
      });
    } catch (err) {
      const errorMessage = String(err?.message || err);
      setError(errorMessage);
      setHistory((previous) => {
        const item = {
          key: `${Date.now()}-error-${normalizedOrderId}`,
          executedAt: new Date().toISOString(),
          order_id: normalizedOrderId,
          ok: false,
          status: "ERROR",
          message: errorMessage,
          compensation: {},
        };
        return [item, ...previous].slice(0, MAX_HISTORY_ITEMS);
      });
    } finally {
      setRunning(false);
    }
  }

  function handleUseOrderFromHistory(value) {
    setOrderId(String(value || ""));
  }

  function handleClearHistory() {
    setHistory([]);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ver saúde
          </Link>
        </div>
        <div style={healthHeaderStyle}>
          <h2 style={{ margin: 0 }}>Saúde Operacional ({healthLookbackHours}h)</h2>
          <button
            type="button"
            onClick={() => void loadOpsHealth()}
            disabled={healthLoading}
            style={buttonGhostStyle}
          >
            {healthLoading ? "Atualizando..." : "Atualizar"}
          </button>
        </div>
        <div style={healthPresetRowStyle}>
          <span style={healthPresetLabelStyle}>Presets de janela</span>
          {OPS_RECON_HEALTH_WINDOW_PRESETS.map((hours) => (
            <button
              key={hours}
              type="button"
              onClick={() => applyHealthWindowPreset(hours)}
              style={healthPresetButtonStyle(healthLookbackHours === hours)}
            >
              {hours < 24 ? `${hours}h` : hours === 24 ? "24h" : hours === 168 ? "7d" : `${Math.floor(hours / 24)}d`}
            </button>
          ))}
        </div>

        {healthError ? (
          <pre style={errorStyle}>{healthError}</pre>
        ) : health ? (
          <>
            <div style={kpiGridStyle}>
              <OpsTrendKpiCard label="Ações OPS" value={health?.kpis?.total_ops_actions ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard
                label="Taxa de erro"
                value={`${(Number(health?.kpis?.error_rate || 0) * 100).toFixed(1)}%`}
                baseStyle={kpiBoxStyle}
                showTrend={false}
              />
              <OpsTrendKpiCard label="Pendências abertas" value={health?.kpis?.pending_open_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
              <OpsTrendKpiCard label="FAILED_FINAL" value={health?.kpis?.pending_failed_final_count ?? 0} baseStyle={kpiBoxStyle} showTrend={false} />
            </div>

            <div style={{ marginTop: 10, color: "rgba(245, 247, 250, 0.78)", fontSize: 13 }}>
              Janela: {health?.window?.from ? new Date(health.window.from).toLocaleString("pt-BR") : "-"} até{" "}
              {health?.window?.to ? new Date(health.window.to).toLocaleString("pt-BR") : "-"}
            </div>

            <div style={alertsWrapStyle}>
              {(health?.alerts || []).length === 0 ? (
                <span style={getSeverityBadgeStyle("OK")}>Sem alertas ativos</span>
              ) : (
                (health?.alerts || []).map((alert, index) => (
                  <span key={`${alert.code}-${index}`} style={getSeverityBadgeStyle(alert.severity)}>
                    {alert.code}: {alert.message}
                  </span>
                ))
              )}
            </div>
          </>
        ) : (
          <p style={{ marginBottom: 0, color: "rgba(245, 247, 250, 0.8)" }}>
            Carregando saúde operacional...
          </p>
        )}
      </section>

      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Reconciliação de pedido</h1>
        <p style={mutedTextStyle}>
          Use esta ação para reconciliar pedidos com crédito e/ou slot presos por falha parcial.
          Informe o <code>order_id</code> e execute.
        </p>

        <label style={labelStyle}>
          Order ID
          <input
            type="text"
            value={orderId}
            onChange={(event) => setOrderId(event.target.value)}
            placeholder="Ex.: 3cf0bf89-edd2-4fc6-9dc0-ed4a933df031"
            style={inputStyle}
          />
        </label>

        <div style={toolbarStyle}>
          <button onClick={handleReconcile} disabled={running} style={buttonPrimaryStyle}>
            {running ? "Reconciliando..." : "Executar reconciliação"}
          </button>
        </div>
      </section>

      {result ? (
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Resultado</h2>
          <div style={summaryBoxStyle}>
            <div>
              <b>ok:</b> {String(result.ok)}
            </div>
            <div>
              <b>order_id:</b> {result.order_id}
            </div>
            <div>
              <b>status:</b> {result.status}
            </div>
            <div>
              <b>message:</b> {result.message}
            </div>
          </div>

          <h3>Compensation</h3>
          <pre style={preStyle}>{JSON.stringify(result.compensation || {}, null, 2)}</pre>
        </section>
      ) : null}

      <section style={cardStyle}>
        <div style={historyHeaderStyle}>
          <h2 style={{ margin: 0 }}>Histórico local da sessão</h2>
          <div style={historyToolbarStyle}>
            <div style={filterGroupStyle}>
              <button
                type="button"
                onClick={() => setHistoryFilter("ALL")}
                style={filterButtonStyle(historyFilter === "ALL")}
              >
                Todos ({historyCounts.all})
              </button>
              <button
                type="button"
                onClick={() => setHistoryFilter("OK")}
                style={filterButtonStyle(historyFilter === "OK", "OK")}
              >
                OK ({historyCounts.ok})
              </button>
              <button
                type="button"
                onClick={() => setHistoryFilter("ERROR")}
                style={filterButtonStyle(historyFilter === "ERROR", "ERROR")}
              >
                ERRO ({historyCounts.error})
              </button>
            </div>
            <button
              type="button"
              onClick={handleClearHistory}
              disabled={history.length === 0}
              style={buttonGhostStyle}
            >
              Limpar histórico
            </button>
          </div>
        </div>

        {history.length === 0 ? (
          <p style={{ marginBottom: 0, color: "rgba(245, 247, 250, 0.8)" }}>
            Nenhuma reconciliação executada nesta sessão ainda.
          </p>
        ) : filteredHistory.length === 0 ? (
          <p style={{ marginBottom: 0, color: "rgba(245, 247, 250, 0.8)" }}>
            Nenhum item encontrado para o filtro selecionado.
          </p>
        ) : (
          <div style={historyListStyle}>
            {filteredHistory.map((item) => (
              <article key={item.key} style={historyItemStyle}>
                <div style={historyTopRowStyle}>
                  <strong>{item.order_id}</strong>
                  <span style={getSeverityBadgeStyle(item.ok ? "OK" : "ERROR")}>
                    {item.ok ? "OK" : "ERRO"}
                  </span>
                </div>
                <div style={historyMetaStyle}>
                  <span>
                    <b>Status:</b> {item.status}
                  </span>
                  <span>
                    <b>Executado em:</b> {new Date(item.executedAt).toLocaleString("pt-BR")}
                  </span>
                </div>
                <div style={historyActionsStyle}>
                  <button
                    type="button"
                    onClick={() => handleUseOrderFromHistory(item.order_id)}
                    style={buttonGhostStyle}
                  >
                    Reusar order_id
                  </button>
                  <Link to={`/meus-pedidos/${encodeURIComponent(item.order_id)}`}>Ver pedido</Link>
                </div>
                <pre style={preStyle}>
                  {JSON.stringify(item.compensation || {}, null, 2)}
                </pre>
              </article>
            ))}
          </div>
        )}
      </section>

      {error ? <pre style={errorStyle}>{error}</pre> : null}
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
  marginBottom: 16,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 0,
  marginBottom: 14,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const toolbarStyle = {
  display: "flex",
  gap: 12,
  marginTop: 16,
};

const historyHeaderStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-start",
  justifyContent: "space-between",
  flexWrap: "wrap",
};

const healthHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 10,
  flexWrap: "wrap",
};

const healthPresetRowStyle = {
  marginTop: 8,
  display: "flex",
  gap: 8,
  alignItems: "center",
  flexWrap: "wrap",
};

const healthPresetLabelStyle = {
  color: "rgba(245,247,250,0.75)",
  fontSize: 12,
};

const healthPresetButtonStyle = (active) => ({
  padding: "6px 10px",
  borderRadius: 999,
  border: active ? "1px solid rgba(59,130,246,0.9)" : "1px solid rgba(255,255,255,0.16)",
  color: active ? "#dbeafe" : "#e2e8f0",
  background: active ? "rgba(59,130,246,0.24)" : "transparent",
  fontWeight: 700,
  fontSize: 12,
  cursor: "pointer",
});

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

const kpiGridStyle = {
  marginTop: 12,
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
  marginTop: 10,
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
};

const historyToolbarStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexWrap: "wrap",
};

const filterGroupStyle = {
  display: "inline-flex",
  gap: 8,
  alignItems: "center",
};

const historyListStyle = {
  marginTop: 12,
  display: "grid",
  gap: 12,
};

const historyItemStyle = {
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.10)",
  background: "rgba(255,255,255,0.03)",
  padding: 12,
};

const historyTopRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const historyMetaStyle = {
  marginTop: 6,
  display: "grid",
  gap: 4,
  color: "rgba(245, 247, 250, 0.85)",
  fontSize: 13,
};

const historyActionsStyle = {
  marginTop: 8,
  display: "flex",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap",
};

const buttonPrimaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(31,122,63,0.40)",
  background: "#1f7a3f",
  color: "white",
  fontWeight: 700,
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

const filterButtonStyle = (active, variant = "ALL") => {
  const palette = {
    ALL: {
      color: active ? "#bfdbfe" : "#e2e8f0",
      border: active
        ? "1px solid rgba(96, 165, 250, 0.75)"
        : "1px solid rgba(255,255,255,0.16)",
      background: active ? "rgba(96, 165, 250, 0.18)" : "transparent",
    },
    OK: {
      color: active ? "#86efac" : "#4ade80",
      border: active
        ? "1px solid rgba(31,122,63,0.75)"
        : "1px solid rgba(31,122,63,0.45)",
      background: active ? "rgba(31,122,63,0.22)" : "transparent",
    },
    ERROR: {
      color: active ? "#fecaca" : "#fca5a5",
      border: active
        ? "1px solid rgba(179,38,30,0.75)"
        : "1px solid rgba(179,38,30,0.45)",
      background: active ? "rgba(179,38,30,0.22)" : "transparent",
    },
  };
  const selected = palette[variant] || palette.ALL;
  return {
    padding: "6px 10px",
    cursor: "pointer",
    borderRadius: 999,
    border: selected.border,
    background: selected.background,
    color: selected.color,
    fontWeight: 700,
    fontSize: 12,
  };
};

const summaryBoxStyle = {
  marginTop: 6,
  display: "grid",
  gap: 6,
  padding: 12,
  borderRadius: 12,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.08)",
};

const preStyle = {
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12,
  padding: 12,
  overflow: "auto",
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};
