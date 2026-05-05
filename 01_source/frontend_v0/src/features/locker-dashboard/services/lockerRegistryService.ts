
import {
  buildFallbackLockersByRegion,
  normalizeLockerItem,
  parseLockersResponse,
  type NormalizedLockerItem,
} from "../utils/dashboardMappers";
import { fetchGeoScopedLockerIdSet } from "../../../utils/lockerGeoFilter";

export async function fetchLockersByRegion({
  gatewayBase,
  region,
  orderPickupBase,
  channel = "ONLINE",
  tenant = "",
}: {
  gatewayBase: string;
  region: string;
  orderPickupBase: string;
  channel?: string;
  tenant?: string;
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

  const data = JSON.parse(text) as unknown;
  let items = parseLockersResponse(data)
    .map(normalizeLockerItem)
    .filter((item) => item.active);

  if (geoScope.lockerIds instanceof Set) {
    items = items.filter((item) => geoScope.lockerIds!.has(item.locker_id));
  }

  if ("lockerItems" in geoScope && Array.isArray(geoScope.lockerItems) && geoScope.lockerItems.length) {
    const geoMap = new Map(
      geoScope.lockerItems.map((item) => {
        const row = item as Record<string, unknown>;
        return [
          String(row?.locker_id || "").trim(),
          {
            country_code: String(row?.country_code || "").trim().toUpperCase(),
            province_code: String(row?.province_code || "").trim().toUpperCase(),
          },
        ] as const;
      })
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
}: {
  gatewayBase: string;
  region: string;
  orderPickupBase: string;
  channel?: string;
  tenant?: string;
}): Promise<{
  items: NormalizedLockerItem[];
  source: "gateway" | "gateway+geo" | "fallback";
  error: string;
}> {
  try {
    const result = await fetchLockersByRegion({ gatewayBase, region, orderPickupBase, channel, tenant });
    const geoApplied = result.geoScope.source === "geo-filter-applied";

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
      error: `Falha ao carregar lockers do gateway: ${String((error as Error)?.message || error)}`,
    };
  }
}

