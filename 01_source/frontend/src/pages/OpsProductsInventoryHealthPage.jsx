import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard, { resolveTrendByDelta } from "../components/OpsTrendKpiCard";
import { getTrendBadgeStyle, getTrendToken } from "../components/opsVisualTokens";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const FILTERS_PREF_KEY = "ops_products_inventory_health:last_filters";
const AUTO_REFRESH_PREF_KEY = "ops_products_inventory_health:auto_refresh_on_preset";
const CONTINUOUS_REFRESH_PREF_KEY = "ops_products_inventory_health:continuous_auto_refresh";
const CONTINUOUS_REFRESH_SECONDS_PREF_KEY = "ops_products_inventory_health:continuous_auto_refresh_seconds";

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

function parseError(payload, fallback = "Nao foi possivel carregar saude de reservas OPS.") {
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
  if (!raw) return "Falha de comunicacao com a API OPS de Inventory Health.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao com a API OPS (${endpoint}). Verifique se o backend esta ativo e se o proxy /api/op esta configurado no frontend.`;
  }
  return raw;
}

function persistSnapshot(snapshot) {
  try {
    window.localStorage.setItem(FILTERS_PREF_KEY, JSON.stringify(snapshot));
  } catch (_) {
    // fallback silencioso
  }
}

function loadSnapshot(now) {
  const defaultFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) {
      return {
        from: toLocalInputValue(defaultFrom),
        to: toLocalInputValue(now),
        preset: "7d",
        limit: 20,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      from: typeof parsed?.from === "string" && parsed.from.trim() ? parsed.from : toLocalInputValue(defaultFrom),
      to: typeof parsed?.to === "string" && parsed.to.trim() ? parsed.to : toLocalInputValue(now),
      preset: typeof parsed?.preset === "string" && parsed.preset.trim() ? parsed.preset : "7d",
      limit: Number.isFinite(parsed?.limit) ? Math.max(1, Math.min(100, Number(parsed.limit))) : 20,
    };
  } catch (_) {
    return {
      from: toLocalInputValue(defaultFrom),
      to: toLocalInputValue(now),
      preset: "7d",
      limit: 20,
    };
  }
}

export default function OpsProductsInventoryHealthPage() {
  const { token } = useAuth();
  const now = new Date();
  const snapshot = loadSnapshot(now);

  const [from, setFrom] = useState(snapshot.from);
  const [to, setTo] = useState(snapshot.to);
  const [preset, setPreset] = useState(snapshot.preset);
  const [limit, setLimit] = useState(snapshot.limit);
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
  const [continuousAutoRefresh, setContinuousAutoRefresh] = useState(() => {
    try {
      return window.localStorage.getItem(CONTINUOUS_REFRESH_PREF_KEY) === "true";
    } catch (_) {
      return false;
    }
  });
  const [continuousRefreshSeconds, setContinuousRefreshSeconds] = useState(() => {
    try {
      const raw = Number(window.localStorage.getItem(CONTINUOUS_REFRESH_SECONDS_PREF_KEY) || 60);
      return raw === 30 ? 30 : 60;
    } catch (_) {
      return 60;
    }
  });
  const [nextRefreshInSec, setNextRefreshInSec] = useState(0);
  const [lastRefreshAt, setLastRefreshAt] = useState("");
  const [lastRefreshMode, setLastRefreshMode] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  function storeCurrent(overrides = {}) {
    persistSnapshot({
      from: overrides.from ?? from,
      to: overrides.to ?? to,
      preset: overrides.preset ?? preset,
      limit: overrides.limit ?? limit,
    });
  }

  function applyPreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    if (presetId === "1h") start = new Date(referenceNow.getTime() - 1 * 60 * 60 * 1000);
    else if (presetId === "6h") start = new Date(referenceNow.getTime() - 6 * 60 * 60 * 1000);
    else if (presetId === "24h") start = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);
    else if (presetId === "30d") start = new Date(referenceNow.getTime() - 30 * 24 * 60 * 60 * 1000);
    else if (presetId === "month") start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    const nextFrom = toLocalInputValue(start);
    const nextTo = toLocalInputValue(referenceNow);
    setFrom(nextFrom);
    setTo(nextTo);
    setPreset(presetId);
    storeCurrent({ from: nextFrom, to: nextTo, preset: presetId });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void loadHealth({ fromOverride: nextFrom, toOverride: nextTo });
      }, 0);
    }
  }

  async function loadHealth({ fromOverride = null, toOverride = null, source = "manual" } = {}) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(fromOverride || from);
      const toIso = toIsoOrNull(toOverride || to);
      const params = new URLSearchParams();
      if (fromIso) params.set("period_from", fromIso);
      if (toIso) params.set("period_to", toIso);
      params.set("limit", String(limit));
      const endpoint = `${ORDER_PICKUP_BASE}/ops/inventory/reservation-health?${params.toString()}`;
      const response = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setPayload(data || null);
      storeCurrent({ from: fromOverride || from, to: toOverride || to });
      setLastRefreshAt(new Date().toLocaleString("pt-BR"));
      setLastRefreshMode(source === "auto" ? "automatica" : "manual");
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/ops/inventory/reservation-health`;
      setError(normalizeNetworkError(err, endpoint));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!continuousAutoRefresh || !token) {
      setNextRefreshInSec(0);
      return undefined;
    }
    const refreshWindow = Number(continuousRefreshSeconds || 60);
    setNextRefreshInSec(refreshWindow);
    const timer = window.setInterval(() => {
      setNextRefreshInSec((prev) => {
        if (prev <= 1) {
          void loadHealth({ source: "auto" });
          return refreshWindow;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [continuousAutoRefresh, continuousRefreshSeconds, token, from, to, limit]);

  const ranking = Array.isArray(payload?.ranking) ? payload.ranking : [];

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Products Inventory Health</h1>
        <p style={mutedStyle}>Saúde de reservas por locker/produto com ranking de divergências e tendência por janela.</p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            From
            <input
              type="datetime-local"
              value={from}
              onChange={(e) => {
                setFrom(e.target.value);
                storeCurrent({ from: e.target.value });
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
                setTo(e.target.value);
                storeCurrent({ to: e.target.value });
              }}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Ranking limit
            <input
              type="number"
              min={1}
              max={100}
              value={limit}
              onChange={(e) => {
                const next = Math.max(1, Math.min(100, Number(e.target.value || 20)));
                setLimit(next);
                storeCurrent({ limit: next });
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
                onChange={(e) => {
                  setAutoRefreshOnPreset(e.target.checked);
                  try {
                    window.localStorage.setItem(AUTO_REFRESH_PREF_KEY, String(e.target.checked));
                  } catch (_) {
                    // fallback silencioso
                  }
                }}
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

        <div style={continuousRefreshSectionStyle}>
          <div style={presetHeadRowStyle}>
            <span style={presetLabelStyle}>Auto-refresh continuo (NOC)</span>
            <label style={toggleLabelStyle}>
              <input
                type="checkbox"
                checked={continuousAutoRefresh}
                onChange={(e) => {
                  const next = e.target.checked;
                  setContinuousAutoRefresh(next);
                  try {
                    window.localStorage.setItem(CONTINUOUS_REFRESH_PREF_KEY, String(next));
                  } catch (_) {
                    // fallback silencioso
                  }
                }}
              />
              Ativar
            </label>
          </div>
          <div style={{ ...presetWrapStyle, marginTop: 6 }}>
            <span style={presetLabelStyle}>Intervalo:</span>
            {[30, 60].map((seconds) => (
              <button
                key={seconds}
                type="button"
                onClick={() => {
                  setContinuousRefreshSeconds(seconds);
                  try {
                    window.localStorage.setItem(CONTINUOUS_REFRESH_SECONDS_PREF_KEY, String(seconds));
                  } catch (_) {
                    // fallback silencioso
                  }
                }}
                style={presetButtonStyle(continuousRefreshSeconds === seconds)}
              >
                {seconds}s
              </button>
            ))}
          </div>
          <div style={autoRefreshStatusWrapStyle}>
            {continuousAutoRefresh ? (
              <span style={autoRefreshActiveStyle}>
                Auto-refresh ativo · proxima atualizacao em {nextRefreshInSec}s
              </span>
            ) : (
              <span style={autoRefreshIdleStyle}>Auto-refresh continuo desativado.</span>
            )}
            {lastRefreshAt ? (
              <span style={lastRefreshMetaStyle}>
                Ultima atualizacao {lastRefreshMode || "manual"}: {lastRefreshAt}
              </span>
            ) : null}
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <button type="button" style={buttonStyle} onClick={() => void loadHealth({ source: "manual" })} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar Dashboard"}
          </button>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {payload ? (
          <>
            <div style={kpiGridStyle}>
              <OpsTrendKpiCard
                label="Divergence events"
                value={payload?.divergence_events_current ?? 0}
                previousValue={payload?.divergence_events_previous ?? 0}
                trend={resolveTrendByDelta((payload?.divergence_events_current ?? 0) - (payload?.divergence_events_previous ?? 0))}
                deltaLabel={`${payload?.divergence_events_delta_pct ?? 0}%`}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Auto fixes"
                value={payload?.auto_fixes_current ?? 0}
                previousValue={payload?.auto_fixes_previous ?? 0}
                trend={resolveTrendByDelta((payload?.auto_fixes_current ?? 0) - (payload?.auto_fixes_previous ?? 0))}
                deltaLabel={`${payload?.auto_fixes_delta_pct ?? 0}%`}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Orphan alerts"
                value={payload?.orphan_alerts_current ?? 0}
                previousValue={payload?.orphan_alerts_previous ?? 0}
                trend={resolveTrendByDelta((payload?.orphan_alerts_current ?? 0) - (payload?.orphan_alerts_previous ?? 0))}
                deltaLabel={`${payload?.orphan_alerts_delta_pct ?? 0}%`}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Entities with divergence"
                value={payload?.entities_with_divergence_current ?? 0}
                previousValue={payload?.entities_with_divergence_previous ?? 0}
                trend={resolveTrendByDelta((payload?.entities_with_divergence_current ?? 0) - (payload?.entities_with_divergence_previous ?? 0))}
                deltaLabel={String((payload?.entities_with_divergence_current ?? 0) - (payload?.entities_with_divergence_previous ?? 0))}
                baseStyle={kpiCardStyle}
              />
            </div>

            {!ranking.length ? (
              <p style={mutedStyle}>Sem divergencias para o periodo selecionado.</p>
            ) : (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Product</th>
                      <th style={thStyle}>Locker</th>
                      <th style={thStyle}>Slot</th>
                      <th style={thStyle}>Trend</th>
                      <th style={thStyle}>Div curr/prev</th>
                      <th style={thStyle}>Abs delta curr/prev</th>
                      <th style={thStyle}>Auto fix curr/prev</th>
                      <th style={thStyle}>Orphan curr/prev</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranking.map((item) => {
                      const trendToken = getTrendToken(item.trend);
                      return (
                        <tr key={`${item.product_id}-${item.locker_id}-${item.slot_size}`}>
                          <td style={tdStyle}>{item.product_id}</td>
                          <td style={tdStyle}>{item.locker_id}</td>
                          <td style={tdStyle}>{item.slot_size}</td>
                          <td style={tdStyle}>
                            <span style={getTrendBadgeStyle(item.trend)}>
                              {trendToken.symbol} {trendToken.label}
                            </span>
                          </td>
                          <td style={tdStyle}>
                            {item.divergence_events_current} / {item.divergence_events_previous} ({item.divergence_events_delta_pct}%)
                          </td>
                          <td style={tdStyle}>
                            {item.abs_delta_sum_current} / {item.abs_delta_sum_previous} ({item.abs_delta_sum_delta_pct}%)
                          </td>
                          <td style={tdStyle}>
                            {item.auto_fixes_current} / {item.auto_fixes_previous}
                          </td>
                          <td style={tdStyle}>
                            {item.orphan_alerts_current} / {item.orphan_alerts_previous}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : (
          <p style={mutedStyle}>Clique em "Atualizar Dashboard" para carregar os dados.</p>
        )}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 8 };
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 1100 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
const presetSectionStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #1E293B", borderRadius: 10, padding: 10 };
const continuousRefreshSectionStyle = { marginTop: 10, background: "#0B1220", border: "1px solid #1E293B", borderRadius: 10, padding: 10 };
const autoRefreshStatusWrapStyle = { marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 };
const autoRefreshActiveStyle = { fontSize: 12, color: "#86EFAC", border: "1px solid rgba(22,163,74,0.45)", background: "rgba(22,163,74,0.16)", borderRadius: 999, padding: "4px 10px", fontWeight: 700 };
const autoRefreshIdleStyle = { fontSize: 12, color: "#94A3B8", border: "1px solid rgba(100,116,139,0.45)", background: "rgba(71,85,105,0.2)", borderRadius: 999, padding: "4px 10px", fontWeight: 600 };
const lastRefreshMetaStyle = { fontSize: 12, color: "#CBD5E1", border: "1px solid rgba(148,163,184,0.45)", background: "rgba(71,85,105,0.16)", borderRadius: 999, padding: "4px 10px", fontWeight: 600 };
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
