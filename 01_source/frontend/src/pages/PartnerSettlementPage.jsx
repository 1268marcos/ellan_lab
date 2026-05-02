import React, { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsActionButton from "../components/OpsActionButton";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";

function parseError(payload, fallback = "Falha na requisição.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (payload?.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) return payload.detail.message.trim();
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) return payload.detail.type.trim();
  }
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

function csvEscape(val) {
  const s = val == null ? "" : String(val);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function rowsToCsv(headers, rows) {
  const head = headers.map(csvEscape).join(",");
  const body = rows.map((row) => row.map(csvEscape).join(",")).join("\n");
  return `${head}\n${body}\n`;
}

function downloadBlob(filename, mime, body) {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadJson(filename, data) {
  downloadBlob(filename, "application/json", JSON.stringify(data, null, 2));
}

export default function PartnerSettlementPage() {
  const { token } = useAuth();
  const authHeaders = useMemo(() => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  const [partnerId, setPartnerId] = useState("partner_demo_001");
  const [statusFilter, setStatusFilter] = useState("");
  const [fromPeriod, setFromPeriod] = useState("");
  const [toPeriod, setToPeriod] = useState("");
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState("");
  const [itemsPayload, setItemsPayload] = useState(null);
  const [performanceRows, setPerformanceRows] = useState([]);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  const latestSla = performanceRows.length ? performanceRows[0]?.sla_compliance_pct : null;

  const loadPerformance = useCallback(async () => {
    const pid = String(partnerId || "").trim();
    if (!token || !pid) return;
    setLoading("performance");
    setError("");
    try {
      const resp = await fetch(`${ORDER_PICKUP_BASE}/partners/${encodeURIComponent(pid)}/performance?limit=6`, {
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(parseError(data));
      setPerformanceRows(Array.isArray(data.items) ? data.items : []);
    } catch (e) {
      setPerformanceRows([]);
      setError(String(e?.message || e));
    } finally {
      setLoading("");
    }
  }, [authHeaders, partnerId, token]);

  const loadBatches = useCallback(async () => {
    const pid = String(partnerId || "").trim();
    if (!token) {
      setError("Faça login com perfil OPS (admin_operacao / auditoria).");
      return;
    }
    if (!pid) {
      setError("Informe partner_id.");
      return;
    }
    setLoading("batches");
    setError("");
    setItemsPayload(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", "100");
      if (String(statusFilter || "").trim()) params.set("status", String(statusFilter).trim().toUpperCase());
      if (String(fromPeriod || "").trim()) params.set("from_period_start", String(fromPeriod).trim());
      if (String(toPeriod || "").trim()) params.set("to_period_end", String(toPeriod).trim());
      const resp = await fetch(`${ORDER_PICKUP_BASE}/partners/${encodeURIComponent(pid)}/settlements?${params}`, {
        headers: { Accept: "application/json", ...authHeaders },
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(parseError(data));
      const list = Array.isArray(data.items) ? data.items : [];
      setBatches(list);
      setSelectedBatchId((prev) => {
        if (!list.length) return "";
        if (list.some((b) => String(b.id) === String(prev))) return String(prev);
        return String(list[0].id || "");
      });
    } catch (e) {
      setBatches([]);
      setError(String(e?.message || e));
    } finally {
      setLoading("");
    }
  }, [authHeaders, fromPeriod, partnerId, statusFilter, toPeriod, token]);

  const loadItems = useCallback(async () => {
    const pid = String(partnerId || "").trim();
    const bid = String(selectedBatchId || "").trim();
    if (!token || !pid || !bid) {
      setError(!bid ? "Selecione um batch na tabela." : "Informe partner_id.");
      return;
    }
    setLoading("items");
    setError("");
    try {
      const resp = await fetch(
        `${ORDER_PICKUP_BASE}/partners/${encodeURIComponent(pid)}/settlements/${encodeURIComponent(bid)}/items?limit=500&offset=0`,
        { headers: { Accept: "application/json", ...authHeaders } }
      );
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(parseError(data));
      setItemsPayload(data);
    } catch (e) {
      setItemsPayload(null);
      setError(String(e?.message || e));
    } finally {
      setLoading("");
    }
  }, [authHeaders, partnerId, selectedBatchId, token]);

  function exportBatchesJson() {
    const pid = String(partnerId || "").trim();
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    downloadJson(`partner_settlement_batches_${pid || "unknown"}_${ts}.json`, {
      exported_at: new Date().toISOString(),
      partner_id: pid,
      source_tables: ["partner_settlement_batches"],
      batches,
    });
  }

  function exportBatchesCsv() {
    const pid = String(partnerId || "").trim();
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const headers = [
      "id",
      "partner_id",
      "period_start",
      "period_end",
      "status",
      "net_amount_cents",
      "currency",
      "total_orders",
      "gross_revenue_cents",
      "revenue_share_cents",
      "fees_cents",
    ];
    const rows = batches.map((b) => [
      b.id,
      b.partner_id,
      b.period_start,
      b.period_end,
      b.status,
      b.net_amount_cents,
      b.currency,
      b.total_orders,
      b.gross_revenue_cents,
      b.revenue_share_cents,
      b.fees_cents,
    ]);
    downloadBlob(`partner_settlement_batches_${pid || "unknown"}_${ts}.csv`, "text/csv;charset=utf-8", rowsToCsv(headers, rows));
  }

  function exportItemsJson() {
    const pid = String(partnerId || "").trim();
    const bid = String(selectedBatchId || "").trim();
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    downloadJson(`partner_settlement_items_${pid}_${bid}_${ts}.json`, {
      exported_at: new Date().toISOString(),
      partner_id: pid,
      batch_id: bid,
      source_tables: ["partner_settlement_items"],
      ...itemsPayload,
    });
  }

  function exportItemsCsv() {
    const pid = String(partnerId || "").trim();
    const bid = String(selectedBatchId || "").trim();
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    const items = Array.isArray(itemsPayload?.items) ? itemsPayload.items : [];
    const headers = ["id", "batch_id", "order_id", "order_date", "share_cents", "gross_cents", "share_pct", "currency"];
    const rows = items.map((it) => [
      it.id,
      it.batch_id,
      it.order_id,
      it.order_date,
      it.share_cents,
      it.gross_cents,
      it.share_pct,
      it.currency,
    ]);
    downloadBlob(`partner_settlement_items_${pid}_${bid}_${ts}.csv`, "text/csv;charset=utf-8", rowsToCsv(headers, rows));
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <OpsPageTitleHeader title="OPS — Partner settlement (batches & itens)" />
        <p style={mutedStyle}>
          Dados em <code style={codeInline}>partner_settlement_batches</code> (período, status,{" "}
          <code style={codeInline}>net_amount_cents</code>), <code style={codeInline}>partner_settlement_items</code> (
          <code style={codeInline}>order_id</code>, <code style={codeInline}>share_cents</code>) e contexto SLA em{" "}
          <code style={codeInline}>partner_performance_metrics</code> (<code style={codeInline}>sla_compliance_pct</code>).
        </p>
        <div style={navRowStyle}>
          <Link to="/ops/partners/financials-service-areas" style={linkStyle}>
            P-3 Financials & service-areas
          </Link>
          <span style={sepStyle}>·</span>
          <Link to="/ops/partners/reconciliation-dashboard" style={linkStyle}>
            Reconciliation dashboard
          </Link>
        </div>

        <div style={filtersStyle}>
          <label style={labelStyle}>
            partner_id
            <input value={partnerId} onChange={(e) => setPartnerId(e.target.value)} style={inputStyle} placeholder="partner_demo_001" />
          </label>
          <label style={labelStyle}>
            status (opcional)
            <input value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={inputStyle} placeholder="DRAFT | APPROVED | PAID" />
          </label>
          <label style={labelStyle}>
            from_period_start
            <input type="date" value={fromPeriod} onChange={(e) => setFromPeriod(e.target.value)} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            to_period_end
            <input type="date" value={toPeriod} onChange={(e) => setToPeriod(e.target.value)} style={inputStyle} />
          </label>
        </div>

        <div style={actionsStyle}>
          <OpsActionButton type="button" variant="primary" onClick={() => void loadBatches()} disabled={Boolean(loading)}>
            {loading === "batches" ? "Carregando batches…" : "Carregar batches"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void loadPerformance()} disabled={Boolean(loading)}>
            {loading === "performance" ? "Carregando SLA…" : "Carregar métricas (SLA)"}
          </OpsActionButton>
          <OpsActionButton type="button" variant="secondary" onClick={() => void loadItems()} disabled={Boolean(loading) || !selectedBatchId}>
            {loading === "items" ? "Carregando itens…" : "Carregar itens do batch"}
          </OpsActionButton>
        </div>

        {latestSla != null && Number.isFinite(Number(latestSla)) ? (
          <p style={slaStyle}>
            Último <code style={codeInline}>sla_compliance_pct</code> (mês mais recente):{" "}
            <strong>{Number(latestSla).toFixed(2)}%</strong>
            {performanceRows[0]?.period_month ? ` — período ${performanceRows[0].period_month}` : ""}
          </p>
        ) : null}

        {error ? <div style={errorStyle}>{error}</div> : null}

        <div style={exportRowStyle}>
          <span style={mutedStyle}>Export batches:</span>
          <OpsActionButton type="button" variant="copy" onClick={exportBatchesCsv} disabled={!batches.length}>
            CSV
          </OpsActionButton>
          <OpsActionButton type="button" variant="copy" onClick={exportBatchesJson} disabled={!batches.length}>
            JSON
          </OpsActionButton>
          <span style={{ ...mutedStyle, marginLeft: 12 }}>Export itens (batch selecionado):</span>
          <OpsActionButton type="button" variant="copy" onClick={exportItemsCsv} disabled={!itemsPayload?.items?.length}>
            CSV
          </OpsActionButton>
          <OpsActionButton type="button" variant="copy" onClick={exportItemsJson} disabled={!itemsPayload}>
            JSON
          </OpsActionButton>
        </div>
      </section>

      <section style={cardStyle}>
        <h2 style={h2Style}>Batches</h2>
        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Período</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Net (¢)</th>
                <th style={thStyle}>Pedidos</th>
                <th style={thStyle}>batch_id</th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={5} style={tdEmptyStyle}>
                    Nenhum batch carregado.
                  </td>
                </tr>
              ) : (
                batches.map((b) => {
                  const active = String(b.id) === String(selectedBatchId);
                  return (
                    <tr
                      key={b.id}
                      style={active ? trSelectedStyle : trStyle}
                      onClick={() => setSelectedBatchId(String(b.id))}
                      onKeyDown={(ev) => {
                        if (ev.key === "Enter" || ev.key === " ") {
                          ev.preventDefault();
                          setSelectedBatchId(String(b.id));
                        }
                      }}
                      tabIndex={0}
                      role="button"
                      aria-pressed={active}
                    >
                      <td style={tdStyle}>
                        {b.period_start} → {b.period_end}
                      </td>
                      <td style={tdStyle}>{b.status}</td>
                      <td style={tdMonoStyle}>{b.net_amount_cents}</td>
                      <td style={tdStyle}>{b.total_orders}</td>
                      <td style={tdMonoStyle}>{String(b.id).slice(0, 10)}…</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <p style={hintStyle}>Clique numa linha para selecionar o batch e carregar itens.</p>
      </section>

      <section style={cardStyle}>
        <h2 style={h2Style}>Itens do batch {selectedBatchId ? <code style={codeInline}>{selectedBatchId}</code> : "(nenhum)"}</h2>
        {itemsPayload ? (
          <p style={mutedStyle}>
            Total linhas: {itemsPayload.total} · share_total_cents: {itemsPayload.share_total_cents} · gross_total_cents:{" "}
            {itemsPayload.gross_total_cents}
          </p>
        ) : null}
        <div style={tableWrapStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>order_id</th>
                <th style={thStyle}>order_date</th>
                <th style={thStyle}>share_cents</th>
                <th style={thStyle}>gross_cents</th>
              </tr>
            </thead>
            <tbody>
              {!itemsPayload?.items?.length ? (
                <tr>
                  <td colSpan={4} style={tdEmptyStyle}>
                    Carregue itens após selecionar um batch.
                  </td>
                </tr>
              ) : (
                itemsPayload.items.map((it) => (
                  <tr key={it.id} style={trStyle}>
                    <td style={tdMonoStyle}>{it.order_id}</td>
                    <td style={tdStyle}>{it.order_date}</td>
                    <td style={tdMonoStyle}>{it.share_cents}</td>
                    <td style={tdMonoStyle}>{it.gross_cents}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "#E2E8F0", fontFamily: "system-ui, sans-serif", display: "grid", gap: 12 };
const cardStyle = { background: "#111827", border: "1px solid #334155", borderRadius: 16, padding: 16 };
const mutedStyle = { color: "#94A3B8", fontSize: 13, marginTop: 0 };
const codeInline = { fontSize: 12, color: "#CBD5E1" };
const navRowStyle = { display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginTop: 8 };
const linkStyle = { color: "#93C5FD", fontSize: 13 };
const sepStyle = { color: "#64748B" };
const filtersStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginTop: 12 };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };
const inputStyle = { padding: "8px 10px", borderRadius: 8, border: "1px solid #475569", background: "#020617", color: "#E2E8F0" };
const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 };
const exportRowStyle = { display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginTop: 14 };
const errorStyle = { marginTop: 10, padding: 10, borderRadius: 8, background: "rgba(220,38,38,0.15)", border: "1px solid rgba(248,113,113,0.4)", color: "#FCA5A5", fontSize: 13 };
const slaStyle = { marginTop: 10, fontSize: 13, color: "#A7F3D0" };
const h2Style = { marginTop: 0, fontSize: 16 };
const tableWrapStyle = { overflowX: "auto", marginTop: 8 };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const thStyle = { textAlign: "left", padding: "8px 10px", borderBottom: "1px solid #334155", color: "#94A3B8" };
const tdStyle = { padding: "8px 10px", borderBottom: "1px solid #1E293B" };
const tdMonoStyle = { ...tdStyle, fontFamily: "ui-monospace, monospace", fontSize: 12 };
const tdEmptyStyle = { ...tdStyle, color: "#64748B", fontStyle: "italic" };
const trStyle = { cursor: "pointer" };
const trSelectedStyle = { ...trStyle, background: "rgba(59,130,246,0.12)" };
const hintStyle = { fontSize: 12, color: "#64748B", marginBottom: 0 };
