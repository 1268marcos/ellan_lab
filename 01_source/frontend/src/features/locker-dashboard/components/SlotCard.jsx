// 01_source/frontend/src/features/locker-dashboard/components/SlotCard.jsx

import React from "react";
import { STATE_STYLE } from "../utils/dashboardConstants.js";
import { formatPlainMoney } from "../utils/dashboardFormatters.js";

export default function SlotCard({
  slot,
  state,
  name,
  skuId,
  priceCents,
  isActive,
  hasCatalogData = false,
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
        minHeight: 92,
        borderRadius: 10,
        border: selected ? "2px solid #fff" : "1px solid rgba(255,255,255,0.2)",
        background: meta.bg,
        color: meta.fg,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.74 : 1,
        display: "grid",
        gap: 6,
        padding: "8px 9px",
        boxShadow: selected ? "0 0 0 2px rgba(0,0,0,0.25)" : "none",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 6, alignItems: "center" }}>
        <div style={{ fontSize: 14, fontWeight: 800 }}>Gaveta {slot}</div>
        <div style={{ fontSize: 10, opacity: 0.95 }}>{meta.label}</div>
      </div>

      <div style={{ fontSize: 11, fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {name || "Produto sem nome"}
      </div>

      <div style={{ fontSize: 10, opacity: 0.88 }}>
        SKU: {skuId || "-"} • Preço: {priceCents == null ? "-" : formatPlainMoney(priceCents)}
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 10, opacity: 0.88 }}>
          Catálogo: {isActive ? "ATIVO" : "INATIVO"}
        </span>
        <span
          style={{
            fontSize: 10,
            fontWeight: 700,
            borderRadius: 999,
            padding: "2px 6px",
            background: hasCatalogData ? "rgba(4,120,87,0.26)" : "rgba(185,28,28,0.26)",
            border: hasCatalogData
              ? "1px solid rgba(16,185,129,0.62)"
              : "1px solid rgba(248,113,113,0.62)",
          }}
        >
          {hasCatalogData ? "CATALOGO REAL" : "FALLBACK"}
        </span>
      </div>
    </button>
  );
}