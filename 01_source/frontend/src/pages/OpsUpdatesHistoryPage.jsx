import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const TIMELINE_TEMPLATE_JSON = `{
  "date": "YYYY-MM-DD",
  "scope": "L-3 D4",
  "title": "Resumo curto da entrega",
  "description": "Descrição breve do valor operacional entregue.",
  "routes": [
    "GET /alguma/rota",
    "POST /alguma/rota"
  ],
  "directLink": "/ops/alguma-pagina",
  "directLinkLabel": "Abrir página operacional"
}`;

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

function parseError(payload, fallback = "Nao foi possivel carregar o overview de manifestos.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

const UPDATES = [
  {
    date: "2026-04-26",
    scope: "L-3 D1",
    title: "Fundação de dados/manifests",
    description:
      "Migrações idempotentes, modelos e contratos para manifests/capacidade/rates, com endpoints base e auditoria OPS.",
    routes: [
      "POST /logistics/manifests",
      "POST /logistics/{partner_id}/capacity",
      "GET /logistics/manifests",
      "GET /logistics/{partner_id}/capacity",
    ],
    directLink: "/ops/logistics/manifests",
    directLinkLabel: "Abrir operação de manifests (D1/D2)",
  },
  {
    date: "2026-04-26",
    scope: "L-3 D2",
    title: "Fluxo operacional de manifesto",
    description:
      "Itens de manifesto, fechamento idempotente com reconciliação e endpoint de exception idempotente por item.",
    routes: [
      "GET /logistics/manifests/{manifest_id}/items",
      "POST /logistics/manifests/{manifest_id}/close",
      "POST /logistics/manifests/{manifest_id}/items/{item_id}/exception",
    ],
    directLink: "/ops/logistics/manifests",
    directLinkLabel: "Abrir operação D2 de manifests",
  },
  {
    date: "2026-04-26",
    scope: "L-3 D3",
    title: "Observabilidade de manifestos + painel OPS",
    description:
      "Overview OPS de manifestos com comparação temporal, confidence_badge, alertas e página dedicada para operação.",
    routes: [
      "GET /logistics/ops/manifests/overview",
      "GET /logistics/ops/manifests/view",
      "UI /ops/logistics/manifests-overview",
    ],
    directLink: "/ops/logistics/manifests-overview",
    directLinkLabel: "Abrir painel OPS de manifests",
  },
  {
    date: "2026-04-26",
    scope: "Pr-1 D1",
    title: "Assets de catálogo (media + barcodes)",
    description:
      "Endpoints mínimos para gestão de media e barcodes por produto, com página OPS dedicada para operação rápida.",
    routes: [
      "POST /products/{id}/media",
      "GET /products/{id}/media",
      "POST /products/{id}/barcodes",
      "GET /products/{id}/barcodes",
      "UI /ops/products/assets",
    ],
    directLink: "/ops/products/assets",
    directLinkLabel: "Abrir OPS de assets de produtos",
  },
];

export default function OpsUpdatesHistoryPage() {
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
  const [copyStatus, setCopyStatus] = useState("");

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
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(data));
      setPayload(data || null);
    } catch (err) {
      setError(String(err?.message || err || "erro desconhecido"));
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleCopyTemplate() {
    try {
      await navigator.clipboard.writeText(TIMELINE_TEMPLATE_JSON);
      setCopyStatus("Template copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch (_) {
      setCopyStatus("Não foi possível copiar automaticamente. Copie manualmente o bloco JSON.");
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>OPS - Updates History</h1>
        <p style={mutedStyle}>
          Histórico de acréscimos OPS com descrição curta de valor e trilha técnica por sprint.
        </p>

        <details style={templateBoxStyle}>
          <summary style={templateSummaryStyle}>Mini-template JSON (novos itens da timeline)</summary>
          <p style={{ ...mutedStyle, marginTop: 8 }}>
            Campos obrigatórios: <b>scope</b>, <b>description</b>, <b>routes</b>, <b>directLink</b>.
          </p>
          <button type="button" style={copyButtonStyle} onClick={() => void handleCopyTemplate()}>
            Copiar template
          </button>
          {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}
          <pre style={templateJsonStyle}>{TIMELINE_TEMPLATE_JSON}</pre>
        </details>

        <div style={timelineStyle}>
          {UPDATES.map((entry) => (
            <article key={`${entry.date}-${entry.scope}-${entry.title}`} style={entryStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                <strong>{entry.title}</strong>
                <span style={badgeStyle}>{entry.scope}</span>
              </div>
              <small style={{ color: "#94A3B8" }}>{entry.date}</small>
              <p style={{ margin: "8px 0", color: "#CBD5E1" }}>{entry.description}</p>
              <ul style={routesListStyle}>
                {entry.routes.map((route) => (
                  <li key={route} style={{ color: "#BFDBFE", fontSize: 12 }}>
                    {route}
                  </li>
                ))}
              </ul>
              {entry.directLink ? (
                <div style={{ marginTop: 8 }}>
                  <Link to={entry.directLink} style={directLinkStyle}>
                    {entry.directLinkLabel || "Abrir rota relacionada"}
                  </Link>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Overview D3 - Manifests</h2>
        <p style={mutedStyle}>Consumo da rota `/logistics/ops/manifests/overview` para validação operacional contínua.</p>
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
        <button type="button" onClick={() => void loadOverview()} style={buttonStyle} disabled={loading}>
          {loading ? "Atualizando..." : "Atualizar overview"}
        </button>

        {error ? <pre style={errorStyle}>{error}</pre> : null}
        {payload ? (
          <div style={{ marginTop: 12 }}>
            <div style={kpiGridStyle}>
              <Kpi label="Confidence" value={payload?.confidence_badge || "-"} />
              <Kpi label="Current total" value={payload?.totals?.current_total ?? 0} />
              <Kpi label="Pending/In transit" value={payload?.totals?.pending_or_in_transit ?? 0} />
              <Kpi label="Partial/Failed rate" value={`${payload?.totals?.partial_failed_rate_pct ?? 0}%`} />
            </div>
            <pre style={jsonStyle}>{JSON.stringify(payload, null, 2)}</pre>
          </div>
        ) : (
          <p style={mutedStyle}>Clique em "Atualizar overview" para carregar os dados.</p>
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

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8" };
const templateBoxStyle = { marginTop: 10, marginBottom: 12, background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10 };
const templateSummaryStyle = { cursor: "pointer", color: "#BFDBFE", fontWeight: 700 };
const copyButtonStyle = { marginTop: 8, padding: "6px 10px", borderRadius: 999, border: "1px solid rgba(59,130,246,0.45)", background: "rgba(59,130,246,0.12)", color: "#BFDBFE", fontWeight: 700, cursor: "pointer", fontSize: 12 };
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "#93C5FD" };
const templateJsonStyle = { marginTop: 8, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 10, overflow: "auto", fontSize: 12 };
const timelineStyle = { display: "grid", gap: 10 };
const entryStyle = { border: "1px solid #334155", borderRadius: 12, padding: 12, background: "#0B1220" };
const badgeStyle = { border: "1px solid #1D4ED8", borderRadius: 999, padding: "2px 8px", color: "#BFDBFE", fontSize: 11, fontWeight: 700 };
const routesListStyle = { margin: 0, paddingLeft: 16, display: "grid", gap: 4 };
const directLinkStyle = {
  display: "inline-flex",
  textDecoration: "none",
  color: "#93C5FD",
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(59,130,246,0.12)",
  borderRadius: 999,
  padding: "4px 10px",
  fontSize: 12,
  fontWeight: 700,
};
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 10 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const buttonStyle = { padding: "10px 14px", borderRadius: 10, border: "none", background: "#1D4ED8", color: "#F8FAFC", fontWeight: 700, cursor: "pointer" };
const errorStyle = { marginTop: 10, background: "rgba(220,38,38,0.12)", color: "#FCA5A5", border: "1px solid rgba(220,38,38,0.45)", borderRadius: 10, padding: 10 };
const jsonStyle = { marginTop: 10, background: "#020617", border: "1px solid #1E293B", borderRadius: 10, padding: 12, overflow: "auto", fontSize: 12 };
const kpiGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 8 };
const kpiStyle = { background: "#0B1220", border: "1px solid #334155", borderRadius: 10, padding: 10, display: "grid", gap: 4 };
