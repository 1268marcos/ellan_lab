// 01_source/frontend/src/features/locker-dashboard/components/SlotSelectionBanner.jsx

import React from "react";

export default function SlotSelectionBanner({
  selectedLocker,
  selectedSlot,
  hasActiveSlotSelection,
  slotSelectionRemainingSec,
  onClear,
}) {
  if (!hasActiveSlotSelection || !selectedSlot) return null;

  return (
    <section
      style={{
        background: "rgba(27,88,131,0.18)",
        border: "1px solid rgba(27,88,131,0.34)",
        borderRadius: 14,
        padding: 12,
        display: "flex",
        justifyContent: "space-between",
        gap: 12,
        alignItems: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{ fontSize: 12 }}>
        Gaveta <b>{selectedSlot}</b> selecionada no locker{" "}
        <b>{selectedLocker?.display_name || "-"}</b> • expira em{" "}
        <b>{slotSelectionRemainingSec}s</b>
      </div>

      <button
        onClick={onClear}
        style={{
          padding: "8px 10px",
          borderRadius: 10,
          border: "1px solid rgba(255,255,255,0.18)",
          background: "rgba(255,255,255,0.08)",
          color: "white",
          cursor: "pointer",
          fontWeight: 700,
        }}
      >
        Limpar seleção
      </button>
    </section>
  );
}