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

interface CheckoutState {
  currentOrder: CurrentOrder | null;
  orderError: string;
  payResp: PaymentResponse | null;
  pickupResp: PickupResponse | null;
  ordersLoading: boolean;
  ordersError: string;
  ordersData: Array<Record<string, unknown>>;
  syncStatus: "idle" | "syncing" | "stale";
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
  setSyncStatus: (status: CheckoutState["syncStatus"]) => void;
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
  syncStatus: "idle",
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
  setSyncStatus: (status) => set({ syncStatus: status }),
  resetFlow: () =>
    set({
      currentOrder: null,
      orderError: "",
      payResp: null,
      pickupResp: null,
      ordersLoading: false,
      ordersError: "",
      ordersData: [],
      syncStatus: "idle",
    }),
}));
