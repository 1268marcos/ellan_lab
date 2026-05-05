
import type { CSSProperties } from "react";
import React from "react";
import { formatDateTime, formatPlainMoney } from "../utils/dashboardFormatters";
import type { OrdersRow, OrdersTableProps } from "./lockerDashboardPanelProps";

export default function OrdersTable({
  ordersData,
  currentOrder,
  onSelectOrder,
  maxHeight = 484,
}: OrdersTableProps) {
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
          {ordersData.map((item: OrdersRow) => {
            const oid = String(item.order_id ?? "");
            const selected = currentOrder?.order_id === oid;

            return (
              <tr
                key={oid}
                onClick={() => onSelectOrder?.(item)}
                style={{
                  cursor: "pointer",
                  background: selected ? "rgba(27,88,131,0.22)" : "transparent",
                }}
              >
                <td style={tdStyle}>{oid}</td>
                <td style={tdStyle}>{String(item.channel ?? "-")}</td>
                <td style={tdStyle}>{String(item.locker_id ?? item.totem_id ?? "-")}</td>
                <td style={tdStyle}>{item.slot != null ? String(item.slot) : "-"}</td>
                <td style={tdStyle}>{String(item.status ?? "-")}</td>
                <td style={tdStyle}>{formatPlainMoney(Number(item.amount_cents))}</td>
                <td style={tdStyle}>{String(item.payment_method ?? "-")}</td>
                <td style={tdStyle}>
                  {formatDateTime(String(item.created_at ?? ""), String(item.region ?? "PT"))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const thStyle: CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "1px solid rgba(255,255,255,0.12)",
  fontWeight: 800,
  whiteSpace: "nowrap",
};

const tdStyle: CSSProperties = {
  padding: "10px 12px",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  whiteSpace: "nowrap",
};
