/** Cliente HTTP centralizado para ml_predictor_service (ML / intelligence). */
const BASE = () => String(import.meta.env.VITE_ML_PREDICTOR_BASE_URL || "").replace(/\/$/, "");

async function _j(path, opts = {}) {
  const u = `${BASE()}${path}`;
  const r = await fetch(u, { ...opts, headers: { Accept: "application/json", ...(opts.headers || {}) } });
  const t = await r.text();
  let body;
  try {
    body = t ? JSON.parse(t) : null;
  } catch {
    body = { raw: t };
  }
  if (!r.ok) throw new Error(body?.detail || body?.error || `${r.status} ${t || ""}`);
  return body;
}

export const mlIntelligenceApi = {
  baseUrl: BASE,
  dashboard: () => _j("/intelligence/dashboard"),
  models: () => _j("/intelligence/models"),
  atRisk: (q) => {
    const p = new URLSearchParams(q || {});
    return _j(`/intelligence/at-risk?${p.toString()}`);
  },
  history: (q) => {
    const p = new URLSearchParams(q || {});
    return _j(`/intelligence/history?${p.toString()}`);
  },
  train: () => _j("/train", { method: "POST" }),
  churnRisk: (q) => {
    const p = new URLSearchParams(q || {});
    return _j(`/ops/partners/churn-risk?${p.toString()}`);
  },
  /** POST body: { locker_id, product_id, session_id?, apply_proxy_learning?, persist_bandit?, random_seed? } */
  dynamicPricingSuggest: (body) =>
    _j("/pricing/dynamic-suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }),
  occupancyForecast: (lockerId, hours = 24) =>
    _j(`/ops/lockers/${encodeURIComponent(lockerId)}/occupancy-forecast?hours=${hours}`),
};
