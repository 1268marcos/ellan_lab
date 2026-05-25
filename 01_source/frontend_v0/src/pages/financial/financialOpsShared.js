export const PAGE_VERSION = "v0/financial v1.0";
export const FINANCIAL_API = import.meta.env.VITE_FINANCIAL_API_BASE || "/api/v1/financial";
export const ANALYTICS_API = `${import.meta.env.VITE_ANALYTICS_SERVICE_BASE_URL || "/api/analytics"}/api/v1/analytics`;

export const TAB_ITEMS = [
  { id: "dashboard", to: "/financial", label: "Executive Dashboard", end: true },
  { id: "pnl", to: "/financial/locker-pnl", label: "Locker P&L" },
  { id: "expansion", to: "/financial/expansion", label: "Expansion Simulator" },
  { id: "partners", to: "/financial/partners", label: "Partner Settlements" },
];

export function parseFinancialError(payload, fallback = "Falha na API financial.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  if (typeof payload?.error === "string" && payload.error.trim()) return payload.error.trim();
  return fallback;
}

export function normalizeFinancialError(err, endpoint = FINANCIAL_API) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicação com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexão (${endpoint}). Verifique analytics-service na porta 8127.`;
  }
  if (lower.includes("missing_bearer") || lower.includes("unauthorized")) {
    return "Sessão OPS inválida ou expirada. Faça login novamente.";
  }
  return raw;
}

export function financialHeaders(token) {
  const headers = {
    "X-Actor-Roles": "admin_operacao",
    "X-Service-Name": "frontend_v0_ops",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export function brlFromReais(value) {
  if (value == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
}

export function brlCents(cents) {
  if (cents == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(cents) / 100);
}

export function pct(value) {
  if (value == null) return "—";
  return `${Number(value).toFixed(1)}%`;
}
