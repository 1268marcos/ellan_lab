import { describe, expect, it } from "vitest";
import {
  FISCAL_D10_TASKS,
  createDefaultD10Tracker,
  d10ProgressFromTracker,
  mergeLsPatchIntoD10Tracker,
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
});
