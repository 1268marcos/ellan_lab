/**
 * Sprint 2 — trilha **D10** (governança fiscal OPS): checklist persistido em `localStorage`
 * usado em `OpsFiscalProvidersPage.jsx`.
 */

export const FISCAL_D10_TRACKER_KEY = "ellan_ops_fiscal_d10_tracker_v1";

/** Handoff publicado em OPS (paridade com `ellan_ops_fiscal_d11_handoff_v1`) para `fiscal/management-daily`. */
export const FISCAL_D10_HANDOFF_KEY = "ellan_ops_fiscal_d10_handoff_v1";

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

/**
 * Lê o tracker D10 persistido (mesmo formato que `OpsFiscalProvidersPage` grava em `localStorage`).
 * @param {string | null | undefined} raw
 * @returns {Record<string, boolean> | null} `null` se não houver string válida
 */
export function parseD10TrackerFromLocalStorageRaw(raw) {
  if (!raw || typeof raw !== "string") return null;
  const merged = mergeLsPatchIntoD10Tracker(createDefaultD10Tracker(), raw);
  return merged;
}

/**
 * Payload de evidência Sprint 2 — trilha **D10** (export JSON / anexo ZIP assinado).
 * @param {{ generatedAt: string, source: string, tracker: Record<string, unknown>, goNoGoBr?: { go_no_go?: string, summary?: string } | null, goNoGoPt?: { go_no_go?: string, summary?: string } | null }} args
 */
export function buildD10ProvidersEvidencePayload({ generatedAt, source, tracker, goNoGoBr, goNoGoPt }) {
  const base = createDefaultD10Tracker();
  const map = tracker && typeof tracker === "object" ? tracker : {};
  const normalized = { ...base };
  for (const row of FISCAL_D10_TASKS) {
    if (typeof map[row.id] === "boolean") {
      normalized[row.id] = map[row.id];
    }
  }
  const progress = d10ProgressFromTracker(normalized);
  const tasks = FISCAL_D10_TASKS.map((row) => ({
    id: row.id,
    label: row.label,
    done: Boolean(normalized[row.id]),
  }));
  const snapBr = goNoGoBr && typeof goNoGoBr === "object";
  const snapPt = goNoGoPt && typeof goNoGoPt === "object";
  /** @type {Record<string, unknown>} */
  const out = {
    scope: "SPRINT2_D10_PROVIDERS_TRACKER_ATTACH",
    generated_at: String(generatedAt || new Date().toISOString()),
    source: String(source || "/ops/fiscal/providers"),
    progress,
    tasks,
    tracker: normalized,
  };
  if (snapBr || snapPt) {
    out.go_no_go_snapshot = {
      br: snapBr
        ? {
            go_no_go: String(goNoGoBr.go_no_go || "NO_GO"),
            summary: goNoGoBr.summary != null ? String(goNoGoBr.summary).slice(0, 4000) : "",
          }
        : { go_no_go: "NO_GO", summary: "" },
      pt: snapPt
        ? {
            go_no_go: String(goNoGoPt.go_no_go || "NO_GO"),
            summary: goNoGoPt.summary != null ? String(goNoGoPt.summary).slice(0, 4000) : "",
          }
        : { go_no_go: "NO_GO", summary: "" },
    };
  }
  return out;
}

/**
 * @param {object} [providersHealth]
 * @param {unknown[]} [providersHealth.items] linhas de status do provider (payload `/admin/fiscal/providers/status`)
 * @param {unknown[]} [providersHealth.canonical_error_codes]
 */
export function buildD10OpsHandoffPayload({ generatedAt, source, tracker, goNoGoBr, goNoGoPt, providersHealth }) {
  const evidence = buildD10ProvidersEvidencePayload({
    generatedAt,
    source,
    tracker,
    goNoGoBr,
    goNoGoPt,
  });
  const progress = evidence.progress;
  const providerItems = Array.isArray(providersHealth?.items) ? providersHealth.items : [];
  const summary = {
    d10_progress_pct: progress.progressPct,
    d10_done_count: progress.doneCount,
    d10_total_tasks: FISCAL_D10_TASKS.length,
    providers_count: providerItems.length,
    go_no_go_br: goNoGoBr && typeof goNoGoBr === "object" ? String(goNoGoBr.go_no_go || "NO_GO") : null,
    go_no_go_pt: goNoGoPt && typeof goNoGoPt === "object" ? String(goNoGoPt.go_no_go || "NO_GO") : null,
  };
  const providers_health =
    providersHealth && typeof providersHealth === "object"
      ? {
          items: providerItems.slice(0, 24).map((row) => ({
            country: row?.country,
            namespace: row?.namespace,
            last_status: row?.last_status,
            last_error_code: row?.last_error_code ?? row?.last_error,
          })),
          canonical_error_codes: Array.isArray(providersHealth.canonical_error_codes)
            ? providersHealth.canonical_error_codes.slice(0, 40)
            : [],
        }
      : null;
  return {
    scope: "SPRINT2_D10_PROVIDERS_OPS_HANDOFF",
    generated_at: String(generatedAt || new Date().toISOString()),
    source: String(source || "/ops/fiscal/providers"),
    summary,
    d10_tracker_evidence: evidence,
    providers_health,
  };
}

/**
 * @param {string | null | undefined} raw
 * @returns {Record<string, unknown> | null}
 */
export function parseD10OpsHandoffFromLocalStorageRaw(raw) {
  if (!raw || typeof raw !== "string") return null;
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object") return null;
  if (parsed.scope !== "SPRINT2_D10_PROVIDERS_OPS_HANDOFF") return null;
  return parsed;
}
