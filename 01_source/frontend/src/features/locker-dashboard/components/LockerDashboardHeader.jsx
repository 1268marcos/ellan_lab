// 01_source/frontend/src/features/locker-dashboard/components/LockerDashboardHeader.jsx

import React from "react";

export default function LockerDashboardHeader({
  region,
  selectedLocker,
  lockersSource,
  syncEnabled,
  setSyncEnabled,
  syncStatus,
}) {
  return (
    <section
      style={{
        background: "linear-gradient(135deg, rgba(95,61,196,0.22), rgba(27,88,131,0.18))",
        border: "1px solid rgba(255,255,255,0.14)",
        borderRadius: 18,
        padding: 18,
        display: "grid",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 24, fontWeight: 900 }}>Locker Dashboard</div>
          <div style={{ fontSize: 13, opacity: 0.78 }}>
            Painel operacional e administrativo por locker.
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span
            style={{
              padding: "6px 10px",
              borderRadius: 999,
              background: "rgba(255,255,255,0.10)",
              border: "1px solid rgba(255,255,255,0.16)",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            Região: {region}
          </span>

          <span
            style={{
              padding: "6px 10px",
              borderRadius: 999,
              background: "rgba(255,255,255,0.10)",
              border: "1px solid rgba(255,255,255,0.16)",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            Fonte lockers: {lockersSource}
          </span>

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
              onChange={(e) => setSyncEnabled(e.target.checked)}
            />
            Sync automático
          </label>
        </div>
      </div>

      <div
        style={{
          fontSize: 12,
          borderRadius: 10,
          padding: 10,
          background: syncStatus?.ok ? "rgba(31,122,63,0.16)" : "rgba(179,38,30,0.18)",
          border: syncStatus?.ok
            ? "1px solid rgba(31,122,63,0.32)"
            : "1px solid rgba(179,38,30,0.35)",
        }}
      >
        <b>Locker atual:</b> {selectedLocker?.display_name || "-"}
        {" • "}
        <b>Sync:</b> {syncStatus?.msg || "—"}
      </div>
    </section>
  );
}