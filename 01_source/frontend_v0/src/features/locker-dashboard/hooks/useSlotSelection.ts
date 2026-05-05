
/**
 * Responsável por:
 * selectedSlot, activeGroup, slotSelectionExpiresAt, slotSelectionRemainingSec,
 * timeout da seleção, selectSlot, clearSlotSelection
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import type { CheckoutCurrentOrder } from "../../checkout/types";
import { groupIndexFromSlot, groupSlots, type SlotsMap } from "../utils/dashboardSlotUtils";

export type UseSlotSelectionParams = {
  slots: SlotsMap;
  totalSlots?: number;
  currentOrder: CheckoutCurrentOrder | null;
  selectionTimeoutMs?: number;
};

export default function useSlotSelection({
  slots,
  totalSlots = 24,
  currentOrder,
  selectionTimeoutMs = 45_000,
}: UseSlotSelectionParams) {
  const [selectedSlot, setSelectedSlot] = useState<number | null>(null);
  const [activeGroup, setActiveGroup] = useState(0);
  const [slotSelectionExpiresAt, setSlotSelectionExpiresAt] = useState<number | null>(null);
  const [slotSelectionTick, setSlotSelectionTick] = useState(0);

  const selectedSlotState = selectedSlot ? slots[selectedSlot]?.state || "AVAILABLE" : null;

  const slotSelectionRemainingSec = useMemo(() => {
    if (!slotSelectionExpiresAt) return 0;
    return Math.max(0, Math.ceil((slotSelectionExpiresAt - Date.now()) / 1000));
  }, [slotSelectionExpiresAt, slotSelectionTick]);

  const hasActiveSlotSelection = useMemo(
    () =>
      !!selectedSlot &&
      !currentOrder &&
      !!slotSelectionExpiresAt &&
      slotSelectionRemainingSec > 0,
    [currentOrder, selectedSlot, slotSelectionExpiresAt, slotSelectionRemainingSec]
  );

  const totalGroups = useMemo(
    () => Math.max(1, Math.ceil((Number(totalSlots) || 0) / 4)),
    [totalSlots]
  );
  const maxGroupIndex = totalGroups - 1;

  const groupSlotsList = useMemo(() => groupSlots(activeGroup), [activeGroup]);

  const selectSlot = useCallback(
    (slot: number) => {
      const slotState = slots[slot]?.state || "AVAILABLE";
      if (slotState !== "AVAILABLE") return false;

      setSelectedSlot(slot);
      setActiveGroup(groupIndexFromSlot(slot));
      setSlotSelectionExpiresAt(Date.now() + selectionTimeoutMs);
      return true;
    },
    [selectionTimeoutMs, slots]
  );

  const clearSlotSelection = useCallback(() => {
    setSelectedSlot(null);
    setSlotSelectionExpiresAt(null);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setSlotSelectionTick((value) => value + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!slotSelectionExpiresAt) return;
    if (Date.now() < slotSelectionExpiresAt) return;

    setSelectedSlot(null);
    setSlotSelectionExpiresAt(null);
  }, [slotSelectionExpiresAt, slotSelectionTick]);

  useEffect(() => {
    setActiveGroup((prev) => Math.min(prev, maxGroupIndex));
  }, [maxGroupIndex]);

  return {
    selectedSlot,
    setSelectedSlot,
    activeGroup,
    setActiveGroup,
    slotSelectionExpiresAt,
    setSlotSelectionExpiresAt,
    slotSelectionRemainingSec,
    hasActiveSlotSelection,
    selectedSlotState,
    groupSlotsList,
    selectSlot,
    clearSlotSelection,
  };
}
