// 01_source/frontend/src/features/locker-dashboard/components/OperationalOrdersPanel.jsx

import React from "react";
import OrdersCardList from "./OrdersCardList.jsx";
import OrdersTable from "./OrdersTable.jsx";
import {
  actionButtonStyle,
  errorBannerStyle,
  fieldStyle,
  infoBannerStyle,
  panelStyle,
} from "../utils/dashboardUiStyles.js";

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
  ordersLastUpdatedAt,
  syncEnabled,
  useTable = false,
  ordersTableHeight = 484,
}) {
  const formattedUpdatedAt = ordersLastUpdatedAt
    ? new Date(ordersLastUpdatedAt).toLocaleTimeString()
    : null;

  return (
    <section style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800 }}>Pedidos Operacionais</div>
          <div style={{ fontSize: 12, opacity: 0.72 }}>
            Lista de pedidos do locker selecionado.
          </div>
        </div>

        <button
          onClick={() => setShowOrdersPanel((prev) => !prev)}
          style={actionButtonStyle()}
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
            style={fieldStyle}
          >
            <option value="">Todos</option>
            <option value="PAYMENT_PENDING">PAYMENT_PENDING</option>
            <option value="PAID_PENDING_PICKUP">PAID_PENDING_PICKUP</option>
            <option value="PICKED_UP">PICKED_UP</option>
            <option value="DISPENSED">DISPENSED</option>
            <option value="EXPIRED">EXPIRED</option>
            <option value="EXPIRED_CREDIT_50">EXPIRED_CREDIT_50</option>
          </select>
        </label>

        <label style={{ display: "grid", gap: 4, fontSize: 12 }}>
          <span>Canal</span>
          <select
            value={ordersFilterChannel}
            onChange={(e) => setOrdersFilterChannel(e.target.value)}
            style={fieldStyle}
          >
            <option value="">Todos</option>
            <option value="ONLINE">ONLINE</option>
            <option value="KIOSK">KIOSK</option>
          </select>
        </label>

        <div style={{ display: "flex", alignItems: "end" }}>
          <button
            onClick={() => fetchOrdersOnce?.(1)}
            style={actionButtonStyle({ tone: "primary" })}
          >
            Atualizar
          </button>
        </div>
      </div>

      {syncEnabled ? (
        <div style={infoBannerStyle}>
          O sync automatico atualiza apenas as gavetas. Para refletir mudancas em pedidos, clique em{" "}
          <b>Atualizar</b>.
          {formattedUpdatedAt ? (
            <>
              {" "}
              Ultima carga dos pedidos: <b>{formattedUpdatedAt}</b>.
            </>
          ) : null}
        </div>
      ) : null}

      {ordersError ? (
        <div style={errorBannerStyle}>
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
                style={actionButtonStyle({ disabled: !ordersHasPrev })}
              >
                ◀
              </button>

              <div>
                Página <b>{ordersPage}</b> / <b>{totalOrdersPages}</b>
              </div>

              <button
                onClick={() => setOrdersPage((prev) => prev + 1)}
                disabled={!ordersHasNext}
                style={actionButtonStyle({ disabled: !ordersHasNext })}
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