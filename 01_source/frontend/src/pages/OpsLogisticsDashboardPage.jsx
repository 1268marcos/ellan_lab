import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import { getTrendBadgeStyle, getTrendToken } from "../components/opsVisualTokens";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const AUTO_REFRESH_PREF_KEY = "ops_logistics_dashboard:auto_refresh_on_preset";
const FILTERS_PREF_KEY = "ops_logistics_dashboard:last_filters";

function loadLastFilters() {
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return {
      carrierCode:
        typeof parsed.carrierCode === "string" ? parsed.carrierCode : "",
      preset:
        typeof parsed.preset === "string" && parsed.preset.trim()
          ? parsed.preset
          : "7d",
      from:
        typeof parsed.from === "string" && parsed.from.trim()
          ? parsed.from
          : null,
      to:
        typeof parsed.to === "string" && parsed.to.trim()
          ? parsed.to
          : null,
    };
  } catch (_) {
    return null;
  }
}

function persistLastFilters({ carrierCode, preset, from, to }) {
  try {
    window.localStorage.setItem(
      FILTERS_PREF_KEY,
      JSON.stringify({
        carrierCode: String(carrierCode || ""),
        preset: String(preset || "7d"),
        from: from ? String(from) : null,
        to: to ? String(to) : null,
      })
    );
  } catch (_) {
    // fallback silencioso para ambientes sem localStorage
  }
}

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

function parseError(payload, fallback = "Nao foi possivel carregar dashboard OPS de Logistics.") {
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
  if (!raw) return "Falha de comunicacao com a API OPS de Logistics.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao com a API OPS (${endpoint}). Verifique se o backend esta ativo e se o proxy /api/op esta configurado no frontend.`;
  }
  return raw;
}

export default function OpsLogisticsDashboardPage() {
  const { token } = useAuth();
  const now = new Date();
  const fromDefault = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const lastFilters = loadLastFilters();

  const [from, setFrom] = useState(lastFilters?.from || toLocalInputValue(fromDefault));
  const [to, setTo] = useState(lastFilters?.to || toLocalInputValue(now));
  const [selectedPreset, setSelectedPreset] = useState(lastFilters?.preset || "7d");
  const [autoRefreshOnPreset, setAutoRefreshOnPreset] = useState(() => {
    try {
      const stored = window.localStorage.getItem(AUTO_REFRESH_PREF_KEY);
      if (stored === "true") return true;
      if (stored === "false") return false;
    } catch (_) {
      // fallback silencioso para ambientes sem localStorage
    }
    return true;
  });
  const [carrierCode, setCarrierCode] = useState(lastFilters?.carrierCode || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  function applyPreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    if (presetId === "1h") {
      start = new Date(referenceNow.getTime() - 1 * 60 * 60 * 1000);
    } else if (presetId === "6h") {
      start = new Date(referenceNow.getTime() - 6 * 60 * 60 * 1000);
    } else if (presetId === "24h") {
      start = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);
    } else if (presetId === "30d") {
      start = new Date(referenceNow.getTime() - 30 * 24 * 60 * 60 * 1000);
    } else if (presetId === "month") {
      start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    }
    const nextFrom = toLocalInputValue(start);
    const nextTo = toLocalInputValue(referenceNow);
    setFrom(nextFrom);
    setTo(nextTo);
    setSelectedPreset(presetId);
    persistLastFilters({
      carrierCode,
      preset: presetId,
      from: nextFrom,
      to: nextTo,
    });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void loadDashboard(nextFrom, nextTo);
      }, 0);
    }
  }

  function handleToggleAutoRefresh(nextValue) {
    setAutoRefreshOnPreset(nextValue);
    try {
      window.localStorage.setItem(AUTO_REFRESH_PREF_KEY, String(nextValue));
    } catch (_) {
      // fallback silencioso para ambientes sem localStorage
    }
  }

  async function loadDashboard(fromOverride = null, toOverride = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      const fromIso = toIsoOrNull(fromOverride || from);
      const toIso = toIsoOrNull(toOverride || to);
      if (fromIso) params.set("from", fromIso);
      if (toIso) params.set("to", toIso);
      if (String(carrierCode || "").trim()) params.set("carrier_code", String(carrierCode).trim());

      persistLastFilters({
        carrierCode,
        preset: selectedPreset,
        from: fromOverride || from,
        to: toOverride || to,
      });

      const endpoint = `${ORDER_PICKUP_BASE}/logistics/ops/overview?${params.toString()}`;
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseError(data));
      }
      setPayload(data || null);
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/ops/overview`;
      setError(normalizeNetworkError(err, endpoint));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Logistics Dashboard</h1>
        <p style={mutedStyle}>
          Acompanhamento operacional de tracking events, delivery attempts e shipment labels.
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
                persistLastFilters({ carrierCode, preset: selectedPreset, from: next, to });
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
                persistLastFilters({ carrierCode, preset: selectedPreset, from, to: next });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Carrier code (opcional)
            <input
              value={carrierCode}
              onChange={(e) => {
                const next = e.target.value;
                setCarrierCode(next);
                persistLastFilters({ carrierCode: next, preset: selectedPreset, from, to });
              }}
              placeholder="ex.: UPS, CORREIOS, FEDEX"
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
                onChange={(event) => handleToggleAutoRefresh(event.target.checked)}
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
            ].map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => applyPreset(preset.id)}
                style={presetButtonStyle(selectedPreset === preset.id)}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <button type="button" onClick={() => void loadDashboard()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar Dashboard"}
          </button>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {payload ? (
          <>
            <div style={kpiGridStyle}>
              <OpsTrendKpiCard
                label="Tracking events"
                value={payload?.totals?.events ?? "-"}
                previousValue={payload?.totals?.events_previous ?? 0}
                trend={resolveKpiTrend(payload?.totals?.events, payload?.totals?.events_previous).trend}
                deltaLabel={resolveKpiTrend(payload?.totals?.events, payload?.totals?.events_previous).deltaLabel}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Delivery attempts"
                value={payload?.totals?.attempts ?? "-"}
                previousValue={payload?.totals?.attempts_previous ?? 0}
                trend={resolveKpiTrend(payload?.totals?.attempts, payload?.totals?.attempts_previous).trend}
                deltaLabel={resolveKpiTrend(payload?.totals?.attempts, payload?.totals?.attempts_previous).deltaLabel}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Shipment labels"
                value={payload?.totals?.labels ?? "-"}
                previousValue={payload?.totals?.labels_previous ?? 0}
                trend={resolveKpiTrend(payload?.totals?.labels, payload?.totals?.labels_previous).trend}
                deltaLabel={resolveKpiTrend(payload?.totals?.labels, payload?.totals?.labels_previous).deltaLabel}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Carrier filtro"
                value={payload?.carrier_code || "GLOBAL"}
                baseStyle={kpiCardStyle}
                showTrend={false}
              />
            </div>

            <div style={topsGridStyle}>
              <TopListCard
                title="Top event codes"
                items={Array.isArray(payload?.by_event_code) ? payload.by_event_code : []}
                emptyLabel="Sem eventos no periodo."
              />
              <TopListCard
                title="Top attempt statuses"
                items={Array.isArray(payload?.by_attempt_status) ? payload.by_attempt_status : []}
                emptyLabel="Sem tentativas no periodo."
              />
              <TopListCard
                title="Top carriers de label"
                items={Array.isArray(payload?.by_label_carrier) ? payload.by_label_carrier : []}
                emptyLabel="Sem labels no periodo."
              />
            </div>

            <details style={detailsStyle}>
              <summary style={summaryStyle}>Ver JSON tecnico (apoio)</summary>
              <pre style={jsonStyle}>{JSON.stringify(payload, null, 2)}</pre>
            </details>
          </>
        ) : (
          <p style={mutedStyle}>Clique em "Atualizar Dashboard" para carregar os dados.</p>
        )}
      </section>
    </div>
  );
}

function resolveKpiTrend(value, previousValue) {
  const current = Number(value ?? 0);
  const previous = Number(previousValue ?? 0);
  if (Number.isNaN(current) || Number.isNaN(previous)) {
    return { trend: "stable", deltaLabel: "0" };
  }
  const delta = current - previous;
  if (delta > 0) return { trend: "up", deltaLabel: `+${delta}` };
  if (delta < 0) return { trend: "down", deltaLabel: String(delta) };
  return { trend: "stable", deltaLabel: "0" };
}

function TopListCard({ title, items, emptyLabel }) {
  return (
    <article style={topCardStyle}>
      <h3 style={topCardTitleStyle}>{title}</h3>
      {!items.length ? (
        <p style={topCardEmptyStyle}>{emptyLabel}</p>
      ) : (
        <ul style={topListStyle}>
          {items.slice(0, 8).map((item, idx) => (
            <li key={`${item?.key || "n/a"}-${idx}`} style={topListItemStyle}>
              <div style={{ display: "grid", gap: 4 }}>
                <span style={topKeyStyle}>{item?.key || "-"}</span>
                <div style={topSubRowStyle}>
                  <TrendBadge trend={item?.trend} />
                  <span style={topDeltaStyle}>
                    Δ {Number(item?.delta ?? 0) > 0 ? `+${item?.delta}` : item?.delta ?? 0}
                  </span>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <strong style={topCountStyle}>{item?.count ?? 0}</strong>
                <div style={topPrevStyle}>prev: {item?.previous_count ?? 0}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function TrendBadge({ trend }) {
  const token = getTrendToken(trend);
  return <span style={getTrendBadgeStyle(trend)}>{token.label}</span>;
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const topsGridStyle = { marginTop: 14, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const topCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const topCardTitleStyle = { margin: 0, marginBottom: 10, fontSize: 14, color: "#E2E8F0" };
const topCardEmptyStyle = { margin: 0, color: "#94A3B8", fontSize: 12 };
const topListStyle = { margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 8 };
const topListItemStyle = { display: "flex", alignItems: "center", justifyContent: "space-between", background: "#020617", border: "1px solid #1E293B", borderRadius: 8, padding: "8px 10px" };
const topKeyStyle = { color: "#CBD5E1", fontSize: 12, fontWeight: 600 };
const topCountStyle = { color: "#BFDBFE", fontSize: 13 };
const topPrevStyle = { color: "#94A3B8", fontSize: 11, marginTop: 2 };
const topSubRowStyle = { display: "flex", alignItems: "center", gap: 6 };
const topDeltaStyle = { color: "#94A3B8", fontSize: 11 };
const detailsStyle = { marginTop: 12 };
const summaryStyle = { cursor: "pointer", color: "#94A3B8", fontSize: 12 };
const jsonStyle = { marginTop: 14, background: "#020617", border: "1px solid #1E293B", borderRadius: 12, padding: 12, overflow: "auto", fontSize: 12, lineHeight: 1.4 };
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
