// 01_source/frontend/src/features/locker-dashboard/hooks/useLockerDashboardController.js

import { useCallback, useEffect, useMemo, useState } from "react";
import useLockerRegistry from "./useLockerRegistry.js";
import useLockerSlotsSync from "./useLockerSlotsSync.js";
import useOperationalOrders from "./useOperationalOrders.js";
import useSlotSelection from "./useSlotSelection.js";
import useCurrentOrder from "./useCurrentOrder.js";
import useOperationalPayment from "./useOperationalPayment.js";
import useOperationalPickup from "./useOperationalPickup.js";

export default function useLockerDashboardController({
  token,
  region = "PT",
  backendSp,
  backendPt,
  gatewayBase,
  orderPickupBase,
  internalToken,
}) {
  const [syncEnabled, setSyncEnabled] = useState(true);

  const registry = useLockerRegistry({
    region,
    gatewayBase,
  });

  const {
    selectedLocker,
    selectedLockerId,
    setSelectedLockerId,
  } = registry;

  const backendBase = useMemo(() => {
    const effectiveRegion = selectedLocker?.backend_region || region;
    return effectiveRegion === "SP" ? backendSp : backendPt;
  }, [backendPt, backendSp, region, selectedLocker]);

  const gatewayUrl = useMemo(
    () => `${gatewayBase}/gateway/pagamento`,
    [gatewayBase]
  );

  const currentOrderState = useCurrentOrder();

  const {
    currentOrder,
    setCurrentOrder,
    orderError,
    setOrderError,
    handleSelectOrder: buildOrderSelectionPatch,
    clearCurrentOrderForRecovery,
  } = currentOrderState;

  const slotsSync = useLockerSlotsSync({
    backendBase,
    selectedLocker,
    syncEnabled,
    pollIntervalMs: 3000,
  });

  const {
    slots,
    syncStatus,
    totalSlots,
    fetchSlotsOnce,
    setStateOnBackend,
  } = slotsSync;

  const slotSelection = useSlotSelection({
    slots,
    currentOrder,
    selectionTimeoutMs: 45_000,
  });

  const orders = useOperationalOrders({
    orderPickupBase,
    token,
    region,
    selectedLocker,
  });

  const payment = useOperationalPayment({
    token,
    region,
    gatewayUrl,
    internalToken,
    orderPickupBase,
    selectedLocker,
    currentOrder,
    selectedSlot: slotSelection.selectedSlot,
    slotSelectionRemainingSec: slotSelection.slotSelectionRemainingSec,
    fetchOrdersOnce: orders.fetchOrdersOnce,
  });

  const pickup = useOperationalPickup({
    token,
    region,
    orderPickupBase,
    currentOrder,
    setCurrentOrder,
    fetchOrdersOnce: orders.fetchOrdersOnce,
  });

  useEffect(() => {
    if (!selectedLocker) return;

    slotSelection.setSelectedSlot(null);
    setCurrentOrder(null);
    setOrderError("");
    pickup.setPickupResp("");
    payment.setPayResp("");
    payment.setPendingPaymentContext(null);
    slotSelection.setSlotSelectionExpiresAt(null);
  }, [
    payment,
    pickup,
    selectedLocker?.locker_id,
    setCurrentOrder,
    setOrderError,
    slotSelection,
  ]);

  const applyOrderSelectionPatch = useCallback(
    (patch) => {
      if (!patch) return;

      if ("currentOrder" in patch) setCurrentOrder(patch.currentOrder);
      if ("selectedSlot" in patch) slotSelection.setSelectedSlot(patch.selectedSlot);
      if ("activeGroup" in patch) slotSelection.setActiveGroup(patch.activeGroup);
      if ("slotSelectionExpiresAt" in patch) {
        slotSelection.setSlotSelectionExpiresAt(patch.slotSelectionExpiresAt);
      }
      if ("orderError" in patch) setOrderError(patch.orderError);
      if ("pickupResp" in patch) pickup.setPickupResp(patch.pickupResp);
      if ("payResp" in patch) payment.setPayResp(patch.payResp);
      if ("pendingPaymentContext" in patch) {
        payment.setPendingPaymentContext(patch.pendingPaymentContext ?? null);
      }
      if ("selectedLockerId" in patch && patch.selectedLockerId) {
        setSelectedLockerId(patch.selectedLockerId);
      }
      if ("payMethod" in patch && patch.payMethod) payment.setPayMethod(patch.payMethod);
      if ("payValue" in patch && Number.isFinite(patch.payValue)) {
        payment.setPayValue(patch.payValue);
      }
      if ("walletProvider" in patch) payment.setWalletProvider(patch.walletProvider || "");
      if ("paySlot" in patch && Number.isFinite(patch.paySlot)) {
        payment.setPaySlot(patch.paySlot);
      }
    },
    [payment, pickup, setCurrentOrder, setOrderError, setSelectedLockerId, slotSelection]
  );

  const handleSelectOrder = useCallback(
    (item) => {
      const patch = buildOrderSelectionPatch(item);
      applyOrderSelectionPatch(patch);
    },
    [applyOrderSelectionPatch, buildOrderSelectionPatch]
  );

  const handleSelectSlot = useCallback(
    (slot) => {
      const selected = slotSelection.selectSlot(slot);
      if (!selected) return;

      setCurrentOrder(null);
      setOrderError("");
      pickup.setPickupResp("");
      payment.setPayResp("");
      payment.setPendingPaymentContext(null);
    },
    [payment, pickup, setCurrentOrder, setOrderError, slotSelection]
  );

  const handleCreateOnlineOrder = useCallback(async () => {
    const result = await payment.createOnlineOrder();
    if (!result) return result;

    if (result.ok) {
      applyOrderSelectionPatch(result);
      return result;
    }

    if (result.orderError) {
      setOrderError(result.orderError);
    }

    return result;
  }, [applyOrderSelectionPatch, payment, setOrderError]);

  const handleSimulatePayment = useCallback(async () => {
    const result = await payment.simulatePayment();
    if (!result) return result;

    if (result.staleRecovery) {
      const recoveryPatch = clearCurrentOrderForRecovery(result.recoveryMessage);
      applyOrderSelectionPatch(recoveryPatch);
      return result;
    }

    if (result.ok) {
      applyOrderSelectionPatch(result);
    }

    return result;
  }, [applyOrderSelectionPatch, clearCurrentOrderForRecovery, payment]);

  const handleConfirmPendingCustomerAction = useCallback(async () => {
    const result = await payment.confirmPendingCustomerAction();
    if (result?.ok) {
      applyOrderSelectionPatch(result);
    }
    return result;
  }, [applyOrderSelectionPatch, payment]);

  const handleManualRedeemSuccess = useCallback(
    async (data) => {
      await pickup.handleManualRedeemSuccess(data);
    },
    [pickup]
  );

  const handleQrRedeemSuccess = useCallback(
    async (data) => {
      await pickup.handleQrRedeemSuccess(data);
    },
    [pickup]
  );

  const handleClearSlotSelection = useCallback(() => {
    slotSelection.clearSlotSelection();
    payment.setPaySlot(1);
    payment.setPayResp("");
    payment.setPendingPaymentContext(null);
  }, [payment, slotSelection]);

  const headerProps = useMemo(
    () => ({
      region,
      selectedLocker,
      lockersSource: registry.lockersSource,
      syncEnabled,
      setSyncEnabled,
      syncStatus,
    }),
    [region, registry.lockersSource, selectedLocker, syncEnabled, syncStatus]
  );

  const syncBarProps = useMemo(
    () => ({
      selectedLocker,
      syncStatus,
      syncEnabled,
      onToggleSync: setSyncEnabled,
    }),
    [selectedLocker, syncEnabled, syncStatus]
  );

  const lockerSelectorProps = useMemo(
    () => ({
      region,
      lockers: registry.lockers,
      lockersLoading: registry.lockersLoading,
      lockersError: registry.lockersError,
      lockersSource: registry.lockersSource,
      selectedLockerId,
      setSelectedLockerId,
      selectedLocker,
    }),
    [
      region,
      registry.lockers,
      registry.lockersError,
      registry.lockersLoading,
      registry.lockersSource,
      selectedLocker,
      selectedLockerId,
      setSelectedLockerId,
    ]
  );

  const currentOrderCardProps = useMemo(
    () => ({
      currentOrder,
      currentOrderMeta: currentOrderState.currentOrderMeta,
      currentPickupMeta: currentOrderState.currentPickupMeta,
      currentAllocationMeta: currentOrderState.currentAllocationMeta,
      currentOrderWarning: currentOrderState.currentOrderWarning,
      orderError,
    }),
    [
      currentOrder,
      currentOrderState.currentAllocationMeta,
      currentOrderState.currentOrderMeta,
      currentOrderState.currentOrderWarning,
      currentOrderState.currentPickupMeta,
      orderError,
    ]
  );

  const slotSelectionBannerProps = useMemo(
    () => ({
      selectedLocker,
      selectedSlot: slotSelection.selectedSlot,
      hasActiveSlotSelection: slotSelection.hasActiveSlotSelection,
      slotSelectionRemainingSec: slotSelection.slotSelectionRemainingSec,
      onClear: handleClearSlotSelection,
    }),
    [
      handleClearSlotSelection,
      selectedLocker,
      slotSelection.hasActiveSlotSelection,
      slotSelection.selectedSlot,
      slotSelection.slotSelectionRemainingSec,
    ]
  );

  const slotsPanelProps = useMemo(
    () => ({
      totalSlots,
      activeGroup: slotSelection.activeGroup,
      setActiveGroup: slotSelection.setActiveGroup,
      groupSlotsList: slotSelection.groupSlotsList,
      slots,
      selectedSlot: slotSelection.selectedSlot,
      onSelectSlot: handleSelectSlot,
      hasActiveSlotSelection: slotSelection.hasActiveSlotSelection,
      slotSelectionRemainingSec: slotSelection.slotSelectionRemainingSec,
    }),
    [
      handleSelectSlot,
      slotSelection.activeGroup,
      slotSelection.groupSlotsList,
      slotSelection.hasActiveSlotSelection,
      slotSelection.selectedSlot,
      slotSelection.setActiveGroup,
      slotSelection.slotSelectionRemainingSec,
      slots,
      totalSlots,
    ]
  );

  const paymentPanelProps = useMemo(
    () => ({
      availablePaymentMethods: payment.availablePaymentMethods,
      payMethod: payment.payMethod,
      setPayMethod: payment.setPayMethod,
      payValue: payment.payValue,
      setPayValue: payment.setPayValue,
      cardType: payment.cardType,
      setCardType: payment.setCardType,
      customerPhone: payment.customerPhone,
      setCustomerPhone: payment.setCustomerPhone,
      walletProvider: payment.walletProvider,
      isWalletMethodSelected: payment.isWalletMethodSelected,
      orderLoading: payment.orderLoading,
      payLoading: payment.payLoading,
      payResp: payment.payResp,
      onCreateOnlineOrder: handleCreateOnlineOrder,
      onSimulatePayment: handleSimulatePayment,
      onConfirmPendingCustomerAction: handleConfirmPendingCustomerAction,
      pendingPaymentContext: payment.pendingPaymentContext,
      currentOrder,
    }),
    [
      currentOrder,
      handleConfirmPendingCustomerAction,
      handleCreateOnlineOrder,
      handleSimulatePayment,
      payment.availablePaymentMethods,
      payment.cardType,
      payment.customerPhone,
      payment.isWalletMethodSelected,
      payment.orderLoading,
      payment.payLoading,
      payment.payMethod,
      payment.payResp,
      payment.payValue,
      payment.pendingPaymentContext,
      payment.setCardType,
      payment.setCustomerPhone,
      payment.setPayMethod,
      payment.setPayValue,
      payment.walletProvider,
    ]
  );

  const paymentPendingPanelProps = useMemo(
    () => ({
      pendingPaymentContext: payment.pendingPaymentContext,
      region,
      onConfirm: handleConfirmPendingCustomerAction,
      loading: payment.payLoading,
    }),
    [handleConfirmPendingCustomerAction, payment.payLoading, payment.pendingPaymentContext, region]
  );

  const pickupPanelProps = useMemo(
    () => ({
      currentOrder,
      regenCodeLoading: pickup.regenCodeLoading,
      canRegenerateManualCode: currentOrderState.canRegenerateManualCode,
      onRegenerateManualCode: pickup.regenerateManualCode,
      pickupResp: pickup.pickupResp,
      onManualRedeemSuccess: handleManualRedeemSuccess,
      onQrRedeemSuccess: handleQrRedeemSuccess,
      token,
    }),
    [
      currentOrder,
      currentOrderState.canRegenerateManualCode,
      handleManualRedeemSuccess,
      handleQrRedeemSuccess,
      pickup.pickupResp,
      pickup.regenCodeLoading,
      pickup.regenerateManualCode,
      token,
    ]
  );

  const ordersPanelProps = useMemo(
    () => ({
      showOrdersPanel: orders.showOrdersPanel,
      setShowOrdersPanel: orders.setShowOrdersPanel,
      ordersLoading: orders.ordersLoading,
      ordersError: orders.ordersError,
      ordersData: orders.ordersData,
      currentOrder,
      onSelectOrder: handleSelectOrder,
      ordersFilterStatus: orders.ordersFilterStatus,
      setOrdersFilterStatus: orders.setOrdersFilterStatus,
      ordersFilterChannel: orders.ordersFilterChannel,
      setOrdersFilterChannel: orders.setOrdersFilterChannel,
      ordersPage: orders.ordersPage,
      setOrdersPage: orders.setOrdersPage,
      ordersHasPrev: orders.ordersHasPrev,
      ordersHasNext: orders.ordersHasNext,
      ordersTotal: orders.ordersTotal,
      visibleOrdersFrom: orders.visibleOrdersFrom,
      visibleOrdersTo: orders.visibleOrdersTo,
      totalOrdersPages: orders.totalOrdersPages,
      fetchOrdersOnce: orders.fetchOrdersOnce,
      useTable: true,
      ordersTableHeight: orders.ordersTableHeight,
    }),
    [
      currentOrder,
      handleSelectOrder,
      orders.fetchOrdersOnce,
      orders.ordersData,
      orders.ordersError,
      orders.ordersFilterChannel,
      orders.ordersFilterStatus,
      orders.ordersHasNext,
      orders.ordersHasPrev,
      orders.ordersLoading,
      orders.ordersPage,
      orders.ordersTableHeight,
      orders.ordersTotal,
      orders.setOrdersFilterChannel,
      orders.setOrdersFilterStatus,
      orders.setOrdersPage,
      orders.setShowOrdersPanel,
      orders.showOrdersPanel,
      orders.totalOrdersPages,
      orders.visibleOrdersFrom,
      orders.visibleOrdersTo,
    ]
  );

  return {
    region,
    syncEnabled,
    setSyncEnabled,
    backendBase,
    gatewayUrl,

    registry,
    orders,
    currentOrderState,
    slotsSync,
    slotSelection,
    payment,
    pickup,

    selectedLocker,
    selectedLockerId,
    setSelectedLockerId,

    currentOrder,
    setCurrentOrder,
    orderError,
    setOrderError,
    handleSelectOrder,
    clearCurrentOrderForRecovery,

    slots,
    syncStatus,
    totalSlots,
    fetchSlotsOnce,
    setStateOnBackend,

    selectedSlot: slotSelection.selectedSlot,
    setSelectedSlot: slotSelection.setSelectedSlot,
    activeGroup: slotSelection.activeGroup,
    setActiveGroup: slotSelection.setActiveGroup,
    slotSelectionExpiresAt: slotSelection.slotSelectionExpiresAt,
    setSlotSelectionExpiresAt: slotSelection.setSlotSelectionExpiresAt,
    slotSelectionRemainingSec: slotSelection.slotSelectionRemainingSec,
    hasActiveSlotSelection: slotSelection.hasActiveSlotSelection,
    groupSlotsList: slotSelection.groupSlotsList,
    selectSlot: slotSelection.selectSlot,
    clearSlotSelection: handleClearSlotSelection,
    handleSelectSlot,

    handleCreateOnlineOrder,
    handleSimulatePayment,
    handleConfirmPendingCustomerAction,
    handleManualRedeemSuccess,
    handleQrRedeemSuccess,

    headerProps,
    syncBarProps,
    lockerSelectorProps,
    currentOrderCardProps,
    slotSelectionBannerProps,
    slotsPanelProps,
    paymentPanelProps,
    paymentPendingPanelProps,
    pickupPanelProps,
    ordersPanelProps,
  };
}