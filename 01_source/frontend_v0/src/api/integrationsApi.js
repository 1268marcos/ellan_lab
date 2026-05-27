const BASE = "/api/v1";

async function parseJson(res) {
  const text = await res.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = { message: text };
  }
  if (!res.ok) {
    const msg =
      payload?.detail?.message ||
      payload?.detail ||
      payload?.message ||
      `HTTP ${res.status}`;
    throw new Error(String(msg));
  }
  return payload;
}

function buildUrl(path, params) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value != null && value !== "") url.searchParams.set(key, String(value));
    });
  }
  return url.pathname + url.search;
}

async function request(method, path, { params, body } = {}) {
  const init = {
    method,
    headers: { Accept: "application/json" },
  };
  if (body != null) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(buildUrl(path, params), init);
  const data = await parseJson(res);
  return { data };
}

export const integrationsApi = {
  listPartners: (params) => request("GET", "/partners", { params }),
  getPartner: (id) => request("GET", `/partners/${encodeURIComponent(id)}`),
  createPartner: (body) => request("POST", "/partners", { body }),
  updatePartner: (id, body) => request("PUT", `/partners/${encodeURIComponent(id)}`, { body }),
  deletePartner: (id) => request("DELETE", `/partners/${encodeURIComponent(id)}`),
  listCapabilities: (partnerId) =>
    request("GET", `/partners/${encodeURIComponent(partnerId)}/capabilities`),
  createCapability: (partnerId, body) =>
    request("POST", `/partners/${encodeURIComponent(partnerId)}/capabilities`, { body }),
  listMarketplaceConnections: (params) => request("GET", "/marketplaces/connections", { params }),
  listCarrierRates: (params) => request("GET", "/carriers/rates", { params }),
  createCarrierRate: (body) => request("POST", "/carriers/rates", { body }),
  updateRateLimit: (partnerId, limit_per_minute) =>
    request("PUT", `/partners/${encodeURIComponent(partnerId)}/rate-limit`, {
      body: { limit_per_minute },
    }),
  getHealth: (partnerId) => request("GET", `/partners/${encodeURIComponent(partnerId)}/health`),
  runHealthCheck: (partnerId, endpoint_url) =>
    request("POST", `/partners/${encodeURIComponent(partnerId)}/health/check`, {
      body: { endpoint_url },
    }),
  testWebhook: (body) => request("POST", "/partners/webhook/test", { body }),
};
