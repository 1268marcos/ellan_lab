
import { describe, expect, it } from "vitest";
import {
  D18_CHECKLIST_ITEMS,
  D18_CLOSEOUT_STORAGE_KEY,
  buildD18CloseoutPayload,
  countD18ChecklistDone,
  createInitialP1RiskRows,
  loadD18CloseoutFromStorage,
} from "./fiscalSprint2D18Content";

describe("createInitialP1RiskRows", () => {
  it("cria cinco linhas template vazias com ids estáveis", () => {
    const rows = createInitialP1RiskRows();
    expect(rows).toHaveLength(5);
    expect(rows.map((r) => r.id)).toEqual(["p1_0", "p1_1", "p1_2", "p1_3", "p1_4"]);
    expect(rows[0]).toEqual({ id: "p1_0", title: "", owner: "", eta: "", impact: "" });
  });
});

describe("countD18ChecklistDone", () => {
  it("conta apenas ids conhecidos do checklist D18", () => {
    expect(countD18ChecklistDone({})).toBe(0);
    expect(countD18ChecklistDone({ d10: true, d11: true })).toBe(2);
    expect(countD18ChecklistDone(null)).toBe(0);
  });

  it("ignora chaves estranhas e marca checklist completo", () => {
    const all = Object.fromEntries(D18_CHECKLIST_ITEMS.map((row) => [row.id, true]));
    expect(countD18ChecklistDone({ ...all, extra: true })).toBe(D18_CHECKLIST_ITEMS.length);
  });
});

describe("loadD18CloseoutFromStorage", () => {
  it("retorna estado inicial quando não há localStorage", () => {
    const s = loadD18CloseoutFromStorage();
    expect(s.checklist).toEqual({});
    expect(s.p1Risks).toHaveLength(5);
    expect(s.certification).toBeNull();
  });

  it("faz merge de checklist e p1Risks a partir de JSON válido", () => {
    window.localStorage.setItem(
      D18_CLOSEOUT_STORAGE_KEY,
      JSON.stringify({
        checklist: { d10: true },
        p1Risks: [{ title: "Risco A", owner: "ops", eta: "D+1", impact: "MED" }],
        certification: { certified_at: "2026-05-01", certified_by: "qa", note: "ok" },
      }),
    );
    const s = loadD18CloseoutFromStorage();
    expect(s.checklist).toEqual({ d10: true });
    expect(s.p1Risks[0].title).toBe("Risco A");
    expect(s.p1Risks[0].owner).toBe("ops");
    expect(s.certification).toEqual({
      certified_at: "2026-05-01",
      certified_by: "qa",
      note: "ok",
    });
  });

  it("descarta certificação incompleta", () => {
    window.localStorage.setItem(
      D18_CLOSEOUT_STORAGE_KEY,
      JSON.stringify({
        checklist: {},
        certification: { certified_at: "", certified_by: "x" },
      }),
    );
    expect(loadD18CloseoutFromStorage().certification).toBeNull();
  });

  it("JSON inválido volta ao estado inicial", () => {
    window.localStorage.setItem(D18_CLOSEOUT_STORAGE_KEY, "{");
    const s = loadD18CloseoutFromStorage();
    expect(s.checklist).toEqual({});
    expect(s.certification).toBeNull();
  });
});

describe("buildD18CloseoutPayload", () => {
  const iso = "2026-05-02T10:00:00.000Z";
  const ctx = { decision_consolidated: "go", risk_level: "medio", readiness_version: "rv2" };

  it("usa scope diário fora do accounting-close", () => {
    const p1 = createInitialP1RiskRows();
    const out = buildD18CloseoutPayload({
      generatedAt: iso,
      checklistById: { d10: true },
      p1Rows: p1,
      source: "fiscal/management-daily",
      context: ctx,
      certification: null,
    });
    expect(out.scope).toBe("SPRINT2_D18_FINANCE_CLOSEOUT");
    expect(out.source).toBe("fiscal/management-daily");
    expect(out.checklist_done).toBe(1);
    expect(out.checklist_total).toBe(D18_CHECKLIST_ITEMS.length);
    expect(out.checklist_pass_ratio).toBe(`1/${D18_CHECKLIST_ITEMS.length}`);
    expect(out.checklist_progress.find((r) => r.id === "d10")?.done).toBe(true);
    expect(out.checklist_progress.find((r) => r.id === "d11")?.done).toBe(false);
    expect(out.context.decision_consolidated).toBe("GO");
    expect(out.closeout_certification).toBeNull();
  });

  it("usa scope executivo em fiscal/accounting-close", () => {
    const out = buildD18CloseoutPayload({
      generatedAt: iso,
      checklistById: {},
      p1Rows: [],
      source: "fiscal/accounting-close",
      context: {},
      certification: { certified_at: "t1", certified_by: "cfo", note: "" },
    });
    expect(out.scope).toBe("SPRINT2_D18_EXEC_FINANCE_CLOSEOUT");
    expect(out.closeout_certification).toEqual({
      certified_at: "t1",
      certified_by: "cfo",
      note: "-",
    });
  });

  it("normaliza contexto por defeito", () => {
    const out = buildD18CloseoutPayload({
      generatedAt: iso,
      checklistById: {},
      p1Rows: [],
      source: "fiscal/management-daily",
      context: undefined,
      certification: null,
    });
    expect(out.context).toEqual({
      decision_consolidated: "NO_GO",
      risk_level: "UNKNOWN",
      readiness_version: "-",
    });
  });
});

