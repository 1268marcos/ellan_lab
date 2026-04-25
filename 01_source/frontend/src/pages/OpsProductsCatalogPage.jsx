import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard, { resolveTrendByDelta } from "../components/OpsTrendKpiCard";
import { getSeverityBadgeStyle } from "../components/opsVisualTokens";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const FILTERS_PREF_KEY = "ops_products_catalog:last_filters";
const AUTO_REFRESH_PREF_KEY = "ops_products_catalog:auto_refresh_on_preset";

const STATUS_OPTIONS = ["", "DRAFT", "ACTIVE", "INACTIVE", "DISCONTINUED"];

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

function parseError(payload, fallback = "Nao foi possivel carregar catalogo OPS de produtos.") {
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
  if (!raw) return "Falha de comunicacao com a API OPS de Products.";
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
        status: "",
        category: "",
        preset: "7d",
        limit: 20,
      };
    }
    const parsed = JSON.parse(raw);
    return {
      from: typeof parsed?.from === "string" && parsed.from.trim() ? parsed.from : toLocalInputValue(defaultFrom),
      to: typeof parsed?.to === "string" && parsed.to.trim() ? parsed.to : toLocalInputValue(now),
      status: typeof parsed?.status === "string" ? parsed.status : "",
      category: typeof parsed?.category === "string" ? parsed.category : "",
      preset: typeof parsed?.preset === "string" && parsed.preset.trim() ? parsed.preset : "7d",
      limit: Number.isFinite(parsed?.limit) ? Math.max(1, Math.min(200, Number(parsed.limit))) : 20,
    };
  } catch (_) {
    return {
      from: toLocalInputValue(defaultFrom),
      to: toLocalInputValue(now),
      status: "",
      category: "",
      preset: "7d",
      limit: 20,
    };
  }
}

function countByStatus(items) {
  const counts = { DRAFT: 0, ACTIVE: 0, INACTIVE: 0, DISCONTINUED: 0 };
  for (const row of items || []) {
    const key = String(row?.status || "").toUpperCase();
    if (counts[key] !== undefined) counts[key] += 1;
  }
  return counts;
}

function severityByProductStatus(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "ACTIVE") return "OK";
  if (normalized === "INACTIVE") return "WARN";
  return "HIGH";
}

export default function OpsProductsCatalogPage() {
  const { token } = useAuth();
  const now = new Date();
  const snapshot = loadSnapshot(now);

  const [from, setFrom] = useState(snapshot.from);
  const [to, setTo] = useState(snapshot.to);
  const [status, setStatus] = useState(snapshot.status);
  const [category, setCategory] = useState(snapshot.category);
  const [limit, setLimit] = useState(snapshot.limit);
  const [offset, setOffset] = useState(0);
  const [preset, setPreset] = useState(snapshot.preset);
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
  const [current, setCurrent] = useState(null);
  const [previous, setPrevious] = useState(null);

  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  function storeCurrent(overrides = {}) {
    persistSnapshot({
      from: overrides.from ?? from,
      to: overrides.to ?? to,
      status: overrides.status ?? status,
      category: overrides.category ?? category,
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
    setOffset(0);
    storeCurrent({ from: nextFrom, to: nextTo, preset: presetId });
    if (autoRefreshOnPreset) {
      setTimeout(() => {
        void loadCatalog({ fromOverride: nextFrom, toOverride: nextTo, offsetOverride: 0 });
      }, 0);
    }
  }

  async function fetchProducts({ fromIso, toIso, queryLimit, queryOffset }) {
    const params = new URLSearchParams();
    if (fromIso) params.set("updated_from", fromIso);
    if (toIso) params.set("updated_to", toIso);
    if (String(status || "").trim()) params.set("status", String(status).trim().toUpperCase());
    if (String(category || "").trim()) params.set("category", String(category).trim());
    params.set("limit", String(queryLimit));
    params.set("offset", String(queryOffset));
    const endpoint = `${ORDER_PICKUP_BASE}/products?${params.toString()}`;
    const response = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseError(data));
    return data || {};
  }

  async function loadCatalog({ fromOverride = null, toOverride = null, offsetOverride = null } = {}) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const localFrom = fromOverride || from;
      const localTo = toOverride || to;
      const fromIso = toIsoOrNull(localFrom);
      const toIso = toIsoOrNull(localTo);
      const offsetValue = offsetOverride ?? offset;

      storeCurrent({ from: localFrom, to: localTo });
      if (offsetOverride !== null && offsetOverride !== undefined) setOffset(offsetOverride);

      const currentPage = await fetchProducts({ fromIso, toIso, queryLimit: limit, queryOffset: offsetValue });
      const currentAgg = await fetchProducts({ fromIso, toIso, queryLimit: 200, queryOffset: 0 });

      const fromDate = fromIso ? new Date(fromIso) : null;
      const toDate = toIso ? new Date(toIso) : null;
      let previousAgg = { items: [], total: 0 };
      if (fromDate && toDate && !Number.isNaN(fromDate.getTime()) && !Number.isNaN(toDate.getTime()) && fromDate <= toDate) {
        const windowMs = toDate.getTime() - fromDate.getTime();
        const prevTo = new Date(fromDate.getTime());
        const prevFrom = new Date(fromDate.getTime() - windowMs);
        previousAgg = await fetchProducts({
          fromIso: prevFrom.toISOString(),
          toIso: prevTo.toISOString(),
          queryLimit: 200,
          queryOffset: 0,
        });
      }

      setCurrent({
        page: currentPage,
        aggregate: currentAgg,
      });
      setPrevious(previousAgg);
    } catch (err) {
      const endpoint = `${ORDER_PICKUP_BASE}/products`;
      setError(normalizeNetworkError(err, endpoint));
      setCurrent(null);
      setPrevious(null);
    } finally {
      setLoading(false);
    }
  }

  const currentAggItems = Array.isArray(current?.aggregate?.items) ? current.aggregate.items : [];
  const previousAggItems = Array.isArray(previous?.items) ? previous.items : [];
  const currentCounts = countByStatus(currentAggItems);
  const previousCounts = countByStatus(previousAggItems);

  const pageItems = Array.isArray(current?.page?.items) ? current.page.items : [];
  const pageTotal = Number(current?.page?.total || 0);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Products Catalog</h1>
        <p style={mutedStyle}>Distribuição por status e tendência simples por janela (atual vs anterior).</p>

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
            Status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                storeCurrent({ status: e.target.value });
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
            Category (opcional)
            <input
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                storeCurrent({ category: e.target.value });
              }}
              placeholder="ex.: MEDICAL_EQUIPMENT"
              style={inputStyle}
            />
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

        <div style={actionsRowStyle}>
          <button type="button" style={buttonStyle} onClick={() => void loadCatalog({ offsetOverride: 0 })} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar Catálogo"}
          </button>
          <button
            type="button"
            style={secondaryButtonStyle}
            onClick={() => void loadCatalog({ offsetOverride: Math.max(0, offset - limit) })}
            disabled={loading || offset <= 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            style={secondaryButtonStyle}
            onClick={() => void loadCatalog({ offsetOverride: offset + limit })}
            disabled={loading || offset + limit >= pageTotal}
          >
            Próxima pagina
          </button>
          <span style={mutedStyleSmall}>offset={offset} total={pageTotal}</span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        <div style={kpiGridStyle}>
          <OpsTrendKpiCard
            label="Produtos filtrados"
            value={current?.aggregate?.total ?? 0}
            previousValue={previous?.total ?? 0}
            trend={resolveTrendByDelta((current?.aggregate?.total ?? 0) - (previous?.total ?? 0))}
            deltaLabel={String((current?.aggregate?.total ?? 0) - (previous?.total ?? 0))}
            baseStyle={kpiCardStyle}
          />
          <OpsTrendKpiCard
            label="ACTIVE"
            value={currentCounts.ACTIVE}
            previousValue={previousCounts.ACTIVE}
            trend={resolveTrendByDelta(currentCounts.ACTIVE - previousCounts.ACTIVE)}
            deltaLabel={String(currentCounts.ACTIVE - previousCounts.ACTIVE)}
            baseStyle={kpiCardStyle}
          />
          <OpsTrendKpiCard
            label="INACTIVE"
            value={currentCounts.INACTIVE}
            previousValue={previousCounts.INACTIVE}
            trend={resolveTrendByDelta(currentCounts.INACTIVE - previousCounts.INACTIVE)}
            deltaLabel={String(currentCounts.INACTIVE - previousCounts.INACTIVE)}
            baseStyle={kpiCardStyle}
          />
          <OpsTrendKpiCard
            label="DISCONTINUED"
            value={currentCounts.DISCONTINUED}
            previousValue={previousCounts.DISCONTINUED}
            trend={resolveTrendByDelta(currentCounts.DISCONTINUED - previousCounts.DISCONTINUED)}
            deltaLabel={String(currentCounts.DISCONTINUED - previousCounts.DISCONTINUED)}
            baseStyle={kpiCardStyle}
          />
        </div>

        {!current ? (
          <p style={mutedStyle}>Clique em "Atualizar Catálogo" para carregar os dados.</p>
        ) : !pageItems.length ? (
          <p style={mutedStyle}>Nenhum produto encontrado para os filtros atuais.</p>
        ) : (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Product ID</th>
                  <th style={thStyle}>Nome</th>
                  <th style={thStyle}>Category</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>is_active</th>
                  <th style={thStyle}>Updated at</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.name}</td>
                    <td style={tdStyle}>{row.category_id || "-"}</td>
                    <td style={tdStyle}>
                      <span style={getSeverityBadgeStyle(severityByProductStatus(row.status))}>{row.status}</span>
                    </td>
                    <td style={tdStyle}>{String(!!row.is_active)}</td>
                    <td style={tdStyle}>{row.updated_at}</td>
                  </tr>
                ))}
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
const kpiGridStyle = { marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 };
const kpiCardStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const tableWrapStyle = { marginTop: 16, overflowX: "auto", border: "1px solid #1E293B", borderRadius: 12 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 900 };
const thStyle = { textAlign: "left", padding: 10, fontSize: 12, color: "#94A3B8", borderBottom: "1px solid #1E293B", background: "#020617" };
const tdStyle = { padding: 10, fontSize: 12, color: "#E2E8F0", borderBottom: "1px solid #1E293B" };
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
