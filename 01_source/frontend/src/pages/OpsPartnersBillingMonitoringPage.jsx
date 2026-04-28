import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
  const [externalReference, setExternalReference] = useState("");
  const [onlyMismatches, setOnlyMismatches] = useState(true);
  const [auditRows, setAuditRows] = useState([]);
  const [kpiDate, setKpiDate] = useState(new Date().toISOString().slice(0, 10));
  const [kpiDailyRows, setKpiDailyRows] = useState([]);
  const [revRecRows, setRevRecRows] = useState([]);

  function buildKpiAlerts(rows) {
    const alerts = [];
    rows.forEach((row) => {
      const dso = Number(row?.dso_days || 0);
      const grossMargin = Number(row?.gross_margin_pct || 0);
      const revenue = Number(row?.revenue_recognized_cents || 0);
      const codeSuffix = `${row?.partner_id || "UNKNOWN"}:${row?.locker_id || "GLOBAL"}`;
      if (dso >= 45) {
        alerts.push({
          severity: "CRITICAL",
          code: "OPS_DSO_HIGH",
          title: "DSO operacional acima do limite",
          impact: `DSO em ${dso.toFixed(2)} dias para ${codeSuffix}.`,
          action: "Revisar inadimplência, política de cobrança e aging de AR.",
        });
      }
      if (grossMargin > 0 && grossMargin <= 10) {
        alerts.push({
          severity: "HIGH",
          code: "OPS_GROSS_MARGIN_LOW",
          title: "Margem bruta operacional baixa",
          impact: `Gross margin em ${grossMargin.toFixed(2)}% para ${codeSuffix}.`,
          action: "Validar OPEX/depreciação alocada e revisar preço por ciclo.",
        });
      }
      if (revenue === 0) {
        alerts.push({
          severity: "MEDIUM",
          code: "OPS_REVENUE_RECOGNITION_ZERO",
          title: "Receita reconhecida zerada no dia",
          impact: `Sem receita reconhecida para ${codeSuffix} em ${kpiDate}.`,
          action: "Verificar emissão de invoices, regras de reconhecimento e backfill.",
        });
      }
    });
    const rank = { CRITICAL: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
    return alerts.sort((a, b) => (rank[a.severity] || 10) - (rank[b.severity] || 10));
  }

  async function fetchSection(path, params) {
    const query = buildQuery({ ...params, limit: DEFAULT_LIMIT });
    const response = await fetch(`${BILLING_BASE}${path}?${query}`, { method: "GET", headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(payload, "Falha na consulta de acompanhamento."));
    return Array.isArray(payload?.items) ? payload.items : [];
  }

  async function fetchPayload(path, params) {
    const query = buildQuery(params || {});
    const response = await fetch(`${BILLING_BASE}${path}?${query}`, { method: "GET", headers });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(payload, "Falha na consulta."));
    return payload || {};
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
      const [nextCycles, nextInvoices, nextCreditNotes, nextDisputes, nextAudit, nextKpiDaily, nextRevRec] = await Promise.all([
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
        fetchSection("/admin/fiscal/ledger-compat/audit", {
          external_reference: externalReference,
          only_mismatches: onlyMismatches ? "true" : "false",
          offset: 0,
          limit: 50,
        }),
        fetchPayload("/admin/fiscal/kpi/daily", {
          date_ref: kpiDate,
          limit: 50,
          offset: 0,
        }),
        fetchPayload("/admin/fiscal/revenue-recognition", {
          from_date: kpiDate,
          to_date: kpiDate,
          limit: 50,
          offset: 0,
        }),
      ]);

      setCycles(nextCycles);
      setInvoices(nextInvoices);
      setCreditNotes(nextCreditNotes);
      setDisputes(nextDisputes);
      setAuditRows(nextAudit);
      setKpiDailyRows(Array.isArray(nextKpiDaily?.items) ? nextKpiDaily.items : []);
      setRevRecRows(Array.isArray(nextRevRec?.items) ? nextRevRec.items : []);
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
        <div style={actionsStyle}>
          <Link to="/ops/partners/hypertables" style={opsLinkStyle}>
            Abrir página de Hypertables (FA-5 Timescale)
          </Link>
        </div>

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
          <label style={labelStyle}>
            external_reference (audit)
            <input
              style={inputStyle}
              value={externalReference}
              onChange={(e) => setExternalReference(e.target.value)}
              placeholder="acct:BILLING_CYCLE_COMPUTED:..."
            />
          </label>
          <label style={labelStyle}>
            data KPI diário (FA-5)
            <input style={inputStyle} type="date" value={kpiDate} onChange={(e) => setKpiDate(e.target.value)} />
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
              setExternalReference("");
            }}
          >
            Limpar filtros
          </button>
          <label style={{ ...labelStyle, display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={onlyMismatches}
              onChange={(e) => setOnlyMismatches(Boolean(e.target.checked))}
            />
            somente divergências (only_mismatches=true)
          </label>
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

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>Ledger vs Journal (auditoria rápida)</h3>
          <TableWrap>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>external_reference</th>
                  <th style={thStyle}>event_type</th>
                  <th style={thStyle}>journal_balanced</th>
                  <th style={thStyle}>amount_matches_compat</th>
                  <th style={thStyle}>ledger_amount_cents</th>
                  <th style={thStyle}>journal_amount_cents_derived</th>
                </tr>
              </thead>
              <tbody>
                {auditRows.length ? auditRows.map((row) => (
                  <tr key={`${row.external_reference}-${row.journal?.journal_entry_id || "no-journal"}`}>
                    <td style={tdStyle}>{row.external_reference || "-"}</td>
                    <td style={tdStyle}>{row.event_type || "-"}</td>
                    <td style={tdStyle}>{String(Boolean(row.audit?.journal_balanced))}</td>
                    <td style={tdStyle}>{String(Boolean(row.audit?.amount_matches_compat))}</td>
                    <td style={tdStyle}>{row.ledger?.amount_cents ?? "-"}</td>
                    <td style={tdStyle}>{row.journal?.amount_cents_derived ?? "-"}</td>
                  </tr>
                )) : (
                  <tr><td style={tdStyle} colSpan={6}>Sem divergências para o filtro atual.</td></tr>
                )}
              </tbody>
            </table>
          </TableWrap>
        </section>

        <section style={sectionStyle}>
          <h3 style={sectionTitleStyle}>FA-5 - Revenue Recognition & KPI Daily (OPS style)</h3>
          <div style={healthSectionStyle}>
            <header style={healthHeaderStyle}>
              <strong>Alertas ativos - exibindo {buildKpiAlerts(kpiDailyRows).length}/1</strong>
              <div style={healthFiltersRowStyle}>
                <input style={inputStyle} readOnly value={(buildKpiAlerts(kpiDailyRows)[0]?.severity || "SEM_ALERTA")} />
                <input style={inputStyle} readOnly value={(buildKpiAlerts(kpiDailyRows)[0]?.code || "OPS_OK")} />
                <input style={inputStyle} readOnly value={String(kpiDailyRows.length)} />
                <button
                  type="button"
                  style={buttonGhostStyle}
                  onClick={() => {
                    setKpiDailyRows([]);
                    setRevRecRows([]);
                  }}
                >
                  Limpar seção
                </button>
              </div>
            </header>
            {buildKpiAlerts(kpiDailyRows).length ? (
              <article style={alertCardStyle}>
                <span style={severityTagStyle(buildKpiAlerts(kpiDailyRows)[0]?.severity)}>{buildKpiAlerts(kpiDailyRows)[0]?.severity}</span>
                <strong style={{ marginLeft: 8 }}>{buildKpiAlerts(kpiDailyRows)[0]?.code}</strong>
                <p style={mutedTextStyle}>{buildKpiAlerts(kpiDailyRows)[0]?.title}</p>
                <p style={mutedTextStyle}>Impacto: {buildKpiAlerts(kpiDailyRows)[0]?.impact}</p>
                <p style={mutedTextStyle}>Ação: {buildKpiAlerts(kpiDailyRows)[0]?.action}</p>
              </article>
            ) : (
              <p style={mutedTextStyle}>Sem alertas ativos para a data selecionada.</p>
            )}
            <TableWrap>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>partner_id</th>
                    <th style={thStyle}>locker_id</th>
                    <th style={thStyle}>revenue_recognized</th>
                    <th style={thStyle}>gross_margin_pct</th>
                    <th style={thStyle}>dso_days</th>
                    <th style={thStyle}>arpl</th>
                  </tr>
                </thead>
                <tbody>
                  {kpiDailyRows.length ? kpiDailyRows.map((row) => (
                    <tr key={`${row.partner_id}-${row.locker_id || "global"}`}>
                      <td style={tdStyle}>{row.partner_id}</td>
                      <td style={tdStyle}>{row.locker_id || "GLOBAL"}</td>
                      <td style={tdStyle}>{formatCents(row.revenue_recognized_cents, row.currency || "BRL")}</td>
                      <td style={tdStyle}>{Number(row.gross_margin_pct || 0).toFixed(2)}%</td>
                      <td style={tdStyle}>{Number(row.dso_days || 0).toFixed(2)}</td>
                      <td style={tdStyle}>{formatCents(row.arpl_cents, row.currency || "BRL")}</td>
                    </tr>
                  )) : (
                    <tr><td style={tdStyle} colSpan={6}>Sem registros de KPI diário.</td></tr>
                  )}
                </tbody>
              </table>
            </TableWrap>
            <TableWrap>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>recognition_date</th>
                    <th style={thStyle}>partner_id</th>
                    <th style={thStyle}>locker_id</th>
                    <th style={thStyle}>source_type</th>
                    <th style={thStyle}>source_id</th>
                    <th style={thStyle}>recognized_amount</th>
                  </tr>
                </thead>
                <tbody>
                  {revRecRows.length ? revRecRows.map((row) => (
                    <tr key={`${row.source_type}-${row.source_id}-${row.recognition_date}`}>
                      <td style={tdStyle}>{row.recognition_date}</td>
                      <td style={tdStyle}>{row.partner_id}</td>
                      <td style={tdStyle}>{row.locker_id || "GLOBAL"}</td>
                      <td style={tdStyle}>{row.source_type}</td>
                      <td style={tdStyle}>{row.source_id}</td>
                      <td style={tdStyle}>{formatCents(row.recognized_amount_cents, row.currency || "BRL")}</td>
                    </tr>
                  )) : (
                    <tr><td style={tdStyle} colSpan={6}>Sem registros de revenue recognition no período.</td></tr>
                  )}
                </tbody>
              </table>
            </TableWrap>
          </div>
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
const healthSectionStyle = { border: "1px solid rgba(255,255,255,0.10)", borderRadius: 12, padding: 12, background: "#0f172a" };
const healthHeaderStyle = { display: "grid", gap: 8, marginBottom: 12 };
const healthFiltersRowStyle = { display: "grid", gridTemplateColumns: "1fr 1fr 100px auto", gap: 8 };
const alertCardStyle = { border: "1px solid rgba(248,113,113,0.35)", borderRadius: 12, padding: 12, marginBottom: 12, background: "rgba(127,29,29,0.25)" };
const severityTagStyle = (severity) => ({
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 8,
  fontSize: 11,
  fontWeight: 700,
  border: "1px solid rgba(255,255,255,0.16)",
  background:
    severity === "CRITICAL"
      ? "#7f1d1d"
      : severity === "HIGH"
        ? "#78350f"
        : severity === "MEDIUM"
          ? "#1e3a8a"
          : "#334155",
});
const opsLinkStyle = {
  textDecoration: "none",
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(59,130,246,0.14)",
  color: "#bfdbfe",
  fontWeight: 700,
};
