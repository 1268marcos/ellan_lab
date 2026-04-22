// 01_source/frontend/src/pages/LockerDashboard.jsx

import React from "react";
import { useAuth } from "../context/AuthContext";
import PickupHealthPanel from "../components/PickupHealthPanel.jsx";

import {
  CurrentOrderCard,
  DashboardLegend,
  FlowProgressPanel,
  LockerDashboardHeader,
  LockerDashboardLayout,
  LockerSelectorCard,
  LockerSlotsPanel,
  OperationalOrdersPanel,
  PaymentPanel,
  PaymentPendingPanel,
  PickupOperationsPanel,
  SlotSelectionBanner,
  SyncStatusBar,
  useLockerDashboardController,
} from "../features/locker-dashboard";

export default function LockerDashboard({ region = "PT" }) {
  const { token } = useAuth();

  const BACKEND_SP = import.meta.env.VITE_BACKEND_SP_BASE_URL || "http://localhost:8201";
  const BACKEND_PT = import.meta.env.VITE_BACKEND_PT_BASE_URL || "http://localhost:8202";
  const RUNTIME_BASE = import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";
  const GATEWAY_BASE = import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";
  const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
  const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

  const controller = useLockerDashboardController({
    token,
    region,
    backendSp: BACKEND_SP,
    backendPt: BACKEND_PT,
    runtimeBase: RUNTIME_BASE,
    gatewayBase: GATEWAY_BASE,
    orderPickupBase: ORDER_PICKUP_BASE,
    internalToken: INTERNAL_TOKEN,
  });

  const handleFlowStepClick = (stepKey) => {
    const targetByStep = {
      slot: "locker-slots-panel",
      order: "payment-panel",
      payment: "payment-panel",
      pickup: "pickup-operations-panel",
    };

    const targetId = targetByStep[stepKey];
    if (!targetId) return;

    const element = document.getElementById(targetId);
    if (!element) return;
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <LockerDashboardLayout>
      <LockerDashboardHeader {...controller.headerProps} />
      <section style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Contexto Operacional</div>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
          <LockerSelectorCard {...controller.lockerSelectorProps} />
          <SyncStatusBar {...controller.syncBarProps} />
        </div>
      </section>

      <section style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Jornada Guiada</div>
        <SlotSelectionBanner {...controller.slotSelectionBannerProps} />
        <FlowProgressPanel
          {...controller.flowProgressProps}
          onStepClick={handleFlowStepClick}
        />
      </section>

      <section style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Execucao do Fluxo</div>
        <div
          style={{
            display: "grid",
            gap: 16,
            gridTemplateColumns: "minmax(320px, 1.05fr) minmax(320px, 0.95fr)",
            alignItems: "start",
          }}
        >
          <div style={{ display: "grid", gap: 16 }}>
            <div id="locker-slots-panel">
              <LockerSlotsPanel {...controller.slotsPanelProps} />
            </div>
            <div id="pickup-operations-panel">
              <PickupOperationsPanel {...controller.pickupPanelProps} />
            </div>
          </div>

          <div id="payment-panel" style={{ display: "grid", gap: 16 }}>
            <CurrentOrderCard {...controller.currentOrderCardProps} />
            <PaymentPanel {...controller.paymentPanelProps} />
            <PaymentPendingPanel {...controller.paymentPendingPanelProps} />
          </div>
        </div>
      </section>

      <section style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Pedidos Operacionais</div>
        <OperationalOrdersPanel {...controller.ordersPanelProps} />
      </section>

      <section style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Monitoramento e Referencias</div>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))" }}>
          <DashboardLegend />
          <PickupHealthPanel />
        </div>
      </section>
    </LockerDashboardLayout>
  );
}