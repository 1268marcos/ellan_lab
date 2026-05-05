
/**
 * Responsável por: regenerateManualCode, pickupResp, regenCodeLoading,
 * callbacks de redeem manual/QR
 */

import { useCallback, useState } from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import { regeneratePickupToken } from "../services/operationalPickupService";
import { buildManualCodeSummary, buildRedeemSummary } from "../utils/dashboardOrderUtils";

export type UseOperationalPickupParams = {
  token: string;
  region: string;
  orderPickupBase: string;
  fetchOrdersOnce?: (targetPage?: number, targetPageSize?: number) => Promise<void>;
  currentOrder?: CheckoutCurrentOrder | null;
  setCurrentOrder?: (
    order:
      | CheckoutCurrentOrder
      | null
      | ((prev: CheckoutCurrentOrder | null) => CheckoutCurrentOrder | null)
  ) => void;
};

export default function useOperationalPickup({
  token,
  region,
  orderPickupBase,
  currentOrder: currentOrderProp,
  setCurrentOrder: setCurrentOrderProp,
  fetchOrdersOnce,
}: UseOperationalPickupParams) {
  const storeCurrentOrder = useCheckoutStore((state) => state.currentOrder);
  const setStoreCurrentOrder = useCheckoutStore((state) => state.setCurrentOrder);
  const setStorePickupResp = useCheckoutStore((state) => state.setPickupResp);
  const pickupResp = useCheckoutStore((state) => state.pickupResp?.message ?? "");

  const effectiveCurrentOrder = currentOrderProp ?? storeCurrentOrder;
  const effectiveSetCurrentOrder = setCurrentOrderProp ?? setStoreCurrentOrder;

  const [regenCodeLoading, setRegenCodeLoading] = useState(false);

  const setPickupResp = useCallback(
    (message: string) => {
      const normalized = String(message || "");
      if (!normalized) {
        setStorePickupResp(null);
        return;
      }
      setStorePickupResp({
        status: "idle",
        message: normalized,
        raw: { source: "useOperationalPickup" },
      });
    },
    [setStorePickupResp]
  );

  const regenerateManualCode = useCallback(async () => {
    if (!effectiveCurrentOrder?.order_id) {
      setPickupResp(
        "❌ Nenhum pedido selecionado para regenerar código.\n\nAção recomendada: selecione um pedido pago aguardando retirada."
      );
      return;
    }

    if (effectiveCurrentOrder?.status !== "PAID_PENDING_PICKUP") {
      setPickupResp(
        "❌ Só é possível regenerar código para pedido em PAID_PENDING_PICKUP.\n\nVerifique o status do pedido atual."
      );
      return;
    }

    setRegenCodeLoading(true);

    try {
      const data = await regeneratePickupToken({
        orderPickupBase,
        token,
        orderId: effectiveCurrentOrder.order_id,
      });
      const dataRec = data as Record<string, unknown>;

      effectiveSetCurrentOrder((prev) =>
        prev
          ? ({
              ...prev,
              manual_code: String(dataRec.manual_code ?? prev.manual_code ?? ""),
              pickup_id: String(dataRec.pickup_id ?? prev.pickup_id ?? ""),
              ...(typeof dataRec.token_id === "string" ? { token_id: dataRec.token_id } : {}),
              ...(dataRec.expires_at != null
                ? {
                    expires_at: dataRec.expires_at,
                    pickup_deadline_at: dataRec.expires_at,
                  }
                : {}),
            } as unknown as CheckoutCurrentOrder)
          : prev
      );

      const summary = buildManualCodeSummary(data, region);

      setPickupResp(
        `${summary}\n\n--- JSON bruto ---\n${JSON.stringify(
          {
            step: "manual_code_regenerated",
            response: data,
            security_note:
              "Códigos anteriores foram invalidados; use somente o código recém-gerado.",
          },
          null,
          2
        )}`
      );

      await fetchOrdersOnce?.(1);
    } catch (error: unknown) {
      setPickupResp(
        `❌ Erro ao regenerar código manual\n${String(error instanceof Error ? error.message : error)}`
      );
    } finally {
      setRegenCodeLoading(false);
    }
  }, [
    effectiveCurrentOrder,
    effectiveSetCurrentOrder,
    fetchOrdersOnce,
    orderPickupBase,
    region,
    token,
    setPickupResp,
  ]);

  const handleManualRedeemSuccess = useCallback(
    async (data: Record<string, unknown>) => {
      effectiveSetCurrentOrder((prev) =>
        prev
          ? (() => {
              const prevRow = prev as CheckoutCurrentOrder & Record<string, unknown>;
              const prevAlloc = prevRow.allocation as Record<string, unknown> | undefined;
              return {
                ...prev,
                status: "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
                picked_up_at: (data.picked_up_at as string | undefined) || new Date().toISOString(),
                pickup_status: (data.pickup_status as string | undefined) || "REDEEMED",
                allocation: {
                  allocation_id: prevAlloc?.allocation_id,
                  slot: data.slot ?? prevAlloc?.slot,
                  state: data.allocation_state || "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
                },
              } as unknown as CheckoutCurrentOrder;
            })()
          : prev
      );

      const summary = buildRedeemSummary(data, region, "manual");
      setPickupResp(
        `${summary}\n\n--- JSON bruto ---\n${JSON.stringify(
          {
            step: "manual_redeem_success",
            response: data,
          },
          null,
          2
        )}`
      );

      await fetchOrdersOnce?.(1);
    },
    [effectiveSetCurrentOrder, fetchOrdersOnce, region, setPickupResp]
  );

  const handleQrRedeemSuccess = useCallback(
    async (data: Record<string, unknown>) => {
      effectiveSetCurrentOrder((prev) =>
        prev
          ? (() => {
              const prevRow = prev as CheckoutCurrentOrder & Record<string, unknown>;
              const prevAlloc = prevRow.allocation as Record<string, unknown> | undefined;
              return {
                ...prev,
                status: "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
                picked_up_at: (data.picked_up_at as string | undefined) || new Date().toISOString(),
                pickup_status: (data.pickup_status as string | undefined) || "REDEEMED",
                allocation: {
                  allocation_id: prevAlloc?.allocation_id,
                  slot: data.slot ?? prevAlloc?.slot,
                  state: data.allocation_state || "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
                },
              } as unknown as CheckoutCurrentOrder;
            })()
          : prev
      );

      const summary = buildRedeemSummary(data, region, "qr");
      setPickupResp(
        `${summary}\n\n--- JSON bruto ---\n${JSON.stringify(
          {
            step: "qr_redeem_success",
            response: data,
          },
          null,
          2
        )}`
      );

      await fetchOrdersOnce?.(1);
    },
    [effectiveSetCurrentOrder, fetchOrdersOnce, region, setPickupResp]
  );

  return {
    pickupResp,
    setPickupResp,
    regenCodeLoading,
    regenerateManualCode,
    handleManualRedeemSuccess,
    handleQrRedeemSuccess,
  };
}

