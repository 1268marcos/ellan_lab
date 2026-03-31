// 01_source/frontend/src/features/locker-dashboard/utils/dashboardSlotUtils.js

import { DEFAULT_GROUP_SIZE, DEFAULT_SLOT_STATE } from "./dashboardConstants.js";

export function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

export function groupIndexFromSlot(slot, groupSize = DEFAULT_GROUP_SIZE) {
  return Math.floor((Number(slot) - 1) / groupSize);
}

export function groupSlots(groupIdx, groupSize = DEFAULT_GROUP_SIZE) {
  const start = groupIdx * groupSize + 1;
  return Array.from({ length: groupSize }, (_, index) => start + index);
}

export function slotsListToMap(list, totalSlots = 24) {
  const out = {};
  const safeTotalSlots = Math.max(1, Number(totalSlots) || 24);

  for (let i = 1; i <= safeTotalSlots; i += 1) {
    out[i] = { slot: i, ...DEFAULT_SLOT_STATE };
  }

  for (const item of list || []) {
    const slot = Number(item?.slot);
    if (!Number.isFinite(slot) || slot < 1 || slot > safeTotalSlots) continue;

    out[slot] = {
      slot,
      state: item?.state || DEFAULT_SLOT_STATE.state,
      product_id: item?.product_id ?? DEFAULT_SLOT_STATE.product_id,
      updated_at: item?.updated_at ?? DEFAULT_SLOT_STATE.updated_at,
    };
  }

  return out;
}

export function buildInitialCakes(totalSlots = 24) {
  const cakes = {};
  const safeTotalSlots = Math.max(1, Number(totalSlots) || 24);

  for (let i = 1; i <= safeTotalSlots; i += 1) {
    cakes[i] = { name: "", notes: "", imageUrl: "" };
  }

  return cakes;
}

export function normalizeSlotNumber(slot) {
  const value = Number(slot);
  if (!Number.isFinite(value) || value <= 0) return null;
  return Math.trunc(value);
}