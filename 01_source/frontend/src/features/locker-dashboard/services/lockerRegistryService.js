// 01_source/frontend/src/features/locker-dashboard/services/lockerRegistryService.js

import {
  buildFallbackLockersByRegion,
  normalizeLockerItem,
  parseLockersResponse,
} from "../utils/dashboardMappers.js";

export async function fetchLockersByRegion({
  gatewayBase,
  region,
}) {
  const res = await fetch(
    `${gatewayBase}/lockers?region=${encodeURIComponent(region)}&active_only=true`
  );

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const data = JSON.parse(text);
  const items = parseLockersResponse(data)
    .map(normalizeLockerItem)
    .filter((item) => item.active);

  if (!items.length) {
    throw new Error(`Nenhum locker ativo retornado pelo gateway para a região ${region}.`);
  }

  return items;
}

export async function fetchLockersWithFallback({
  gatewayBase,
  region,
}) {
  try {
    const items = await fetchLockersByRegion({ gatewayBase, region });

    return {
      items,
      source: "gateway",
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