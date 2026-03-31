// 01_source/frontend/src/features/locker-dashboard/components/PaymentPendingPanel.jsx

import React from "react";
import { formatEpochDateTime } from "../utils/dashboardFormatters.js";

export default function PaymentPendingPanel({
  pendingPaymentContext,
  region = "PT",
  onConfirm,
  loading = false,
}) {
  if (!pendingPaymentContext) return null;

  return (
    <section
      style={{
        background: "rgba(199,146,0,0.16)",
        border: "1px solid rgba(199,146,0,0.35)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 12,
      }}
    >
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Pagamento pendente</div>
        <div style={{ fontSize: 12, opacity: 0.82 }}>
          Aguardando ação do cliente ou confirmação operacional.
        </div>
      </div>

      <div style={{ display: "grid", gap: 8, fontSize: 13 }}>
        <div>
          <b>Pedido:</b> {pendingPaymentContext.order_id || "-"}
        </div>
        <div>
          <b>Locker:</b> {pendingPaymentContext.locker_id || "-"}
        </div>
        <div>
          <b>Método:</b> {pendingPaymentContext.payment_method || "-"}
        </div>
        <div>
          <b>Instruction type:</b> {pendingPaymentContext.instructionType || "-"}
        </div>
        <div>
          <b>Instruction:</b> {pendingPaymentContext.instruction || "-"}
        </div>
        <div>
          <b>Transaction ID:</b> {pendingPaymentContext.transaction_id || "-"}
        </div>
        <div>
          <b>Expira em:</b>{" "}
          {pendingPaymentContext.expiresAtEpoch
            ? formatEpochDateTime(pendingPaymentContext.expiresAtEpoch, region)
            : "-"}
        </div>

        {pendingPaymentContext.copyPasteCode ? (
          <div
            style={{
              borderRadius: 10,
              padding: 10,
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.12)",
              wordBreak: "break-all",
            }}
          >
            <b>Código copia e cola:</b>
            <div style={{ marginTop: 6, fontFamily: "monospace", fontSize: 12 }}>
              {pendingPaymentContext.copyPasteCode}
            </div>
          </div>
        ) : null}
      </div>

      <div>
        <button
          onClick={onConfirm}
          disabled={loading}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(27,88,131,0.22)",
            color: "white",
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: 700,
          }}
        >
          {loading ? "Confirmando..." : "Confirmar pagamento pendente"}
        </button>
      </div>
    </section>
  );
}