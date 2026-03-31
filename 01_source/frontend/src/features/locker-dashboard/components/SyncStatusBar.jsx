// 01_source/frontend/src/features/locker-dashboard/components/SyncStatusBar.jsx

import React from "react";

export default function SyncStatusBar({
  selectedLocker,
  syncStatus,
  syncEnabled,
  onToggleSync,
}) {
  return (
    <section
      style={{
        background: syncStatus?.ok
          ? "rgba(31,122,63,0.12)"
          : "rgba(179,38,30,0.16)",
        border: syncStatus?.ok
          ? "1px solid rgba(31,122,63,0.28)"
          : "1px solid rgba(179,38,30,0.32)",
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
        <b>Locker:</b> {selectedLocker?.display_name || "-"}
        {" • "}
        <b>Sync:</b> {syncStatus?.msg || "—"}
      </div>

      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12,
          fontWeight: 700,
          cursor: "pointer",
        }}
      >
        <input
          type="checkbox"
          checked={syncEnabled}
          onChange={(e) => onToggleSync?.(e.target.checked)}
        />
        Sync automático
      </label>
    </section>
  );
}