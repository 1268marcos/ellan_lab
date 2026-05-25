import React from "react";
import { cardStyle } from "../../styles/opsShellStyles";

export default function OpsOccupancyGauge({ pct, level, label = "Ocupação" }) {
  const value = pct != null && !Number.isNaN(Number(pct)) ? Math.max(0, Math.min(100, Number(pct))) : null;
  const color =
    level === "HIGH" || (value != null && value >= 80)
      ? "#f87171"
      : level === "MEDIUM" || (value != null && value >= 50)
        ? "#fbbf24"
        : "#34d399";
  return (
    <div style={{ ...cardStyle, borderColor: "rgba(51,65,85,0.8)" }}>
      <p style={{ fontSize: 11, textTransform: "uppercase", color: "#94a3b8", margin: 0 }}>{label}</p>
      <p style={{ fontSize: 32, fontWeight: 700, color, margin: "8px 0 0" }}>
        {value != null ? `${value.toFixed(1)}%` : "—"}
      </p>
      <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>{level ?? "N/D"}</p>
    </div>
  );
}
