import React from "react";
const cardInner = {
  borderRadius: 12,
  padding: 14,
  boxSizing: "border-box",
};

const STYLES = {
  HIGH_PERFORMANCE: { border: "1px solid rgba(16,185,129,0.5)", background: "rgba(6,78,59,0.35)" },
  MODERATE: { border: "1px solid rgba(56,189,248,0.5)", background: "rgba(12,74,110,0.35)" },
  LOW_PERFORMANCE: { border: "1px solid rgba(251,191,36,0.5)", background: "rgba(120,53,15,0.35)" },
  UNDERPERFORMING: { border: "1px solid rgba(249,115,22,0.5)", background: "rgba(124,45,18,0.35)" },
  INVIABLE: { border: "1px solid rgba(239,68,68,0.5)", background: "rgba(127,29,29,0.35)" },
};

function brl(value) {
  if (value == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
}

export default function ROICards({ items = [], limit = 6 }) {
  const rows = items.slice(0, limit);
  if (!rows.length) return <p style={{ color: "#94a3b8" }}>Sem dados de ROI.</p>;
  return (
    <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))" }}>
      {rows.map((row) => (
        <article
          key={row.locker_id}
          style={{ ...cardInner, ...(STYLES[row.viability_classification] || { border: "1px solid rgba(148,163,184,0.25)", background: "rgba(15,23,42,0.55)" }) }}
        >
          <p style={{ margin: 0, fontSize: 11, textTransform: "uppercase", opacity: 0.8 }}>
            {row.viability_classification || "N/A"}
          </p>
          <h4 style={{ margin: "6px 0 4px", fontSize: 15 }}>{row.display_name || row.locker_id}</h4>
          <p style={{ margin: 0, fontSize: 12, color: "#94a3b8" }}>
            {row.city || "—"} · {row.region || "—"}
          </p>
          <p style={{ margin: "8px 0 0", fontSize: 13 }}>
            ROI {row.annual_roi_pct != null ? `${row.annual_roi_pct}%` : "—"} · Payback{" "}
            {row.payback_months != null ? `${row.payback_months}m` : "—"}
          </p>
          <p style={{ margin: "4px 0 0", fontSize: 12 }}>Lucro/mês {brl(row.avg_monthly_profit_brl)}</p>
          <p style={{ margin: "4px 0 0", fontSize: 11, opacity: 0.85 }}>{row.recommendation}</p>
        </article>
      ))}
    </div>
  );
}
