
/**
 * Sprint 3 P0-2 — agregados de scorecard SLO fiscal/OPS (export + UI).
 * Limiares base por janela + perfis BR/PT (calibragem presencial).
 */

export const SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA = "sprint3-slo-scorecard-v3";
export const SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION = "sprint3-v6-br-pt-calibration";

export const SLO_THRESHOLDS_BY_PERIOD = Object.freeze({
  "24H": {
    errorRate: {
      medium: 0.08,
      critical: 0.2,
    },
    latencyP95Ms: {
      medium: 700,
      high: 1200,
    },
    hoursSinceLatestApproval: {
      high: 8,
    },
    prolongedDiff: {
      critical: true,
      divergenceWindow: 6,
      prolongedEdges: 2,
    },
  },
  "7D": {
    errorRate: {
      medium: 0.09,
      critical: 0.28,
    },
    latencyP95Ms: {
      medium: 880,
      high: 1450,
    },
    hoursSinceLatestApproval: {
      high: 24,
    },
    prolongedDiff: {
      critical: true,
      divergenceWindow: 10,
      prolongedEdges: 3,
    },
  },
  "30D": {
    errorRate: {
      medium: 0.11,
      critical: 0.33,
    },
    latencyP95Ms: {
      medium: 980,
      high: 1650,
    },
    hoursSinceLatestApproval: {
      high: 48,
    },
    prolongedDiff: {
      critical: true,
      divergenceWindow: 16,
      prolongedEdges: 4,
    },
  },
});

/** Multiplicadores < 1 = limiares mais apertados (alerta mais cedo). */
export const COUNTRY_CALIBRATION_PROFILES = Object.freeze({
  GLOBAL: {
    label: "Global baseline",
    errorRateMultiplier: 1,
    latencyMultiplier: 1,
    approvalHoursMultiplier: 1,
  },
  BR: {
    label: "BR operacional (calibragem presencial — mais sensível a erro)",
    errorRateMultiplier: 0.88,
    latencyMultiplier: 0.9,
    approvalHoursMultiplier: 0.85,
  },
  PT: {
    label: "PT operacional (calibragem presencial — latência ligeiramente mais exigente)",
    errorRateMultiplier: 0.93,
    latencyMultiplier: 0.94,
    approvalHoursMultiplier: 0.9,
  },
});

export function resolveSprint3SloBaseThresholds(period) {
  return SLO_THRESHOLDS_BY_PERIOD[period] || SLO_THRESHOLDS_BY_PERIOD["7D"];
}

export function applySprint3CountryCalibration(baseThresholds, calibrationKey) {
  const profile = COUNTRY_CALIBRATION_PROFILES[calibrationKey] || COUNTRY_CALIBRATION_PROFILES.GLOBAL;
  return {
    ...baseThresholds,
    errorRate: {
      medium: Number((baseThresholds.errorRate.medium * profile.errorRateMultiplier).toFixed(4)),
      critical: Number((baseThresholds.errorRate.critical * profile.errorRateMultiplier).toFixed(4)),
    },
    latencyP95Ms: {
      medium: Math.max(1, Math.round(baseThresholds.latencyP95Ms.medium * profile.latencyMultiplier)),
      high: Math.max(1, Math.round(baseThresholds.latencyP95Ms.high * profile.latencyMultiplier)),
    },
    hoursSinceLatestApproval: {
      high: Number((baseThresholds.hoursSinceLatestApproval.high * profile.approvalHoursMultiplier).toFixed(2)),
    },
  };
}

/**
 * Snapshot explícito GLOBAL vs BR vs PT para anexar ao daily (calibragem BR/PT).
 * @param {string} period "24H" | "7D" | "30D"
 */
export function buildSloThresholdsExportBundle(period) {
  const base = resolveSprint3SloBaseThresholds(period);
  return {
    bundle_version: SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION,
    period,
    by_profile: {
      GLOBAL: {
        profile: "GLOBAL",
        label: COUNTRY_CALIBRATION_PROFILES.GLOBAL.label,
        thresholds: applySprint3CountryCalibration(base, "GLOBAL"),
      },
      BR: {
        profile: "BR",
        label: COUNTRY_CALIBRATION_PROFILES.BR.label,
        thresholds: applySprint3CountryCalibration(base, "BR"),
      },
      PT: {
        profile: "PT",
        label: COUNTRY_CALIBRATION_PROFILES.PT.label,
        thresholds: applySprint3CountryCalibration(base, "PT"),
      },
    },
  };
}

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

