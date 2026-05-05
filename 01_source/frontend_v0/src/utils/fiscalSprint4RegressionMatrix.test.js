
import { describe, expect, it } from "vitest";
import {
  SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY,
  SPRINT4_GO_NO_GO_REGISTER_SUMMARY_SCHEMA,
  SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG,
  SPRINT4_KIOSK_TOUCH_UAT_PROTOCOL_VERSION,
  SPRINT4_KIOSK_UAT_MODELS,
  SPRINT4_MATRIX_DEFAULT_ITEMS,
  SPRINT4_MATRIX_N_CASES,
  SPRINT4_MATRIX_VERSION,
  normalizePresencialFunctionalChecklist,
  SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
  SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA,
  SPRINT4_REGRESSION_EXPORT_SCHEMA,
  buildSprint4GoNoGoRegisterSummaryPayload,
  buildSprint4KioskTouchUatModelsPayload,
  buildSprint4PersonaFunctionalChecklistPayload,
  buildSprint4RegressionMatrixPayload,
  computeSprint4CombinedFunctionalPct,
  computeSprint4GoNoGoReadinessDocumentationPct,
  mergeSprint4KioskUatRows,
  mergeSprint4MatrixRows,
  normalizeSprint4GoNoGoState,
  normalizeKioskHardwarePresencialStamp,
} from "./fiscalSprint4RegressionMatrix";

describe("fiscalSprint4RegressionMatrix", () => {
  it("mantém versão de storage alinhada ao incremento da matriz", () => {
    expect(SPRINT4_MATRIX_VERSION).toBeGreaterThanOrEqual(4);
    expect(SPRINT4_MATRIX_DEFAULT_ITEMS.length).toBe(SPRINT4_MATRIX_N_CASES);
    expect(SPRINT4_MATRIX_N_CASES).toBe(21);
  });

  it("checklist por persona referencia ids existentes na matriz (schema v2)", () => {
    const matrixIds = new Set(SPRINT4_MATRIX_DEFAULT_ITEMS.map((i) => i.id));
    for (const block of SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST) {
      expect(Array.isArray(block.matrix_case_ids)).toBe(true);
      expect(block.matrix_case_ids.length).toBeGreaterThan(0);
      for (const id of block.matrix_case_ids) {
        expect(matrixIds.has(id)).toBe(true);
      }
    }
    expect(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA).toMatch(/sprint4-persona-functional-checklist-v2/);
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

  it("payload da matriz inclui export_schema v3, checklist, schema persona e combinado", () => {
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
    expect(p.export_schema).toBe("sprint4-regression-matrix-v4");
    expect(p.export_schema).toBe(SPRINT4_REGRESSION_EXPORT_SCHEMA);
    expect(p.matrix_n_cases).toBe(SPRINT4_MATRIX_N_CASES);
    expect(p.matrix_execution_evidence?.total).toBe(SPRINT4_MATRIX_N_CASES);
    expect(p.persona_functional_checklist).toEqual(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST);
    expect(p.persona_functional_checklist_schema).toBe(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA);
    expect(typeof p.combined_functional_pct).toBe("number");
    expect(p.progress.total).toBe(SPRINT4_MATRIX_DEFAULT_ITEMS.length);
  });

  it("mergeSprint4KioskUatRows inclui protocolo manual por modelo", () => {
    const rows = mergeSprint4KioskUatRows({});
    expect(rows).toHaveLength(4);
    const a = rows.find((r) => r.id === "model_a_quick_buy");
    expect(a?.manual_steps?.length).toBeGreaterThanOrEqual(3);
    expect(a?.e2e_anchors?.length).toBeGreaterThanOrEqual(1);
    expect(a?.aligned_e2e_tests?.length).toBeGreaterThanOrEqual(1);
    expect(a?.hardware_presencial?.steps?.length).toBeGreaterThanOrEqual(1);
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
    expect(p.kiosk_touch_uat_protocol_version).toBe(SPRINT4_KIOSK_TOUCH_UAT_PROTOCOL_VERSION);
    expect(p.kiosk_touch_uat_protocol_version).toMatch(/v3/);
    expect(p.presencial_hardware_residual).toMatch(/Protocolo v3/);
    expect(p.manual_protocol).toHaveLength(4);
    expect(p.manual_protocol[0].aligned_e2e_tests?.length).toBeGreaterThanOrEqual(1);
    expect(p.manual_protocol[0].hardware_presencial?.steps?.length).toBeGreaterThanOrEqual(1);
    expect(p.zip_executive_attachment_hint).toContain("accounting-close");
    expect(p.kiosk_uat_execution?.models?.[0]?.id).toBe("model_a_quick_buy");
    expect(p.kiosk_final_carimbo).toMatch(/PENDING|CLOSED/);
  });

  it("kiosk_touch_uat_presencial_stamp_complete quando 4 PASS + carimbo hardware completo", () => {
    const now = "2026-05-01T20:00:00.000Z";
    const stamp = {
      session_id: "hw-1",
      site_pilot: "piloto-x",
      session_signed_at: now,
      operator_name: "Ops Lead",
      device_inventory_tag: "TOTEM-PT-01",
      model_attestations: SPRINT4_KIOSK_UAT_MODELS.map((m) => ({
        model_id: m.id,
        hardware_cycle_at: now,
        evidence_ref: "ticket-123",
        operator_initials: "OL",
      })),
    };
    const stored = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "qa",
      rows: {},
      kiosk_uat: {
        models: Object.fromEntries(SPRINT4_KIOSK_UAT_MODELS.map((m) => [m.id, { pass: true, note: "hw ok", marked_at: now }])),
      },
      go_no_go: {},
      kiosk_hardware_presencial_stamp: stamp,
    };
    const p = buildSprint4KioskTouchUatModelsPayload(now, stored);
    expect(p.kiosk_touch_uat_presencial_stamp_complete).toBe(true);
    expect(p.kiosk_final_carimbo).toBe("SPRINT4_KIOSK_TOUCH_UAT_CLOSED_100_PCT");
    expect(normalizeKioskHardwarePresencialStamp(stamp)?.model_attestations).toHaveLength(4);
  });

  it("go_no_go_register inclui riscos, tópicos de mitigação e readiness", () => {
    const now = "2026-05-01T15:00:00.000Z";
    const riskIds = Object.fromEntries(SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.map((r) => [r.id, true]));
    const topicIds = Object.fromEntries(SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.map((t) => [t.id, true]));
    const stored = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "comite",
      rows: {},
      kiosk_uat: {
        models: Object.fromEntries(SPRINT4_KIOSK_UAT_MODELS.map((m) => [m.id, { pass: true, note: "ok", marked_at: now }])),
      },
      go_no_go: {
        decision: "GO",
        residual_risk: "LOW",
        mitigation_plan: "x".repeat(85),
        owner: "comite",
        updated_at: now,
        residual_risk_ids: riskIds,
        mitigation_topic_ids: topicIds,
      },
    };
    const p = buildSprint4RegressionMatrixPayload(now, stored);
    expect(p.go_no_go_register.residual_risks_documented?.length).toBe(SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.length);
    expect(p.go_no_go_register.mitigation_plan_topics?.selected_from_library?.length).toBe(
      SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.length
    );
    expect(p.go_no_go_register.readiness_documentation_pct).toBeGreaterThanOrEqual(80);
    const summary = buildSprint4GoNoGoRegisterSummaryPayload(now, stored);
    expect(summary.scope).toBe("SPRINT4_GO_NO_GO_REGISTER_SUMMARY");
    expect(summary.register_summary_schema).toBe(SPRINT4_GO_NO_GO_REGISTER_SUMMARY_SCHEMA);
    expect(summary.residual_risks_catalog).toHaveLength(SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.length);
    expect(summary.mitigation_topics_library).toHaveLength(SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.length);
    expect(summary.readiness_documentation_pct_formula?.version).toBe("sprint4-readiness-doc-v2-final");
    expect(summary.readiness_documentation_pct).toBe(p.go_no_go_register.readiness_documentation_pct);
  });

  it("readiness_documentation_pct pode atingir 100 com catálogo completo + GO + matriz/UAT fortes", () => {
    const now = "2026-05-01T16:00:00.000Z";
    const riskIds = Object.fromEntries(SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.map((r) => [r.id, true]));
    const topicIds = Object.fromEntries(SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.map((t) => [t.id, true]));
    const stored = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "comite",
      rows: Object.fromEntries(SPRINT4_MATRIX_DEFAULT_ITEMS.map((it) => [it.id, { done: true, note: "ok", last_marked_at: now }])),
      kiosk_uat: {
        models: Object.fromEntries(SPRINT4_KIOSK_UAT_MODELS.map((m) => [m.id, { pass: true, note: "ok", marked_at: now }])),
      },
      go_no_go: {
        decision: "GO",
        residual_risk: "LOW",
        mitigation_plan: "x".repeat(85),
        owner: "comite",
        updated_at: now,
        residual_risk_ids: riskIds,
        mitigation_topic_ids: topicIds,
      },
    };
    const p = buildSprint4RegressionMatrixPayload(now, stored);
    expect(p.go_no_go_register.readiness_documentation_pct).toBe(100);
  });

  it("normalizeSprint4GoNoGoState tolera ausência de ids", () => {
    const n = normalizeSprint4GoNoGoState({ decision: "PENDING_REVIEW" });
    expect(n.residual_risk_ids).toEqual({});
    expect(computeSprint4GoNoGoReadinessDocumentationPct(n, { pct: 0, total: 1, done: 0 }, { pct: 0, all_pass: false })).toBeLessThan(50);
  });

  it("buildSprint4PersonaFunctionalChecklistPayload expõe referência, checklist_schema e rollups", () => {
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
    expect(p.checklist_schema).toBe(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA);
    expect(p.export_schema).toBe(SPRINT4_REGRESSION_EXPORT_SCHEMA);
    expect(p.reference).toEqual(SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST);
    expect(Array.isArray(p.persona_rollups)).toBe(true);
    expect(p.matrix_n_cases).toBe(21);
    expect(p.presencial_functional_signoff).toBe(null);
  });

  it("normalizePresencialFunctionalChecklist exige sessão mínima", () => {
    expect(normalizePresencialFunctionalChecklist(null)).toBe(null);
    expect(normalizePresencialFunctionalChecklist({})).toBe(null);
    const n = normalizePresencialFunctionalChecklist({
      session_id: "s1",
      facilitator_name: "F",
      session_signed_at: "2026-05-01T10:00:00.000Z",
      persona_signoffs: [{ persona: "OPS", signer_name: "A", signer_role: "r", signed_at: "t", location: "L" }],
    });
    expect(n?.session_id).toBe("s1");
    expect(n?.persona_signoffs?.length).toBe(1);
  });

  it("presencial_functional_signoff_complete quando matriz 21/21 + todas personas assinadas", () => {
    const now = "2026-05-01T18:00:00.000Z";
    const rows = Object.fromEntries(
      SPRINT4_MATRIX_DEFAULT_ITEMS.map((it) => [it.id, { done: true, note: "ok", last_marked_at: now }])
    );
    const persona_signoffs = SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST.map((b) => ({
      persona: b.persona,
      signer_name: "Chair",
      signer_role: "lead",
      signed_at: now,
      location: "LAB-A",
    }));
    const p = buildSprint4PersonaFunctionalChecklistPayload(now, {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: now,
      owner: "qa",
      rows,
      kiosk_uat: { models: {} },
      go_no_go: {},
      presencial_functional_checklist: {
        session_id: "spr4-pres-1",
        facilitator_name: "Fac",
        session_signed_at: now,
        persona_signoffs,
      },
    });
    expect(p.presencial_functional_signoff_complete).toBe(true);
    expect(p.matrix_execution_evidence?.all_matrix_cases_marked).toBe(true);
  });
});

