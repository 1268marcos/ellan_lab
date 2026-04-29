import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

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

export default function OpsLogisticsManifestsOverviewPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);
  const now = new Date();
  const fromDefault = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const [from, setFrom] = useState(toLocalInputValue(fromDefault));
  const [to, setTo] = useState(toLocalInputValue(now));
  const [partnerId, setPartnerId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);

  async function loadOverview() {
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
      const endpoint = `${ORDER_PICKUP_BASE}/logistics/ops/manifests/overview?${params.toString()}`;
      const response = await fetch(endpoint, { method: "GET", headers: { Accept: "application/json", ...authHeaders } });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail?.message || data?.detail || "Falha no overview de manifestos");
      }
      setPayload(data || null);
    } catch (err) {
      setError(String(err?.message || err || "erro desconhecido"));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS - Logistics Manifests Overview" />
        <p style={mutedStyle}>Painel D3 para backlog, taxa de partial/failed, confidence badge e alertas operacionais.</p>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            From
            <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            To
            <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Partner ID (opcional)
            <input value={partnerId} onChange={(e) => setPartnerId(e.target.value)} style={inputStyle} placeholder="ex.: lpt_001" />
          </label>
        </div>

        <button type="button" style={buttonStyle} onClick={() => void loadOverview()} disabled={loading}>
          {loading ? "Atualizando..." : "Atualizar overview"}
        </button>
        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {payload ? (
          <>
            <div style={kpiGridStyle}>
              <Kpi label="Confidence" value={payload?.confidence_badge || "-"} />
              <Kpi label="Current total" value={payload?.totals?.current_total ?? 0} />
              <Kpi label="Pending/In transit" value={payload?.totals?.pending_or_in_transit ?? 0} />
              <Kpi label="Partial/Failed %" value={`${payload?.totals?.partial_failed_rate_pct ?? 0}%`} />
            </div>

            <section style={subCardStyle}>
              <h3 style={{ marginTop: 0 }}>Alertas operacionais</h3>
              {!Array.isArray(payload?.alerts) || payload.alerts.length === 0 ? (
                <p style={mutedStyle}>Sem alertas na janela atual.</p>
              ) : (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {payload.alerts.map((alert, idx) => (
                    <li key={`${alert?.type || "alert"}-${idx}`} style={{ marginBottom: 6 }}>
                      <b>{alert?.type || "ALERT"}</b>: {alert?.message || "-"} (value={String(alert?.value ?? "-")}, threshold={String(alert?.threshold ?? "-")})
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <pre style={jsonStyle}>{JSON.stringify(payload, null, 2)}</pre>
          </>
        ) : (
          <p style={mutedStyle}>Clique em "Atualizar overview" para carregar indicadores.</p>
        )}
      </section>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <article style={kpiStyle}>
      <strong style={{ color: "#BFDBFE", fontSize: 20 }}>{value}</strong>
      <small style={{ color: "#94A3B8" }}>{label}</small>
    </article>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const subCardStyle = { marginTop: 12, background: "#0B1220", border: "1px solid #334155", borderRadius: 12, padding: 12 };
const mutedStyle = { color: "#94A3B8" };
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errorStyle = { marginTop: 10, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const jsonStyle = { marginTop: 12, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12 };
const kpiGridStyle = { marginTop: 12, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 8 };
const kpiStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10, display: "grid", gap: 4 };
