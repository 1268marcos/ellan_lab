
import { describe, expect, it } from "vitest";
import {
  OPS_ENABLEMENT_CHECKLIST,
  computeOpsEnablementProgress,
  mergeOpsEnablementChecklist,
} from "./fiscalSprint3OpsEnablement";

describe("fiscalSprint3OpsEnablement", () => {
  it("mergeOpsEnablementChecklist preserves canonical rows and merges saved flags", () => {
    const rows = mergeOpsEnablementChecklist({
      ops_health: { done: true, marked_at: "2026-04-30T10:00:00Z" },
    });
    expect(rows).toHaveLength(OPS_ENABLEMENT_CHECKLIST.length);
    const health = rows.find((r) => r.id === "ops_health");
    expect(health?.done).toBe(true);
    expect(health?.marked_at).toBe("2026-04-30T10:00:00Z");
    const slo = rows.find((r) => r.id === "fiscal_slo");
    expect(slo?.done).toBe(false);
  });

  it("computeOpsEnablementProgress counts done rows", () => {
    const rows = mergeOpsEnablementChecklist({});
    rows[0] = { ...rows[0], done: true };
    rows[1] = { ...rows[1], done: true };
    const p = computeOpsEnablementProgress(rows);
    expect(p.total).toBe(rows.length);
    expect(p.done).toBe(2);
    expect(p.pct).toBeGreaterThan(0);
  });
});

