import {
  FINANCIAL_API,
  financialHeaders,
  normalizeFinancialError,
  parseFinancialError,
} from "../pages/financial/financialOpsShared";

async function apiGet(path, token) {
  const res = await fetch(`${FINANCIAL_API}${path}`, { headers: financialHeaders(token) });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseFinancialError(body, normalizeFinancialError({ message: `HTTP ${res.status}` })));
  return body;
}

async function apiPost(path, payload, token) {
  const res = await fetch(`${FINANCIAL_API}${path}`, {
    method: "POST",
    headers: { ...financialHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseFinancialError(body));
  return body;
}

export const financialExecutiveApi = {
  kpis: (token) => apiGet("/kpis", token),
  lockerRoi: (params, token) => {
    const q = new URLSearchParams(params).toString();
    return apiGet(`/locker-roi${q ? `?${q}` : ""}`, token);
  },
  lockerPnl: (params, token) => {
    const q = new URLSearchParams(params).toString();
    return apiGet(`/locker-pnl${q ? `?${q}` : ""}`, token);
  },
  partnerRevenue: (params, token) => {
    const q = new URLSearchParams(params).toString();
    return apiGet(`/partner-revenue${q ? `?${q}` : ""}`, token);
  },
  revenueTrend: (months, token) => apiGet(`/revenue-trend?months=${months}`, token),
  simulateExpansion: (body, token) => apiPost("/simulate-expansion", body, token),
  exportUrl: (format, dataset) => `${FINANCIAL_API}/export/${format}?dataset=${encodeURIComponent(dataset)}`,
};
