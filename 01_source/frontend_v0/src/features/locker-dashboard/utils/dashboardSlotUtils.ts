
import { DEFAULT_GROUP_SIZE, DEFAULT_SLOT_STATE } from "./dashboardConstants";

export function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export function groupIndexFromSlot(slot: unknown, groupSize = DEFAULT_GROUP_SIZE) {
  return Math.floor((Number(slot) - 1) / groupSize);
}

export function groupSlots(groupIdx: number, groupSize = DEFAULT_GROUP_SIZE) {
  const start = groupIdx * groupSize + 1;
  return Array.from({ length: groupSize }, (_, index) => start + index);
}

export type SlotRowState = {
  slot: number;
  state: string;
  product_id: string | null;
  updated_at: string | null;
  /** Campos opcionais após merge com catálogo (locker dashboard). */
  sku_id?: string | null;
  name?: string | null;
  price_cents?: number | null;
  is_active?: boolean;
  catalog_updated_at?: string | null;
};

export type SlotsMap = Record<number, SlotRowState>;

export function slotsListToMap(
  list: Iterable<Record<string, unknown>> | null | undefined,
  totalSlots = 24
): SlotsMap {
  const out: SlotsMap = {};
  const safeTotalSlots = Math.max(1, Number(totalSlots) || 24);

  for (let i = 1; i <= safeTotalSlots; i += 1) {
    out[i] = { slot: i, ...DEFAULT_SLOT_STATE };
  }

  for (const item of list || []) {
    const slot = Number(item?.slot);
    if (!Number.isFinite(slot) || slot < 1 || slot > safeTotalSlots) continue;

    out[slot] = {
      slot,
      state: String(item?.state || DEFAULT_SLOT_STATE.state),
      product_id: (item?.product_id as string | null | undefined) ?? DEFAULT_SLOT_STATE.product_id,
      updated_at: (item?.updated_at as string | null | undefined) ?? DEFAULT_SLOT_STATE.updated_at,
    };
  }

  return out;
}

export function buildInitialCakes(totalSlots = 24): Record<number, { name: string; notes: string; imageUrl: string }> {
  const cakes: Record<number, { name: string; notes: string; imageUrl: string }> = {};
  const safeTotalSlots = Math.max(1, Number(totalSlots) || 24);

  for (let i = 1; i <= safeTotalSlots; i += 1) {
    cakes[i] = { name: "", notes: "", imageUrl: "" };
  }

  return cakes;
}

export function normalizeSlotNumber(slot: unknown) {
  const value = Number(slot);
  if (!Number.isFinite(value) || value <= 0) return null;
  return Math.trunc(value);
}
