import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  billingFiscalGet,
  bfBtn,
  bfCardStyle,
  bfErr,
  bfInput,
  bfLabel,
  bfMuted,
  bfPageStyle,
  bfRow,
  bfTable,
  bfTableWrap,
  bfTd,
  bfTh,
} from "../utils/billingFiscalOpsApi";

export default function BillingReconciliationGapsPage() {
  const { token } = useAuth();
  const [date, setDate] = useState("");
  const [status, setStatus] = useState("OPEN");
  const [refresh, setRefresh] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const qs = new URLSearchParams({
        status,
        limit: "200",
        refresh: refresh ? "true" : "false",
      });
      if (date.trim()) qs.set("date", date.trim());
      const payload = await billingFiscalGet(`/admin/fiscal/gaps?${qs.toString()}`, token);
      setCount(Number(payload?.count || 0));
      setItems(Array.isArray(payload?.items) ? payload.items : []);
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={bfPageStyle}>
      <section style={bfCardStyle}>
        <OpsPageTitleHeader title="OPS — Billing / Fiscal — Reconciliation gaps" />
        <p style={bfMuted}>GET <code>/admin/fiscal/gaps</code> (opcional scan com <code>refresh=true</code>).</p>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", maxWidth: 720 }}>
          <label style={bfLabel}>
            date (YYYY-MM-DD, opcional)
            <input style={bfInput} type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <label style={bfLabel}>
            status
            <select style={bfInput} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="OPEN">OPEN</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="">(vazio)</option>
            </select>
          </label>
          <label style={{ ...bfLabel, flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={refresh} onChange={(e) => setRefresh(e.target.checked)} />
            refresh (re-scan)
          </label>
        </div>
        <div style={bfRow}>
          <button type="button" style={bfBtn} onClick={load} disabled={loading}>
            {loading ? "Carregando…" : `Carregar (${count})`}
          </button>
        </div>
        {error ? <div style={bfErr}>{error}</div> : null}
        {items.length ? (
          <div style={bfTableWrap}>
            <table style={bfTable}>
              <thead>
                <tr>
                  <th style={bfTh}>tipo</th>
                  <th style={bfTh}>severidade</th>
                  <th style={bfTh}>order_id</th>
                  <th style={bfTh}>invoice_id</th>
                  <th style={bfTh}>dedupe_key</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id}>
                    <td style={bfTd}>{r.gap_type}</td>
                    <td style={bfTd}>{r.severity}</td>
                    <td style={bfTd}>{r.order_id}</td>
                    <td style={bfTd}>{r.invoice_id || "—"}</td>
                    <td style={bfTd}>{r.dedupe_key}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
