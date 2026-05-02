/** Base URL do billing_fiscal_service (dev: Vite proxy `/api/bf` → :8020). */
export const BILLING_FISCAL_BASE =
  String(import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "").trim() || "/api/bf";

export function billingFiscalHeaders(token) {
  const internal = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(internal ? { "X-Internal-Token": internal } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function parseBillingFiscalError(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (typeof payload?.message === "string" && payload.message.trim()) return payload.message.trim();
  return fallback;
}

export async function billingFiscalGet(path, token) {
  const url = `${BILLING_FISCAL_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { method: "GET", headers: billingFiscalHeaders(token) });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseBillingFiscalError(payload, `HTTP ${res.status}`));
  return payload;
}

export const bfPageStyle = {
  width: "100%",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};
export const bfCardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
};
export const bfMuted = { color: "rgba(245,247,250,0.8)", marginTop: 0, marginBottom: 8 };
export const bfLabel = { display: "grid", gap: 4, fontSize: 12, color: "#dbeafe" };
export const bfInput = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};
export const bfRow = { marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" };
export const bfBtn = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(31,122,63,0.50)",
  background: "#1f7a3f",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
};
export const bfErr = {
  marginTop: 12,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};
export const bfTableWrap = { overflowX: "auto", marginTop: 12 };
export const bfTable = { width: "100%", borderCollapse: "collapse", minWidth: 640, fontSize: 12 };
export const bfTh = { textAlign: "left", borderBottom: "1px solid rgba(255,255,255,0.14)", padding: "8px 10px" };
export const bfTd = { borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "8px 10px", verticalAlign: "top" };
