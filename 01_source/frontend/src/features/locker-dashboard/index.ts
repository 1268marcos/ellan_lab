// Barrel ESM: imports sem extensão — Vite resolve .ts/.tsx; compatível com tsc strict-core.

export { default as useLockerRegistry } from "./hooks/useLockerRegistry";
export { default as useLockerSlotsSync } from "./hooks/useLockerSlotsSync";
export { default as useOperationalOrders } from "./hooks/useOperationalOrders";
export { default as useSlotSelection } from "./hooks/useSlotSelection";
export { default as useCurrentOrder } from "./hooks/useCurrentOrder";
export { default as useOperationalPayment } from "./hooks/useOperationalPayment";
export { default as useOperationalPickup } from "./hooks/useOperationalPickup";
export { default as useLockerDashboardController } from "./hooks/useLockerDashboardController";

export { default as SlotCard } from "./components/SlotCard";
export { default as OrdersCardList } from "./components/OrdersCardList";
export { default as OrdersTable } from "./components/OrdersTable";
export { default as InfoRow } from "./components/InfoRow";
export { default as Carousel } from "./components/Carousel";
export { default as LockerSelectorCard } from "./components/LockerSelectorCard";
export { default as LockerSlotsPanel } from "./components/LockerSlotsPanel";
export { default as CurrentOrderCard } from "./components/CurrentOrderCard";
export { default as PaymentPanel } from "./components/PaymentPanel";
export { default as PaymentPendingPanel } from "./components/PaymentPendingPanel";
export { default as PickupOperationsPanel } from "./components/PickupOperationsPanel";
export { default as OperationalOrdersPanel } from "./components/OperationalOrdersPanel";
export { default as LockerDashboardHeader } from "./components/LockerDashboardHeader";
export { default as DashboardLegend } from "./components/DashboardLegend";
export { default as SyncStatusBar } from "./components/SyncStatusBar";
export { default as SlotSelectionBanner } from "./components/SlotSelectionBanner";
export { default as FlowProgressPanel } from "./components/FlowProgressPanel";
export { default as LockerDashboardLayout } from "./components/LockerDashboardLayout";

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
