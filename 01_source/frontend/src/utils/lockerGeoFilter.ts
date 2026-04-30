type UnknownRecord = Record<string, unknown>;

export type GeoSelection = { country_code: string; province_code: string };

const DEFAULT_REGION_GEO_FILTERS: Record<string, GeoSelection> = {
  "SP/KIOSK/TENANT_X": { country_code: "BR", province_code: "BR-SP" },
  "SP/ONLINE/TENANT_X": { country_code: "BR", province_code: "BR-SP" },
  "PT/KIOSK/TENANT_X": { country_code: "PT", province_code: "PT-13" },
  "PT/ONLINE/TENANT_X": { country_code: "PT", province_code: "PT-13" },
  "SP/KIOSK": { country_code: "BR", province_code: "BR-SP" },
  "SP/ONLINE": { country_code: "BR", province_code: "BR-SP" },
  "PT/KIOSK": { country_code: "PT", province_code: "PT-13" },
  "PT/ONLINE": { country_code: "PT", province_code: "PT-13" },
};

const GEO_TENANT_STORAGE_KEY = "ellan_geo_scope_tenant";
const GEO_TENANT_QUERY_PARAM = "geoTenant";
const GEO_TENANT_EVENT = "ellan:geo-tenant-changed";

function notifyTenantChange(tenant = "") {
  if (typeof window === "undefined") return;
  try {
    window.dispatchEvent(
      new CustomEvent(GEO_TENANT_EVENT, {
        detail: { tenant: String(tenant || "").trim().toUpperCase() },
      })
    );
  } catch (_e) {
    // no-op
  }
}

function parseRegionGeoFiltersFromEnv(): Record<string, unknown> {
  const raw = String(import.meta.env.VITE_REGION_GEO_FILTERS_JSON || "").trim();
  if (!raw) return DEFAULT_REGION_GEO_FILTERS;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return DEFAULT_REGION_GEO_FILTERS;
    return { ...DEFAULT_REGION_GEO_FILTERS, ...(parsed as UnknownRecord) };
  } catch (_e) {
    return DEFAULT_REGION_GEO_FILTERS;
  }
}

function normalizeGeoSelection(selected: unknown): GeoSelection {
  if (!selected || typeof selected !== "object") {
    return { country_code: "", province_code: "" };
  }
  const o = selected as UnknownRecord;
  return {
    country_code: String(o.country_code || "").trim().toUpperCase(),
    province_code: String(o.province_code || "").trim().toUpperCase(),
  };
}

function readTenantFromRuntimeOverride() {
  if (typeof window === "undefined") return "";
  const params = new URLSearchParams(window.location.search || "");
  const queryTenant = String(params.get(GEO_TENANT_QUERY_PARAM) || "").trim().toUpperCase();
  if (queryTenant) {
    try {
      window.localStorage.setItem(GEO_TENANT_STORAGE_KEY, queryTenant);
      notifyTenantChange(queryTenant);
    } catch (_e) {
      // no-op
    }
    return queryTenant;
  }
  try {
    return String(window.localStorage.getItem(GEO_TENANT_STORAGE_KEY) || "").trim().toUpperCase();
  } catch (_e) {
    return "";
  }
}

export function resolveGeoScopeTenant(defaultTenant = "") {
  const runtimeTenant = readTenantFromRuntimeOverride();
  if (runtimeTenant) return runtimeTenant;
  const envTenant = String(import.meta.env.VITE_GEO_SCOPE_TENANT || "").trim().toUpperCase();
  if (envTenant) return envTenant;
  return String(defaultTenant || "").trim().toUpperCase();
}

export function getRuntimeGeoScopeTenantOverride() {
  if (typeof window === "undefined") return "";
  try {
    return String(window.localStorage.getItem(GEO_TENANT_STORAGE_KEY) || "").trim().toUpperCase();
  } catch (_e) {
    return "";
  }
}

export function setRuntimeGeoScopeTenantOverride(tenant: unknown) {
  const normalized = String(tenant || "").trim().toUpperCase();
  if (typeof window === "undefined") return normalized;
  try {
    if (normalized) {
      window.localStorage.setItem(GEO_TENANT_STORAGE_KEY, normalized);
    } else {
      window.localStorage.removeItem(GEO_TENANT_STORAGE_KEY);
    }
    notifyTenantChange(normalized);
  } catch (_e) {
    // no-op
  }
  return normalized;
}

export function clearRuntimeGeoScopeTenantOverride() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(GEO_TENANT_STORAGE_KEY);
    notifyTenantChange("");
  } catch (_e) {
    // no-op
  }
}

export function listConfiguredGeoTenants() {
  const map = parseRegionGeoFiltersFromEnv();
  const out = new Set<string>();
  for (const key of Object.keys(map || {})) {
    const parts = String(key || "").split("/").filter(Boolean);
    if (parts.length >= 3) {
      out.add(String(parts[2]).trim().toUpperCase());
    }
  }
  const envTenant = String(import.meta.env.VITE_GEO_SCOPE_TENANT || "").trim().toUpperCase();
  if (envTenant) out.add(envTenant);
  return Array.from(out).filter(Boolean).sort();
}

function hasGeoLeaf(value: unknown) {
  return Boolean(
    value && typeof value === "object" && ("country_code" in value || "province_code" in value)
  );
}

function pickFromEntry(entry: UnknownRecord, channel: string, tenant: string): GeoSelection {
  if (!entry || typeof entry !== "object") return { country_code: "", province_code: "" };
  if (hasGeoLeaf(entry)) return normalizeGeoSelection(entry);

  if (channel && entry[channel]) {
    const channelEntry = entry[channel] as unknown;
    if (tenant && channelEntry && typeof channelEntry === "object") {
      const ce = channelEntry as UnknownRecord;
      if (ce[tenant]) {
        return normalizeGeoSelection(ce[tenant]);
      }
    }
    if (channelEntry && typeof channelEntry === "object") {
      const ce = channelEntry as UnknownRecord;
      if (ce.default) {
        return normalizeGeoSelection(ce.default);
      }
    }
    if (hasGeoLeaf(channelEntry)) {
      return normalizeGeoSelection(channelEntry);
    }
  }

  if (tenant && entry[tenant]) {
    return normalizeGeoSelection(entry[tenant]);
  }
  if (entry.default) {
    return normalizeGeoSelection(entry.default);
  }

  return { country_code: "", province_code: "" };
}

export function resolveGeoFilterForScope(region: unknown, channel = "", tenant = "") {
  const normalizedRegion = String(region || "").trim().toUpperCase();
  const normalizedChannel = String(channel || "").trim().toUpperCase();
  const normalizedTenant = resolveGeoScopeTenant(tenant);
  const map = parseRegionGeoFiltersFromEnv();

  if (normalizedRegion && normalizedChannel && normalizedTenant) {
    const key = `${normalizedRegion}/${normalizedChannel}/${normalizedTenant}`;
    if (map[key]) return normalizeGeoSelection(map[key]);
  }

  if (normalizedRegion && normalizedChannel) {
    const key = `${normalizedRegion}/${normalizedChannel}`;
    if (map[key]) return normalizeGeoSelection(map[key]);
  }

  if (normalizedRegion && normalizedTenant) {
    const key = `${normalizedRegion}/${normalizedTenant}`;
    if (map[key]) return normalizeGeoSelection(map[key]);
  }

  const regionEntry = map[normalizedRegion];
  if (regionEntry && typeof regionEntry === "object") {
    const picked = pickFromEntry(regionEntry as UnknownRecord, normalizedChannel, normalizedTenant);
    if (picked.country_code || picked.province_code) return picked;
  }

  return normalizeGeoSelection(map[normalizedRegion]);
}

export type GeoScopedLockerIdSet =
  | {
      lockerIds: null;
      lockerItems: unknown[];
      source: "geo-filter-skipped" | "geo-filter-fallback";
      reason?: string;
    }
  | {
      lockerIds: Set<string>;
      lockerItems: unknown[];
      source: "geo-filter-applied";
      countryCode: string;
      provinceCode: string;
      tenantCode: string;
    };

export async function fetchGeoScopedLockerIdSet({
  orderPickupBase,
  region,
  channel = "",
  tenant = "",
}: {
  orderPickupBase: string;
  region: string;
  channel?: string;
  tenant?: string;
}): Promise<GeoScopedLockerIdSet> {
  const resolvedTenant = resolveGeoScopeTenant(tenant);
  const geo = resolveGeoFilterForScope(region, channel, resolvedTenant);
  if (!geo.country_code && !geo.province_code) {
    return { lockerIds: null, lockerItems: [], source: "geo-filter-skipped" };
  }

  const params = new URLSearchParams();
  params.set("active_only", "true");
  if (geo.country_code) params.set("country_code", geo.country_code);
  if (geo.province_code) params.set("province_code", geo.province_code);
  const token = localStorage.getItem("ellan_public_auth_token");
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const res = await fetch(`${orderPickupBase}/dev-admin/base/lockers?${params.toString()}`, {
      headers,
    });
    const data = (await res.json().catch(() => ({}))) as { items?: unknown };
    if (!res.ok) {
      return { lockerIds: null, lockerItems: [], source: "geo-filter-fallback", reason: JSON.stringify(data) };
    }
    const items = Array.isArray(data?.items) ? data.items : [];
    const set = new Set(
      items
        .map((item) => String((item as UnknownRecord)?.locker_id || "").trim())
        .filter(Boolean)
    );
    return {
      lockerIds: set,
      lockerItems: items,
      source: "geo-filter-applied",
      countryCode: geo.country_code,
      provinceCode: geo.province_code,
      tenantCode: resolvedTenant,
    };
  } catch (e) {
    return {
      lockerIds: null,
      lockerItems: [],
      source: "geo-filter-fallback",
      reason: String((e as Error)?.message || e),
    };
  }
}
