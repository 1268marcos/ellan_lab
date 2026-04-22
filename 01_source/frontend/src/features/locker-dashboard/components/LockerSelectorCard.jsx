// 01_source/frontend/src/features/locker-dashboard/components/LockerSelectorCard.jsx

import React from "react";
import { formatLockerAddress } from "../utils/dashboardFormatters.js";
import { errorBannerStyle, fieldStyle, panelStyle } from "../utils/dashboardUiStyles.js";

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
    <section style={panelStyle}>
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
            ...fieldStyle,
            color: "#eef4ff",
            background: "rgba(20,28,44,0.95)",
          }}
        >
          {!lockers.length ? (
            <option value="" style={{ color: "#101828", background: "#ffffff" }}>
              Nenhum locker disponível
            </option>
          ) : (
            lockers.map((locker) => (
              <option
                key={locker.locker_id}
                value={locker.locker_id}
                style={{ color: "#101828", background: "#ffffff" }}
              >
                {locker.display_name}
              </option>
            ))
          )}
        </select>
      </div>

      {lockersError ? (
        <div style={errorBannerStyle}>
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