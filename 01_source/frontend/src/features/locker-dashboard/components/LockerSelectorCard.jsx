// 01_source/frontend/src/features/locker-dashboard/components/LockerSelectorCard.jsx

import React from "react";
import { formatLockerAddress } from "../utils/dashboardFormatters.js";

export default function LockerSelectorCard({
  region,
  lockers,
  lockersLoading,
  lockersError,
  lockersSource,
  selectedLockerId,
  setSelectedLockerId,
  selectedLocker,
}) {
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
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Lockers</div>
          <div style={{ fontSize: 12, opacity: 0.72 }}>
            Região: <b>{region}</b> • Fonte: <b>{lockersSource}</b>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <label style={{ fontSize: 13, fontWeight: 700 }}>Locker selecionado</label>
        <select
          value={selectedLockerId}
          onChange={(e) => setSelectedLockerId(e.target.value)}
          disabled={lockersLoading || !lockers.length}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.08)",
            color: "white",
          }}
        >
          {!lockers.length ? (
            <option value="">Nenhum locker disponível</option>
          ) : (
            lockers.map((locker) => (
              <option key={locker.locker_id} value={locker.locker_id}>
                {locker.display_name}
              </option>
            ))
          )}
        </select>
      </div>

      {lockersError ? (
        <div
          style={{
            fontSize: 12,
            color: "#ffd9d6",
            background: "rgba(179,38,30,0.18)",
            border: "1px solid rgba(179,38,30,0.35)",
            borderRadius: 10,
            padding: 10,
            whiteSpace: "pre-wrap",
          }}
        >
          {lockersError}
        </div>
      ) : null}

      {selectedLocker ? (
        <div
          style={{
            display: "grid",
            gap: 8,
            fontSize: 13,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            padding: 12,
          }}
        >
          <div>
            <b>{selectedLocker.display_name}</b>
          </div>
          <div>
            <b>Locker ID:</b> {selectedLocker.locker_id}
          </div>
          <div>
            <b>Endereço:</b> {formatLockerAddress(selectedLocker)}
          </div>
          <div>
            <b>Slots:</b> {selectedLocker.slots}
          </div>
          <div>
            <b>Canais:</b> {(selectedLocker.channels || []).join(", ") || "-"}
          </div>
          <div>
            <b>Métodos de pagamento:</b>{" "}
            {(selectedLocker.payment_methods || []).join(", ") || "-"}
          </div>
        </div>
      ) : null}
    </section>
  );
}