import React, { useMemo, useState } from "react";

const inputStyle = {
  borderRadius: 6,
  border: "1px solid #475569",
  background: "#020617",
  color: "#e2e8f0",
  padding: "6px 8px",
  fontSize: 12,
};

export function TransactionsTable({ rows }) {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      const t = (r.type ?? "").toLowerCase();
      const s = (r.status ?? "").toLowerCase();
      const d = r.created_at ?? r.occurred_at ?? "";
      if (type && !t.includes(type.toLowerCase())) return false;
      if (status && !s.includes(status.toLowerCase())) return false;
      if (from && d && d < from) return false;
      if (to && d && d > `${to}T23:59:59`) return false;
      return true;
    });
  }, [rows, from, to, type, status]);

  return (
    <div style={{ overflow: "hidden", borderRadius: 12, border: "1px solid #334155" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, padding: 12, borderBottom: "1px solid #1e293b", background: "#0f172a" }}>
        <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} style={inputStyle} />
        <input type="date" value={to} onChange={(e) => setTo(e.target.value)} style={inputStyle} />
        <input placeholder="tipo" value={type} onChange={(e) => setType(e.target.value)} style={inputStyle} />
        <input placeholder="status" value={status} onChange={(e) => setStatus(e.target.value)} style={inputStyle} />
      </div>
      <table style={{ width: "100%", textAlign: "left", fontSize: 14, borderCollapse: "collapse" }}>
        <thead style={{ fontSize: 11, textTransform: "uppercase", color: "#64748b" }}>
          <tr>
            <th style={{ padding: "8px 12px" }}>ID</th>
            <th style={{ padding: "8px 12px" }}>Tipo</th>
            <th style={{ padding: "8px 12px" }}>Valor</th>
            <th style={{ padding: "8px 12px" }}>Status</th>
            <th style={{ padding: "8px 12px" }}>Data</th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ padding: 24, textAlign: "center", color: "#64748b" }}>
                Sem transações
              </td>
            </tr>
          ) : (
            filtered.map((r, i) => (
              <tr key={r.transaction_id ?? r.id ?? i} style={{ borderTop: "1px solid #1e293b" }}>
                <td style={{ padding: "8px 12px", fontFamily: "monospace", fontSize: 12, color: "#94a3b8" }}>
                  {r.transaction_id ?? r.id ?? "—"}
                </td>
                <td style={{ padding: "8px 12px", color: "#e2e8f0" }}>{r.type ?? "—"}</td>
                <td style={{ padding: "8px 12px", color: "#e2e8f0", fontVariantNumeric: "tabular-nums" }}>
                  {r.amount != null ? (r.amount / 100).toFixed(2) : "—"}
                </td>
                <td style={{ padding: "8px 12px", color: "#e2e8f0" }}>{r.status ?? "—"}</td>
                <td style={{ padding: "8px 12px", fontSize: 12, color: "#94a3b8" }}>{r.created_at ?? r.occurred_at ?? "—"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
