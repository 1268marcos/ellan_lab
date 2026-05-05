
/**
 * Responsável por: buscar slots, polling, abort, syncStatus, setStateOnBackend, fetchSlotsOnce
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useCheckoutStore } from "../../../store/useCheckoutStore";
import type { NormalizedLockerItem } from "../utils/dashboardMappers";
import {
  fetchCatalogSlots,
  fetchLockerSlots,
  setLockerSlotState,
} from "../services/lockerSlotsService";
import { buildInitialCakes, slotsListToMap, type SlotsMap } from "../utils/dashboardSlotUtils";

function mergeCatalogWithLockerStates({
  catalogRows,
  lockerRows,
  totalSlots,
}: {
  catalogRows: Iterable<Record<string, unknown>> | null | undefined;
  lockerRows: Iterable<Record<string, unknown>> | null | undefined;
  totalSlots: number;
}): SlotsMap {
  const merged = slotsListToMap(lockerRows, totalSlots);
  const safeCatalogRows = Array.isArray(catalogRows) ? catalogRows : [];

  for (const item of safeCatalogRows) {
    const slot = Number(item?.slot);
    if (!Number.isFinite(slot) || slot < 1 || slot > totalSlots) continue;

    merged[slot] = {
      ...merged[slot],
      sku_id: item?.sku_id || null,
      name: item?.name || null,
      price_cents: Number.isFinite(Number(item?.amount_cents))
        ? Number(item.amount_cents)
        : Number.isFinite(Number(item?.price_cents))
          ? Number(item.price_cents)
          : null,
      is_active: Boolean(item?.is_active),
      catalog_updated_at: item?.updated_at || null,
    };
  }

  return merged;
}

export type UseLockerSlotsSyncParams = {
  runtimeBase: string;
  selectedLocker: NormalizedLockerItem | null;
  syncEnabled?: boolean;
  pollIntervalMs?: number;
};

export default function useLockerSlotsSync({
  runtimeBase,
  selectedLocker,
  syncEnabled = true,
  pollIntervalMs = 3000,
}: UseLockerSlotsSyncParams) {
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const syncStatus = useCheckoutStore((s) => s.syncStatus);
  const setSyncStatus = useCheckoutStore((s) => s.setSyncStatus);

  const totalSlots = Math.max(1, Number(selectedLocker?.slots) || 24);

  const [slots, setSlots] = useState<SlotsMap>(() => slotsListToMap([], totalSlots));
  const [cakes, setCakes] = useState(() => buildInitialCakes(totalSlots));

  useEffect(() => {
    setSlots(slotsListToMap([], totalSlots));
    setCakes((prev) => {
      const next = buildInitialCakes(totalSlots);
      for (let i = 1; i <= totalSlots; i += 1) {
        if (prev[i]) next[i] = prev[i];
      }
      return next;
    });
  }, [totalSlots, selectedLocker?.locker_id]);

  const fetchSlotsOnce = useCallback(async () => {
    if (!selectedLocker) {
      setSlots(slotsListToMap([], totalSlots));
      return;
    }

    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const [lockerData, catalogData] = await Promise.all([
        fetchLockerSlots({
          backendBase: runtimeBase,
          lockerId: selectedLocker.locker_id,
          signal: controller.signal,
        }),
        fetchCatalogSlots({
          backendBase: runtimeBase,
          lockerId: selectedLocker.locker_id,
          signal: controller.signal,
        }).catch(() => []),
      ]);

      setSlots(
        mergeCatalogWithLockerStates({
          catalogRows: catalogData as Iterable<Record<string, unknown>>,
          lockerRows: lockerData as Iterable<Record<string, unknown>>,
          totalSlots,
        })
      );
      setSyncStatus({
        ok: true,
        msg: `Atualizado ${new Date().toLocaleTimeString()} • ${selectedLocker.locker_id}`,
      });
    } catch (error: unknown) {
      if (String(error instanceof Error ? error.name : "") === "AbortError") return;
      setSyncStatus({
        ok: false,
        msg: String(error instanceof Error ? error.message : error),
      });
    }
  }, [runtimeBase, selectedLocker, totalSlots]);

  const setStateOnBackend = useCallback(
    async (
      slot: number,
      nextState: string,
      onRefreshOrders?: (() => void) | null | undefined
    ) => {
      if (!slot || !selectedLocker) return;

      const payload = {
        state: nextState,
        product_id: slots[slot]?.product_id ?? null,
      };

      setSlots((prev) => ({
        ...prev,
        [slot]: { ...prev[slot], state: nextState },
      }));

      try {
        await setLockerSlotState({
          backendBase: runtimeBase,
          lockerId: selectedLocker.locker_id,
          slot,
          payload,
        });

        setSyncStatus({
          ok: true,
          msg: `set-state OK (${selectedLocker.locker_id} • ${slot} → ${nextState})`,
        });

        if (
          typeof onRefreshOrders === "function" &&
          (nextState === "PICKED_UP" || nextState === "PAID_PENDING_PICKUP") // PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
        ) {
          onRefreshOrders();
        }
      } catch (error: unknown) {
        setSyncStatus({
          ok: false,
          msg: `set-state erro: ${String(error instanceof Error ? error.message : error)}`,
        });
        await fetchSlotsOnce();
      }
    },
    [fetchSlotsOnce, runtimeBase, selectedLocker, slots]
  );

  const updateCake = useCallback(
    (slot: number, patch: Partial<{ name: string; notes: string; imageUrl: string }>) => {
      setCakes((prev) => ({
        ...prev,
        [slot]: { ...prev[slot], ...patch },
      }));
    },
    []
  );

  useEffect(() => {
    fetchSlotsOnce();

    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
    }

    if (syncEnabled) {
      pollTimerRef.current = setInterval(() => {
        fetchSlotsOnce();
      }, pollIntervalMs);
    }

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [fetchSlotsOnce, pollIntervalMs, syncEnabled]);

  const slotEntries = useMemo(
    () => Object.values(slots).sort((a, b) => Number(a.slot) - Number(b.slot)),
    [slots]
  );

  return {
    slots,
    slotEntries,
    cakes,
    updateCake,
    syncStatus,
    setSyncStatus,
    fetchSlotsOnce,
    setStateOnBackend,
    totalSlots,
  };
}
