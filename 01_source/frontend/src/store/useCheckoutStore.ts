import { create } from "zustand";
import type {
  CheckoutChannel,
  CheckoutCurrentOrder,
  CheckoutPaymentResponse,
  CheckoutPickupResponse,
} from "../features/checkout/types";

export type OrderChannel = CheckoutChannel;
export type CurrentOrder = CheckoutCurrentOrder;
export type PaymentResponse = CheckoutPaymentResponse;
export type PickupResponse = CheckoutPickupResponse;

/** Banner de sync de slots (locker dashboard) — formato consumido por `SyncStatusBar` / header. */
export type CheckoutSlotsSyncBanner = { ok: boolean; msg: string };

const defaultSlotsSyncBanner: CheckoutSlotsSyncBanner = { ok: true, msg: "—" };

interface CheckoutState {
  currentOrder: CurrentOrder | null;
  orderError: string;
  payResp: PaymentResponse | null;
  pickupResp: PickupResponse | null;
  ordersLoading: boolean;
  ordersError: string;
  ordersData: Array<Record<string, unknown>>;
  syncStatus: CheckoutSlotsSyncBanner;
  setCurrentOrder: (
    order:
      | CurrentOrder
      | null
      | ((prev: CurrentOrder | null) => CurrentOrder | null)
  ) => void;
  setPayResp: (resp: PaymentResponse | null) => void;
  setPickupResp: (resp: PickupResponse | null) => void;
  setOrderError: (message: string) => void;
  setOrdersLoading: (value: boolean) => void;
  setOrdersError: (message: string) => void;
  setOrdersData: (data: Array<Record<string, unknown>>) => void;
  setSyncStatus: (status: CheckoutSlotsSyncBanner) => void;
  resetFlow: () => void;
}

export const useCheckoutStore = create<CheckoutState>((set) => ({
  currentOrder: null,
  orderError: "",
  payResp: null,
  pickupResp: null,
  ordersLoading: false,
  ordersError: "",
  ordersData: [],
  syncStatus: defaultSlotsSyncBanner,
  setCurrentOrder: (order) =>
    set((state) => ({
      currentOrder:
        typeof order === "function"
          ? order(state.currentOrder)
          : order,
    })),
  setPayResp: (resp) => set({ payResp: resp }),
  setPickupResp: (resp) => set({ pickupResp: resp }),
  setOrderError: (message) => set({ orderError: String(message || "") }),
  setOrdersLoading: (value) => set({ ordersLoading: Boolean(value) }),
  setOrdersError: (message) => set({ ordersError: String(message || "") }),
  setOrdersData: (data) => set({ ordersData: Array.isArray(data) ? data : [] }),
  setSyncStatus: (status) =>
    set({
      syncStatus: {
        ok: Boolean(status.ok),
        msg: String(status.msg ?? ""),
      },
    }),
  resetFlow: () =>
    set({
      currentOrder: null,
      orderError: "",
      payResp: null,
      pickupResp: null,
      ordersLoading: false,
      ordersError: "",
      ordersData: [],
      syncStatus: defaultSlotsSyncBanner,
    }),
}));
