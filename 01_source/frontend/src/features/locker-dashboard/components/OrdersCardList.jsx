// 01_source/frontend/src/features/locker-dashboard/components/OrdersCardList.jsx

import React from "react";
import {
  CHANNEL_META,
  PICKUP_STATUS_META,
  ALLOCATION_STATUS_META,
  genericBadgeStyle,
  getOperationalRowHighlight,
  statusBadgeStyle,
} from "../utils/dashboardOrderUtils.js";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters.js";

export default function OrdersCardList({
  ordersData,
  ordersLoading,
  currentOrder,
  onSelectOrder,
}) {
  if (ordersLoading) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Carregando pedidos...</div>;
  }

  if (!ordersData.length) {
    return <div style={{ fontSize: 12, opacity: 0.75 }}>Nenhum pedido encontrado.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {ordersData.map((item) => {
        const highlight = getOperationalRowHighlight(item);

        return (
          <button
            key={item.order_id}
            onClick={() => onSelectOrder(item)}
            style={{
              textAlign: "left",
              padding: 10,
              borderRadius: 12,
              border:
                currentOrder?.order_id === item.order_id
                  ? "1px solid rgba(255,255,255,0.38)"
                  : "1px solid rgba(255,255,255,0.12)",
              borderLeft: highlight.borderLeft,
              background:
                currentOrder?.order_id === item.order_id
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
              <div style={{ fontWeight: 700 }}>{item.order_id}</div>

              <div
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                {item.channel ? (
                  <span style={genericBadgeStyle(CHANNEL_META[item.channel])}>
                    {CHANNEL_META[item.channel]?.label || item.channel}
                  </span>
                ) : null}

                <span style={statusBadgeStyle(item.status)}>{item.status}</span>
              </div>
            </div>

            <div style={{ fontSize: 12, opacity: 0.85 }}>
              Locker: <b>{item.locker_id || item.totem_id || "-"}</b> • Slot:{" "}
              <b>{item.slot ?? "-"}</b> • Valor: <b>{formatPlainMoney(item.amount_cents)}</b>
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
                Método: <b>{item.payment_method || "-"}</b> • Pickup: <b>{item.pickup_id || "-"}</b>
              </div>

              {item.pickup_status ? (
                <span style={genericBadgeStyle(PICKUP_STATUS_META[item.pickup_status])}>
                  {PICKUP_STATUS_META[item.pickup_status]?.label || item.pickup_status}
                </span>
              ) : null}

              {item.allocation_state ? (
                <span style={genericBadgeStyle(ALLOCATION_STATUS_META[item.allocation_state])}>
                  {ALLOCATION_STATUS_META[item.allocation_state]?.label || item.allocation_state}
                </span>
              ) : null}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Criado: {formatDateTime(item.created_at, item.region)}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Pago: {formatDateTime(item.paid_at, item.region)} • Retirado:{" "}
              {formatDateTime(item.picked_up_at, item.region)}
            </div>

            <div style={{ fontSize: 11, opacity: 0.62 }}>
              Expira em: {formatDateTime(item.expires_at || item.pickup_deadline_at, item.region)}
            </div>
          </button>
        );
      })}
    </div>
  );
}