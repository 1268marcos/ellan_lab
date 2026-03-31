// 01_source/frontend/src/features/locker-dashboard/hooks/useLockerSlotsSync.js
/**
 * * Responsável por:
 * buscar slots de um locker
 * polling
 * abort controller
 * syncEnabled, syncStatus
 * slots, setStateOnBackend
 * fetchSlotsOnce
 * 
 * Esse é um domínio completo sozinho.
 */ 

// 01_source/frontend/src/features/locker-dashboard/hooks/useLockerSlotsSync.js

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchLockerSlots, setLockerSlotState } from "../services/lockerSlotsService.js";
import { buildInitialCakes, slotsListToMap } from "../utils/dashboardSlotUtils.js";

export default function useLockerSlotsSync({
  backendBase,
  selectedLocker,
  syncEnabled = true,
  pollIntervalMs = 3000,
}) {
  const pollTimerRef = useRef(null);
  const abortRef = useRef(null);

  const totalSlots = Math.max(1, Number(selectedLocker?.slots) || 24);

  const [slots, setSlots] = useState(() => slotsListToMap([], totalSlots));
  const [cakes, setCakes] = useState(() => buildInitialCakes(totalSlots));
  const [syncStatus, setSyncStatus] = useState({ ok: true, msg: "—" });

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
      const data = await fetchLockerSlots({
        backendBase,
        lockerId: selectedLocker.locker_id,
        signal: controller.signal,
      });

      setSlots(slotsListToMap(data, totalSlots));
      setSyncStatus({
        ok: true,
        msg: `Atualizado ${new Date().toLocaleTimeString()} • ${selectedLocker.locker_id}`,
      });
    } catch (error) {
      if (String(error?.name) === "AbortError") return;
      setSyncStatus({ ok: false, msg: String(error?.message || error) });
    }
  }, [backendBase, selectedLocker, totalSlots]);

  const setStateOnBackend = useCallback(
    async (slot, nextState, onRefreshOrders) => {
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
          backendBase,
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
          (nextState === "PICKED_UP" || nextState === "PAID_PENDING_PICKUP")
        ) {
          onRefreshOrders();
        }
      } catch (error) {
        setSyncStatus({ ok: false, msg: `set-state erro: ${String(error?.message || error)}` });
        await fetchSlotsOnce();
      }
    },
    [backendBase, fetchSlotsOnce, selectedLocker, slots]
  );

  const updateCake = useCallback((slot, patch) => {
    setCakes((prev) => ({
      ...prev,
      [slot]: { ...prev[slot], ...patch },
    }));
  }, []);

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