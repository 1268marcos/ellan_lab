import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

function toHeaders(token) {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(INTERNAL_TOKEN ? { "X-Internal-Token": INTERNAL_TOKEN } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function parseApiError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export default function OpsPartnersHypertablesPage() {
  const { token } = useAuth();
  const headers = useMemo(() => toHeaders(token), [token]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState("");

  async function loadStatus() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${BILLING_BASE}/admin/fiscal/timescale/status`, {
        method: "GET",
        headers,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, "Falha ao carregar status de hypertables."));
      setPayload(data || null);
      setLastUpdatedAt(new Date().toLocaleString("pt-BR"));
    } catch (err) {
      setError(String(err?.message || err || "Erro desconhecido"));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0, marginBottom: 8 }}>OPS - Partners Hypertables</h1>
        <p style={mutedStyle}>
          Visão organizada das hypertables/policies do bloco FA-5 (Timescale). Esta tela consolida o smoke operacional.
        </p>
        <div style={actionsStyle}>
          <button type="button" style={buttonPrimaryStyle} onClick={() => void loadStatus()} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar status Timescale"}
          </button>
          <Link to="/ops/partners/billing-monitor" style={linkButtonStyle}>
            Voltar para billing-monitor
          </Link>
          {lastUpdatedAt ? <small style={mutedStyle}>Última atualização: {lastUpdatedAt}</small> : null}
        </div>
        {error ? <pre style={errorStyle}>{error}</pre> : null}
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Resumo de smoke</h2>
        {!payload ? (
          <p style={mutedStyle}>Clique em "Atualizar status Timescale" para carregar o status.</p>
        ) : (
          <div style={kpiGridStyle}>
            <Kpi label="Smoke Result" value={payload.smoke_result || "-"} />
            <Kpi label="Extension" value={payload.ext_ok ? `OK (${payload.extension?.extversion || "?"})` : "Indisponível"} />
            <Kpi label="Hypertables" value={payload.hypertable_count ?? 0} />
            <Kpi label="Policies Jobs" value={payload.policy_count ?? 0} />
            <Kpi label="Dedupe Indexes" value={payload.dedupe_index_count ?? 0} />
          </div>
        )}
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Hypertables</h2>
        <TableWrap>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>schema</th>
                <th style={thStyle}>hypertable_name</th>
              </tr>
            </thead>
            <tbody>
              {(payload?.hypertables || []).length ? (
                payload.hypertables.map((row) => (
                  <tr key={`${row.hypertable_schema}-${row.hypertable_name}`}>
                    <td style={tdStyle}>{row.hypertable_schema}</td>
                    <td style={tdStyle}>{row.hypertable_name}</td>
                  </tr>
                ))
              ) : (
                <tr><td style={tdStyle} colSpan={2}>Sem hypertables encontradas para FA-5.</td></tr>
              )}
            </tbody>
          </table>
        </TableWrap>
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Policies / Jobs</h2>
        <TableWrap>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>hypertable_name</th>
                <th style={thStyle}>proc_name</th>
                <th style={thStyle}>schedule_interval</th>
              </tr>
            </thead>
            <tbody>
              {(payload?.jobs || []).length ? (
                payload.jobs.map((row) => (
                  <tr key={`${row.hypertable_name}-${row.proc_name}`}>
                    <td style={tdStyle}>{row.hypertable_name}</td>
                    <td style={tdStyle}>{row.proc_name}</td>
                    <td style={tdStyle}>{row.schedule_interval || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr><td style={tdStyle} colSpan={3}>Sem jobs encontrados para FA-5.</td></tr>
              )}
            </tbody>
          </table>
        </TableWrap>
      </section>
    </div>
  );
}

function TableWrap({ children }) {
  return <div style={{ overflowX: "auto" }}>{children}</div>;
}

function Kpi({ label, value }) {
  return (
    <article style={kpiStyle}>
      <strong style={{ color: "#BFDBFE", fontSize: 18 }}>{value}</strong>
      <small style={{ color: "#94A3B8" }}>{label}</small>
    </article>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", marginTop: 0 };
const actionsStyle = { marginTop: 10, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" };
const buttonPrimaryStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const linkButtonStyle = { textDecoration: "none", padding: "10px 14px", borderRadius: 10, border: "1px solid rgba(148,163,184,0.5)", color: "#E2E8F0", fontWeight: 600 };
const errorStyle = { marginTop: 10, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const kpiGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 8 };
const kpiStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10, display: "grid", gap: 4 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 680 };
const thStyle = { textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.14)", padding: "8px 10px", fontSize: 12 };
const tdStyle = { borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "8px 10px", verticalAlign: "top", fontSize: 12 };
