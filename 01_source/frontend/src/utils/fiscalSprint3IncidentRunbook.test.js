import { describe, expect, it } from "vitest";

import {
  SPRINT3_ASSISTED_SIMULATION_DURATION_MIN,
  SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M,
  SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS,
  SPRINT3_INCIDENT_CHECKLIST,
  SPRINT3_INCIDENT_RUNBOOK_VERSION,
  SPRINT3_PRESENCIAL_DRILL_EVIDENCE_TEMPLATE,
  buildPresencialDrillEvidenceFromForm,
  buildSprint3AssistedSimulationStampPayload,
} from "./fiscalSprint3IncidentRunbook";

describe("fiscalSprint3IncidentRunbook", () => {
  it("runbook v2 e timeline cobre 15 minutos", () => {
    expect(SPRINT3_INCIDENT_RUNBOOK_VERSION).toContain("v3");
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
    expect(p.presencial_drill_template_ref).toBe("SPRINT3_PRESENCIAL_DRILL_EVIDENCE_TEMPLATE");
    expect(p.stamps_count).toBe(1);
  });

  it("stamp payload inclui presencial_drill quando draft traz evidência", () => {
    const draft = {
      incident_id: "inc-2",
      owner: "ops",
      severity: "LOW",
      simulation_stamps: [{ id: "s1", recorded_at: "2026-05-01T10:00:00.000Z" }],
      presencial_drill: buildPresencialDrillEvidenceFromForm(
        {
          agenda_session_id: "p03-drill-20260501-A",
          turn_label: "tabletop",
          participants_lines: "Ana|OPS\nBob|Fiscal",
          signoff_name: "Fac X",
          agenda_started_at: "2026-05-01T14:00:00.000Z",
          agenda_ended_at: "2026-05-01T15:00:00.000Z",
        },
        "2026-05-01T15:00:00.000Z"
      ),
    };
    const p = buildSprint3AssistedSimulationStampPayload("2026-05-01T16:00:00.000Z", "fiscal/management-daily", draft);
    expect(p.presencial_drill?.agenda_session_id).toBe("p03-drill-20260501-A");
    expect(p.presencial_drill?.participants?.length).toBe(2);
  });

  it.skipIf(process.env.P03_SIM_PRESENCIAL !== "1")("modo presencial (P03_SIM_PRESENCIAL): template e comando documentado", () => {
    expect(SPRINT3_PRESENCIAL_DRILL_EVIDENCE_TEMPLATE.participants.length).toBeGreaterThanOrEqual(1);
    expect(SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS.some((c) => c.includes("--presencial"))).toBe(true);
  });

  it("checklist mantém 6 passos", () => {
    expect(SPRINT3_INCIDENT_CHECKLIST).toHaveLength(6);
  });
});
