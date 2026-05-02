/**
 * Sprint 3 P0-2 — agregados de scorecard SLO fiscal/OPS (export + UI).
 */

export const SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA = "sprint3-slo-scorecard-v2";

function percentile(values, p) {
  const nums = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
  if (nums.length === 0) return 0;
  const index = Math.min(nums.length - 1, Math.ceil((p / 100) * nums.length) - 1);
  return nums[Math.max(index, 0)];
}

/**
 * @param {Array<Record<string, unknown>>} providers
 * @returns {Array<{ country: string, rows: number, errors: number, error_rate: number, latency_p95_ms: number }>}
 */
export function buildCountrySloScorecardRows(providers) {
  const rows = Array.isArray(providers) ? providers : [];
  /** @type {Map<string, { country: string, latencies: number[], errors: number, total: number }>} */
  const map = new Map();
  for (const row of rows) {
    const country = String(row?.country || "").toUpperCase() || "UNKNOWN";
    const cur = map.get(country) || { country, latencies: [], errors: 0, total: 0 };
    cur.total += 1;
    if (String(row?.last_status || "").toUpperCase() !== "OK") cur.errors += 1;
    const lat = Number(row?.last_latency_ms || 0);
    if (Number.isFinite(lat) && lat > 0) cur.latencies.push(lat);
    map.set(country, cur);
  }
  return Array.from(map.values())
    .map((c) => {
      const latSorted = [...c.latencies].sort((a, b) => a - b);
      return {
        country: c.country,
        rows: c.total,
        errors: c.errors,
        error_rate: c.total > 0 ? Number((c.errors / c.total).toFixed(4)) : 0,
        latency_p95_ms: Number(percentile(latSorted, 95).toFixed(2)),
      };
    })
    .sort((a, b) => b.rows - a.rows);
}

/**
 * @param {object} params
 * @param {string} params.sloSeverity
 * @param {number} params.errorRate
 * @param {number} params.latencyP95Ms
 * @param {{ errorRate: { medium: number, critical: number }, latencyP95Ms: { medium: number, high: number } }} params.thresholds
 * @param {number} params.auditMaterializedRate 0..1
 */
export function computeSloFiscalOpsReadinessScore({
  sloSeverity,
  errorRate,
  latencyP95Ms,
  thresholds,
  auditMaterializedRate,
}) {
  let score = 100;
  const sev = String(sloSeverity || "").toUpperCase();
  if (sev === "CRITICAL") score -= 38;
  else if (sev === "HIGH") score -= 24;
  else if (sev === "MEDIUM") score -= 10;

  const erCrit = Number(thresholds?.errorRate?.critical || 0.3);
  const erMed = Number(thresholds?.errorRate?.medium || 0.1);
  if (errorRate >= erCrit) score -= 22;
  else if (errorRate >= erMed) score -= 10;

  const latHigh = Number(thresholds?.latencyP95Ms?.high || 1500);
  const latMed = Number(thresholds?.latencyP95Ms?.medium || 900);
  if (latencyP95Ms >= latHigh) score -= 14;
  else if (latencyP95Ms >= latMed) score -= 6;

  const gap = Math.max(0, 1 - Number(auditMaterializedRate || 0));
  score -= Math.round(gap * 18);

  return Math.max(0, Math.min(100, Math.round(score)));
}
