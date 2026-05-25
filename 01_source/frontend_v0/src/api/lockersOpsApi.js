const BASE = import.meta.env.VITE_OPS_LOCKERS_BASE_URL || "/api/v1/ops";

async function j(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json", ...(opts.body ? { "Content-Type": "application/json" } : {}) },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || res.statusText);
  }
  return res.json();
}

export const lockersOpsApi = {
  listLockers: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return j(`/lockers${q ? `?${q}` : ""}`);
  },
  getLocker: (id) => j(`/lockers/${encodeURIComponent(id)}`),
  getTelemetry: (id, hours = 24) => j(`/lockers/${encodeURIComponent(id)}/telemetry?hours=${hours}`),
  getMaintenance: (id) => j(`/lockers/${encodeURIComponent(id)}/maintenance`),
  createMaintenance: (id, body) =>
    j(`/lockers/${encodeURIComponent(id)}/maintenance`, { method: "POST", body: JSON.stringify(body) }),
  getPickups: (id) => j(`/lockers/${encodeURIComponent(id)}/pickups`),
  getOccupancy: () => j("/lockers/occupancy"),
  getAlerts: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return j(`/alerts${q ? `?${q}` : ""}`);
  },
};

export function opsRealtimeWsUrl(path) {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${path}`;
}
