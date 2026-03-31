// 01_source/frontend/src/features/locker-dashboard/components/PickupOperationsPanel.jsx

import React from "react";
import PickupQRCodePanel from "../../../components/PickupQRCodePanel.jsx";
import ManualPickupPanel from "../../../components/ManualPickupPanel.jsx";

export default function PickupOperationsPanel({
  currentOrder,
  regenCodeLoading,
  canRegenerateManualCode,
  onRegenerateManualCode,
  pickupResp,
  onManualRedeemSuccess,
  onQrRedeemSuccess,
  token,
}) {
  return (
    <section
      style={{
        background: "rgba(255,255,255,0.08)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 16,
      }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Operações de Pickup</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          QR, código manual e ações de retirada.
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          onClick={onRegenerateManualCode}
          disabled={!canRegenerateManualCode || regenCodeLoading}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.18)",
            background: canRegenerateManualCode
              ? "rgba(27,88,131,0.22)"
              : "rgba(255,255,255,0.06)",
            color: "white",
            cursor: canRegenerateManualCode ? "pointer" : "not-allowed",
            fontWeight: 700,
          }}
        >
          {regenCodeLoading ? "Regenerando..." : "Regenerar código manual"}
        </button>
      </div>

      <PickupQRCodePanel
        orderId={currentOrder?.order_id || ""}
        token={token}
        onRedeemSuccess={onQrRedeemSuccess}
      />

      <ManualPickupPanel
        orderId={currentOrder?.order_id || ""}
        initialCode={currentOrder?.manual_code || ""}
        token={token}
        onRedeemSuccess={onManualRedeemSuccess}
      />

      {pickupResp ? (
        <pre
          style={{
            margin: 0,
            fontSize: 12,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            borderRadius: 10,
            padding: 12,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          {pickupResp}
        </pre>
      ) : null}
    </section>
  );
}