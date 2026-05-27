const BASE =
  import.meta.env.VITE_ORDER_PICKUP_PROXY ||
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL ||
  "/api/op";

function formatApiError(res, payload) {
  const status = res.status;
  if (status === 502 || status === 503 || status === 504) {
    return "order_pickup_service indisponível (porta 8003). Verifique se o serviço está rodando e clique em Atualizar.";
  }
  if (status === 401) {
    return "Sessão expirada ou token inválido — faça login novamente.";
  }
  if (status === 403) {
    const detail = payload?.detail;
    if (detail && typeof detail === "object") {
      const roles = Array.isArray(detail.allowed_roles) ? detail.allowed_roles.join(", ") : "";
      const base = detail.message || "Sem permissão para monitoramento OPS.";
      return roles ? `${base} Roles exigidas: ${roles}.` : base;
    }
    return "Sem permissão para monitoramento OPS.";
  }
  const detail = payload?.detail;
  if (detail && typeof detail === "object" && detail.message) {
    return String(detail.message);
  }
  if (typeof detail === "string") {
    return detail;
  }
  return payload?.message || `HTTP ${status}`;
}

async function parseJson(res) {
  const text = await res.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = { message: text };
  }
  if (!res.ok) {
    throw new Error(formatApiError(res, payload));
  }
  return payload;
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchOpsMonitoringSummary(token) {
  const res = await fetch(`${BASE}/ops/monitoring/summary`, {
    headers: { Accept: "application/json", ...authHeaders(token) },
  });
  return parseJson(res);
}

export async function fetchOpsCreditsHealth(token, params = {}) {
  const q = new URLSearchParams();
  if (params.expiring_within_days != null) {
    q.set("expiring_within_days", String(params.expiring_within_days));
  }
  if (params.top_users_limit != null) {
    q.set("top_users_limit", String(params.top_users_limit));
  }
  const suffix = q.toString() ? `?${q}` : "";
  const res = await fetch(`${BASE}/ops/monitoring/credits-health${suffix}`, {
    headers: { Accept: "application/json", ...authHeaders(token) },
  });
  return parseJson(res);
}

export async function fetchOpsReconciliationLag(token) {
  const res = await fetch(`${BASE}/ops/monitoring/reconciliation-lag`, {
    headers: { Accept: "application/json", ...authHeaders(token) },
  });
  return parseJson(res);
}

export async function fetchOpsRuntimeDeadlocks(token, params = {}) {
  const q = new URLSearchParams();
  if (params.lock_age_sec != null) q.set("lock_age_sec", String(params.lock_age_sec));
  if (params.limit != null) q.set("limit", String(params.limit));
  const suffix = q.toString() ? `?${q}` : "";
  const res = await fetch(`${BASE}/ops/monitoring/runtime-deadlocks${suffix}`, {
    headers: { Accept: "application/json", ...authHeaders(token) },
  });
  return parseJson(res);
}
