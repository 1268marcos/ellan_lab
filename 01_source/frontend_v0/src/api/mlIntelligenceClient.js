
/** Cliente HTTP centralizado para ml_predictor_service (ML / intelligence). */
const DEFAULT_ML_BASE = "http://localhost:8000";

/** Base URL só host (sem `/api/ml`); paths usam `/intelligence/...`. */
function mlPredictorBaseUrl() {
  const raw = String(import.meta.env.VITE_ML_PREDICTOR_BASE_URL ?? "").trim();
  const fallback = DEFAULT_ML_BASE;
  if (!raw || raw === "true" || raw === "false") return fallback;
  if (raw === "/api/ml" || raw.startsWith("/api/ml/")) return fallback;
  if (raw.startsWith("/")) return raw.replace(/\/$/, "") || fallback;
  if (!/^https?:\/\//i.test(raw)) return fallback;
  return raw.replace(/\/$/, "").replace(/\/api\/ml$/i, "") || fallback;
}

const BASE = () => mlPredictorBaseUrl();

const DASHBOARD_MOCK = {
  at_risk_count: 0,
  at_risk_lockers: [],
  avg_health_series: [],
  avg_health_score_series_7d: [],
  avg_health_score_series_30d: [],
  active_model: null,
  last_prediction_at: null,
  active_accuracy: null,
  top5_worst_health: [],
};

/** Mesma chave que `AuthContext.tsx` (sessão pública order_pickup). */
function _sessionBearerHeaders() {
  const raw = typeof localStorage !== "undefined" ? localStorage.getItem("ellan_public_auth_token") : null;
  if (!raw) return {};
  return { Authorization: `Bearer ${raw}` };
}

async function _j(path, opts = {}) {
  const u = `${BASE()}${path}`;
  let r;
  try {
    r = await fetch(u, {
      ...opts,
      headers: { Accept: "application/json", ..._sessionBearerHeaders(), ...(opts.headers || {}) },
    });
  } catch {
    if (path === "/intelligence/dashboard") return { ...DASHBOARD_MOCK };
    throw new Error(`fetch failed ${u}`);
  }
  const t = await r.text();
  let body;
  try {
    body = t ? JSON.parse(t) : null;
  } catch {
    body = { raw: t };
  }
  if (!r.ok) {
    if (path === "/intelligence/dashboard") return { ...DASHBOARD_MOCK };
    throw new Error(body?.detail || body?.error || `${r.status} ${t || ""}`);
  }
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
  ltvScores: (q) => {
    const p = new URLSearchParams(q || {});
    return _j(`/intelligence/ltv-scores?${p.toString()}`);
  },
  customerLtv: (userId) => _j(`/customers/${encodeURIComponent(userId)}/ltv`),
  /** POST body: { locker_id, product_id, session_id?, apply_proxy_learning?, persist_bandit?, random_seed? } */
  dynamicPricingSuggest: (body) =>
    _j("/pricing/dynamic-suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }),
  occupancyForecast: (lockerId, hours = 24) =>
    _j(`/ops/lockers/${encodeURIComponent(lockerId)}/occupancy-forecast?hours=${hours}`),
  pickupFraudHotspots: (days = 30) => _j(`/intelligence/pickup-fraud-hotspots?days=${days}`),
  pickupFraudScore: (pickupId) => _j(`/intelligence/pickup-fraud-check/${encodeURIComponent(pickupId)}`),
  pickupFraudCheckPost: (pickupId, body) =>
    _j(`/pickups/${encodeURIComponent(pickupId)}/fraud-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }),
  /** POST body: { locker_ids[], vehicle_capacity_parcels?, time_window_*?, service_time_minutes_default?, k_clusters? } */
  optimizeRoute: (body) =>
    _j("/logistics/optimize-route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }),
  /** POST { text, order_id?, rating?, persist?, source? } */
  feedbackAnalyze: (body) =>
    _j("/feedback/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }),
  feedbackOpsDashboard: (days = 30) => _j(`/feedback/ops-dashboard?days=${encodeURIComponent(String(days))}`),
};

