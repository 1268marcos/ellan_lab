// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPickup.js
/**
 * * Responsável por:
 * regenerateManualCode
 * pickupResp
 * regenCodeLoading
 * callbacks de redeem manual/QR
 * integração com PickupQRCodePanel e ManualPickupPanel
 */

// 01_source/frontend/src/features/locker-dashboard/hooks/useOperationalPickup.js

import { useCallback, useState } from "react";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import { regeneratePickupToken } from "../services/operationalPickupService.js";
import { buildManualCodeSummary, buildRedeemSummary } from "../utils/dashboardOrderUtils.js";

export default function useOperationalPickup({
  token,
  region,
  orderPickupBase,
  currentOrder,
  setCurrentOrder,
  fetchOrdersOnce,
}) {
  const storeCurrentOrder = useCheckoutStore((state) => state.currentOrder);
  const setStoreCurrentOrder = useCheckoutStore((state) => state.setCurrentOrder);
  const setStorePickupResp = useCheckoutStore((state) => state.setPickupResp);

  const effectiveCurrentOrder = currentOrder || storeCurrentOrder;
  const effectiveSetCurrentOrder = setCurrentOrder || setStoreCurrentOrder;

  const [pickupResp, setPickupRespLocal] = useState("");
  const [regenCodeLoading, setRegenCodeLoading] = useState(false);

  const setPickupResp = useCallback(
    (message) => {
      const normalized = String(message || "");
      setPickupRespLocal(normalized);
      if (!normalized) {
        setStorePickupResp(null);
        return;
      }
      setStorePickupResp({
        status: "idle",
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

      effectiveSetCurrentOrder((prev) =>
        prev
          ? {
              ...prev,
              manual_code: data?.manual_code || prev.manual_code,
              pickup_id: data?.pickup_id || prev.pickup_id,
              token_id: data?.token_id || prev.token_id,
              expires_at: data?.expires_at || prev.expires_at,
              pickup_deadline_at: data?.expires_at || prev.pickup_deadline_at,
            }
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
    } catch (error) {
      setPickupResp(`❌ Erro ao regenerar código manual\n${String(error?.message || error)}`);
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
    async (data) => {
      effectiveSetCurrentOrder((prev) =>
        prev
          ? {
              ...prev,
              status: "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
              picked_up_at: data?.picked_up_at || new Date().toISOString(),
              pickup_status: data?.pickup_status || "REDEEMED",
              allocation: {
                allocation_id: prev?.allocation?.allocation_id,
                slot: data?.slot || prev?.allocation?.slot,
                state: data?.allocation_state || "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
              },
            }
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
    async (data) => {
      effectiveSetCurrentOrder((prev) =>
        prev
          ? {
              ...prev,
              status: "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
              picked_up_at: data?.picked_up_at || new Date().toISOString(),
              pickup_status: data?.pickup_status || "REDEEMED",
              allocation: {
                allocation_id: prev?.allocation?.allocation_id,
                slot: data?.slot || prev?.allocation?.slot,
                state: data?.allocation_state || "PICKED_UP", // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
              },
            }
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
