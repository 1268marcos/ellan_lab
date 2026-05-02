import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  billingFiscalGet,
  bfBtn,
  bfCardStyle,
  bfErr,
  bfPageStyle,
  bfRow,
  bfTable,
  bfTableWrap,
  bfTd,
  bfTh,
  bfMuted,
} from "../utils/billingFiscalOpsApi";

export default function BillingInvoiceQueuePage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dead, setDead] = useState(null);
  const [gaps, setGaps] = useState([]);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const [d, g] = await Promise.all([
        billingFiscalGet("/admin/fiscal/dead-letters?threshold=10", token),
        billingFiscalGet("/admin/fiscal/gaps?status=OPEN&limit=80", token),
      ]);
      setDead(d);
      setGaps(Array.isArray(g?.items) ? g.items : []);
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={bfPageStyle}>
      <section style={bfCardStyle}>
        <OpsPageTitleHeader title="OPS — Billing / Fiscal — Fila (dead letters + gaps)" />
        <p style={bfMuted}>
          Não existe <code>GET /internal/invoices/queue</code>. Esta visão compõe{" "}
          <code>/admin/fiscal/dead-letters</code> e gaps OPEN (itens com <code>invoice_id</code> quando houver).
        </p>
        <div style={bfRow}>
          <button type="button" style={bfBtn} onClick={load} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </button>
          <Link to="/ops/billing/invoices" style={{ color: "#93c5fd" }}>
            Ir para busca de invoice
          </Link>
        </div>
        {error ? <div style={bfErr}>{error}</div> : null}
        {dead ? (
          <pre style={{ marginTop: 12, fontSize: 11, color: "#e2e8f0" }}>{JSON.stringify(dead, null, 2)}</pre>
        ) : null}
        {gaps.length ? (
          <div style={bfTableWrap}>
            <table style={bfTable}>
              <thead>
                <tr>
                  <th style={bfTh}>gap_type</th>
                  <th style={bfTh}>severity</th>
                  <th style={bfTh}>order_id</th>
                  <th style={bfTh}>invoice_id</th>
                  <th style={bfTh}>status</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map((r) => (
                  <tr key={r.id || r.dedupe_key}>
                    <td style={bfTd}>{r.gap_type}</td>
                    <td style={bfTd}>{r.severity}</td>
                    <td style={bfTd}>{r.order_id}</td>
                    <td style={bfTd}>{r.invoice_id || "—"}</td>
                    <td style={bfTd}>{r.status}</td>
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
