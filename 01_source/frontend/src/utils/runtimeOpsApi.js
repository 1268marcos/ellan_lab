/** Base path proxied by Vite to backend_runtime (port 8200). */
export const RUNTIME_OPS_PROXY_PREFIX = "/api/rt";

export async function fetchRuntimeJson(path, options = {}) {
  const { headers: extraHeaders = {}, ...init } = options;
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const res = await fetch(`${RUNTIME_OPS_PROXY_PREFIX}${normalized}`, {
    ...init,
    headers: { Accept: "application/json", ...extraHeaders },
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { _raw: text, _parse_error: true };
  }
  if (!res.ok) {
    const msg =
      (data && typeof data.detail === "object" && data.detail?.message) ||
      (typeof data?.detail === "string" && data.detail) ||
      data?.message ||
      `HTTP ${res.status}`;
    const err = new Error(String(msg));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}
