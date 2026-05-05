
import type { Dispatch, ReactNode, SetStateAction } from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import type { NormalizedLockerItem } from "../utils/dashboardMappers";
import type { SlotsMap } from "../utils/dashboardSlotUtils";
import type { getOrderSupportMeta } from "../utils/dashboardOrderUtils";

export type OrdersRow = Record<string, unknown>;

type SupportMeta = ReturnType<typeof getOrderSupportMeta>;

export type CarouselProps = {
  pages: number;
  activeIndex: number;
  onPrev: () => void;
  onNext: () => void;
  onGo: (index: number) => void;
};

export type InfoRowProps = { label: ReactNode; value: ReactNode };

export type LockerDashboardLayoutProps = { children?: ReactNode };

export type LockerDashboardHeaderProps = {
  region: string;
  selectedLocker: NormalizedLockerItem | null;
  lockersSource: string;
  syncEnabled: boolean;
  setSyncEnabled: Dispatch<SetStateAction<boolean>>;
  syncStatus: { ok: boolean; msg?: string };
};

export type SyncStatusBarProps = {
  selectedLocker: NormalizedLockerItem | null;
  syncStatus: { ok: boolean; msg?: string };
  syncEnabled: boolean;
  onToggleSync: Dispatch<SetStateAction<boolean>>;
};

export type LockerSelectorCardProps = {
  region: string;
  lockers: NormalizedLockerItem[];
  lockersLoading: boolean;
  lockersError: string;
  lockersSource: string;
  selectedLockerId: string;
  setSelectedLockerId: Dispatch<SetStateAction<string>>;
  selectedLocker: NormalizedLockerItem | null;
};

export type LockerSlotsPanelProps = {
  totalSlots: number;
  activeGroup: number;
  setActiveGroup: Dispatch<SetStateAction<number>>;
  groupSlotsList: number[];
  slots: SlotsMap;
  selectedSlot: number | null;
  onSelectSlot: (slot: number) => void;
  hasActiveSlotSelection: boolean;
  slotSelectionRemainingSec: number;
};

export type SlotCardProps = {
  slot: number;
  state: string;
  name?: string | null;
  skuId?: string | null;
  priceCents?: number | null;
  isActive?: boolean;
  hasCatalogData?: boolean;
  selected?: boolean;
  disabled?: boolean;
  onClick?: () => void;
};

export type SlotSelectionBannerProps = {
  selectedLocker: NormalizedLockerItem | null;
  selectedSlot: number | null;
  hasActiveSlotSelection: boolean;
  slotSelectionRemainingSec: number;
  onClear: () => void;
};

export type CurrentOrderCardProps = {
  currentOrder: CheckoutCurrentOrder | null;
  orderError: string;
} & Pick<
  SupportMeta,
  "currentOrderMeta" | "currentPickupMeta" | "currentAllocationMeta" | "currentOrderWarning"
>;

export type FlowProgressPanelProps = {
  steps?: Array<{ key: string; label: string; state: string; detail?: string }>;
  actionHint?: string;
  onStepClick?: (key: string) => void;
};

export type OrdersTableProps = {
  ordersData: OrdersRow[];
  currentOrder: CheckoutCurrentOrder | null;
  onSelectOrder?: (item: OrdersRow) => void;
  maxHeight?: number;
};

export type OrdersCardListProps = {
  ordersData: OrdersRow[];
  ordersLoading: boolean;
  currentOrder: CheckoutCurrentOrder | null;
  onSelectOrder: (item: OrdersRow) => void;
};

export type OperationalOrdersPanelProps = {
  showOrdersPanel: boolean;
  setShowOrdersPanel: Dispatch<SetStateAction<boolean>>;
  ordersLoading: boolean;
  ordersError: string;
  ordersData: OrdersRow[];
  currentOrder: CheckoutCurrentOrder | null;
  onSelectOrder: (item: OrdersRow) => void;
  ordersFilterStatus: string;
  setOrdersFilterStatus: Dispatch<SetStateAction<string>>;
  ordersFilterChannel: string;
  setOrdersFilterChannel: Dispatch<SetStateAction<string>>;
  ordersPage: number;
  setOrdersPage: Dispatch<SetStateAction<number>>;
  ordersHasPrev: boolean;
  ordersHasNext: boolean;
  ordersTotal: number;
  visibleOrdersFrom: number;
  visibleOrdersTo: number;
  totalOrdersPages: number;
  fetchOrdersOnce: (targetPage?: number, targetPageSize?: number) => Promise<void>;
  ordersLastUpdatedAt: number | null;
  syncEnabled: boolean;
  useTable?: boolean;
  ordersTableHeight?: number;
};

export type PaymentPanelProps = {
  availablePaymentMethods: Array<string | { code: string }>;
  payMethod: string;
  setPayMethod: Dispatch<SetStateAction<string>>;
  selectedSlotPriceCents: number | null;
  customerPhone: string;
  setCustomerPhone: Dispatch<SetStateAction<string>>;
  walletProvider: string;
  isWalletMethodSelected: boolean;
  orderLoading: boolean;
  payLoading: boolean;
  payResp: string;
  onCreateOnlineOrder: () => void | Promise<unknown>;
  onSimulatePayment: () => void | Promise<unknown>;
  onConfirmPendingCustomerAction: () => void | Promise<unknown>;
  pendingPaymentContext: Record<string, unknown> | null;
  currentOrder: CheckoutCurrentOrder | null;
};

export type PaymentPendingPanelProps = {
  pendingPaymentContext: Record<string, unknown> | null;
  region?: string;
  onConfirm: () => void | Promise<unknown>;
  loading?: boolean;
};

export type PickupOperationsPanelProps = {
  currentOrder: CheckoutCurrentOrder | null;
  regenCodeLoading: boolean;
  canRegenerateManualCode: boolean;
  onRegenerateManualCode: () => void | Promise<unknown>;
  pickupResp: string;
  onManualRedeemSuccess: (data: Record<string, unknown>) => void | Promise<unknown>;
  /** Reservado para integrações futuras (QR); o painel legado ainda não expõe callback tipado. */
  onQrRedeemSuccess: (data: Record<string, unknown>) => void | Promise<unknown>;
};

