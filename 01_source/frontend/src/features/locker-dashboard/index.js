// Barrel ESM: extensões explícitas (.ts hooks, .tsx componentes) — evita falha de resolução com lazy() / Vite.

export { default as useLockerRegistry } from "./hooks/useLockerRegistry.ts";
export { default as useLockerSlotsSync } from "./hooks/useLockerSlotsSync.ts";
export { default as useOperationalOrders } from "./hooks/useOperationalOrders.ts";
export { default as useSlotSelection } from "./hooks/useSlotSelection.ts";
export { default as useCurrentOrder } from "./hooks/useCurrentOrder.ts";
export { default as useOperationalPayment } from "./hooks/useOperationalPayment.ts";
export { default as useOperationalPickup } from "./hooks/useOperationalPickup.ts";
export { default as useLockerDashboardController } from "./hooks/useLockerDashboardController.ts";

export { default as SlotCard } from "./components/SlotCard.tsx";
export { default as OrdersCardList } from "./components/OrdersCardList.tsx";
export { default as OrdersTable } from "./components/OrdersTable.tsx";
export { default as InfoRow } from "./components/InfoRow.tsx";
export { default as Carousel } from "./components/Carousel.tsx";
export { default as LockerSelectorCard } from "./components/LockerSelectorCard.tsx";
export { default as LockerSlotsPanel } from "./components/LockerSlotsPanel.tsx";
export { default as CurrentOrderCard } from "./components/CurrentOrderCard.tsx";
export { default as PaymentPanel } from "./components/PaymentPanel.tsx";
export { default as PaymentPendingPanel } from "./components/PaymentPendingPanel.tsx";
export { default as PickupOperationsPanel } from "./components/PickupOperationsPanel.tsx";
export { default as OperationalOrdersPanel } from "./components/OperationalOrdersPanel.tsx";
export { default as LockerDashboardHeader } from "./components/LockerDashboardHeader.tsx";
export { default as DashboardLegend } from "./components/DashboardLegend.tsx";
export { default as SyncStatusBar } from "./components/SyncStatusBar.tsx";
export { default as SlotSelectionBanner } from "./components/SlotSelectionBanner.tsx";
export { default as FlowProgressPanel } from "./components/FlowProgressPanel.tsx";
export { default as LockerDashboardLayout } from "./components/LockerDashboardLayout.tsx";

export * from "./utils/dashboardConstants";
export * from "./utils/dashboardFormatters";
export * from "./utils/dashboardSlotUtils";
export * from "./utils/dashboardPaymentUtils";
export * from "./utils/dashboardOrderUtils";
export * from "./utils/dashboardMappers";

export * from "./services/lockerRegistryService";
export * from "./services/lockerSlotsService";
export * from "./services/operationalOrdersService";
export * from "./services/operationalPaymentService";
export * from "./services/operationalPickupService";
