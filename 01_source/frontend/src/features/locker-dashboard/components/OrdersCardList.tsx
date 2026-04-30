import React from "react";
import {
  CHANNEL_META,
  PICKUP_STATUS_META,
  ALLOCATION_STATUS_META,
  genericBadgeStyle,
  getOperationalRowHighlight,
  statusBadgeStyle,
} from "../utils/dashboardOrderUtils";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters";
import type { OrdersCardListProps, OrdersRow } from "./lockerDashboardPanelProps";

export default function OrdersCardList({
  ordersData,
  ordersLoading,
  currentOrder,
  onSelectOrder,
}: OrdersCardListProps) {
  if (ordersLoading) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Carregando pedidos...</div>;
  }

  if (!ordersData.length) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Nenhum pedido encontrado.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {ordersData.map((item: OrdersRow) => {
        const highlight = getOperationalRowHighlight(item);
        const orderId = String(item.order_id ?? "");
        const channelKey = String(item.channel ?? "");
        const pickupKey = String(item.pickup_status ?? "");
        const allocKey = String(item.allocation_state ?? "");
        const statusStr = String(item.status ?? "");

        return (
          <button
            key={orderId}
            onClick={() => onSelectOrder(item)}
            style={{
              textAlign: "left",
              padding: 10,
              borderRadius: 12,
              border:
                currentOrder?.order_id === orderId
                  ? "1px solid rgba(255,255,255,0.38)"
                  : "1px solid rgba(255,255,255,0.12)",
              borderLeft: highlight.borderLeft,
              background:
                currentOrder?.order_id === orderId
                  ? "rgba(27,88,131,0.28)"
                  : item.status === "EXPIRED" || item.status === "EXPIRED_CREDIT_50"
                    ? "rgba(179,38,30,0.10)"
                    : highlight.bg !== "transparent"
                      ? highlight.bg
                      : "rgba(255,255,255,0.03)",
              color: "white",
              cursor: "pointer",
              display: "grid",
              gap: 6,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              <div style={{ fontWeight: 700 }}>{orderId}</div>

              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                {channelKey ? (
                  <span
                    style={genericBadgeStyle(
                      CHANNEL_META[channelKey as keyof typeof CHANNEL_META]
                    )}
                  >
                    {CHANNEL_META[channelKey as keyof typeof CHANNEL_META]?.label || channelKey}
                  </span>
                ) : null}

                <span style={statusBadgeStyle(statusStr)}>{statusStr}</span>
              </div>
            </div>

            <div style={{ fontSize: 12, opacity: 0.85 }}>
              Locker: <b>{String(item.locker_id ?? item.totem_id ?? "-")}</b> • Slot:{" "}
              <b>{item.slot != null ? String(item.slot) : "-"}</b> • Valor:{" "}
              <b>{formatPlainMoney(Number(item.amount_cents))}</b>
            </div>

            <div
              style={{
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <div style={{ fontSize: 12, opacity: 0.72 }}>
                Método: <b>{String(item.payment_method ?? "-")}</b> • Pickup:{" "}
                <b>{String(item.pickup_id ?? "-")}</b>
              </div>

              {pickupKey ? (
                <span
                  style={genericBadgeStyle(
                    PICKUP_STATUS_META[pickupKey as keyof typeof PICKUP_STATUS_META]
                  )}
                >
                  {PICKUP_STATUS_META[pickupKey as keyof typeof PICKUP_STATUS_META]?.label ||
                    pickupKey}
                </span>
              ) : null}

              {allocKey ? (
                <span
                  style={genericBadgeStyle(
                    ALLOCATION_STATUS_META[allocKey as keyof typeof ALLOCATION_STATUS_META]
                  )}
                >
                  {ALLOCATION_STATUS_META[allocKey as keyof typeof ALLOCATION_STATUS_META]?.label ||
                    allocKey}
                </span>
              ) : null}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Criado: {formatDateTime(String(item.created_at ?? ""), String(item.region ?? "PT"))}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Pago: {formatDateTime(String(item.paid_at ?? ""), String(item.region ?? "PT"))} •
              Retirado:{" "}
              {formatDateTime(String(item.picked_up_at ?? ""), String(item.region ?? "PT"))}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Expira em:{" "}
              {formatDateTime(
                String(item.expires_at || item.pickup_deadline_at || ""),
                String(item.region ?? "PT")
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}