import React from "react";
import {
  genericBadgeStyle,
} from "../utils/dashboardOrderUtils";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters";
import { errorBannerStyle, panelStyle } from "../utils/dashboardUiStyles";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import type { CurrentOrderCardProps } from "./lockerDashboardPanelProps";

export default function CurrentOrderCard({
  currentOrder,
  currentOrderMeta,
  currentPickupMeta,
  currentAllocationMeta,
  currentOrderWarning,
  orderError,
}: CurrentOrderCardProps) {
  const orderRow =
    currentOrder == null
      ? null
      : (currentOrder as CheckoutCurrentOrder & Record<string, unknown>);

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

      {!orderRow ? (
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
            <div style={{ fontWeight: 800 }}>{orderRow.order_id}</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={genericBadgeStyle(currentOrderMeta)}>
                {currentOrderMeta?.label || orderRow.status}
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
            <b>Locker:</b> {String(orderRow.totem_id ?? "-")} • <b>Canal:</b>{" "}
            {orderRow.channel || "-"}
          </div>

          <div style={{ fontSize: 13 }}>
            <b>Valor:</b> {formatPlainMoney(orderRow.amount_cents as number)} • <b>Método:</b>{" "}
            {String(orderRow.payment_method ?? "-")}
          </div>

          <div style={{ fontSize: 13 }}>
            <b>Pickup:</b> {orderRow.pickup_id || "-"} • <b>Código manual:</b>{" "}
            {orderRow.manual_code || "-"}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Criado:{" "}
            {formatDateTime(String(orderRow.created_at ?? ""), String(orderRow.region || "PT"))}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Pago: {formatDateTime(String(orderRow.paid_at ?? ""), String(orderRow.region || "PT"))}{" "}
            • Retirado:{" "}
            {formatDateTime(String(orderRow.picked_up_at ?? ""), String(orderRow.region || "PT"))}
          </div>

          <div style={{ fontSize: 12, opacity: 0.8 }}>
            Expira em:{" "}
            {formatDateTime(
              String(orderRow.expires_at || orderRow.pickup_deadline_at || ""),
              String(orderRow.region || "PT")
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