import React from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import PickupQRCodePanel from "../../../components/PickupQRCodePanel.jsx";
import ManualPickupPanel from "../../../components/ManualPickupPanel.jsx";
import { actionButtonStyle, panelStyle } from "../utils/dashboardUiStyles";
import type { PickupOperationsPanelProps } from "./lockerDashboardPanelProps";

export default function PickupOperationsPanel({
  currentOrder,
  regenCodeLoading,
  canRegenerateManualCode,
  onRegenerateManualCode,
  pickupResp,
  onManualRedeemSuccess,
  onQrRedeemSuccess: _onQrRedeemSuccess,
}: PickupOperationsPanelProps) {
  void _onQrRedeemSuccess;
  const ord = currentOrder as (CheckoutCurrentOrder & Record<string, unknown>) | null;

  return (
    <section style={{ ...panelStyle, gap: 16 }}>
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
          style={actionButtonStyle({
            tone: "primary",
            disabled: !canRegenerateManualCode || regenCodeLoading,
          })}
        >
          {regenCodeLoading ? "Regenerando..." : "Regenerar código manual"}
        </button>
      </div>

      <PickupQRCodePanel
        region={String(ord?.region ?? "PT")}
        lockerId={String(ord?.totem_id ?? "")}
        pickupId={String(ord?.pickup_id ?? "")}
        orderId={ord?.order_id ?? ""}
      />

      <ManualPickupPanel
        region={String(ord?.region ?? "PT")}
        lockerId={String(ord?.totem_id ?? "")}
        apiBase="/api/op"
        onRedeemed={(data: unknown) => {
          void onManualRedeemSuccess(data as Record<string, unknown>);
        }}
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