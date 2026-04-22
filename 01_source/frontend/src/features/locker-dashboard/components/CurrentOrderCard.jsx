// 01_source/frontend/src/features/locker-dashboard/components/CurrentOrderCard.jsx

import React from "react";
import {
  genericBadgeStyle,
} from "../utils/dashboardOrderUtils.js";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters.js";
import { errorBannerStyle, panelStyle } from "../utils/dashboardUiStyles.js";

export default function CurrentOrderCard({
  currentOrder,
  currentOrderMeta,
  currentPickupMeta,
  currentAllocationMeta,
  currentOrderWarning,
  orderError,
}) {
  return (
    <section style={panelStyle}>
      <div>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Pedido Atual</div>
        <div style={{ fontSize: 12, opacity: 0.72 }}>
          Estado operacional do pedido selecionado.
        </div>
      </div>

      {orderError ? (
        <div style={errorBannerStyle}>
          {orderError}
        </div>
      ) : null}

      {!currentOrder ? (
        <div
          style={{
            fontSize: 13,
            opacity: 0.8,
            borderRadius: 12,
            padding: 12,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          Nenhum pedido selecionado.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gap: 10,
            background: currentOrderMeta?.bg || "rgba(255,255,255,0.04)",
            border: `1px solid ${currentOrderMeta?.border || "rgba(255,255,255,0.12)"}`,
            borderRadius: 12,
            padding: 12,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 800 }}>{currentOrder.order_id}</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={genericBadgeStyle(currentOrderMeta)}>
                {currentOrderMeta?.label || currentOrder.status}
              </span>

              {currentPickupMeta ? (
                <span style={genericBadgeStyle(currentPickupMeta)}>
                  {currentPickupMeta.label}
                </span>
              ) : null}

              {currentAllocationMeta ? (
                <span style={genericBadgeStyle(currentAllocationMeta)}>
                  {currentAllocationMeta.label}
                </span>
              ) : null}
            </div>
          </div>

          <div style={{ fontSize: 13 }}>
            <b>Locker:</b> {currentOrder.totem_id || "-"} • <b>Canal:</b>{" "}
            {currentOrder.channel || "-"}
          </div>

          <div style={{ fontSize: 13 }}>
            <b>Valor:</b> {formatPlainMoney(currentOrder.amount_cents)} • <b>Método:</b>{" "}
            {currentOrder.payment_method || "-"}
          </div>

          <div style={{ fontSize: 13 }}>
            <b>Pickup:</b> {currentOrder.pickup_id || "-"} • <b>Código manual:</b>{" "}
            {currentOrder.manual_code || "-"}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Criado: {formatDateTime(currentOrder.created_at, currentOrder.region || "PT")}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Pago: {formatDateTime(currentOrder.paid_at, currentOrder.region || "PT")} •
            Retirado: {formatDateTime(currentOrder.picked_up_at, currentOrder.region || "PT")}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Expira em:{" "}
            {formatDateTime(
              currentOrder.expires_at || currentOrder.pickup_deadline_at,
              currentOrder.region || "PT"
            )}
          </div>

          {currentOrderWarning ? (
            <div
              style={{
                fontSize: 12,
                color: "#fff2f0",
                borderRadius: 10,
                padding: 10,
                background: "rgba(179,38,30,0.20)",
                border: "1px solid rgba(179,38,30,0.35)",
              }}
            >
              {currentOrderWarning}
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}