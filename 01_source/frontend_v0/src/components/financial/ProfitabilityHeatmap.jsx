import React, { useMemo } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function heatColor(margin) {
  if (margin >= 35) return "#10b981";
  if (margin >= 20) return "#34d399";
  if (margin >= 10) return "#fbbf24";
  if (margin >= 0) return "#f97316";
  return "#ef4444";
}

export default function ProfitabilityHeatmap({ rows = [] }) {
  const data = useMemo(() => {
    const byLocker = new Map();
    for (const r of rows) {
      const margin = Number(r.margin_pct) || 0;
      const prev = byLocker.get(r.locker_id);
      if (!prev || margin < prev.margin) {
        byLocker.set(r.locker_id, {
          locker_id: r.locker_id,
          margin,
          label: r.locker_id.length > 12 ? `${r.locker_id.slice(0, 10)}…` : r.locker_id,
        });
      }
    }
    return [...byLocker.values()].sort((a, b) => b.margin - a.margin).slice(0, 24);
  }, [rows]);

  if (!data.length) return <p style={{ color: "#94a3b8" }}>Sem dados para heatmap.</p>;

  return (
    <div
      style={{
        marginTop: 14,
        background: "rgba(15,23,42,0.55)",
        border: "1px solid rgba(148,163,184,0.25)",
        borderRadius: 12,
        padding: 14,
      }}
    >
      <h3 style={{ margin: "0 0 12px", fontSize: 14, color: "#cbd5e1" }}>Margem por locker</h3>
      <div style={{ width: "100%", height: Math.max(220, data.length * 22) }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
            <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="label" width={100} stroke="#94a3b8" tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(v) => [`${Number(v).toFixed(1)}%`, "Margem"]}
              contentStyle={{ background: "#0f172a", border: "1px solid #475569", borderRadius: 8 }}
            />
            <Bar dataKey="margin" radius={[0, 4, 4, 0]}>
              {data.map((entry) => (
                <Cell key={entry.locker_id} fill={heatColor(entry.margin)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
