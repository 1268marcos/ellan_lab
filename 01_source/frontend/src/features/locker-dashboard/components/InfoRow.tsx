import React from "react";
import type { InfoRowProps } from "./lockerDashboardPanelProps";

export default function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
      <div style={{ opacity: 0.7 }}>{label}:</div>
      <div style={{ fontWeight: 600, wordBreak: "break-all" }}>{value}</div>
    </div>
  );
}