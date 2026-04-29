import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

function toList(value) {
  return Array.isArray(value) ? value : [];
}

function parseError(payload, fallback = "Nao foi possivel carregar erros internos.") {
  if (!payload) return fallback;
  if (typeof payload.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
  }
  if (typeof payload.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsDevErrorsPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [routeFilter, setRouteFilter] = useState("");

  const authHeaders = useMemo(() => {
    const headers = { Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (INTERNAL_TOKEN) headers["X-Internal-Token"] = INTERNAL_TOKEN;
    return headers;
  }, [token]);

  const routeOptions = useMemo(() => {
    const unique = new Set();
    for (const item of items) {
      const path = String(item?.path || "").trim();
      if (path) unique.add(path);
    }
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [items]);

  const statusOptions = useMemo(() => {
    const unique = new Set();
    for (const item of items) {
      const value = Number(item?.status_code || 0);
      if (value > 0) unique.add(value);
    }
    return Array.from(unique).sort((a, b) => a - b);
  }, [items]);

  const filteredItems = useMemo(() => {
    const statusCode = Number(statusFilter || 0);
    return items.filter((item) => {
      const matchesStatus = statusCode > 0 ? Number(item?.status_code || 0) === statusCode : true;
      const matchesRoute = routeFilter ? String(item?.path || "") === routeFilter : true;
      return matchesStatus && matchesRoute;
    });
  }, [items, routeFilter, statusFilter]);

  const kpis = useMemo(() => {
    const total = items.length;
    const filtered = filteredItems.length;
    const http4xx = filteredItems.filter((item) => Number(item?.status_code || 0) >= 400 && Number(item?.status_code || 0) < 500).length;
    const http5xx = filteredItems.filter((item) => Number(item?.status_code || 0) >= 500).length;
    return { total, filtered, http4xx, http5xx };
  }, [items, filteredItems]);

  async function loadErrors() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      if (!INTERNAL_TOKEN) {
        throw new Error("VITE_INTERNAL_TOKEN nao configurado no frontend.");
      }
      const response = await fetch(`${ORDER_PICKUP_BASE}/internal/dev/errors`, {
        method: "GET",
        headers: authHeaders,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(payload));
      setItems(toList(payload?.items));
    } catch (err) {
      setError(String(err?.message || err || "erro desconhecido"));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Ir para ops/health
          </Link>
          <Link to="/ops/audit" style={shortcutLinkStyle}>
            Ir para ops/audit
          </Link>
        </div>

        <OpsPageTitleHeader title="OPS - Dev Errors" />
        <p style={mutedStyle}>
          Visualizacao interna da rota <code>/internal/dev/errors</code> para diagnostico rapido em desenvolvimento.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={inputStyle}>
              <option value="">Todos</option>
              {statusOptions.map((value) => (
                <option key={value} value={String(value)}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Rota
            <select value={routeFilter} onChange={(event) => setRouteFilter(event.target.value)} style={inputStyle}>
              <option value="">Todas</option>
              {routeOptions.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => void loadErrors()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar erros"}
          </button>
          <button
            type="button"
            onClick={() => {
              setStatusFilter("");
              setRouteFilter("");
            }}
            style={buttonSecondaryStyle}
            disabled={loading}
          >
            Limpar filtros
          </button>
          <span style={{ color: "rgba(226,232,240,0.8)", fontSize: 12 }}>
            Token interno: {INTERNAL_TOKEN ? "configurado" : "nao configurado"}
          </span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {!error ? (
          <div style={kpiGridStyle}>
            <OpsTrendKpiCard label="Total eventos" value={kpis.total} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="Apos filtros" value={kpis.filtered} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="HTTP 4xx" value={kpis.http4xx} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="HTTP 5xx" value={kpis.http5xx} baseStyle={kpiBoxStyle} showTrend={false} />
          </div>
        ) : null}

        {!error && filteredItems.length > 0 ? (
          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {filteredItems.map((item, index) => (
              <article key={`${item?.trace_id || "trace"}-${index}`} style={rowStyle}>
                <div style={rowHeadStyle}>
                  <strong>{item?.method || "-"} {item?.path || "-"}</strong>
                  <span style={statusBadgeStyle(Number(item?.status_code || 0))}>{item?.status_code || "-"}</span>
                </div>
                <small style={smallStyle}>ts: {item?.ts || "-"}</small>
                <small style={smallStyle}>trace_id: {item?.trace_id || "-"}</small>
                <small style={smallStyle}>tipo: {item?.error_type || "-"}</small>
                <small style={smallStyle}>nivel: {item?.level || "-"}</small>
                {item?.message ? <small style={smallStyle}>mensagem: {item.message}</small> : null}
              </article>
            ))}
          </div>
        ) : null}

        {!error && !loading && filteredItems.length === 0 ? (
          <p style={{ marginTop: 14, color: "#94a3b8" }}>Nenhum evento encontrado com os filtros atuais.</p>
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

const mutedStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const shortcutRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const filtersGridStyle = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const actionsRowStyle = {
  marginTop: 12,
  display: "flex",
  gap: 10,
  alignItems: "center",
  flexWrap: "wrap",
};

const buttonStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const buttonSecondaryStyle = {
  ...buttonStyle,
  border: "1px solid rgba(96,165,250,0.55)",
  color: "#bfdbfe",
  background: "rgba(30,58,138,0.24)",
};

const errorStyle = {
  marginTop: 14,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

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

const rowStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const rowHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const smallStyle = {
  color: "rgba(226,232,240,0.9)",
  fontSize: 12,
  wordBreak: "break-word",
};

const statusBadgeStyle = (status) => {
  const code = Number(status || 0);
  const is5xx = code >= 500;
  const is4xx = code >= 400 && code < 500;
  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 800,
    lineHeight: 1.2,
    border: is5xx
      ? "1px solid #fecaca"
      : is4xx
        ? "1px solid #fdba74"
        : "1px solid #93c5fd",
    background: is5xx
      ? "#7f1d1d"
      : is4xx
        ? "#9a3412"
        : "#1e3a8a",
    color: "#ffffff",
  };
};
