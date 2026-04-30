import { LOCKER_REGISTRY_FALLBACK } from "./dashboardConstants";

type UnknownRecord = Record<string, unknown>;

export type NormalizedLockerItem = {
  locker_id: string;
  region: string;
  site_id: string;
  display_name: string;
  backend_region: string;
  slots: number;
  channels: string[];
  payment_methods: string[];
  pickup_code_length: number;
  active: boolean;
  country_code: string;
  province_code: string;
  address: UnknownRecord;
};

export function normalizeLockerItem(locker: UnknownRecord | null | undefined): NormalizedLockerItem {
  const address =
    locker?.address && typeof locker.address === "object"
      ? (locker.address as UnknownRecord)
      : {
          address: locker?.address || "",
          number: locker?.number ?? "",
          additional_information: locker?.additional_information || "",
          locality: locker?.locality || "",
          city: locker?.city || "",
          federative_unit: locker?.federative_unit || "",
          postal_code: locker?.postal_code || "",
          country: locker?.country || "",
        };

  return {
    locker_id: String(locker?.locker_id || locker?.id || locker?.external_id || "").trim(),
    region: String(locker?.region || "").toUpperCase(),
    site_id: String(locker?.site_id || ""),
    display_name: String(locker?.display_name || locker?.locker_id || locker?.id || ""),
    backend_region: String(locker?.backend_region || locker?.region || "").toUpperCase(),
    slots: Number(locker?.slots || locker?.slots_count || 24),
    channels: Array.isArray(locker?.channels) ? (locker.channels as unknown[]).map(String) : [],
    payment_methods: Array.isArray(locker?.payment_methods)
      ? (locker.payment_methods as unknown[]).map((m) => String(m).trim())
      : typeof locker?.allowed_payment_methods === "string"
        ? String(locker.allowed_payment_methods)
            .split(",")
            .map((m) => String(m).trim())
            .filter(Boolean)
        : [],
    pickup_code_length: Number(locker?.pickup_code_length || 6),
    active: Boolean(locker?.active),
    country_code: String(locker?.country_code || "")
      .trim()
      .toUpperCase(),
    province_code: String(locker?.province_code || "")
      .trim()
      .toUpperCase(),
    address,
  };
}

export function buildFallbackLockersByRegion(region: string): NormalizedLockerItem[] {
  return Object.entries(LOCKER_REGISTRY_FALLBACK)
    .map(([lockerId, config]) =>
      normalizeLockerItem({
        locker_id: lockerId,
        ...(config as UnknownRecord),
      })
    )
    .filter((item) => item.region === region && item.active)
    .sort((a, b) => a.display_name.localeCompare(b.display_name));
}

export function parseLockersResponse(data: unknown): UnknownRecord[] {
  if (Array.isArray(data)) return data as UnknownRecord[];
  const o = data as { items?: unknown; lockers?: unknown } | null | undefined;
  if (Array.isArray(o?.items)) return o.items as UnknownRecord[];
  if (Array.isArray(o?.lockers)) return o.lockers as UnknownRecord[];
  return [];
}
