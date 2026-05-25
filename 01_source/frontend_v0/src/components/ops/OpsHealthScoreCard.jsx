import React from "react";
import { cardStyle } from "../../styles/opsShellStyles";

export default function OpsHealthScoreCard({ score, status, lastTelemetryAt }) {
  const s = score != null && !Number.isNaN(Number(score)) ? Math.max(0, Math.min(100, Number(score))) : null;
  const color =
    status === "CRITICO" || (s != null && s < 50) ? "#f87171" : status === "ATENCAO" || (s != null && s < 80) ? "#fbbf24" : "#34d399";
  return (
    <div style={{ ...cardStyle, borderColor: "rgba(51,65,85,0.8)" }}>
      <p style={{ fontSize: 11, textTransform: "uppercase", color: "#94a3b8", margin: 0 }}>Health score</p>
      <p style={{ fontSize: 32, fontWeight: 700, color, margin: "8px 0 0" }}>{s != null ? s.toFixed(0) : "—"}</p>
      <p style={{ fontSize: 13, color: "#94a3b8", margin: 0 }}>{status ?? "—"}</p>
      {lastTelemetryAt ? (
        <p style={{ fontSize: 11, color: "#64748b", marginTop: 8 }}>
          Última telemetria: {new Date(lastTelemetryAt).toLocaleString()}
        </p>
      ) : null}
    </div>
  );
}
