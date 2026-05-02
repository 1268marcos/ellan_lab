import { describe, expect, it } from "vitest";
import {
  SPRINT4_KIOSK_UAT_MODELS,
  SPRINT4_MATRIX_DEFAULT_ITEMS,
  SPRINT4_MATRIX_VERSION,
  SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
  SPRINT4_REGRESSION_EXPORT_SCHEMA,
  buildSprint4KioskTouchUatModelsPayload,
  buildSprint4PersonaFunctionalChecklistPayload,
  buildSprint4RegressionMatrixPayload,
  computeSprint4CombinedFunctionalPct,
  mergeSprint4KioskUatRows,
  mergeSprint4MatrixRows,
} from "./fiscalSprint4RegressionMatrix";

describe("fiscalSprint4RegressionMatrix", () => {
  it("mantém versão de storage alinhada ao incremento da matriz", () => {
    expect(SPRINT4_MATRIX_VERSION).toBeGreaterThanOrEqual(2);
    expect(SPRINT4_MATRIX_DEFAULT_ITEMS.length).toBeGreaterThanOrEqual(16);
  });

  it("mergeSprint4MatrixRows inclui todos os ids default", () => {
    const rows = mergeSprint4MatrixRows({});
    const ids = new Set(rows.map((r) => r.id));
    for (const def of SPRINT4_MATRIX_DEFAULT_ITEMS) {
      expect(ids.has(def.id)).toBe(true);
    }
  });

  it("computeSprint4CombinedFunctionalPct pondera matriz 70% e UAT 30%", () => {
    expect(computeSprint4CombinedFunctionalPct({ done: 0, total: 10 }, { pass: 0, total: 4 })).toBe(0);
    expect(computeSprint4CombinedFunctionalPct({ done: 10, total: 10 }, { pass: 4, total: 4 })).toBe(100);
    expect(computeSprint4CombinedFunctionalPct({ done: 5, total: 10 }, { pass: 2, total: 4 })).toBe(50);
  });

  it("payload da matriz inclui export_schema v2, checklist e combinado", () => {
    const now = "2026-05-01T12:00:00.000Z";
    const stored = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "qa",
      rows: {},
      kiosk_uat: { models: {} },
      go_no_go: { decision: "PENDING_REVIEW", residual_risk: "MEDIUM", mitigation_plan: "", owner: "qa", updated_at: now },
    };
    const p = buildSprint4RegressionMatrixPayload(now, stored);
    expect(p.export_schema).toBe(SPRINT4_REGRESSION_EXPORT_SCHEMA);
    expect(p.persona_functional_checklist).toEqual(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST);
    expect(typeof p.combined_functional_pct).toBe("number");
    expect(p.progress.total).toBe(SPRINT4_MATRIX_DEFAULT_ITEMS.length);
  });

  it("mergeSprint4KioskUatRows inclui protocolo manual por modelo", () => {
    const rows = mergeSprint4KioskUatRows({});
    expect(rows).toHaveLength(4);
    const a = rows.find((r) => r.id === "model_a_quick_buy");
    expect(a?.manual_steps?.length).toBeGreaterThanOrEqual(3);
    expect(a?.e2e_anchors?.length).toBeGreaterThanOrEqual(1);
    expect(SPRINT4_KIOSK_UAT_MODELS).toHaveLength(4);
  });

  it("buildSprint4KioskTouchUatModelsPayload inclui manual_protocol e execução", () => {
    const now = "2026-05-01T12:00:00.000Z";
    const p = buildSprint4KioskTouchUatModelsPayload(now, {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "qa",
      rows: {},
      kiosk_uat: {
        models: {
          model_a_quick_buy: { pass: true, note: "e2e verde", marked_at: now },
        },
      },
      go_no_go: {},
    });
    expect(p.scope).toBe("SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D");
    expect(p.manual_protocol).toHaveLength(4);
    expect(p.kiosk_uat_execution?.models?.[0]?.id).toBe("model_a_quick_buy");
  });

  it("buildSprint4PersonaFunctionalChecklistPayload expõe referência e rollups", () => {
    const now = "2026-05-01T12:00:00.000Z";
    const p = buildSprint4PersonaFunctionalChecklistPayload(now, {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "x",
      rows: {},
      kiosk_uat: { models: {} },
      go_no_go: {},
    });
    expect(p.scope).toBe("SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST");
    expect(p.reference).toEqual(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST);
    expect(Array.isArray(p.persona_rollups)).toBe(true);
  });
});
