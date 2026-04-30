// Barrel ESM: extensões explícitas (.ts hooks, .jsx componentes) — evita falha de resolução com lazy() / Vite.

export { default as useLockerRegistry } from "./hooks/useLockerRegistry.ts";
export { default as useLockerSlotsSync } from "./hooks/useLockerSlotsSync.ts";
export { default as useOperationalOrders } from "./hooks/useOperationalOrders.ts";
export { default as useSlotSelection } from "./hooks/useSlotSelection.ts";
export { default as useCurrentOrder } from "./hooks/useCurrentOrder.ts";
export { default as useOperationalPayment } from "./hooks/useOperationalPayment.ts";
export { default as useOperationalPickup } from "./hooks/useOperationalPickup.ts";
export { default as useLockerDashboardController } from "./hooks/useLockerDashboardController.ts";

export { default as SlotCard } from "./components/SlotCard.jsx";
export { default as OrdersCardList } from "./components/OrdersCardList.jsx";
export { default as OrdersTable } from "./components/OrdersTable.jsx";
export { default as InfoRow } from "./components/InfoRow.jsx";
export { default as Carousel } from "./components/Carousel.jsx";
export { default as LockerSelectorCard } from "./components/LockerSelectorCard.jsx";
export { default as LockerSlotsPanel } from "./components/LockerSlotsPanel.jsx";
export { default as CurrentOrderCard } from "./components/CurrentOrderCard.jsx";
export { default as PaymentPanel } from "./components/PaymentPanel.jsx";
export { default as PaymentPendingPanel } from "./components/PaymentPendingPanel.jsx";
export { default as PickupOperationsPanel } from "./components/PickupOperationsPanel.jsx";
export { default as OperationalOrdersPanel } from "./components/OperationalOrdersPanel.jsx";
export { default as LockerDashboardHeader } from "./components/LockerDashboardHeader.jsx";
export { default as DashboardLegend } from "./components/DashboardLegend.jsx";
export { default as SyncStatusBar } from "./components/SyncStatusBar.jsx";
export { default as SlotSelectionBanner } from "./components/SlotSelectionBanner.jsx";
export { default as FlowProgressPanel } from "./components/FlowProgressPanel.jsx";
export { default as LockerDashboardLayout } from "./components/LockerDashboardLayout.jsx";

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
