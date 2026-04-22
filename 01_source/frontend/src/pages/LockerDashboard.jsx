// 01_source/frontend/src/pages/LockerDashboard.jsx

import React, { useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import PickupHealthPanel from "../components/PickupHealthPanel.jsx";
import {
  clearRuntimeGeoScopeTenantOverride,
  listConfiguredGeoTenants,
  resolveGeoScopeTenant,
  setRuntimeGeoScopeTenantOverride,
} from "../utils/lockerGeoFilter";

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
  const envTenant = String(import.meta.env.VITE_GEO_SCOPE_TENANT || "").trim().toUpperCase();
  const tenantOptions = useMemo(() => listConfiguredGeoTenants(), []);
  const [tenantInput, setTenantInput] = useState(resolveGeoScopeTenant(envTenant));

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

  async function applyTenantOverride() {
    const next = setRuntimeGeoScopeTenantOverride(tenantInput);
    setTenantInput(next);
    await controller.registry.fetchLockersOnce();
  }

  async function clearTenantOverride() {
    clearRuntimeGeoScopeTenantOverride();
    const fallback = resolveGeoScopeTenant(envTenant);
    setTenantInput(fallback);
    await controller.registry.fetchLockersOnce();
  }

  return (
    <LockerDashboardLayout>
      <LockerDashboardHeader {...controller.headerProps} />
      <section
        style={{
          display: "grid",
          gap: 8,
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.10)",
          borderRadius: 14,
          padding: 12,
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 800, opacity: 0.86 }}>Escopo Geo por Tenant (DEV)</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <label style={{ display: "grid", gap: 6, fontSize: 12, minWidth: 240 }}>
            Tenant
            <input
              list="geo-tenant-options-locker-dashboard"
              value={tenantInput}
              onChange={(e) => setTenantInput(String(e.target.value || "").toUpperCase())}
              style={{
                padding: "10px 12px",
                borderRadius: 10,
                border: "1px solid rgba(255,255,255,0.18)",
                background: "rgba(15,23,42,0.6)",
                color: "#fff",
              }}
              placeholder="TENANT_X"
            />
            <datalist id="geo-tenant-options-locker-dashboard">
              {tenantOptions.map((tenant) => (
                <option key={tenant} value={tenant} />
              ))}
            </datalist>
          </label>
          <button onClick={applyTenantOverride} style={buttonSecondaryStyle} disabled={controller.registry.lockersLoading}>
            Aplicar tenant
          </button>
          <button onClick={clearTenantOverride} style={buttonSecondaryStyle} disabled={controller.registry.lockersLoading}>
            Limpar override
          </button>
          <span style={{ fontSize: 12, opacity: 0.78 }}>
            Ativo: <b>{resolveGeoScopeTenant(envTenant) || "-"}</b>
          </span>
        </div>
      </section>
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

const buttonSecondaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "white",
  fontWeight: 600,
};