import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";
import useOpsWindowPreset from "../hooks/useOpsWindowPreset";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const FILTERS_PREF_KEY = "ops_logistics_returns:last_filters";
const AUTO_REFRESH_PREF_KEY = "ops_logistics_returns:auto_refresh_on_preset";
const OPS_LOGISTICS_RETURNS_WINDOW_PREF_KEY = "ops_logistics_returns:window_hours";
const OPS_LOGISTICS_RETURNS_WINDOW_PRESETS = [1, 6, 24, 24 * 7, 24 * 30];

const STATUS_OPTIONS = ["", "REQUESTED", "PICKUP_SCHEDULED", "IN_TRANSIT", "RECEIVED", "CLOSED"];

function toLocalInputValue(date) {
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

function parseError(payload, fallback = "Nao foi possivel carregar retornos de Logistics.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API OPS de Returns.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao com a API OPS (${endpoint}). Verifique se o backend esta ativo e se o proxy /api/op esta configurado no frontend.`;
  }
  return raw;
}

function loadLastFilters(now) {
  const defaultFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) {
      return {
        from: toLocalInputValue(defaultFrom),
        to: toLocalInputValue(now),
        partnerId: "",
        status: "",
        preset: "7d",
        limit: 20,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      from: typeof parsed?.from === "string" && parsed.from.trim() ? parsed.from : toLocalInputValue(defaultFrom),
      to: typeof parsed?.to === "string" && parsed.to.trim() ? parsed.to : toLocalInputValue(now),
      partnerId: typeof parsed?.partnerId === "string" ? parsed.partnerId : "",
      status: typeof parsed?.status === "string" ? parsed.status : "",
      preset: typeof parsed?.preset === "string" && parsed.preset.trim() ? parsed.preset : "7d",
      limit: Number.isFinite(parsed?.limit) ? Math.max(1, Math.min(200, Number(parsed.limit))) : 20,
    };
  } catch (_) {
    return {
      from: toLocalInputValue(defaultFrom),
      to: toLocalInputValue(now),
      partnerId: "",
      status: "",
      preset: "7d",
      limit: 20,
    };
  }
}

function persistLastFilters(filters) {
  try {
    window.localStorage.setItem(FILTERS_PREF_KEY, JSON.stringify(filters));
  } catch (_) {
    // fallback silencioso
  }
}

function resolveSeverityByStatus(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "CLOSED") return "OK";
  if (normalized === "RECEIVED") return "WARN";
  return "HIGH";
}

function KpiCard({ label, value }) {
  return (
    <article style={kpiCardStyle}>
      <strong style={{ color: "#BFDBFE", display: "block", fontSize: 26 }}>{value}</strong>
      <small style={{ color: "#94A3B8", display: "block", marginTop: 4 }}>{label}</small>
    </article>
  );
}

export default function OpsLogisticsReturnsPage() {
  const { token } = useAuth();
  const now = new Date();
  const last = loadLastFilters(now);
  const defaultWindowHoursByPreset = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
  };
  const defaultWindowHours = defaultWindowHoursByPreset[last.preset] || 24 * 7;
  const { applyPreset: applyWindowHoursPreset } = useOpsWindowPreset({
    storageKey: OPS_LOGISTICS_RETURNS_WINDOW_PREF_KEY,
    defaultValue: defaultWindowHours,
    minValue: 1,
    maxValue: 24 * 30,
    presetValues: OPS_LOGISTICS_RETURNS_WINDOW_PRESETS,
  });

  const [from, setFrom] = useState(last.from);
  const [to, setTo] = useState(last.to);
  const [partnerId, setPartnerId] = useState(last.partnerId);
  const [status, setStatus] = useState(last.status);
  const [limit, setLimit] = useState(last.limit);
  const [offset, setOffset] = useState(0);
  const [preset, setPreset] = useState(last.preset);
  const [autoRefreshOnPreset, setAutoRefreshOnPreset] = useState(() => {
    try {
      const stored = window.localStorage.getItem(AUTO_REFRESH_PREF_KEY);
      if (stored === "true") return true;
      if (stored === "false") return false;
    } catch (_) {
      // fallback silencioso
    }
    return true;
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  function persistSnapshot(next = {}) {
    persistLastFilters({
      from: next.from ?? from,
      to: next.to ?? to,
      partnerId: next.partnerId ?? partnerId,
      status: next.status ?? status,
      preset: next.preset ?? preset,
      limit: next.limit ?? limit,
    });
  }

  function applyPreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    if (presetId === "month") {
      start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    } else {
      const hoursByPreset = {
        "1h": 1,
        "6h": 6,
        "24h": 24,
        "7d": 24 * 7,
        "30d": 24 * 30,
      };
      const windowHours = hoursByPreset[presetId] || 24 * 7;
      applyWindowHoursPreset(windowHours);
      start = new Date(referenceNow.getTime() - windowHours * 60 * 60 * 1000);
    }
    const nextFrom = toLocalInputValue(start);
    const nextTo = toLocalInputValue(referenceNow);
    setFrom(nextFrom);
    setTo(nextTo);
    setPreset(presetId);
    setOffset(0);
    persistSnapshot({ from: nextFrom, to: nextTo, preset: presetId });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void loadReturns({ fromOverride: nextFrom, toOverride: nextTo, offsetOverride: 0 });
      }, 0);
    }
  }

  function handleAutoRefreshToggle(nextValue) {
    setAutoRefreshOnPreset(nextValue);
    try {
      window.localStorage.setItem(AUTO_REFRESH_PREF_KEY, String(nextValue));
    } catch (_) {
      // fallback silencioso
    }
  }

  async function loadReturns({ fromOverride = null, toOverride = null, offsetOverride = null } = {}) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      const fromIso = toIsoOrNull(fromOverride || from);
      const toIso = toIsoOrNull(toOverride || to);
      if (fromIso) params.set("from", fromIso);
      if (toIso) params.set("to", toIso);
      const normalizedPartner = String(partnerId || "").trim();
      const normalizedStatus = String(status || "").trim().toUpperCase();
      if (normalizedPartner) params.set("partner_id", normalizedPartner);
      if (normalizedStatus) params.set("status", normalizedStatus);
      params.set("limit", String(limit));
      params.set("offset", String(offsetOverride ?? offset));

      persistSnapshot({
        from: fromOverride || from,
        to: toOverride || to,
      });

      const endpoint = `${ORDER_PICKUP_BASE}/logistics/returns?${params.toString()}`;
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      setPayload(data || null);
      if (offsetOverride !== null && offsetOverride !== undefined) setOffset(offsetOverride);
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/returns`;
      setError(normalizeNetworkError(err, endpoint));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  const items = Array.isArray(payload?.items) ? payload.items : [];
  const total = Number(payload?.total || 0);
  const countByStatus = items.reduce((acc, item) => {
    const key = String(item?.status || "UNKNOWN").toUpperCase();
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Logistics Returns</h1>
        <p style={mutedStyle}>
          Visão operacional de devoluções com filtros, presets e persistência para continuidade de contexto.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            From
            <input
              type="datetime-local"
              value={from}
              onChange={(e) => {
                const next = e.target.value;
                setFrom(next);
                persistSnapshot({ from: next });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            To
            <input
              type="datetime-local"
              value={to}
              onChange={(e) => {
                const next = e.target.value;
                setTo(next);
                persistSnapshot({ to: next });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Partner ID (opcional)
            <input
              value={partnerId}
              onChange={(e) => {
                const next = e.target.value;
                setPartnerId(next);
                persistSnapshot({ partnerId: next });
              }}
              placeholder="ex.: ptn_123"
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Status
            <select
              value={status}
              onChange={(e) => {
                const next = e.target.value;
                setStatus(next);
                persistSnapshot({ status: next });
              }}
              style={inputStyle}
            >
              {STATUS_OPTIONS.map((item) => (
                <option key={item || "ALL"} value={item}>
                  {item || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Limit
            <input
              type="number"
              min={1}
              max={200}
              value={limit}
              onChange={(e) => {
                const next = Math.max(1, Math.min(200, Number(e.target.value || 20)));
                setLimit(next);
                persistSnapshot({ limit: next });
              }}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={presetSectionStyle}>
          <div style={presetHeadRowStyle}>
            <span style={presetLabelStyle}>Presets globais</span>
            <label style={toggleLabelStyle}>
              <input
                type="checkbox"
                checked={autoRefreshOnPreset}
                onChange={(e) => handleAutoRefreshToggle(e.target.checked)}
              />
              Auto refresh on preset click
            </label>
          </div>
          <div style={presetWrapStyle}>
            {[
              { id: "1h", label: "1h" },
              { id: "6h", label: "6h" },
              { id: "24h", label: "24h" },
              { id: "7d", label: "7d" },
              { id: "30d", label: "30d" },
              { id: "month", label: "Mes Atual" },
            ].map((item) => (
              <button key={item.id} type="button" onClick={() => applyPreset(item.id)} style={presetButtonStyle(preset === item.id)}>
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => void loadReturns({ offsetOverride: 0 })} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar Returns"}
          </button>
          <button
            type="button"
            onClick={() => void loadReturns({ offsetOverride: Math.max(0, offset - limit) })}
            style={secondaryButtonStyle}
            disabled={loading || offset <= 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            onClick={() => void loadReturns({ offsetOverride: offset + limit })}
            style={secondaryButtonStyle}
            disabled={loading || offset + limit >= total}
          >
            Próxima página
          </button>
          <span style={mutedStyleSmall}>offset={offset} total={total}</span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        <div style={kpiGridStyle}>
          <KpiCard label="Total retornos (filtro)" value={total} />
          <KpiCard label="REQUESTED (pagina)" value={countByStatus.REQUESTED || 0} />
          <KpiCard label="IN_TRANSIT (pagina)" value={countByStatus.IN_TRANSIT || 0} />
          <KpiCard label="CLOSED (pagina)" value={countByStatus.CLOSED || 0} />
        </div>

        {!payload ? (
          <p style={mutedStyle}>Clique em "Atualizar Returns" para carregar os dados.</p>
        ) : !items.length ? (
          <p style={mutedStyle}>Nenhum retorno encontrado para os filtros atuais.</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Return ID</th>
                  <th style={thStyle}>Order ID</th>
                  <th style={thStyle}>Partner</th>
                  <th style={thStyle}>Reason</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Updated at</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => {
                  const rowStatus = String(row?.status || "").toUpperCase();
                  return (
                    <tr key={row.id}>
                      <td style={tdStyle}>{row.id}</td>
                      <td style={tdStyle}>{row.order_id}</td>
                      <td style={tdStyle}>{row.partner_id}</td>
                      <td style={tdStyle}>{row.reason_code}</td>
                      <td style={tdStyle}>
                        <span style={getSeverityBadgeStyle(resolveSeverityByStatus(rowStatus))}>{rowStatus || "-"}</span>
                      </td>
                      <td style={tdStyle}>{row.updated_at}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const mutedStyleSmall = { color: "#94A3B8", fontSize: 12 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const secondaryButtonStyle = { padding: "10px 12px", borderRadius: 10, border: "1px solid #334155", background: "#0B1220", color: "#E2E8F0", fontWeight: 600, cursor: "pointer" };
const actionsRowStyle = { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 12 };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const presetSectionStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #1E293B", borderRadius: 10, padding: 10 };
const presetHeadRowStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" };
const presetWrapStyle = { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginTop: 8 };
const presetLabelStyle = { color: "#94A3B8", fontSize: 12 };
const toggleLabelStyle = { color: "#CBD5E1", fontSize: 12, display: "flex", alignItems: "center", gap: 6 };
const presetButtonStyle = (active) => ({
  padding: "6px 10px",
  borderRadius: 999,
  border: active ? "1px solid #1D4ED8" : "1px solid #334155",
  background: active ? "rgba(29,78,216,0.22)" : "#0B1220",
  color: active ? "#BFDBFE" : "#CBD5E1",
  fontWeight: 700,
  cursor: "pointer",
});
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 900 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
