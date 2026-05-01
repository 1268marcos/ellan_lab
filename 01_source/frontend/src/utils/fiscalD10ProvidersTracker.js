/**
 * Sprint 2 — trilha **D10** (governança fiscal OPS): checklist persistido em `localStorage`
 * usado em `OpsFiscalProvidersPage.jsx`.
 */

export const FISCAL_D10_TRACKER_KEY = "ellan_ops_fiscal_d10_tracker_v1";

export const FISCAL_D10_TASKS = Object.freeze([
  { id: "matrix", label: "Matriz pais/tenant/emissor revisada" },
  { id: "go_no_go_br", label: "GO/NO-GO BR validado com evidência" },
  { id: "go_no_go_pt", label: "GO/NO-GO PT validado com evidência" },
  { id: "fallback", label: "Fallback operacional fiscal confirmado" },
  { id: "handoff", label: "Resumo D10 pronto para handoff" },
]);

export function createDefaultD10Tracker() {
  return Object.fromEntries(FISCAL_D10_TASKS.map((item) => [item.id, false]));
}

/**
 * @param {Record<string, unknown>} tracker
 * @returns {{ doneCount: number, progressPct: number }}
 */
export function d10ProgressFromTracker(tracker) {
  const map = tracker && typeof tracker === "object" ? tracker : {};
  const doneCount = FISCAL_D10_TASKS.filter((item) => Boolean(map[item.id])).length;
  const total = FISCAL_D10_TASKS.length;
  const progressPct = total ? Math.round((doneCount / total) * 100) : 0;
  return { doneCount, progressPct };
}

/**
 * Mescla apenas chaves canónicas com boolean vindas do `localStorage`.
 * @param {Record<string, boolean>} prev
 * @param {string} raw JSON string
 */
export function mergeLsPatchIntoD10Tracker(prev, raw) {
  if (!raw || typeof raw !== "string") return prev;
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return prev;
  }
  if (!parsed || typeof parsed !== "object") return prev;
  const out = { ...prev };
  for (const row of FISCAL_D10_TASKS) {
    if (typeof parsed[row.id] === "boolean") {
      out[row.id] = parsed[row.id];
    }
  }
  return out;
}
