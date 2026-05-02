import { describe, expect, it } from "vitest";

import {
  buildCountrySloScorecardRows,
  computeSloFiscalOpsReadinessScore,
  SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA,
} from "./fiscalSprint3SloScorecardRollup";

describe("fiscalSprint3SloScorecardRollup", () => {
  it("exports schema v2", () => {
    expect(SPRINT3_SLO_SCORECARD_EXPORT_SCHEMA).toBe("sprint3-slo-scorecard-v2");
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
});
