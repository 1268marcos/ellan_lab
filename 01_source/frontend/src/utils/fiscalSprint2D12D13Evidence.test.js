import { describe, expect, it } from "vitest";
import {
  buildExecutiveAccountingApprovalInnerForClose,
  buildSprint2D12AccountingHandoffEvidence,
  wrapSprint2D13AccountingAcceptance,
} from "./fiscalSprint2D12D13Evidence";

describe("fiscalSprint2D12D13Evidence", () => {
  it("buildSprint2D12 inclui scope e ligação D11 quando há lote", () => {
    const iso = "2026-05-01T12:00:00.000Z";
    const out = buildSprint2D12AccountingHandoffEvidence({
      generatedAt: iso,
      source: "fiscal/management-daily",
      stubReadiness: { decision: "GO", checks: [{ status: "PASS" }], countries_not_ready: 0, readiness_version: "v1" },
      catalog: { count: 3 },
      matrix: { count: 2 },
      d11Handoff: {
        generated_at: iso,
        summary: { total_items: 1, severity: { ERROR: 1 }, unique_partners: 1, unique_batches: 1, unique_orders_with_gaps: 1 },
        filters: { x: 1 },
        items: [{ order_id: "o1", severity: "ERROR", gap_type: "G", batch_id: "b1" }],
      },
    });
    expect(out.scope).toBe("SPRINT2_D12_ACCOUNTING_HANDOFF");
    expect(out.fiscal_context.reference.catalog_count).toBe(3);
    expect(out.d11_fiscal_gap_handoff?.total_items).toBe(1);
    expect(out.d11_fiscal_gap_handoff?.order_id_rollup_summary?.unique_orders_with_gaps).toBeGreaterThanOrEqual(1);
  });

  it("wrapSprint2D13 envolve o payload diário", () => {
    const inner = { scope: "FISCAL_ACCOUNTING_DAILY_APPROVAL", generated_at: "t", approval: { owner: "a" } };
    const w = wrapSprint2D13AccountingAcceptance(inner, "2026-05-01T12:00:00.000Z", "fiscal/management-daily");
    expect(w.scope).toBe("SPRINT2_D13_ACCOUNTING_ACCEPTANCE");
    expect(w.fiscal_accounting_daily_approval).toBe(inner);
  });

  it("buildExecutiveAccountingApprovalInnerForClose reflete D11 no contexto", () => {
    const inner = buildExecutiveAccountingApprovalInnerForClose({
      nowIso: "2026-05-01T12:00:00.000Z",
      gateDecision: "NO_GO",
      stubReadiness: { readiness_version: "rv1", countries_not_ready: 1 },
      passedChecks: 1,
      readinessChecksLength: 2,
      failedChecks: 1,
      approvalDraft: { owner: "ops", status: "PENDING_REVIEW", notes: "", timestamp: "t", eta: "" },
      d11Snapshot: {
        generated_at: "g1",
        summary: { total_items: 5, unique_orders_with_gaps: 2 },
        items: [],
      },
    });
    expect(inner.context.d11_total_items).toBe(5);
    expect(inner.context.d11_unique_orders_with_gaps).toBe(2);
  });
});
