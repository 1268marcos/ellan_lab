/**
 * Responsável por: currentOrder, setCurrentOrder, meta de suporte,
 * clearCurrentOrderForRecovery, handleSelectOrder
 */

import { useCallback, useMemo, useState } from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import {
  buildCurrentOrderFromListItem,
  getOrderSupportMeta,
} from "../utils/dashboardOrderUtils";
import { groupIndexFromSlot } from "../utils/dashboardSlotUtils";
import { getWalletProviderForMethod } from "../utils/dashboardPaymentUtils";

export default function useCurrentOrder() {
  const currentOrder = useCheckoutStore((state) => state.currentOrder);
  const setCurrentOrderInStore = useCheckoutStore((state) => state.setCurrentOrder);
  const orderError = useCheckoutStore((state) => state.orderError);
  const setOrderErrorInStore = useCheckoutStore((state) => state.setOrderError);
  const [orderLoading, setOrderLoading] = useState(false);

  const setCurrentOrder = useCallback(
    (next: CheckoutCurrentOrder | null | ((prev: CheckoutCurrentOrder | null) => CheckoutCurrentOrder | null)) => {
      setCurrentOrderInStore(next);
    },
    [setCurrentOrderInStore]
  );

  const setOrderError = useCallback(
    (message: string) => {
      setOrderErrorInStore(String(message || ""));
    },
    [setOrderErrorInStore]
  );

  const supportMeta = useMemo(() => getOrderSupportMeta(currentOrder), [currentOrder]);

  const buildFocusPatch = useCallback((item: Record<string, unknown> | null) => {
    if (!item) {
      return {
        currentOrder: null,
        selectedSlot: null,
        activeGroup: 0,
        payMethod: "",
        payValue: 0,
        walletProvider: "",
        selectedLockerId: "",
      };
    }

    const slotNum = item?.slot ? Number(item.slot) : null;
    const paymentMethod = item?.payment_method || "";
    const amountValue =
      typeof item?.amount_cents === "number" ? Number(item.amount_cents) / 100 : 0;

    return {
      currentOrder: buildCurrentOrderFromListItem(item) as unknown as CheckoutCurrentOrder,
      selectedSlot: slotNum || null,
      activeGroup: slotNum ? groupIndexFromSlot(slotNum) : 0,
      payMethod: paymentMethod,
      payValue: amountValue,
      walletProvider: paymentMethod ? getWalletProviderForMethod(paymentMethod) : "",
      selectedLockerId: item?.totem_id || "",
    };
  }, []);

  const handleSelectOrder = useCallback(
    (item: Record<string, unknown>) => {
      return {
        ...buildFocusPatch(item),
        orderError: "",
        payResp: "",
        pickupResp: "",
        slotSelectionExpiresAt: null,
      };
    },
    [buildFocusPatch]
  );

  const clearCurrentOrderForRecovery = useCallback((message: string) => {
    return {
      currentOrder: null,
      selectedSlot: null,
      activeGroup: 0,
      paySlot: 1,
      slotSelectionExpiresAt: null,
      pickupResp: "",
      orderError: "",
      payResp: `⚠️ ${message}\n\nAção recomendada: selecione uma gaveta disponível e crie um novo pedido.`,
    };
  }, []);

  const setCurrentOrderFromRaw = useCallback((item: Record<string, unknown>) => {
    setCurrentOrderInStore(buildCurrentOrderFromListItem(item) as unknown as CheckoutCurrentOrder);
  }, [setCurrentOrderInStore]);

  const resetCurrentOrder = useCallback(() => {
    setCurrentOrderInStore(null);
    setOrderError("");
  }, [setCurrentOrderInStore]);

  return {
    currentOrder,
    setCurrentOrder,
    setCurrentOrderFromRaw,
    resetCurrentOrder,
    orderLoading,
    setOrderLoading,
    orderError,
    setOrderError,
    buildFocusPatch,
    handleSelectOrder,
    clearCurrentOrderForRecovery,
    ...supportMeta,
  };
}