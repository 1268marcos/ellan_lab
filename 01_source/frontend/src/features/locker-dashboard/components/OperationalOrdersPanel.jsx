// 01_source/frontend/src/features/locker-dashboard/components/OperationalOrdersPanel.jsx

import React from "react";
import OrdersCardList from "./OrdersCardList.jsx";
import OrdersTable from "./OrdersTable.jsx";

export default function OperationalOrdersPanel({
  showOrdersPanel,
  setShowOrdersPanel,
  ordersLoading,
  ordersError,
  ordersData,
  currentOrder,
  onSelectOrder,
  ordersFilterStatus,
  setOrdersFilterStatus,
  ordersFilterChannel,
  setOrdersFilterChannel,
  ordersPage,
  setOrdersPage,
  ordersHasPrev,
  ordersHasNext,
  ordersTotal,
  visibleOrdersFrom,
  visibleOrdersTo,
  totalOrdersPages,
  fetchOrdersOnce,
  useTable = false,
  ordersTableHeight = 484,
}) {
  return (
    <section
      style={{
        background: "rgba(255,255,255,0.08)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: 16,
        display: "grid",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Pedidos Operacionais</div>
          <div style={{ fontSize: 12, opacity: 0.72 }}>
            Lista de pedidos do locker selecionado.
          </div>
        </div>

        <button
          onClick={() => setShowOrdersPanel((prev) => !prev)}
          style={{
            padding: "10px 12px",
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.18)",
            background: "rgba(255,255,255,0.08)",
            color: "white",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          {showOrdersPanel ? "Ocultar" : "Mostrar"}
        </button>
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <label style={{ display: "grid", gap: 4, fontSize: 12 }}>
          <span>Status</span>
          <select
            value={ordersFilterStatus}
            onChange={(e) => setOrdersFilterStatus(e.target.value)}
            style={{
              padding: 10,
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(255,255,255,0.08)",
              color: "white",
            }}
          >
            <option value="">Todos</option>
            <option value="PAYMENT_PENDING">PAYMENT_PENDING</option>
            <option value="PAID_PENDING_PICKUP">PAID_PENDING_PICKUP</option>
            <option value="PICKED_UP">PICKED_UP</option>
            <option value="EXPIRED">EXPIRED</option>
            <option value="EXPIRED_CREDIT_50">EXPIRED_CREDIT_50</option>
            <option value="DISPENSED">DISPENSED</option>
          </select>
        </label>

        <label style={{ display: "grid", gap: 4, fontSize: 12 }}>
          <span>Canal</span>
          <select
            value={ordersFilterChannel}
            onChange={(e) => setOrdersFilterChannel(e.target.value)}
            style={{
              padding: 10,
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(255,255,255,0.08)",
              color: "white",
            }}
          >
            <option value="">Todos</option>
            <option value="ONLINE">ONLINE</option>
            <option value="KIOSK">KIOSK</option>
          </select>
        </label>

        <div style={{ display: "flex", alignItems: "end" }}>
          <button
            onClick={() => fetchOrdersOnce?.(1)}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.18)",
              background: "rgba(27,88,131,0.22)",
              color: "white",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            Atualizar
          </button>
        </div>
      </div>

      {ordersError ? (
        <div
          style={{
            fontSize: 12,
            color: "#ffd9d6",
            background: "rgba(179,38,30,0.18)",
            border: "1px solid rgba(179,38,30,0.35)",
            borderRadius: 10,
            padding: 10,
            whiteSpace: "pre-wrap",
          }}
        >
          {ordersError}
        </div>
      ) : null}

      {showOrdersPanel ? (
        <>
          {useTable ? (
            <OrdersTable
              ordersData={ordersData}
              currentOrder={currentOrder}
              onSelectOrder={onSelectOrder}
              maxHeight={ordersTableHeight}
            />
          ) : (
            <OrdersCardList
              ordersData={ordersData}
              ordersLoading={ordersLoading}
              currentOrder={currentOrder}
              onSelectOrder={onSelectOrder}
            />
          )}

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              alignItems: "center",
              flexWrap: "wrap",
              fontSize: 12,
              opacity: 0.82,
            }}
          >
            <div>
              Exibindo <b>{visibleOrdersFrom}</b>–<b>{visibleOrdersTo}</b> de <b>{ordersTotal}</b>
            </div>

            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button
                onClick={() => setOrdersPage((prev) => Math.max(1, prev - 1))}
                disabled={!ordersHasPrev}
                style={{
                  padding: "8px 10px",
                  borderRadius: 8,
                  border: "1px solid rgba(255,255,255,0.18)",
                  background: ordersHasPrev ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)",
                  color: "white",
                  cursor: ordersHasPrev ? "pointer" : "not-allowed",
                }}
              >
                ◀
              </button>

              <div>
                Página <b>{ordersPage}</b> / <b>{totalOrdersPages}</b>
              </div>

              <button
                onClick={() => setOrdersPage((prev) => prev + 1)}
                disabled={!ordersHasNext}
                style={{
                  padding: "8px 10px",
                  borderRadius: 8,
                  border: "1px solid rgba(255,255,255,0.18)",
                  background: ordersHasNext ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)",
                  color: "white",
                  cursor: ordersHasNext ? "pointer" : "not-allowed",
                }}
              >
                ▶
              </button>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}