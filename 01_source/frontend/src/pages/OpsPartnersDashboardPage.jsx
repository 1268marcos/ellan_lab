import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import OpsTrendKpiCard, { resolveTrendByDelta } from "../components/OpsTrendKpiCard";
import { getConfidenceBadgeStyle, getDataQualityFlagStyle } from "../components/opsVisualTokens";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const AUTO_REFRESH_PREF_KEY = "ops_partners_dashboard:auto_refresh_on_preset";
const FILTERS_PREF_KEY = "ops_partners_dashboard:last_filters";

function loadLastFilters() {
  try {
    const raw = window.localStorage.getItem(FILTERS_PREF_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return {
      partnerId: typeof parsed.partnerId === "string" ? parsed.partnerId : "",
      includeSections:
        typeof parsed.includeSections === "string" && parsed.includeSections.trim()
          ? parsed.includeSections
          : "kpis,compare,changes_series",
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

function persistLastFilters({ partnerId, includeSections, preset, from, to }) {
  try {
    window.localStorage.setItem(
      FILTERS_PREF_KEY,
      JSON.stringify({
        partnerId: String(partnerId || ""),
        includeSections: String(includeSections || "kpis,compare,changes_series"),
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

function parseError(payload, fallback = "Não foi possível carregar dashboard OPS.") {
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
  if (!raw) return "Falha de comunicação com a API OPS.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexão com a API OPS (${endpoint}). Verifique se o backend está ativo e se o proxy /api/op está configurado no frontend.`;
  }
  return raw;
}

export default function OpsPartnersDashboardPage() {
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
  const [partnerId, setPartnerId] = useState(lastFilters?.partnerId || "");
  const [includeSections, setIncludeSections] = useState(
    lastFilters?.includeSections || "kpis,compare,changes_series"
  );
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
    setFrom(toLocalInputValue(start));
    setTo(toLocalInputValue(referenceNow));
    setSelectedPreset(presetId);
    persistLastFilters({
      partnerId,
      includeSections,
      preset: presetId,
      from: toLocalInputValue(start),
      to: toLocalInputValue(referenceNow),
    });
    if (autoRefreshOnPreset) {
      // Auto refresh ao selecionar preset de período.
      setTimeout(() => {
        void loadDashboard();
      }, 0);
    }
  }

  function applySectionsPreset(value) {
    setIncludeSections(value);
    persistLastFilters({
      partnerId,
      includeSections: value,
      preset: selectedPreset,
      from,
      to,
    });
    if (autoRefreshOnPreset) {
      // Auto refresh ao selecionar preset de seções.
      setTimeout(() => {
        void loadDashboard();
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

  async function loadDashboard() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      const fromIso = toIsoOrNull(from);
      const toIso = toIsoOrNull(to);
      if (fromIso) params.set("from", fromIso);
      if (toIso) params.set("to", toIso);
      if (String(partnerId || "").trim()) params.set("partner_id", String(partnerId).trim());
      if (String(includeSections || "").trim()) {
        params.set("include_sections", String(includeSections).trim());
      }
      persistLastFilters({
        partnerId,
        includeSections,
        preset: selectedPreset,
        from,
        to,
      });

      const endpoint = `${ORDER_PICKUP_BASE}/partners/ops/dashboard?${params.toString()}`;
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
      const endpoint = `${ORDER_PICKUP_BASE}/partners/ops/dashboard`;
      setError(normalizeNetworkError(err, endpoint));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Partners Dashboard" />
        <p style={mutedStyle}>
          Visualização consolidada de KPI, comparativo e série temporal (global ou foco por parceiro).
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
                  persistLastFilters({
                    partnerId,
                    includeSections,
                    preset: selectedPreset,
                    from: next,
                    to,
                  });
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
                  persistLastFilters({
                    partnerId,
                    includeSections,
                    preset: selectedPreset,
                    from,
                    to: next,
                  });
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
                  persistLastFilters({
                    partnerId: next,
                    includeSections,
                    preset: selectedPreset,
                  });
                }}
                placeholder="ex.: ptn_123"
                style={inputStyle}
              />
          </label>
          <label style={labelStyle}>
            Include Sections
              <input
                value={includeSections}
                onChange={(e) => {
                  const next = e.target.value;
                  setIncludeSections(next);
                  persistLastFilters({
                    partnerId,
                    includeSections: next,
                    preset: selectedPreset,
                  });
                }}
                placeholder="kpis,compare,changes_series"
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
              { id: "month", label: "Mês Atual" },
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

        <div style={presetSectionStyle}>
          <span style={presetLabelStyle}>Presets include sections</span>
          <div style={presetWrapStyle}>
            {[
              { id: "all", label: "Tudo", value: "kpis,compare,changes_series" },
              { id: "fast", label: "Rápido", value: "kpis,compare" },
              { id: "trend", label: "Tendência", value: "compare,changes_series" },
              { id: "kpi", label: "Só KPI", value: "kpis" },
              { id: "compare", label: "Só Compare", value: "compare" },
              { id: "series", label: "Só Série", value: "changes_series" },
            ].map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => applySectionsPreset(preset.value)}
                style={presetButtonStyle(includeSections === preset.value)}
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
                label="Total eventos"
                value={payload?.kpis?.total_events ?? "-"}
                previousValue={payload?.compare?.total_previous}
                trend={resolveTrendByDelta(payload?.compare?.total_delta_count)}
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Erro %"
                value={payload?.kpis ? `${payload.kpis.error_rate_pct}%` : "-"}
                baseStyle={kpiCardStyle}
                showTrend={false}
              />
              <OpsTrendKpiCard
                label="Delta total %"
                value={payload?.compare ? `${payload.compare.total_delta_pct}%` : "-"}
                trend={resolveTrendByDelta(payload?.compare?.total_delta_count)}
                deltaLabel={
                  payload?.compare
                    ? `${Number(payload.compare.total_delta_count) > 0 ? "+" : ""}${payload.compare.total_delta_count}`
                    : null
                }
                baseStyle={kpiCardStyle}
              />
              <OpsTrendKpiCard
                label="Confianca"
                value={payload?.compare?.confidence_level ?? "-"}
                baseStyle={kpiCardStyle}
                showTrend={false}
              />
            </div>
            <div style={badgesRowStyle}>
              <span style={getConfidenceBadgeStyle(payload?.compare?.confidence_level)}>
                Confidence: {payload?.compare?.confidence_level || "-"}
              </span>
              {(payload?.compare?.data_quality_flags || []).map((flag) => (
                <span key={flag} style={getDataQualityFlagStyle(flag)}>
                  {flag}
                </span>
              ))}
            </div>
            <pre style={jsonStyle}>{JSON.stringify(payload, null, 2)}</pre>
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
const filtersGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#0B1220", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#0F766E", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errorStyle = { marginTop: 12, background: "rgba(220, 38, 38, 0.12)", color: "#FCA5A5", border: "1px solid rgba(220, 38, 38, 0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const badgesRowStyle = { marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" };
const jsonStyle = { marginTop: 14, background: "#020617", border: "1px solid #1E293B", borderRadius: 12, padding: 12, overflow: "auto", fontSize: 12, lineHeight: 1.4 };
const presetSectionStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #1E293B", borderRadius: 10, padding: 10 };
const presetHeadRowStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" };
const presetWrapStyle = { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginTop: 8 };
const presetLabelStyle = { color: "#94A3B8", fontSize: 12 };
const toggleLabelStyle = { color: "#CBD5E1", fontSize: 12, display: "flex", alignItems: "center", gap: 6 };
const presetButtonStyle = (active) => ({
  padding: "6px 10px",
  borderRadius: 999,
  border: active ? "1px solid #0F766E" : "1px solid #334155",
  background: active ? "rgba(15,118,110,0.22)" : "#0B1220",
  color: active ? "#99F6E4" : "#CBD5E1",
  fontWeight: 700,
  cursor: "pointer",
});
