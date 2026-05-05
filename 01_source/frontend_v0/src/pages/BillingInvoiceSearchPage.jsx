
import React, { useMemo, useState } from "react";
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
} from "../utils/billingFiscalOpsApi";

export default function BillingInvoiceSearchPage() {
  const { token } = useAuth();
  const [mode, setMode] = useState("order");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  const path = useMemo(() => {
    const v = String(q || "").trim();
    if (!v) return "";
    if (mode === "order") return `/internal/invoices/by-order/${encodeURIComponent(v)}`;
    if (mode === "receipt") return `/internal/invoices/by-receipt-code/${encodeURIComponent(v)}`;
    return `/internal/invoices/${encodeURIComponent(v)}`;
  }, [mode, q]);

  async function runSearch() {
    setError("");
    setData(null);
    if (!path) {
      setError("Informe um identificador.");
      return;
    }
    setLoading(true);
    try {
      setData(await billingFiscalGet(path, token));
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={bfPageStyle}>
      <section style={bfCardStyle}>
        <OpsPageTitleHeader title="OPS — Billing / Fiscal — Busca de invoice" />
        <p style={bfMuted}>
          Usa apenas GET existentes em <code>/internal/invoices</code> (por pedido, ID ou código de comprovante). Não há
          listagem paginada no backend.
        </p>
        <div style={{ display: "grid", gap: 10, maxWidth: 520 }}>
          <label style={bfLabel}>
            Modo
            <select style={bfInput} value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="order">by-order (order_id)</option>
              <option value="id">id (invoice_id)</option>
              <option value="receipt">by-receipt-code</option>
            </select>
          </label>
          <label style={bfLabel}>
            Valor
            <input style={bfInput} value={q} onChange={(e) => setQ(e.target.value)} placeholder="order-uuid / inv_… / chave" />
          </label>
        </div>
        <div style={bfRow}>
          <button type="button" style={bfBtn} onClick={runSearch} disabled={loading}>
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>
        {error ? <div style={bfErr}>{error}</div> : null}
        {data ? (
          <pre style={{ marginTop: 16, fontSize: 11, overflow: "auto", maxHeight: "60vh", color: "#e2e8f0" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        ) : null}
      </section>
    </div>
  );
}

