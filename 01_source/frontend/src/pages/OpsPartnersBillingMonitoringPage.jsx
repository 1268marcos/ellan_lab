import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const DEFAULT_LIMIT = 20;

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
  if (typeof payload?.error?.message === "string" && payload.error.message.trim()) return payload.error.message.trim();
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === null || v === undefined) return;
    const normalized = String(v).trim();
    if (!normalized) return;
    query.set(k, normalized);
  });
  return query.toString();
}

export default function OpsPartnersBillingMonitoringPage() {
  const { token } = useAuth();
  const headers = useMemo(() => toHeaders(token), [token]);

  const [partnerId, setPartnerId] = useState("");
  const [countryCode, setCountryCode] = useState("");
  const [jurisdictionCode, setJurisdictionCode] = useState("");
  const [cycleStatus, setCycleStatus] = useState("");
  const [invoiceStatus, setInvoiceStatus] = useState("");

  const [cycleSortBy, setCycleSortBy] = useState("period_start");
  const [cycleSortOrder, setCycleSortOrder] = useState("desc");
  const [invoiceSortBy, setInvoiceSortBy] = useState("created_at");
  const [invoiceSortOrder, setInvoiceSortOrder] = useState("desc");

  const [cycleOffset, setCycleOffset] = useState(0);
  const [invoiceOffset, setInvoiceOffset] = useState(0);
  const [creditOffset, setCreditOffset] = useState(0);
  const [disputeOffset, setDisputeOffset] = useState(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdatedAt, setLastUpdatedAt] = useState("");
  const [cycles, setCycles] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [creditNotes, setCreditNotes] = useState([]);
  const [disputes, setDisputes] = useState([]);

  async function fetchSection(path, params) {
    const query = buildQuery({ ...params, limit: DEFAULT_LIMIT });
    const response = await fetch(`${BILLING_BASE}${path}?${query}`, { method: "GET", headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(payload, "Falha na consulta de acompanhamento."));
    return Array.isArray(payload?.items) ? payload.items : [];
  }

  async function loadAll() {
    const pid = String(partnerId || "").trim();
    if (!pid) {
      setError("Informe um partner_id para acompanhar os dados de billing.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [nextCycles, nextInvoices, nextCreditNotes, nextDisputes] = await Promise.all([
        fetchSection(`/v1/partners/${encodeURIComponent(pid)}/billing/cycles`, {
          country_code: countryCode,
          jurisdiction_code: jurisdictionCode,
          status: cycleStatus,
          sort_by: cycleSortBy,
          sort_order: cycleSortOrder,
          offset: cycleOffset,
        }),
        fetchSection(`/v1/partners/${encodeURIComponent(pid)}/invoices`, {
          country_code: countryCode,
          jurisdiction_code: jurisdictionCode,
          status: invoiceStatus,
          sort_by: invoiceSortBy,
          sort_order: invoiceSortOrder,
          offset: invoiceOffset,
        }),
        fetchSection(`/v1/partners/${encodeURIComponent(pid)}/credit-notes`, {
          country_code: countryCode,
          jurisdiction_code: jurisdictionCode,
          offset: creditOffset,
          sort_by: "created_at",
          sort_order: "desc",
        }),
        fetchSection(`/v1/partners/${encodeURIComponent(pid)}/billing/disputes`, {
          country_code: countryCode,
          jurisdiction_code: jurisdictionCode,
          offset: disputeOffset,
          sort_by: "created_at",
          sort_order: "desc",
        }),
      ]);

      setCycles(nextCycles);
      setInvoices(nextInvoices);
      setCreditNotes(nextCreditNotes);
      setDisputes(nextDisputes);
      setLastUpdatedAt(new Date().toLocaleString("pt-BR"));
    } catch (err) {
      setError(String(err?.message || err || "Erro desconhecido"));
    } finally {
      setLoading(false);
    }
  }

  function resetPagination() {
    setCycleOffset(0);
    setInvoiceOffset(0);
    setCreditOffset(0);
    setDisputeOffset(0);
  }

  function formatCents(value, currency = "BRL") {
    const amount = Number(value || 0) / 100;
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(amount);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0, marginBottom: 8 }}>OPS - Partners Billing Monitor</h1>
        <p style={mutedTextStyle}>
          Página simples de acompanhamento para ciclos, invoices, credit notes e histórico de disputas.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            partner_id (obrigatório)
            <input style={inputStyle} value={partnerId} onChange={(e) => setPartnerId(e.target.value)} placeholder="partner-001" />
          </label>
          <label style={labelStyle}>
            country_code
            <input style={inputStyle} value={countryCode} onChange={(e) => setCountryCode(e.target.value.toUpperCase())} placeholder="BR" />
          </label>
          <label style={labelStyle}>
            jurisdiction_code
            <input style={inputStyle} value={jurisdictionCode} onChange={(e) => setJurisdictionCode(e.target.value)} placeholder="SP" />
          </label>
          <label style={labelStyle}>
            cycle status
            <input style={inputStyle} value={cycleStatus} onChange={(e) => setCycleStatus(e.target.value.toUpperCase())} placeholder="OPEN" />
          </label>
          <label style={labelStyle}>
            invoice status
            <input style={inputStyle} value={invoiceStatus} onChange={(e) => setInvoiceStatus(e.target.value.toUpperCase())} placeholder="ISSUED" />
          </label>
        </div>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            cycle sort_by
            <select style={inputStyle} value={cycleSortBy} onChange={(e) => setCycleSortBy(e.target.value)}>
              <option value="period_start">period_start</option>
              <option value="period_end">period_end</option>
              <option value="created_at">created_at</option>
              <option value="updated_at">updated_at</option>
              <option value="total_amount_cents">total_amount_cents</option>
            </select>
          </label>
          <label style={labelStyle}>
            cycle sort_order
            <select style={inputStyle} value={cycleSortOrder} onChange={(e) => setCycleSortOrder(e.target.value)}>
              <option value="desc">desc</option>
              <option value="asc">asc</option>
            </select>
          </label>
          <label style={labelStyle}>
            invoice sort_by
            <select style={inputStyle} value={invoiceSortBy} onChange={(e) => setInvoiceSortBy(e.target.value)}>
              <option value="created_at">created_at</option>
              <option value="updated_at">updated_at</option>
              <option value="issued_at">issued_at</option>
              <option value="due_date">due_date</option>
              <option value="amount_cents">amount_cents</option>
            </select>
          </label>
          <label style={labelStyle}>
            invoice sort_order
            <select style={inputStyle} value={invoiceSortOrder} onChange={(e) => setInvoiceSortOrder(e.target.value)}>
              <option value="desc">desc</option>
              <option value="asc">asc</option>
            </select>
          </label>
        </div>

        <div style={actionsStyle}>
          <button
            type="button"
            style={buttonPrimaryStyle}
            disabled={loading}
            onClick={() => {
              resetPagination();
              void loadAll();
            }}
          >
            {loading ? "Atualizando..." : "Atualizar monitor"}
          </button>
          <button
            type="button"
            style={buttonGhostStyle}
            disabled={loading}
            onClick={() => {
              resetPagination();
              setCycleStatus("");
              setInvoiceStatus("");
              setCountryCode("");
              setJurisdictionCode("");
            }}
          >
            Limpar filtros
          </button>
          {lastUpdatedAt ? <small style={mutedTextStyle}>Última atualização: {lastUpdatedAt}</small> : null}
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>Cycles</h3>
          <TableWrap>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>cycle_id</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>period</th>
                  <th style={thStyle}>total</th>
                  <th style={thStyle}>currency</th>
                </tr>
              </thead>
              <tbody>
                {cycles.length ? cycles.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.period_start} - {row.period_end}</td>
                    <td style={tdStyle}>{formatCents(row.total_amount_cents, row.currency || "BRL")}</td>
                    <td style={tdStyle}>{row.currency || "-"}</td>
                  </tr>
                )) : (
                  <tr><td style={tdStyle} colSpan={5}>Sem registros.</td></tr>
                )}
              </tbody>
            </table>
          </TableWrap>
          <Pager
            offset={cycleOffset}
            onPrev={() => setCycleOffset((v) => Math.max(0, v - DEFAULT_LIMIT))}
            onNext={() => setCycleOffset((v) => v + DEFAULT_LIMIT)}
            onRefresh={() => void loadAll()}
            disabled={loading}
          />
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>Invoices</h3>
          <TableWrap>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>invoice_id</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>due_date</th>
                  <th style={thStyle}>amount</th>
                  <th style={thStyle}>document_type</th>
                </tr>
              </thead>
              <tbody>
                {invoices.length ? invoices.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.due_date || "-"}</td>
                    <td style={tdStyle}>{formatCents(row.amount_cents, row.currency || "BRL")}</td>
                    <td style={tdStyle}>{row.document_type || "-"}</td>
                  </tr>
                )) : (
                  <tr><td style={tdStyle} colSpan={5}>Sem registros.</td></tr>
                )}
              </tbody>
            </table>
          </TableWrap>
          <Pager
            offset={invoiceOffset}
            onPrev={() => setInvoiceOffset((v) => Math.max(0, v - DEFAULT_LIMIT))}
            onNext={() => setInvoiceOffset((v) => v + DEFAULT_LIMIT)}
            onRefresh={() => void loadAll()}
            disabled={loading}
          />
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>Credit Notes</h3>
          <TableWrap>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>credit_note_id</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>reason_code</th>
                  <th style={thStyle}>amount</th>
                </tr>
              </thead>
              <tbody>
                {creditNotes.length ? creditNotes.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.reason_code}</td>
                    <td style={tdStyle}>{formatCents(row.amount_cents, row.currency || "BRL")}</td>
                  </tr>
                )) : (
                  <tr><td style={tdStyle} colSpan={4}>Sem registros.</td></tr>
                )}
              </tbody>
            </table>
          </TableWrap>
          <Pager
            offset={creditOffset}
            onPrev={() => setCreditOffset((v) => Math.max(0, v - DEFAULT_LIMIT))}
            onNext={() => setCreditOffset((v) => v + DEFAULT_LIMIT)}
            onRefresh={() => void loadAll()}
            disabled={loading}
          />
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>Disputes History</h3>
          <TableWrap>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>cycle_id</th>
                  <th style={thStyle}>status</th>
                  <th style={thStyle}>dispute_reason</th>
                  <th style={thStyle}>updated_at</th>
                </tr>
              </thead>
              <tbody>
                {disputes.length ? disputes.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>{row.id}</td>
                    <td style={tdStyle}>{row.status}</td>
                    <td style={tdStyle}>{row.dispute_reason || "-"}</td>
                    <td style={tdStyle}>{row.updated_at || "-"}</td>
                  </tr>
                )) : (
                  <tr><td style={tdStyle} colSpan={4}>Sem registros.</td></tr>
                )}
              </tbody>
            </table>
          </TableWrap>
          <Pager
            offset={disputeOffset}
            onPrev={() => setDisputeOffset((v) => Math.max(0, v - DEFAULT_LIMIT))}
            onNext={() => setDisputeOffset((v) => v + DEFAULT_LIMIT)}
            onRefresh={() => void loadAll()}
            disabled={loading}
          />
        </section>
      </section>
    </div>
  );
}

function TableWrap({ children }) {
  return <div style={tableWrapStyle}>{children}</div>;
}

function Pager({ offset, onPrev, onNext, onRefresh, disabled }) {
  return (
    <div style={pagerStyle}>
      <small style={mutedTextStyle}>offset: {offset}</small>
      <div style={actionsStyle}>
        <button type="button" style={buttonGhostStyle} onClick={onPrev} disabled={disabled || offset === 0}>Anterior</button>
        <button type="button" style={buttonGhostStyle} onClick={onNext} disabled={disabled}>Próxima</button>
        <button type="button" style={buttonGhostStyle} onClick={onRefresh} disabled={disabled}>Recarregar seção</button>
      </div>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#f5f7fa", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "#11161c", border: "1px solid rgba(255,255,255,0.10)", borderRadius: 16, padding: 16 };
const mutedTextStyle = { color: "rgba(245,247,250,0.8)", marginTop: 0, marginBottom: 0 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#dbeafe" };
const filtersGridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" };
const inputStyle = { padding: "8px 10px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.14)", background: "#0b0f14", color: "#f5f7fa" };
const actionsStyle = { marginTop: 12, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" };
const buttonPrimaryStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(31,122,63,0.50)", background: "#1f7a3f", color: "#fff", cursor: "pointer", fontWeight: 700 };
const buttonGhostStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.16)", background: "transparent", color: "#e2e8f0", cursor: "pointer", fontWeight: 600 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const sectionStyle = { marginTop: 16, border: "1px solid rgba(148,163,184,0.25)", borderRadius: 10, padding: 10, background: "rgba(255,255,255,0.02)" };
const sectionTitleStyle = { marginTop: 0, marginBottom: 8, fontSize: 16 };
const tableWrapStyle = { overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 780 };
const thStyle = { textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.14)", padding: "8px 10px", fontSize: 12 };
const tdStyle = { borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "8px 10px", verticalAlign: "top", fontSize: 12 };
const pagerStyle = { marginTop: 8, display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap", alignItems: "center" };
