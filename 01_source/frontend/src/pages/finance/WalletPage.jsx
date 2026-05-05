import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { walletApi } from "../../api/wallet";
import { BalanceCard } from "../../components/finance/BalanceCard";
import { TransactionsTable } from "../../components/finance/TransactionsTable";

const shell = { maxWidth: 960, margin: "0 auto", padding: "24px 16px", color: "#e2e8f0", minHeight: "60vh" };
const label = { display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 4 };
const input = {
  width: "100%",
  maxWidth: 480,
  marginTop: 4,
  padding: "8px 10px",
  borderRadius: 6,
  border: "1px solid #475569",
  background: "#020617",
  color: "#f8fafc",
  fontFamily: "monospace",
  fontSize: 14,
};

const DEFAULT_ID = import.meta.env.VITE_WALLET_USER_ID || "user-demo-001";

export default function WalletPage() {
  const [partnerId, setPartnerId] = useState(DEFAULT_ID);
  const [balance, setBalance] = useState(null);
  const prevBal = useRef(null);
  const [deltaPct, setDeltaPct] = useState(null);
  const [txs, setTxs] = useState([]);
  const [expired, setExpired] = useState(null);
  const [amount, setAmount] = useState("1000");
  const [orderId, setOrderId] = useState("order-manual-1");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setMsg(null);
    try {
      const { data } = await walletApi.getBalance(partnerId);
      const b = data.balance ?? 0;
      const prev = prevBal.current;
      if (prev != null && prev !== 0) setDeltaPct(((b - prev) / Math.abs(prev)) * 100);
      else setDeltaPct(null);
      prevBal.current = b;
      setBalance({ ...data, balance: b });
    } catch {
      setBalance({ balance: 0, version: 0 });
      setDeltaPct(null);
    }
    try {
      const { data } = await walletApi.getTransactions(partnerId, {});
      setTxs(Array.isArray(data) ? data : []);
    } catch {
      setTxs([]);
    }
    try {
      const { data } = await walletApi.getExpiredCredits(partnerId);
      setExpired(data);
    } catch {
      setExpired(null);
    }
  }, [partnerId]);

  useEffect(() => {
    prevBal.current = null;
    setDeltaPct(null);
    void load();
  }, [partnerId, load]);

  async function apply(e) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await walletApi.applyCredit(partnerId, Number(amount), orderId);
      setMsg("Crédito aplicado / oferta criada.");
      await load();
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
          <h1 style={{ fontSize: 24, fontWeight: 600, color: "#fff", margin: 0 }}>Wallet</h1>
          <p style={{ fontSize: 14, color: "#94a3b8", marginTop: 4 }}>Saldo · transações · créditos expirados</p>
        </div>
        <Link to="/finance/reconcile" style={{ fontSize: 14, color: "#34d399" }}>
          Reconciliação →
        </Link>
      </div>

      <label style={label}>
        Parceiro / user_id
        <input
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value.trim())}
          onBlur={() => void load()}
          style={input}
        />
      </label>

      {balance && <BalanceCard label="Saldo" balanceCents={balance.balance} pctChange={deltaPct} />}

      <section style={{ marginTop: 24 }}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1", marginBottom: 8 }}>Transações</h2>
        <TransactionsTable rows={txs} />
      </section>

      <section style={{ marginTop: 24, borderRadius: 12, border: "1px solid #334155", padding: 16, background: "#0f172a99" }}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1" }}>Créditos expirados (JSON)</h2>
        <pre style={{ marginTop: 8, maxHeight: 160, overflow: "auto", background: "#020617", padding: 12, fontSize: 12, color: "#94a3b8" }}>
          {expired != null ? JSON.stringify(expired, null, 2) : "—"}
        </pre>
      </section>

      <form onSubmit={apply} style={{ marginTop: 24, borderRadius: 12, border: "1px solid #334155", padding: 16, background: "#0f172a99" }}>
        <h2 style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1" }}>Aplicar crédito manual</h2>
        <input type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)} style={{ ...input, marginTop: 12 }} />
        <input value={orderId} onChange={(e) => setOrderId(e.target.value)} placeholder="order_id" style={{ ...input, marginTop: 12 }} />
        <button
          type="submit"
          disabled={busy}
          style={{
            marginTop: 12,
            padding: "10px 16px",
            borderRadius: 6,
            border: "none",
            background: busy ? "#475569" : "#059669",
            color: "#fff",
            fontWeight: 600,
            cursor: busy ? "not-allowed" : "pointer",
          }}
        >
          {busy ? "Enviando…" : "POST apply-credit"}
        </button>
        {msg && <p style={{ marginTop: 8, fontSize: 12, color: "#94a3b8" }}>{msg}</p>}
      </form>
    </div>
  );
}
