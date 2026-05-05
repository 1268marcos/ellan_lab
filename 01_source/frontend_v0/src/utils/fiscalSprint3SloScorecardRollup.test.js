
import { describe, expect, it } from "vitest";

import {
  applySprint3CountryCalibration,
  buildCountrySloScorecardRows,
  buildSloThresholdsExportBundle,
  computeSloFiscalOpsReadinessScore,
  resolveSprint3SloBaseThresholds,
  SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA,
  SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION,
} from "./fiscalSprint3SloScorecardRollup";

describe("fiscalSprint3SloScorecardRollup", () => {
  it("exports schema v3 e bundle v6", () => {
    expect(SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA).toBe("sprint3-slo-scorecard-v3");
    expect(SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION).toBe("sprint3-v6-br-pt-calibration");
  });

  it("buildCountrySloScorecardRows aggregates by country", () => {
    const rows = buildCountrySloScorecardRows([
      { country: "BR", provider_name: "A", last_status: "OK", last_latency_ms: 100 },
      { country: "BR", provider_name: "B", last_status: "ERROR", last_latency_ms: 200 },
      { country: "PT", provider_name: "C", last_status: "OK", last_latency_ms: 50 },
    ]);
    const br = rows.find((r) => r.country === "BR");
    const pt = rows.find((r) => r.country === "PT");
    expect(br?.rows).toBe(2);
    expect(br?.errors).toBe(1);
    expect(pt?.rows).toBe(1);
  });

  it("buildSloThresholdsExportBundle: BR mais apertado que GLOBAL em 7D", () => {
    const bundle = buildSloThresholdsExportBundle("7D");
    expect(bundle.bundle_version).toBe(SPRINT3_SLO_THRESHOLD_BUNDLE_VERSION);
    const g = bundle.by_profile.GLOBAL.thresholds.errorRate.medium;
    const br = bundle.by_profile.BR.thresholds.errorRate.medium;
    const pt = bundle.by_profile.PT.thresholds.errorRate.medium;
    expect(br).toBeLessThan(g);
    expect(pt).toBeLessThan(g);
    expect(br).toBeLessThanOrEqual(pt);
    expect(bundle.by_profile.BR.thresholds.latencyP95Ms.medium).toBeLessThan(bundle.by_profile.GLOBAL.thresholds.latencyP95Ms.medium);
  });

  it("resolveSprint3SloBaseThresholds 24H difere de 7D", () => {
    const d1 = resolveSprint3SloBaseThresholds("24H");
    const d7 = resolveSprint3SloBaseThresholds("7D");
    expect(d1.errorRate.medium).not.toEqual(d7.errorRate.medium);
  });

  it("computeSloFiscalOpsReadinessScore penalizes high severity", () => {
    const low = computeSloFiscalOpsReadinessScore({
      sloSeverity: "LOW",
      errorRate: 0.01,
      latencyP95Ms: 100,
      thresholds: {
        errorRate: { medium: 0.1, critical: 0.3 },
        latencyP95Ms: { medium: 900, high: 1500 },
      },
      auditMaterializedRate: 1,
    });
    const critical = computeSloFiscalOpsReadinessScore({
      sloSeverity: "CRITICAL",
      errorRate: 0.35,
      latencyP95Ms: 2000,
      thresholds: {
        errorRate: { medium: 0.1, critical: 0.3 },
        latencyP95Ms: { medium: 900, high: 1500 },
      },
      auditMaterializedRate: 0.5,
    });
    expect(low).toBeGreaterThan(critical);
    expect(critical).toBeLessThanOrEqual(100);
    expect(critical).toBeGreaterThanOrEqual(0);
  });

  it("applySprint3CountryCalibration preserva prolongedDiff", () => {
    const base = resolveSprint3SloBaseThresholds("7D");
    const br = applySprint3CountryCalibration(base, "BR");
    expect(br.prolongedDiff).toEqual(base.prolongedDiff);
  });
});

