
/** Base URL do order_lifecycle_service (dev: proxy Vite `/api/ol`). */
export function getOrderLifecycleBase() {
  const fromEnv = String(import.meta.env.VITE_ORDER_LIFECYCLE_BASE_URL || "").trim();
  if (fromEnv) return fromEnv;
  if (import.meta.env.DEV) return "/api/ol";
  return "http://localhost:8010";
}

export async function olFetch(path, init = {}) {
  const token = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();
  const headers = new Headers(init.headers || {});
  if (token) headers.set("X-Internal-Token", token);
  const base = getOrderLifecycleBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  const res = await fetch(`${base}${p}`, { ...init, headers });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`HTTP ${res.status}: ${t.slice(0, 240)}`);
  }
  return res.json();
}

