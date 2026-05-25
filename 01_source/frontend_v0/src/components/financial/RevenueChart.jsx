import React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
export default function RevenueChart({ data = [], height = 280 }) {
  const safe = Array.isArray(data) ? data : [];
  return (
    <div
      style={{
        background: "rgba(15,23,42,0.55)",
        border: "1px solid rgba(148,163,184,0.25)",
        borderRadius: 12,
        padding: 14,
      }}
    >
      <h3 style={{ margin: "0 0 12px", fontSize: 14, color: "#cbd5e1" }}>Receita e lucro (mensal)</h3>
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer>
          <LineChart data={safe} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.35} />
            <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 11 }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #475569", borderRadius: 8 }} />
            <Legend />
            <Line type="monotone" dataKey="revenue_brl" name="Receita" stroke="#6366f1" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="profit_brl" name="Lucro" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
