// 01_source/frontend/src/features/locker-dashboard/components/SlotCard.jsx

import React from "react";
import { STATE_STYLE } from "../utils/dashboardConstants.js";

export default function SlotCard({
  slot,
  state,
  selected,
  disabled,
  onClick,
}) {
  const meta = STATE_STYLE[state] || { bg: "#333", fg: "white", label: state };

  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={`Gaveta ${slot} • ${meta.label}`}
      style={{
        width: "100%",
        aspectRatio: "3 / 2",
        borderRadius: 10,
        border: selected ? "3px solid #fff" : "1px solid rgba(255,255,255,0.2)",
        background: meta.bg,
        color: meta.fg,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.72 : 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: 10,
        boxShadow: selected ? "0 0 0 3px rgba(0,0,0,0.25)" : "none",
      }}
    >
      <div style={{ fontSize: 16, fontWeight: 800 }}>{slot}</div>
      <div style={{ fontSize: 11, opacity: 0.9, textAlign: "right" }}>
        {meta.label}
      </div>
    </button>
  );
}