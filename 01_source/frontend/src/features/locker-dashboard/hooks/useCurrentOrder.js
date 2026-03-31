// 01_source/frontend/src/features/locker-dashboard/hooks/useCurrentOrder.js
/**
 * * Responsável por:
 * currentOrder
 * setCurrentOrder
 * currentOrderMeta
 * currentPickupMeta
 * currentAllocationMeta
 * currentOrderWarning
 * isOrderAlreadyPaid
 * canRegenerateManualCode
 * clearCurrentOrderForRecovery
 * handleSelectOrder
 */

// 01_source/frontend/src/features/locker-dashboard/hooks/useCurrentOrder.js

import { useCallback, useMemo, useState } from "react";
import {
  buildCurrentOrderFromListItem,
  getOrderSupportMeta,
} from "../utils/dashboardOrderUtils.js";
import { groupIndexFromSlot } from "../utils/dashboardSlotUtils.js";
import { getWalletProviderForMethod } from "../utils/dashboardPaymentUtils.js";

export default function useCurrentOrder() {
  const [currentOrder, setCurrentOrder] = useState(null);
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderError, setOrderError] = useState("");

  const supportMeta = useMemo(() => getOrderSupportMeta(currentOrder), [currentOrder]);

  const buildFocusPatch = useCallback((item) => {
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
      currentOrder: buildCurrentOrderFromListItem(item),
      selectedSlot: slotNum || null,
      activeGroup: slotNum ? groupIndexFromSlot(slotNum) : 0,
      payMethod: paymentMethod,
      payValue: amountValue,
      walletProvider: paymentMethod ? getWalletProviderForMethod(paymentMethod) : "",
      selectedLockerId: item?.totem_id || "",
    };
  }, []);

  const handleSelectOrder = useCallback(
    (item) => {
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

  const clearCurrentOrderForRecovery = useCallback((message) => {
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

  const setCurrentOrderFromRaw = useCallback((item) => {
    setCurrentOrder(buildCurrentOrderFromListItem(item));
  }, []);

  const resetCurrentOrder = useCallback(() => {
    setCurrentOrder(null);
    setOrderError("");
  }, []);

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