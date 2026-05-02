/**
 * Sprint 3 P0-2 — registo operacional de decisões tomadas após recomendações automáticas do SLO (`fiscal/slo-alerts`).
 */

export const SPRINT3_SLO_POST_REC_DECISIONS_KEY = "ellan_fiscal_sprint3_slo_post_rec_decisions_v1";
export const SPRINT3_SLO_POST_REC_VERSION = "sprint3-p02-decisions-v2";

export type SloPostRecDecisionEntry = Record<string, unknown>;

export function loadSloPostRecommendationDecisions(): SloPostRecDecisionEntry[] {
  try {
    const raw = window.localStorage.getItem(SPRINT3_SLO_POST_REC_DECISIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as { decisions?: unknown };
    return Array.isArray(parsed?.decisions) ? (parsed.decisions as SloPostRecDecisionEntry[]) : [];
  } catch {
    return [];
  }
}

export function saveSloPostRecommendationDecisions(decisions: SloPostRecDecisionEntry[]) {
  const capped = decisions.slice(-25);
  window.localStorage.setItem(
    SPRINT3_SLO_POST_REC_DECISIONS_KEY,
    JSON.stringify({
      version: SPRINT3_SLO_POST_REC_VERSION,
      updated_at: new Date().toISOString(),
      decisions: capped,
    })
  );
  return capped;
}

export function appendSloPostRecommendationDecision(entry: SloPostRecDecisionEntry) {
  const next = [...loadSloPostRecommendationDecisions(), entry];
  return saveSloPostRecommendationDecisions(next);
}

export function clearSloPostRecommendationDecisions() {
  window.localStorage.removeItem(SPRINT3_SLO_POST_REC_DECISIONS_KEY);
}

/** Payload fonte (sem envelope SHA-256). */
export function buildSloPostRecommendationDecisionsPayload(
  nowIso: string,
  decisions: SloPostRecDecisionEntry[],
  sourcePage: string,
  scorecardSnapshot?: Record<string, unknown> | null
) {
  const timeline = decisions.slice(-25);
  return {
    scope: "SPRINT3_P0_2_POST_RECOMMENDATION_DECISIONS",
    generated_at: nowIso,
    source: String(sourcePage || "fiscal/slo-alerts"),
    sprint3_version: SPRINT3_SLO_POST_REC_VERSION,
    export_schema: "sprint3-p0-2-post-rec-v2",
    decisions_count: timeline.length,
    decisions_last_3: timeline.slice(-3),
    decisions: timeline,
    ...(scorecardSnapshot && Object.keys(scorecardSnapshot).length
      ? { attached_scorecard_digest: scorecardSnapshot }
      : {}),
  };
}
