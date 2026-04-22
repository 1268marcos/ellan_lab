// 01_source/frontend/src/features/locker-dashboard/services/lockerRegistryService.js

import {
  buildFallbackLockersByRegion,
  normalizeLockerItem,
  parseLockersResponse,
} from "../utils/dashboardMappers.js";
import { fetchGeoScopedLockerIdSet } from "../../../utils/lockerGeoFilter.js";

export async function fetchLockersByRegion({
  gatewayBase,
  region,
  orderPickupBase,
  channel = "ONLINE",
  tenant = "",
}) {
  const geoScope = await fetchGeoScopedLockerIdSet({
    orderPickupBase,
    region,
    channel,
    tenant,
  });

  const res = await fetch(
    `${gatewayBase}/lockers?region=${encodeURIComponent(region)}&active_only=true`
  );

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const data = JSON.parse(text);
  let items = parseLockersResponse(data)
    .map(normalizeLockerItem)
    .filter((item) => item.active);

  if (geoScope?.lockerIds instanceof Set) {
    items = items.filter((item) => geoScope.lockerIds.has(item.locker_id));
  }

  if (geoScope?.lockerItems?.length) {
    const geoMap = new Map(
      geoScope.lockerItems.map((item) => [
        String(item?.locker_id || "").trim(),
        {
          country_code: String(item?.country_code || "").trim().toUpperCase(),
          province_code: String(item?.province_code || "").trim().toUpperCase(),
        },
      ])
    );
    items = items.map((item) => ({
      ...item,
      country_code: geoMap.get(item.locker_id)?.country_code || item.country_code || "",
      province_code: geoMap.get(item.locker_id)?.province_code || item.province_code || "",
    }));
  }

  if (!items.length) {
    throw new Error(`Nenhum locker ativo para o escopo da região ${region}.`);
  }

  return {
    items,
    geoScope,
  };
}

export async function fetchLockersWithFallback({
  gatewayBase,
  region,
  orderPickupBase,
  channel = "ONLINE",
  tenant = "",
}) {
  try {
    const result = await fetchLockersByRegion({ gatewayBase, region, orderPickupBase, channel, tenant });
    const geoApplied = result?.geoScope?.source === "geo-filter-applied";

    return {
      items: result.items,
      source: geoApplied ? "gateway+geo" : "gateway",
      error: "",
    };
  } catch (error) {
    const fallbackItems = buildFallbackLockersByRegion(region);

    return {
      items: fallbackItems,
      source: "fallback",
      error: `Falha ao carregar lockers do gateway: ${String(error?.message || error)}`,
    };
  }
}