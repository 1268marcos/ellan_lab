// 01_source/frontend/src/features/locker-dashboard/components/OrdersTable.jsx

import React from "react";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters.js";

export default function OrdersTable({
  ordersData,
  currentOrder,
  onSelectOrder,
  maxHeight = 484,
}) {
  if (!ordersData?.length) {
    return (
      <div style={{ fontSize: 12, opacity: 0.75 }}>
        Nenhum pedido encontrado.
      </div>
    );
  }

  return (
    <div
      style={{
        overflow: "auto",
        maxHeight,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.12)",
      }}
    >
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 12,
          background: "rgba(255,255,255,0.03)",
        }}
      >
        <thead>
          <tr style={{ background: "rgba(255,255,255,0.08)" }}>
            <th style={thStyle}>Pedido</th>
            <th style={thStyle}>Canal</th>
            <th style={thStyle}>Locker</th>
            <th style={thStyle}>Slot</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Valor</th>
            <th style={thStyle}>Método</th>
            <th style={thStyle}>Criado</th>
          </tr>
        </thead>
        <tbody>
          {ordersData.map((item) => {
            const selected = currentOrder?.order_id === item.order_id;

            return (
              <tr
                key={item.order_id}
                onClick={() => onSelectOrder?.(item)}
                style={{
                  cursor: "pointer",
                  background: selected ? "rgba(27,88,131,0.22)" : "transparent",
                }}
              >
                <td style={tdStyle}>{item.order_id}</td>
                <td style={tdStyle}>{item.channel || "-"}</td>
                <td style={tdStyle}>{item.locker_id || item.totem_id || "-"}</td>
                <td style={tdStyle}>{item.slot ?? "-"}</td>
                <td style={tdStyle}>{item.status || "-"}</td>
                <td style={tdStyle}>{formatPlainMoney(item.amount_cents)}</td>
                <td style={tdStyle}>{item.payment_method || "-"}</td>
                <td style={tdStyle}>{formatDateTime(item.created_at, item.region)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const thStyle = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  fontWeight: 800,
  whiteSpace: "nowrap",
};

const tdStyle = {
  padding: "10px 12px",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  whiteSpace: "nowrap",
};