
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

export default function BillingKpiDailyPage() {
  const { token } = useAuth();
  const [dateRef, setDateRef] = useState(new Date().toISOString().slice(0, 10));
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState("");

  async function load() {
    setError("");
    setLoading(true);
    try {
      const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (dateRef.trim()) qs.set("date_ref", dateRef.trim());
      const payload = await billingFiscalGet(`/admin/fiscal/kpi/daily?${qs.toString()}`, token);
      setItems(Array.isArray(payload?.items) ? payload.items : []);
      setMeta(JSON.stringify({ snapshot_date: payload?.snapshot_date, count: payload?.count }, null, 2));
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={bfPageStyle}>
      <section style={bfCardStyle}>
        <OpsPageTitleHeader title="OPS — Billing / Fiscal — KPI diário" />
        <p style={bfMuted}>GET <code>/admin/fiscal/kpi/daily</code></p>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", maxWidth: 560 }}>
          <label style={bfLabel}>
            date_ref
            <input style={bfInput} type="date" value={dateRef} onChange={(e) => setDateRef(e.target.value)} />
          </label>
          <label style={bfLabel}>
            limit
            <input style={bfInput} type="number" min={1} max={1000} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          </label>
          <label style={bfLabel}>
            offset
            <input style={bfInput} type="number" min={0} value={offset} onChange={(e) => setOffset(Number(e.target.value))} />
          </label>
        </div>
        <div style={bfRow}>
          <button type="button" style={bfBtn} onClick={load} disabled={loading}>
            {loading ? "Carregando…" : "Carregar"}
          </button>
        </div>
        {error ? <div style={bfErr}>{error}</div> : null}
        {meta ? (
          <pre style={{ marginTop: 8, fontSize: 11, color: "#cbd5e1" }}>{meta}</pre>
        ) : null}
        {items.length ? (
          <div style={bfTableWrap}>
            <table style={bfTable}>
              <thead>
                <tr>
                  <th style={bfTh}>partner_id</th>
                  <th style={bfTh}>locker_id</th>
                  <th style={bfTh}>revenue_cents</th>
                  <th style={bfTh}>dso_days</th>
                  <th style={bfTh}>margin %</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r, i) => (
                  <tr key={`${r.partner_id}-${r.locker_id}-${i}`}>
                    <td style={bfTd}>{r.partner_id}</td>
                    <td style={bfTd}>{r.locker_id ?? "—"}</td>
                    <td style={bfTd}>{r.revenue_recognized_cents}</td>
                    <td style={bfTd}>{r.dso_days}</td>
                    <td style={bfTd}>{r.gross_margin_pct}</td>
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

