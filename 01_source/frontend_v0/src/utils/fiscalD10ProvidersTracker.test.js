
import { describe, expect, it } from "vitest";
import {
  FISCAL_D10_TASKS,
  buildD10OpsHandoffPayload,
  buildD10ProvidersEvidencePayload,
  createDefaultD10Tracker,
  d10ProgressFromTracker,
  mergeLsPatchIntoD10Tracker,
  parseD10OpsHandoffFromLocalStorageRaw,
  parseD10TrackerFromLocalStorageRaw,
} from "./fiscalD10ProvidersTracker";

describe("fiscalD10ProvidersTracker", () => {
  it("createDefaultD10Tracker inicializa todas as tarefas a false", () => {
    const t = createDefaultD10Tracker();
    expect(Object.keys(t)).toHaveLength(FISCAL_D10_TASKS.length);
    expect(FISCAL_D10_TASKS.every((row) => t[row.id] === false)).toBe(true);
  });

  it("d10ProgressFromTracker calcula percentagem", () => {
    const base = createDefaultD10Tracker();
    expect(d10ProgressFromTracker(base)).toEqual({ doneCount: 0, progressPct: 0 });
    const half = { ...base, matrix: true, go_no_go_br: true, go_no_go_pt: true };
    expect(d10ProgressFromTracker(half).doneCount).toBe(3);
    expect(d10ProgressFromTracker(half).progressPct).toBe(60);
    const all = Object.fromEntries(FISCAL_D10_TASKS.map((row) => [row.id, true]));
    expect(d10ProgressFromTracker(all)).toEqual({ doneCount: 5, progressPct: 100 });
  });

  it("mergeLsPatchIntoD10Tracker só aplica ids canónicos booleanos", () => {
    const prev = createDefaultD10Tracker();
    const raw = JSON.stringify({
      matrix: true,
      unknown: true,
      handoff: "not-boolean",
    });
    const merged = mergeLsPatchIntoD10Tracker(prev, raw);
    expect(merged.matrix).toBe(true);
    expect(merged.handoff).toBe(false);
    expect("unknown" in merged).toBe(false);
  });

  it("mergeLsPatchIntoD10Tracker com JSON inválido devolve prev", () => {
    const prev = createDefaultD10Tracker();
    expect(mergeLsPatchIntoD10Tracker(prev, "{")).toEqual(prev);
  });

  it("parseD10TrackerFromLocalStorageRaw devolve null sem raw", () => {
    expect(parseD10TrackerFromLocalStorageRaw(null)).toBe(null);
    expect(parseD10TrackerFromLocalStorageRaw("")).toBe(null);
  });

  it("parseD10TrackerFromLocalStorageRaw mescla JSON válido", () => {
    const raw = JSON.stringify({ matrix: true, handoff: true });
    const t = parseD10TrackerFromLocalStorageRaw(raw);
    expect(t?.matrix).toBe(true);
    expect(t?.handoff).toBe(true);
    expect(t?.go_no_go_br).toBe(false);
  });

  it("buildD10ProvidersEvidencePayload inclui scope e progresso", () => {
    const tracker = { ...createDefaultD10Tracker(), matrix: true, go_no_go_br: true };
    const p = buildD10ProvidersEvidencePayload({
      generatedAt: "2026-05-01T12:00:00.000Z",
      source: "/ops/fiscal/providers",
      tracker,
    });
    expect(p.scope).toBe("SPRINT2_D10_PROVIDERS_TRACKER_ATTACH");
    expect(p.generated_at).toBe("2026-05-01T12:00:00.000Z");
    expect(p.progress).toEqual({ doneCount: 2, progressPct: 40 });
    expect(Array.isArray(p.tasks)).toBe(true);
    expect(p.tasks?.length).toBe(FISCAL_D10_TASKS.length);
    expect("go_no_go_snapshot" in p).toBe(false);
  });

  it("buildD10ProvidersEvidencePayload inclui go_no_go_snapshot quando BR/PT passados", () => {
    const p = buildD10ProvidersEvidencePayload({
      generatedAt: "2026-05-01T12:00:00.000Z",
      source: "/ops/fiscal/providers",
      tracker: createDefaultD10Tracker(),
      goNoGoBr: { go_no_go: "GO", summary: "ok" },
      goNoGoPt: { go_no_go: "NO_GO", summary: "warn" },
    });
    expect(p.go_no_go_snapshot?.br?.go_no_go).toBe("GO");
    expect(p.go_no_go_snapshot?.pt?.go_no_go).toBe("NO_GO");
  });

  it("buildD10OpsHandoffPayload inclui scope OPS e amostra de providers", () => {
    const ho = buildD10OpsHandoffPayload({
      generatedAt: "2026-05-01T12:00:00.000Z",
      source: "/ops/fiscal/providers",
      tracker: { ...createDefaultD10Tracker(), matrix: true },
      goNoGoBr: { go_no_go: "GO", summary: "x" },
      providersHealth: {
        items: [{ country: "BR", namespace: "n1", last_status: "OK", last_error_code: "" }],
        canonical_error_codes: ["E1"],
      },
    });
    expect(ho.scope).toBe("SPRINT2_D10_PROVIDERS_OPS_HANDOFF");
    expect(ho.summary?.d10_progress_pct).toBe(20);
    expect(ho.summary?.providers_count).toBe(1);
    expect(ho.d10_tracker_evidence?.scope).toBe("SPRINT2_D10_PROVIDERS_TRACKER_ATTACH");
    expect(Array.isArray(ho.providers_health?.items)).toBe(true);
    expect(ho.providers_health?.items?.[0]?.country).toBe("BR");
  });

  it("parseD10OpsHandoffFromLocalStorageRaw valida scope", () => {
    expect(parseD10OpsHandoffFromLocalStorageRaw(JSON.stringify({ scope: "WRONG" }))).toBe(null);
    const ok = buildD10OpsHandoffPayload({
      generatedAt: "2026-05-01T12:00:00.000Z",
      source: "/ops/fiscal/providers",
      tracker: createDefaultD10Tracker(),
    });
    const parsed = parseD10OpsHandoffFromLocalStorageRaw(JSON.stringify(ok));
    expect(parsed?.scope).toBe("SPRINT2_D10_PROVIDERS_OPS_HANDOFF");
  });
});

