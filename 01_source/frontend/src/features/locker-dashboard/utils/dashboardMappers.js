// 01_source/frontend/src/features/locker-dashboard/utils/dashboardMappers.js
// 16/04/2026 - inclusão de pickup_code_length


import { LOCKER_REGISTRY_FALLBACK } from "./dashboardConstants.js";

export function normalizeLockerItem(locker) {
  const address =
    locker?.address && typeof locker.address === "object"
      ? locker.address
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
    site_id: locker?.site_id || "",
    display_name: locker?.display_name || locker?.locker_id || locker?.id || "",
    backend_region: String(locker?.backend_region || locker?.region || "").toUpperCase(),
    slots: Number(locker?.slots || locker?.slots_count || 24),
    channels: Array.isArray(locker?.channels) ? locker.channels.map(String) : [],
    payment_methods: Array.isArray(locker?.payment_methods)
      ? locker.payment_methods.map((m) => String(m).trim()) //.toUpperCase()
      : typeof locker?.allowed_payment_methods === "string"
        ? locker.allowed_payment_methods.split(",").map((m) => String(m).trim()).filter(Boolean)
        : [],
    pickup_code_length: Number(locker?.pickup_code_length || 6),
    active: Boolean(locker?.active),
    country_code: String(locker?.country_code || "").trim().toUpperCase(),
    province_code: String(locker?.province_code || "").trim().toUpperCase(),
    address,
  };
}

export function buildFallbackLockersByRegion(region) {
  return Object.entries(LOCKER_REGISTRY_FALLBACK)
    .map(([lockerId, config]) =>
      normalizeLockerItem({
        locker_id: lockerId,
        ...config,
      })
    )
    .filter((item) => item.region === region && item.active)
    .sort((a, b) => a.display_name.localeCompare(b.display_name));
}

export function parseLockersResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.lockers)) return data.lockers;
  return [];
}