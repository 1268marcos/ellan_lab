
import { describe, expect, it } from "vitest";
import {
  SPRINT2_FINANCE_GATE_V2_STORAGE_KEY,
  SPRINT2_FINANCE_GATE_V2_THRESHOLDS,
  clampSprint2GatePct,
  loadSprint2FinanceGateV2State,
  summarizeSprint2FinanceGateV2,
} from "./fiscalSprint2FinanceGate";

describe("clampSprint2GatePct", () => {
  it("arredonda e limita ao intervalo 0–100", () => {
    expect(clampSprint2GatePct(27.4)).toBe(27);
    expect(clampSprint2GatePct(-5)).toBe(0);
    expect(clampSprint2GatePct(100.9)).toBe(100);
  });

  it("NaN e não-numérico viram 0", () => {
    expect(clampSprint2GatePct(Number.NaN)).toBe(0);
    expect(clampSprint2GatePct(undefined)).toBe(0);
    expect(clampSprint2GatePct("x")).toBe(0);
  });
});

describe("summarizeSprint2FinanceGateV2", () => {
  it("retorna null para entrada inválida", () => {
    expect(summarizeSprint2FinanceGateV2(null)).toBeNull();
    expect(summarizeSprint2FinanceGateV2(undefined)).toBeNull();
    expect(summarizeSprint2FinanceGateV2("x")).toBeNull();
  });

  it("aplica percentuais por defeito quando campos faltam", () => {
    const s = summarizeSprint2FinanceGateV2({});
    expect(s).not.toBeNull();
    expect(s.fiscal_percent).toBe(26);
    expect(s.accounting_percent).toBe(15);
    expect(s.consolidated_percent).toBe(52);
    expect(s.overall_pass).toBe(false);
  });

  it("PASS só com três limiares e nota P0 ≥24 caracteres", () => {
    const pass = summarizeSprint2FinanceGateV2({
      fiscal_percent: 50,
      accounting_percent: 40,
      consolidated_percent: 55,
      p0_evidence_note: "x".repeat(24),
      updated_at: "2026-05-01T12:00:00Z",
    });
    expect(pass.fiscal_ok).toBe(true);
    expect(pass.accounting_ok).toBe(true);
    expect(pass.consolidated_ok).toBe(true);
    expect(pass.p0_evidence_ok).toBe(true);
    expect(pass.overall_pass).toBe(true);
    expect(pass.updated_at).toBe("2026-05-01T12:00:00Z");
  });

  it("falha P0 com nota curta (<24) mesmo com percentuais altos", () => {
    const s = summarizeSprint2FinanceGateV2({
      fiscal_percent: 80,
      accounting_percent: 80,
      consolidated_percent: 80,
      p0_evidence_note: "curta",
    });
    expect(s.p0_evidence_ok).toBe(false);
    expect(s.overall_pass).toBe(false);
  });

  it("falha se qualquer limiar v2 estiver abaixo", () => {
    const longNote = "Nota operacional com mais de vinte e quatro chars.";
    const s = summarizeSprint2FinanceGateV2({
      fiscal_percent: SPRINT2_FINANCE_GATE_V2_THRESHOLDS.fiscal - 1,
      accounting_percent: SPRINT2_FINANCE_GATE_V2_THRESHOLDS.accounting,
      consolidated_percent: SPRINT2_FINANCE_GATE_V2_THRESHOLDS.consolidated,
      p0_evidence_note: longNote,
    });
    expect(s.fiscal_ok).toBe(false);
    expect(s.overall_pass).toBe(false);
  });
});

describe("loadSprint2FinanceGateV2State", () => {
  it("retorna null quando não há estado", () => {
    expect(loadSprint2FinanceGateV2State()).toBeNull();
  });

  it("lê JSON válido do localStorage", () => {
    const payload = { fiscal_percent: 30, p0_evidence_note: "x".repeat(30) };
    window.localStorage.setItem(SPRINT2_FINANCE_GATE_V2_STORAGE_KEY, JSON.stringify(payload));
    expect(loadSprint2FinanceGateV2State()).toEqual(payload);
  });

  it("retorna null quando JSON é inválido", () => {
    window.localStorage.setItem(SPRINT2_FINANCE_GATE_V2_STORAGE_KEY, "{");
    expect(loadSprint2FinanceGateV2State()).toBeNull();
  });
});

