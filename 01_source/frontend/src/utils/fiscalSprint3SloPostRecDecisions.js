/**
 * Sprint 3 P0-2 — registo operacional de decisões tomadas após recomendações automáticas do SLO (`fiscal/slo-alerts`).
 */

export const SPRINT3_SLO_POST_REC_DECISIONS_KEY = "ellan_fiscal_sprint3_slo_post_rec_decisions_v1";
export const SPRINT3_SLO_POST_REC_VERSION = "sprint3-p02-decisions-v1";

/** @returns {object[]} */
export function loadSloPostRecommendationDecisions() {
  try {
    const raw = window.localStorage.getItem(SPRINT3_SLO_POST_REC_DECISIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed?.decisions) ? parsed.decisions : [];
  } catch {
    return [];
  }
}

/**
 * @param {object[]} decisions
 */
export function saveSloPostRecommendationDecisions(decisions) {
  const capped = decisions.slice(-25);
  window.localStorage.setItem(
    SPRINT3_SLO_POST_REC_DECISIONS_KEY,
    JSON.stringify({ version: SPRINT3_SLO_POST_REC_VERSION, updated_at: new Date().toISOString(), decisions: capped })
  );
  return capped;
}

/**
 * @param {object} entry
 */
export function appendSloPostRecommendationDecision(entry) {
  const next = [...loadSloPostRecommendationDecisions(), entry];
  return saveSloPostRecommendationDecisions(next);
}

export function clearSloPostRecommendationDecisions() {
  window.localStorage.removeItem(SPRINT3_SLO_POST_REC_DECISIONS_KEY);
}

/**
 * Payload fonte (sem envelope SHA-256).
 * @param {string} sourcePage ex.: fiscal/slo-alerts
 */
export function buildSloPostRecommendationDecisionsPayload(nowIso, decisions, sourcePage) {
  const timeline = decisions.slice(-25);
  return {
    scope: "SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS",
    generated_at: nowIso,
    source: String(sourcePage || "fiscal/slo-alerts"),
    sprint3_version: SPRINT3_SLO_POST_REC_VERSION,
    decisions_count: timeline.length,
    decisions_last_3: timeline.slice(-3),
    decisions: timeline,
  };
}
