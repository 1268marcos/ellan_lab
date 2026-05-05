
/**
 * Responsável por: createOnlineOrder, simulatePayment, confirmPaymentInternally,
 * estado de pagamento e pendingPaymentContext
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import type { NormalizedLockerItem } from "../utils/dashboardMappers";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import {
  createOperationalOrder,
  executeGatewayPayment,
  confirmOperationalPayment,
} from "../services/operationalPaymentService";
import {
  extractPendingPaymentData,
  generateClientTransactionId,
  getWalletProviderForMethod,
  isDigitalWalletMethod,
  pickGatewayTransactionId,
} from "../utils/dashboardPaymentUtils";
import {
  buildPaymentSummary,
  extractOperationalErrorMessage,
  extractOperationalErrorType,
  isStaleCurrentOrderErrorType,
} from "../utils/dashboardOrderUtils";
import { groupIndexFromSlot, type SlotsMap } from "../utils/dashboardSlotUtils";

type PendingPaymentContext = Record<string, unknown>;

export type UseOperationalPaymentParams = {
  token: string;
  region: string;
  gatewayUrl: string;
  internalToken: string;
  orderPickupBase: string;
  selectedLocker: NormalizedLockerItem | null;
  currentOrder: CheckoutCurrentOrder | null;
  slots: SlotsMap;
  selectedSlot: number | null;
  slotSelectionRemainingSec: number;
  fetchOrdersOnce?: (targetPage?: number, targetPageSize?: number) => Promise<void>;
};

const CARD_METHODS = new Set([
  "CARTAO",
  "CREDIT_CARD",
  "DEBIT_CARD",
  "creditCard",
  "debitCard",
]);

function isCardMethod(method: unknown) {
  return CARD_METHODS.has(String(method || "").trim());
}

function resolveCardType(method: unknown, fallbackType: string) {
  const normalized = String(method || "").trim();
  if (normalized === "CREDIT_CARD" || normalized === "creditCard") return "creditCard";
  if (normalized === "DEBIT_CARD" || normalized === "debitCard") return "debitCard";
  return fallbackType;
}

function resolveInternalProvider(method: unknown) {
  const normalized = String(method || "").trim();
  const upper = normalized.toUpperCase();

  if (upper === "PIX") return "pix";
  if (upper === "MBWAY") return "mbway";
  if (upper === "MULTIBANCO_REFERENCE") return "multibanco_reference";
  if (upper === "NFC") return "nfc";
  if (upper === "APPLE_PAY") return "apple_pay";
  if (upper === "GOOGLE_PAY") return "google_pay";
  if (upper === "MERCADO_PAGO_WALLET") return "mercado_pago_wallet";

  if (upper === "CARTAO") {
    return "creditCard";
  }
  if (upper === "CREDIT_CARD") return "creditCard";
  if (upper === "DEBIT_CARD") return "debitCard";
  if (upper === "CREDITCARD") return "creditCard";
  if (upper === "DEBITCARD") return "debitCard";

  return normalized;
}

function resolveAmountCentsFromSlot(slots: SlotsMap | undefined, slotNum: number) {
  const slotAmount = Number(slots?.[slotNum]?.price_cents);
  return Number.isFinite(slotAmount) && slotAmount > 0 ? slotAmount : null;
}

function buildDefaultSkuId(region: string, slot: number, lockerId: string) {
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
  slots,
  selectedSlot,
  slotSelectionRemainingSec,
  fetchOrdersOnce,
}: UseOperationalPaymentParams) {
  const storeCurrentOrder = useCheckoutStore((state) => state.currentOrder);
  const setStoreCurrentOrder = useCheckoutStore((state) => state.setCurrentOrder);
  const setStorePayResp = useCheckoutStore((state) => state.setPayResp);
  const payResp = useCheckoutStore((state) => state.payResp?.message ?? "");

  const effectiveCurrentOrder = currentOrder || storeCurrentOrder;

  const [payMethod, setPayMethod] = useState("CARTAO");
  const [payValue, setPayValue] = useState(100);
  const [paySlot, setPaySlot] = useState(1);
  const [payLoading, setPayLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [pendingPaymentContext, setPendingPaymentContext] = useState<PendingPaymentContext | null>(
    null
  );
  const [cardType, setCardType] = useState("creditCard");
  const [customerPhone, setCustomerPhone] = useState("");
  const [walletProvider, setWalletProvider] = useState("");

  const setPayResp = useCallback(
    (message: string) => {
      const normalized = String(message || "");
      if (!normalized) {
        setStorePayResp(null);
        return;
      }
      setStorePayResp({
        status: "idle",
        message: normalized,
        raw: { source: "useOperationalPayment" },
      });
    },
    [setStorePayResp]
  );

  const availablePaymentMethods = useMemo(
    () => (Array.isArray(selectedLocker?.payment_methods) ? selectedLocker.payment_methods : []),
    [selectedLocker]
  );

  const isWalletMethodSelected = useMemo(
    () => isDigitalWalletMethod(payMethod),
    [payMethod]
  );

  useEffect(() => {
    if (isCardMethod(payMethod)) {
      setCardType((prev) => resolveCardType(payMethod, prev || "creditCard"));
    } else {
      setCardType("creditCard");
    }
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
    async (orderId: string, transactionId: string) => {
      if (!internalToken) {
        throw new Error("VITE_INTERNAL_TOKEN não configurado no frontend.");
      }

      if (!effectiveCurrentOrder) {
        throw new Error("Nenhum pedido atual carregado para confirmação interna.");
      }

      const orderRow = effectiveCurrentOrder as CheckoutCurrentOrder & Record<string, unknown>;
      const totemId = String(orderRow.totem_id ?? selectedLocker?.locker_id ?? "");
      const amountCents =
        typeof effectiveCurrentOrder.amount_cents === "number"
          ? effectiveCurrentOrder.amount_cents
          : Math.round(Number(payValue) * 100);

      const payload = {
        order_id: orderId,
        region,
        totem_id: totemId,
        channel: "ONLINE",
        provider: resolveInternalProvider(payMethod),
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
      effectiveCurrentOrder,
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

    if (payMethod === "MBWAY" && !customerPhone.trim()) {
      return { ok: false, orderError: "Informe o telefone para pagamento MB WAY." };
    }

    const slotNum = Number(selectedSlot);
    const realSkuId = slots?.[slotNum]?.sku_id;
    const skuId = realSkuId || buildDefaultSkuId(region, slotNum, selectedLocker.locker_id);
    const totemId = selectedLocker.locker_id;
    const amountCents = resolveAmountCentsFromSlot(slots, slotNum) ?? Math.round(Number(payValue) * 100);

    setOrderLoading(true);
    setPayResp("");
    setPendingPaymentContext(null);

    try {
      const payload: Record<string, unknown> = {
        region,
        sku_id: skuId,
        totem_id: totemId,
        desired_slot: slotNum,
        amount_cents: amountCents,
        payment_method: payMethod,
        payment_interface: "web_token",
      };

      if (isCardMethod(payMethod)) {
        payload.card_type = resolveCardType(payMethod, "creditCard");
      }

      if (payMethod === "MBWAY") {
        payload.customer_phone = customerPhone.trim();
      }

      const wallet = getWalletProviderForMethod(payMethod);
      if (wallet) {
        payload.wallet_provider = wallet;
      }

      const data = (await createOperationalOrder({
        orderPickupBase,
        token,
        payload,
      })) as Record<string, unknown>;

      if (typeof data?.amount_cents === "number") {
        setPayValue(Number(data.amount_cents) / 100);
      }

      if (data?.payment_method) {
        setPayMethod(String(data.payment_method));
        setWalletProvider(getWalletProviderForMethod(String(data.payment_method)));
      }

      setPayResp(JSON.stringify({ step: "order_created", response: data }, null, 2));
      await fetchOrdersOnce?.(1);

      const allocation = data?.allocation as Record<string, unknown> | undefined;
      const allocatedSlot = allocation?.slot ? Number(allocation.slot) : slotNum;

      const nextCurrentOrder = { ...data, totem_id: totemId } as unknown as CheckoutCurrentOrder;
      setStoreCurrentOrder(nextCurrentOrder);

      return {
        ok: true,
        currentOrder: nextCurrentOrder,
        selectedSlot: allocatedSlot,
        paySlot: allocatedSlot,
        activeGroup: groupIndexFromSlot(allocatedSlot),
        slotSelectionExpiresAt: null,
        orderError: "",
        pickupResp: "",
      };
    } catch (error: unknown) {
      return { ok: false, orderError: String(error instanceof Error ? error.message : error) };
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
    slots,
    selectedSlot,
    slotSelectionRemainingSec,
    token,
  ]);

  const simulatePayment = useCallback(async () => {
    if (!selectedLocker) {
      setPayResp("❌ Nenhum locker selecionado.");
      return { ok: false };
    }

    if (!effectiveCurrentOrder?.order_id) {
      setPayResp(
        "❌ Nenhum pedido atual carregado.\n\nAção recomendada: selecione uma gaveta disponível e clique em “Criar pedido online”."
      );
      return { ok: false };
    }

    if (effectiveCurrentOrder?.status === "PAID_PENDING_PICKUP") {
      setPayResp("⚠️ Este pedido já está pago.");
      return { ok: false };
    }

    if (effectiveCurrentOrder?.status === "PICKED_UP") { // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
      setPayResp("⚠️ Este pedido já foi retirado.");
      return { ok: false };
    }

    if (effectiveCurrentOrder?.status === "DISPENSED") { // máquina liberou - pickup.door_opened
      setPayResp("⚠️ Este pedido já foi retirado na máquina.");
      return { ok: false };
    }    

    if (!payMethod) {
      setPayResp("❌ Selecione um método de pagamento.");
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
      const simOrder = effectiveCurrentOrder as CheckoutCurrentOrder & Record<string, unknown>;
      const totemId = String(simOrder.totem_id ?? selectedLocker.locker_id);
      const transactionId = generateClientTransactionId();

      const payload: Record<string, unknown> = {
        regiao: region,
        canal: "ONLINE",
        metodo: payMethod,
        valor:
          typeof effectiveCurrentOrder.amount_cents === "number"
            ? Number(effectiveCurrentOrder.amount_cents) / 100
            : Number(payValue),
        porta: Number(
          (effectiveCurrentOrder as CheckoutCurrentOrder & { allocation?: { slot?: number } })
            ?.allocation?.slot || selectedSlot || paySlot || 0
        ),
        locker_id: totemId,
        order_id: effectiveCurrentOrder.order_id,
      };

      if (isCardMethod(payMethod)) {
        payload.card_type = resolveCardType(payMethod, "creditCard");
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
        const context: PendingPaymentContext = {
          ...pending,
          order_id: effectiveCurrentOrder.order_id,
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
        effectiveCurrentOrder.order_id,
        effectiveTransactionId
      );

      const summary = buildPaymentSummary({
        gatewayData,
        confirmData,
        region,
        currentOrderId: effectiveCurrentOrder.order_id,
        lockerId: totemId,
      });

      const extOrder = effectiveCurrentOrder as CheckoutCurrentOrder & Record<string, unknown>;
      const confirm = confirmData as Record<string, unknown> | null | undefined;
      const priorAlloc = (extOrder as Record<string, unknown>).allocation as
        | Record<string, unknown>
        | undefined;
      const nextCurrentOrder = {
        ...extOrder,
        status: "PAID_PENDING_PICKUP",
        paid_at: confirm?.paid_at || extOrder?.paid_at,
        pickup_id: confirm?.pickup_id || extOrder?.pickup_id,
        manual_code: confirm?.manual_code || extOrder?.manual_code,
        token_id: confirm?.token_id || extOrder?.token_id,
        pickup_status: confirm?.pickup_status || extOrder?.pickup_status,
        pickup_deadline_at:
          confirm?.pickup_deadline_at ||
          confirm?.pickup_expires_at ||
          extOrder?.pickup_deadline_at,
        allocation: {
          allocation_id: confirm?.allocation_id || priorAlloc?.allocation_id,
          slot: confirm?.slot || priorAlloc?.slot,
          state: confirm?.allocation_state || priorAlloc?.state,
        },
      } as CheckoutCurrentOrder;

      setStoreCurrentOrder(nextCurrentOrder);
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

      setPayResp(
        `❌ Erro ao simular/confirmar pagamento\n${String(error instanceof Error ? error.message : error)}`
      );
      return { ok: false };
    } finally {
      setPayLoading(false);
    }
  }, [
    cardType,
    confirmPaymentInternally,
    currentOrder,
    effectiveCurrentOrder,
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
    const pendingOid = pendingPaymentContext?.order_id;
    if (typeof pendingOid !== "string" || !pendingOid) {
      setPayResp("❌ Não há pagamento pendente aguardando confirmação.");
      return { ok: false };
    }

    setPayLoading(true);

    try {
      const txRaw = pendingPaymentContext.transaction_id;
      const confirmData = await confirmPaymentInternally(
        pendingOid,
        (typeof txRaw === "string" && txRaw) || generateClientTransactionId()
      );

      const confirmRec = confirmData as Record<string, unknown>;
      const summary = buildPaymentSummary({
        gatewayData: {
          payment: { currency: pendingPaymentContext.currency },
        } as Record<string, unknown>,
        confirmData: confirmRec,
        region,
        currentOrderId: pendingOid,
        lockerId:
          typeof pendingPaymentContext.locker_id === "string"
            ? pendingPaymentContext.locker_id
            : String(pendingPaymentContext.locker_id ?? ""),
      });

      const extEff = effectiveCurrentOrder as
        | (CheckoutCurrentOrder & Record<string, unknown>)
        | null;
      const pendingPriorAlloc = extEff
        ? ((extEff as Record<string, unknown>).allocation as Record<string, unknown> | undefined)
        : undefined;
      const nextCurrentOrder = extEff
        ? ({
            ...extEff,
            status: "PAID_PENDING_PICKUP",
            paid_at: confirmRec?.paid_at || extEff?.paid_at,
            pickup_id: confirmRec?.pickup_id || extEff?.pickup_id,
            manual_code: confirmRec?.manual_code || extEff?.manual_code,
            token_id: confirmRec?.token_id || extEff?.token_id,
            pickup_status: confirmRec?.pickup_status || extEff?.pickup_status,
            pickup_deadline_at:
              confirmRec?.pickup_deadline_at ||
              confirmRec?.pickup_expires_at ||
              extEff?.pickup_deadline_at,
            allocation: {
              allocation_id: confirmRec?.allocation_id || pendingPriorAlloc?.allocation_id,
              slot: confirmRec?.slot || pendingPriorAlloc?.slot,
              state: confirmRec?.allocation_state || pendingPriorAlloc?.state,
            },
          } as CheckoutCurrentOrder)
        : null;

      setStoreCurrentOrder(nextCurrentOrder);
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
    } catch (error: unknown) {
      setPayResp(
        `❌ Falha ao confirmar pagamento pendente\n${String(error instanceof Error ? error.message : error)}`
      );
      return { ok: false };
    } finally {
      setPayLoading(false);
    }
  }, [
    confirmPaymentInternally,
    currentOrder,
    effectiveCurrentOrder,
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
