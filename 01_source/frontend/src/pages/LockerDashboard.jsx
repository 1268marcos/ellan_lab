// 01_source/frontend/src/pages/LockerDashboard.jsx

import React from "react";
import { useAuth } from "../context/AuthContext";
import PickupHealthPanel from "../components/PickupHealthPanel.jsx";

import {
  CurrentOrderCard,
  DashboardLegend,
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
  const GATEWAY_BASE = import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";
  const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
  const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

  const controller = useLockerDashboardController({
    token,
    region,
    backendSp: BACKEND_SP,
    backendPt: BACKEND_PT,
    gatewayBase: GATEWAY_BASE,
    orderPickupBase: ORDER_PICKUP_BASE,
    internalToken: INTERNAL_TOKEN,
  });

  return (
    <LockerDashboardLayout>
      <LockerDashboardHeader {...controller.headerProps} />

      <SyncStatusBar {...controller.syncBarProps} />

      <SlotSelectionBanner {...controller.slotSelectionBannerProps} />

      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        }}
      >
        <LockerSelectorCard {...controller.lockerSelectorProps} />
        <CurrentOrderCard {...controller.currentOrderCardProps} />
      </div>

      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "minmax(320px, 1.1fr) minmax(320px, 0.9fr)",
        }}
      >
        <LockerSlotsPanel {...controller.slotsPanelProps} />

        <div style={{ display: "grid", gap: 16 }}>
          <PaymentPanel {...controller.paymentPanelProps} />
          <PaymentPendingPanel {...controller.paymentPendingPanelProps} />
        </div>
      </div>

      <PickupOperationsPanel {...controller.pickupPanelProps} />

      <OperationalOrdersPanel {...controller.ordersPanelProps} />

      <DashboardLegend />

      <PickupHealthPanel />
    </LockerDashboardLayout>
  );
}