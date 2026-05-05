import React from "react";

const card = {
  borderRadius: 12,
  border: "1px solid #334155",
  background: "linear-gradient(145deg, #0f172a, #020617)",
  padding: 24,
};

export function BalanceCard({ label, balanceCents, pctChange }) {
  const brl = (balanceCents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const pct =
    pctChange == null
      ? null
      : `${pctChange >= 0 ? "↑" : "↓"} ${Math.abs(pctChange).toFixed(2)}%`;

  return (
    <div style={card}>
      <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.06em", color: "#64748b" }}>{label}</p>
      <p style={{ marginTop: 8, fontSize: 28, fontWeight: 700, color: "#fff", fontVariantNumeric: "tabular-nums" }}>
        {brl}
      </p>
      {pct != null && (
        <p style={{ marginTop: 8, fontSize: 14, fontWeight: 600, color: pctChange >= 0 ? "#34d399" : "#f87171" }}>
          {pct}
        </p>
      )}
    </div>
  );
}
