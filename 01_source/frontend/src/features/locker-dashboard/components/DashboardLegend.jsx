// 01_source/frontend/src/features/locker-dashboard/components/DashboardLegend.jsx

import React from "react";
import {
  OPERATIONAL_HIGHLIGHT_LEGEND,
  STATE_STYLE,
} from "../utils/dashboardConstants.js";

export default function DashboardLegend() {
  return (
    <section
      style={{
        background: "rgba(255,255,255,0.08)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 12,
      }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Legenda Operacional</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          Estados visuais das gavetas e destaques dos pedidos.
        </div>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        <div style={{ fontSize: 13, fontWeight: 700 }}>Estados das gavetas</div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {Object.entries(STATE_STYLE).map(([key, meta]) => (
            <div
              key={key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 10px",
                borderRadius: 10,
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)",
                fontSize: 12,
              }}
            >
              <span
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: 4,
                  display: "inline-block",
                  background: meta.bg,
                  border: "1px solid rgba(255,255,255,0.18)",
                }}
              />
              <span>{meta.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        <div style={{ fontSize: 13, fontWeight: 700 }}>Destaques operacionais</div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {OPERATIONAL_HIGHLIGHT_LEGEND.map((item) => (
            <div
              key={item.key}
              style={{
                padding: "8px 10px",
                borderRadius: 10,
                background: item.bg,
                border: `1px solid ${item.border}`,
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              {item.label}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}