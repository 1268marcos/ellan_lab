// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPayment.js
/**
 * * Responsável por:
 * createOnlineOrder
 * simulatePayment
 * confirmPaymentInternally
 * payMethod, setPayMethod
 * payValue, setPayValue
 * cardType, customerPhone, walletProvider
 * payResp, payLoading
 * pendingPaymentContext
 * 
 * E aqui fica a regra crítica de não espalhar lógica de pagamento em UI.
 * 
 * Também é aqui que eu recomendo corrigir o envio de amount_cents no 
 * dashboard operacional, porque hoje ele ainda envia valor do frontend.
 */

// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPayment.js

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createOperationalOrder,
  executeGatewayPayment,
  confirmOperationalPayment,
} from "../services/operationalPaymentService.js";
import {
  extractPendingPaymentData,
  generateClientTransactionId,
  getWalletProviderForMethod,
  isDigitalWalletMethod,
  pickGatewayTransactionId,
} from "../utils/dashboardPaymentUtils.js";
import {
  buildPaymentSummary,
  extractOperationalErrorMessage,
  extractOperationalErrorType,
  isStaleCurrentOrderErrorType,
} from "../utils/dashboardOrderUtils.js";
import { groupIndexFromSlot } from "../utils/dashboardSlotUtils.js";

function buildDefaultSkuId(region, slot, lockerId) {
  const safeLocker = String(lockerId || "LOCKER").replace(/[^A-Z0-9_-]/gi, "_");
  return `${safeLocker}_SLOT_${slot}_${region}`;
}

export default function useOperationalPayment({
  token,
  region,
  gatewayUrl,
  internalToken,
  orderPickupBase,
  selectedLocker,
  currentOrder,
  selectedSlot,
  slotSelectionRemainingSec,
  fetchOrdersOnce,
}) {
  const [payMethod, setPayMethod] = useState("CARTAO");
  const [payValue, setPayValue] = useState(100);
  const [paySlot, setPaySlot] = useState(1);
  const [payResp, setPayResp] = useState("");
  const [payLoading, setPayLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [pendingPaymentContext, setPendingPaymentContext] = useState(null);
  const [cardType, setCardType] = useState("creditCard");
  const [customerPhone, setCustomerPhone] = useState("");
  const [walletProvider, setWalletProvider] = useState("");

  const availablePaymentMethods = useMemo(
    () => (Array.isArray(selectedLocker?.payment_methods) ? selectedLocker.payment_methods : []),
    [selectedLocker]
  );

  const isWalletMethodSelected = useMemo(
    () => isDigitalWalletMethod(payMethod),
    [payMethod]
  );

  useEffect(() => {
    if (payMethod !== "CARTAO") setCardType("creditCard");
    if (payMethod !== "MBWAY") setCustomerPhone("");

    const wallet = getWalletProviderForMethod(payMethod);
    setWalletProvider(wallet || "");
  }, [payMethod]);

  useEffect(() => {
    if (!selectedLocker) return;

    setPayMethod((prev) => {
      if (prev && availablePaymentMethods.includes(prev)) return prev;
      return availablePaymentMethods[0] || "CARTAO";
    });
  }, [availablePaymentMethods, selectedLocker]);

  const confirmPaymentInternally = useCallback(
    async (orderId, transactionId) => {
      if (!internalToken) {
        throw new Error("VITE_INTERNAL_TOKEN não configurado no frontend.");
      }

      if (!currentOrder) {
        throw new Error("Nenhum pedido atual carregado para confirmação interna.");
      }

      const totemId = currentOrder?.totem_id || selectedLocker?.locker_id;
      const amountCents =
        typeof currentOrder.amount_cents === "number"
          ? currentOrder.amount_cents
          : Math.round(Number(payValue) * 100);

      const payload = {
        order_id: orderId,
        region,
        totem_id: totemId,
        channel: "ONLINE",
        provider: payMethod,
        transaction_id: transactionId,
        amount_cents: amountCents,
        currency: region === "SP" ? "BRL" : "EUR",
      };

      return confirmOperationalPayment({
        orderPickupBase,
        internalToken,
        orderId,
        payload,
      });
    },
    [
      currentOrder,
      internalToken,
      orderPickupBase,
      payMethod,
      payValue,
      region,
      selectedLocker,
    ]
  );

  const createOnlineOrder = useCallback(async () => {
    if (!selectedLocker) {
      return { ok: false, orderError: "Selecione um locker antes de criar o pedido." };
    }

    if (!selectedSlot) {
      return { ok: false, orderError: "Selecione uma gaveta antes de criar o pedido." };
    }

    if (!payMethod) {
      return { ok: false, orderError: "Selecione um método de pagamento." };
    }

    if (slotSelectionRemainingSec <= 0) {
      return { ok: false, orderError: "A seleção da gaveta expirou. Escolha novamente." };
    }

    if (payMethod === "CARTAO" && !cardType) {
      return { ok: false, orderError: "Escolha se o cartão é crédito ou débito." };
    }

    if (payMethod === "MBWAY" && !customerPhone.trim()) {
      return { ok: false, orderError: "Informe o telefone para pagamento MB WAY." };
    }

    const slotNum = Number(selectedSlot);
    const skuId = buildDefaultSkuId(region, slotNum, selectedLocker.locker_id);
    const totemId = selectedLocker.locker_id;

    setOrderLoading(true);
    setPayResp("");
    setPendingPaymentContext(null);

    try {
      const payload = {
        region,
        sku_id: skuId,
        totem_id: totemId,
        desired_slot: slotNum,
        payment_method: payMethod,
      };

      if (payMethod === "CARTAO") {
        payload.card_type = cardType;
      }

      if (payMethod === "MBWAY") {
        payload.customer_phone = customerPhone.trim();
      }

      const wallet = getWalletProviderForMethod(payMethod);
      if (wallet) {
        payload.wallet_provider = wallet;
      }

      const data = await createOperationalOrder({
        orderPickupBase,
        token,
        payload,
      });

      if (typeof data?.amount_cents === "number") {
        setPayValue(Number(data.amount_cents) / 100);
      }

      if (data?.payment_method) {
        setPayMethod(data.payment_method);
        setWalletProvider(getWalletProviderForMethod(data.payment_method));
      }

      setPayResp(JSON.stringify({ step: "order_created", response: data }, null, 2));
      await fetchOrdersOnce?.(1);

      const allocatedSlot = data?.allocation?.slot ? Number(data.allocation.slot) : slotNum;

      return {
        ok: true,
        currentOrder: { ...data, totem_id: totemId },
        selectedSlot: allocatedSlot,
        paySlot: allocatedSlot,
        activeGroup: groupIndexFromSlot(allocatedSlot),
        slotSelectionExpiresAt: null,
        orderError: "",
        pickupResp: "",
      };
    } catch (error) {
      return { ok: false, orderError: String(error?.message || error) };
    } finally {
      setOrderLoading(false);
    }
  }, [
    cardType,
    customerPhone,
    fetchOrdersOnce,
    orderPickupBase,
    payMethod,
    region,
    selectedLocker,
    selectedSlot,
    slotSelectionRemainingSec,
    token,
  ]);

  const simulatePayment = useCallback(async () => {
    if (!selectedLocker) {
      setPayResp("❌ Nenhum locker selecionado.");
      return { ok: false };
    }

    if (!currentOrder?.order_id) {
      setPayResp(
        "❌ Nenhum pedido atual carregado.\n\nAção recomendada: selecione uma gaveta disponível e clique em “Criar pedido online”."
      );
      return { ok: false };
    }

    if (currentOrder?.status === "PAID_PENDING_PICKUP") {
      setPayResp("⚠️ Este pedido já está pago.");
      return { ok: false };
    }

    if (currentOrder?.status === "PICKED_UP") { // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
      setPayResp("⚠️ Este pedido já foi retirado.");
      return { ok: false };
    }

    if (currentOrder?.status === "DISPENSED") { // máquina liberou - pickup.door_opened
      setPayResp("⚠️ Este pedido já foi retirado na máquina.");
      return { ok: false };
    }    

    if (!payMethod) {
      setPayResp("❌ Selecione um método de pagamento.");
      return { ok: false };
    }

    if (payMethod === "CARTAO" && !cardType) {
      setPayResp("❌ Escolha se o cartão é crédito ou débito.");
      return { ok: false };
    }

    if (payMethod === "MBWAY" && !customerPhone.trim()) {
      setPayResp("❌ Informe o telefone MB WAY.");
      return { ok: false };
    }

    setPayLoading(true);
    setPayResp("");
    setPendingPaymentContext(null);

    try {
      const totemId = currentOrder?.totem_id || selectedLocker.locker_id;
      const transactionId = generateClientTransactionId();

      const payload = {
        pedido_id: currentOrder.order_id,
        totem_id: totemId,
        metodo: payMethod,
        valor:
          typeof currentOrder.amount_cents === "number"
            ? Number(currentOrder.amount_cents) / 100
            : Number(payValue),
      };

      if (payMethod === "CARTAO") {
        payload.card_type = cardType;
      }

      if (payMethod === "MBWAY") {
        payload.customer_phone = customerPhone.trim();
      }

      if (walletProvider) {
        payload.wallet_provider = walletProvider;
      }

      const gatewayData = await executeGatewayPayment({
        gatewayUrl,
        token,
        payload,
      });

      const pending = extractPendingPaymentData(gatewayData);
      const effectiveTransactionId =
        pending.transactionId || pickGatewayTransactionId(gatewayData) || transactionId;

      if (
        pending.status === "PENDING_CUSTOMER_ACTION" ||
        pending.instructionType === "DISPLAY_QR" ||
        pending.instructionType === "SHOW_INSTRUCTIONS"
      ) {
        const context = {
          ...pending,
          order_id: currentOrder.order_id,
          locker_id: totemId,
          payment_method: payMethod,
          transaction_id: effectiveTransactionId,
        };

        setPendingPaymentContext(context);
        setPayResp(
          JSON.stringify(
            {
              step: "payment_pending_customer_action",
              response: gatewayData,
            },
            null,
            2
          )
        );
        return { ok: true, pendingPaymentContext: context };
      }

      const confirmData = await confirmPaymentInternally(
        currentOrder.order_id,
        effectiveTransactionId
      );

      const summary = buildPaymentSummary({
        gatewayData,
        confirmData,
        region,
        currentOrderId: currentOrder.order_id,
        lockerId: totemId,
      });

      const nextCurrentOrder = {
        ...currentOrder,
        status: "PAID_PENDING_PICKUP",
        paid_at: confirmData?.paid_at || currentOrder?.paid_at,
        pickup_id: confirmData?.pickup_id || currentOrder?.pickup_id,
        manual_code: confirmData?.manual_code || currentOrder?.manual_code,
        token_id: confirmData?.token_id || currentOrder?.token_id,
        pickup_status: confirmData?.pickup_status || currentOrder?.pickup_status,
        pickup_deadline_at:
          confirmData?.pickup_deadline_at ||
          confirmData?.pickup_expires_at ||
          currentOrder?.pickup_deadline_at,
        allocation: {
          allocation_id:
            confirmData?.allocation_id || currentOrder?.allocation?.allocation_id,
          slot: confirmData?.slot || currentOrder?.allocation?.slot,
          state: confirmData?.allocation_state || currentOrder?.allocation?.state,
        },
      };

      setPendingPaymentContext(null);
      setPayResp(
        `${summary}\n\n--- JSON bruto ---\n${JSON.stringify(
          {
            step: "payment_confirmed",
            gateway_response: gatewayData,
            confirm_response: confirmData,
          },
          null,
          2
        )}`
      );

      await fetchOrdersOnce?.(1);

      return {
        ok: true,
        currentOrder: nextCurrentOrder,
        pendingPaymentContext: null,
      };
    } catch (error) {
      const type = extractOperationalErrorType(error);
      const message = extractOperationalErrorMessage(error);

      if (isStaleCurrentOrderErrorType(type)) {
        return {
          ok: false,
          staleRecovery: true,
          recoveryMessage: `${message}\n\nO pedido atual ficou inconsistente ou foi reprocessado.`,
        };
      }

      setPayResp(`❌ Erro ao simular/confirmar pagamento\n${String(error?.message || error)}`);
      return { ok: false };
    } finally {
      setPayLoading(false);
    }
  }, [
    cardType,
    confirmPaymentInternally,
    currentOrder,
    customerPhone,
    fetchOrdersOnce,
    gatewayUrl,
    payMethod,
    payValue,
    region,
    selectedLocker,
    token,
    walletProvider,
  ]);

  const confirmPendingCustomerAction = useCallback(async () => {
    if (!pendingPaymentContext?.order_id) {
      setPayResp("❌ Não há pagamento pendente aguardando confirmação.");
      return { ok: false };
    }

    setPayLoading(true);

    try {
      const confirmData = await confirmPaymentInternally(
        pendingPaymentContext.order_id,
        pendingPaymentContext.transaction_id || generateClientTransactionId()
      );

      const summary = buildPaymentSummary({
        gatewayData: { payment: { currency: pendingPaymentContext.currency } },
        confirmData,
        region,
        currentOrderId: pendingPaymentContext.order_id,
        lockerId: pendingPaymentContext.locker_id,
      });

      const nextCurrentOrder = currentOrder
        ? {
            ...currentOrder,
            status: "PAID_PENDING_PICKUP",
            paid_at: confirmData?.paid_at || currentOrder?.paid_at,
            pickup_id: confirmData?.pickup_id || currentOrder?.pickup_id,
            manual_code: confirmData?.manual_code || currentOrder?.manual_code,
            token_id: confirmData?.token_id || currentOrder?.token_id,
            pickup_status: confirmData?.pickup_status || currentOrder?.pickup_status,
            pickup_deadline_at:
              confirmData?.pickup_deadline_at ||
              confirmData?.pickup_expires_at ||
              currentOrder?.pickup_deadline_at,
            allocation: {
              allocation_id:
                confirmData?.allocation_id || currentOrder?.allocation?.allocation_id,
              slot: confirmData?.slot || currentOrder?.allocation?.slot,
              state: confirmData?.allocation_state || currentOrder?.allocation?.state,
            },
          }
        : null;

      setPendingPaymentContext(null);
      setPayResp(
        `${summary}\n\n--- JSON bruto ---\n${JSON.stringify(
          {
            step: "pending_payment_confirmed",
            confirm_response: confirmData,
          },
          null,
          2
        )}`
      );

      await fetchOrdersOnce?.(1);

      return {
        ok: true,
        currentOrder: nextCurrentOrder,
        pendingPaymentContext: null,
      };
    } catch (error) {
      setPayResp(`❌ Falha ao confirmar pagamento pendente\n${String(error?.message || error)}`);
      return { ok: false };
    } finally {
      setPayLoading(false);
    }
  }, [
    confirmPaymentInternally,
    currentOrder,
    fetchOrdersOnce,
    pendingPaymentContext,
    region,
  ]);

  return {
    payMethod,
    setPayMethod,
    payValue,
    setPayValue,
    paySlot,
    setPaySlot,
    payResp,
    setPayResp,
    payLoading,
    orderLoading,
    pendingPaymentContext,
    setPendingPaymentContext,
    cardType,
    setCardType,
    customerPhone,
    setCustomerPhone,
    walletProvider,
    setWalletProvider,
    availablePaymentMethods,
    isWalletMethodSelected,
    createOnlineOrder,
    simulatePayment,
    confirmPendingCustomerAction,
  };
}