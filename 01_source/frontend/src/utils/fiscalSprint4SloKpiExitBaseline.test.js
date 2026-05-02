import { describe, expect, it } from "vitest";
import {
  FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG,
  SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA,
  SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION,
  SPRINT4_SLO_METRICS_COLLECT_COMMANDS,
} from "./fiscalSprint4SloKpiExitBaseline";

describe("fiscalSprint4SloKpiExitBaseline", () => {
  it("expõe baseline numérico por persona (Sprint 4)", () => {
    expect(SPRINT4_SLO_KPI_EXIT_BASELINE_VERSION).toMatch(/sprint4-slo-kpi-exit-baseline-v1/);
    expect(SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA.length).toBe(7);
    for (const row of SPRINT4_SLO_KPI_EXIT_BASELINE_BY_PERSONA) {
      expect(typeof row.persona).toBe("string");
      expect(typeof row.kpi).toBe("string");
      expect(Number.isFinite(row.value)).toBe(true);
      expect(row.unit.length).toBeGreaterThan(0);
    }
  });

  it("documenta config mínima produção slo-alerts e comandos de coleta", () => {
    expect(FISCAL_SLO_ALERTS_PRODUCTION_MIN_CONFIG.api_endpoints.length).toBeGreaterThanOrEqual(5);
    expect(SPRINT4_SLO_METRICS_COLLECT_COMMANDS.some((l) => l.includes("providers/status"))).toBe(true);
  });
});
