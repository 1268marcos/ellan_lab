import { describe, expect, it } from "vitest";

import {
  SPRINT3_ASSISTED_SIMULATION_DURATION_MIN,
  SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M,
  SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS,
  SPRINT3_INCIDENT_CHECKLIST,
  SPRINT3_INCIDENT_RUNBOOK_VERSION,
  buildSprint3AssistedSimulationStampPayload,
} from "./fiscalSprint3IncidentRunbook";

describe("fiscalSprint3IncidentRunbook", () => {
  it("runbook v2 e timeline cobre 15 minutos", () => {
    expect(SPRINT3_INCIDENT_RUNBOOK_VERSION).toContain("v2");
    expect(SPRINT3_ASSISTED_SIMULATION_DURATION_MIN).toBe(15);
    const last = SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M[SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M.length - 1];
    expect(last.minute_end).toBe(15);
    expect(SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M[0].minute_start).toBe(0);
  });

  it("stamp payload inclui SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH e timeline", () => {
    const draft = {
      incident_id: "inc-1",
      owner: "fac",
      severity: "HIGH",
      simulation_scenario: "Teste tabletop",
      simulation_stamps: [{ id: "s1", recorded_at: "2026-05-01T10:00:00.000Z" }],
    };
    const p = buildSprint3AssistedSimulationStampPayload("2026-05-01T12:00:00.000Z", "fiscal/management-daily", draft);
    expect(p.scope).toBe("SPRINT3_P0_3_ASSISTED_SIMULATION_STAMP");
    expect(p.stamp_attach_scope).toBe("SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH");
    expect(p.daily_zip_filename_pattern).toContain("SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH");
    expect(p.simulation_timeline.length).toBeGreaterThanOrEqual(4);
    expect(p.cli_commands_reference).toEqual(SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS);
    expect(p.stamps_count).toBe(1);
  });

  it("checklist mantém 6 passos", () => {
    expect(SPRINT3_INCIDENT_CHECKLIST).toHaveLength(6);
  });
});
