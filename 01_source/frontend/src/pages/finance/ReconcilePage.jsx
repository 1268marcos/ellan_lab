import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { walletApi } from "../../api/wallet";

const shell = { maxWidth: 960, margin: "0 auto", padding: "24px 16px", color: "#e2e8f0", minHeight: "60vh" };
const box = { marginTop: 16, borderRadius: 12, border: "1px solid #334155", padding: 16, background: "#0f172a99" };

export default function ReconcilePage() {
  const [divs, setDivs] = useState(null);
  const [hist, setHist] = useState(null);
  const [rep, setRep] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const { data } = await walletApi.getDivergences();
      setDivs(data);
    } catch {
      setDivs([]);
    }
    try {
      const { data } = await walletApi.getReconcileHistory();
      setHist(data);
    } catch {
      setHist([]);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function runReconcile() {
    setBusy(true);
    setMsg(null);
    try {
      const { data } = await walletApi.reconcile();
      setRep(data);
      setMsg("Reconciliação executada.");
      await refresh();
    } catch (err) {
      setMsg(err?.message || "Erro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={shell}>
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 12, marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 600, color: "#fff", margin: 0 }}>Reconciliação</h1>
          <p style={{ fontSize: 14, color: "#94a3b8", marginTop: 4 }}>Job manual · divergências · histórico</p>
        </div>
        <Link to="/finance/wallet" style={{ fontSize: 14, color: "#34d399" }}>
          ← Wallet
        </Link>
      </div>

      <button
        type="button"
        disabled={busy}
        onClick={runReconcile}
        style={{
          padding: "10px 16px",
          borderRadius: 6,
          border: "none",
          background: busy ? "#475569" : "#d97706",
          color: "#fff",
          fontWeight: 600,
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        {busy ? "Executando…" : "POST /wallet/reconcile"}
      </button>
      {msg && <p style={{ marginTop: 8, fontSize: 14, color: "#94a3b8" }}>{msg}</p>}

      <section style={box}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1" }}>Relatório (última execução)</h2>
        <pre style={{ marginTop: 8, maxHeight: 192, overflow: "auto", fontSize: 12, color: "#94a3b8" }}>
          {rep != null ? JSON.stringify(rep, null, 2) : "—"}
        </pre>
      </section>

      <section style={box}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1" }}>Divergências</h2>
        <pre style={{ marginTop: 8, maxHeight: 192, overflow: "auto", fontSize: 12, color: "#94a3b8" }}>
          {JSON.stringify(divs, null, 2)}
        </pre>
      </section>

      <section style={box}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1" }}>Histórico</h2>
        <pre style={{ marginTop: 8, maxHeight: 192, overflow: "auto", fontSize: 12, color: "#94a3b8" }}>
          {JSON.stringify(hist, null, 2)}
        </pre>
      </section>
    </div>
  );
}
