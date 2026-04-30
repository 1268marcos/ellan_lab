/**
 * Sprint 4 — matriz mínima de regressão (por persona).
 * Estado persistido em localStorage e reutilizado por exportações (página + pacotes executivos).
 */

export const SPRINT4_MATRIX_STORAGE_KEY = "ellan_fiscal_sprint4_regression_matrix_v1";
export const SPRINT4_PILOT_RUNS_STORAGE_KEY = "ellan_fiscal_sprint4_pilot_runs_v1";
export const SPRINT4_MATRIX_VERSION = 1;
export const SPRINT4_MATRIX_PAGE_VERSION = "fiscal/sprint4-regression-matrix v1.4.0-gonogo-summary";

/** Limite de tamanho (chars JSON do payload sem assinatura) para anexar histórico de pilotos no pacote diário. */
export const SPRINT4_ATTACH_MAX_HISTORY_JSON_CHARS = 120_000;

export const SPRINT4_MATRIX_DEFAULT_ITEMS = [
  {
    id: "online-checkout-payment",
    persona: "Comprador ONLINE",
    area: "Checkout / Pagamento",
    case: "Fluxo feliz + erro acionável + retry seguro",
  },
  {
    id: "online-order-traceability",
    persona: "Comprador ONLINE",
    area: "Pedido / Invoice",
    case: "Rastreabilidade: `order_id` + `invoice_id` + notificações",
  },
  {
    id: "kiosk-quick-buy",
    persona: "Comprador KIOSK",
    area: "Quick Buy",
    case: "Compra rápida + confirmação + recuperação de timeout",
  },
  {
    id: "kiosk-pickup-fast-lane",
    persona: "Comprador KIOSK",
    area: "Pickup Fast Lane",
    case: "Retirada por QR/código + erro de slot + fallback",
  },
  {
    id: "ops-unified-triage",
    persona: "OPS",
    area: "Painel / Incidentes",
    case: "Triagem com macro + export de evidência + lookup (quando configurado)",
  },
  {
    id: "support-journey-console",
    persona: "Suporte",
    area: "Console por jornada",
    case: "Caso recorrente com playbook + handoff com owner/ETA",
  },
  {
    id: "partner-contract-onboarding",
    persona: "Parceiros",
    area: "Onboarding",
    case: "Contrato fiscal mínimo + campos obrigatórios sem bypass manual",
  },
  {
    id: "partner-reconciliation-sample",
    persona: "Parceiros",
    area: "Reconciliação",
    case: "Amostra de settlement x documento fiscal com classificação",
  },
  {
    id: "fiscal-slo-scorecard-export",
    persona: "Fiscal / OPS",
    area: "SLO",
    case: "`/fiscal/slo-alerts` export JSON/ZIP + severidade coerente com thresholds da janela",
  },
  {
    id: "fiscal-e2e-audit-handoff",
    persona: "Fiscal / OPS",
    area: "Auditoria E2E",
    case: "Export evidência única P0-1 + cobertura materializada consultável",
  },
];

export const SPRINT4_KIOSK_UAT_MODELS = [
  { id: "model_a_quick_buy", label: "Modelo A — Quick Buy" },
  { id: "model_b_guided_buy", label: "Modelo B — Guided Buy" },
  { id: "model_c_pickup_fast_lane", label: "Modelo C — Pickup Fast Lane" },
  { id: "model_d_partner_allocation", label: "Modelo D — Partner Allocation" },
];

export function loadSprint4MatrixStateRaw() {
  try {
    const raw = window.localStorage.getItem(SPRINT4_MATRIX_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function mergeSprint4MatrixRows(savedRows) {
  const byId = new Map();
  if (savedRows && typeof savedRows === "object") {
    for (const [id, value] of Object.entries(savedRows)) {
      byId.set(id, value);
    }
  }
  return SPRINT4_MATRIX_DEFAULT_ITEMS.map((item) => {
    const prev = byId.get(item.id) || {};
    return {
      ...item,
      done: Boolean(prev.done),
      note: String(prev.note || ""),
      last_marked_at: prev.last_marked_at || null,
    };
  });
}

export function computeSprint4MatrixProgress(rows) {
  const total = rows.length;
  const done = rows.filter((r) => r.done).length;
  const pct = total > 0 ? Math.round((done / total) * 1000) / 10 : 0;
  return { total, done, pct };
}

/**
 * @param {Record<string, { pass?: boolean, note?: string, marked_at?: string }> | null | undefined} savedRows
 */
export function mergeSprint4KioskUatRows(savedRows) {
  const map = savedRows && typeof savedRows === "object" ? savedRows : {};
  return SPRINT4_KIOSK_UAT_MODELS.map((model) => {
    const prev = map[model.id] || {};
    return {
      ...model,
      pass: Boolean(prev.pass),
      note: String(prev.note || ""),
      marked_at: prev.marked_at || null,
    };
  });
}

export function computeSprint4KioskUatProgress(rows) {
  const total = rows.length;
  const pass = rows.filter((r) => r.pass).length;
  const pct = total > 0 ? Math.round((pass / total) * 1000) / 10 : 0;
  return { total, pass, pct, all_pass: total > 0 && pass === total };
}

export function computeSprint4PersonaRollup(rows) {
  /** @type {Map<string, { persona: string, done: number, total: number }>} */
  const map = new Map();
  for (const r of rows) {
    const persona = String(r?.persona || "UNKNOWN").trim() || "UNKNOWN";
    const cur = map.get(persona) || { persona, done: 0, total: 0 };
    cur.total += 1;
    if (r.done) cur.done += 1;
    map.set(persona, cur);
  }
  return Array.from(map.values()).sort((a, b) => a.persona.localeCompare(b.persona));
}

export function loadSprint4PilotRunsRaw() {
  try {
    const raw = window.localStorage.getItem(SPRINT4_PILOT_RUNS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * @param {object[]} runs
 */
export function saveSprint4PilotRuns(runs) {
  const capped = runs.slice(-25);
  window.localStorage.setItem(SPRINT4_PILOT_RUNS_STORAGE_KEY, JSON.stringify(capped));
  return capped;
}

/**
 * @param {object} run
 */
export function appendSprint4PilotRun(run) {
  const next = [...loadSprint4PilotRunsRaw(), run];
  return saveSprint4PilotRuns(next);
}

/**
 * Histórico de rodadas piloto (paralelo seguro Sprint 4).
 * Payload “fonte” (sem envelope de integridade).
 */
export function buildSprint4PilotHistoryPayload(nowIso, runs) {
  return {
    scope: "SPRINT4_REGRESSION_PILOT_HISTORY",
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    storage: {
      key: SPRINT4_PILOT_RUNS_STORAGE_KEY,
    },
    runs_count: runs.length,
    runs: runs.map((r) => ({
      id: r.id,
      recorded_at: r.recorded_at,
      label: r.label,
      environment: r.environment,
      outcome: r.outcome,
      owner: r.owner,
      notes: r.notes,
      matrix_progress: r.matrix_progress || null,
      persona_progress: r.persona_progress || [],
    })),
  };
}

/**
 * Última rodada piloto isolada (clipboard / evidência pontual).
 */
export function buildSprint4LastPilotRunPayload(nowIso, run) {
  return {
    scope: "SPRINT4_REGRESSION_PILOT_RUN_LATEST",
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    storage: {
      key: SPRINT4_PILOT_RUNS_STORAGE_KEY,
    },
    run: {
      id: run.id,
      recorded_at: run.recorded_at,
      label: run.label,
      environment: run.environment,
      outcome: run.outcome,
      owner: run.owner,
      notes: run.notes,
      matrix_progress: run.matrix_progress || null,
      persona_progress: run.persona_progress || [],
    },
  };
}

/**
 * Só histórico de rodadas piloto Sprint 4 (a matriz pode ir noutro ficheiro do mesmo ZIP, ex. `*_EXEC_REGRESSION_MATRIX_*`).
 *
 * @param {object} opts
 * @param {(p: object) => Promise<object>} opts.buildSignedPayload
 * @param {(s: string) => Uint8Array} opts.strToU8
 * @param {string} opts.fileBasePrefix
 * @param {string} opts.ts
 * @param {string} opts.nowIso
 * @param {Record<string, Uint8Array>} opts.zipEntries
 * @param {string} [opts.source] origem para metadados / artefato SKIPPED
 * @returns {Promise<{ attached: string[] }>}
 */
export async function appendSprint4PilotHistoryOptionalSignedZipEntries({
  buildSignedPayload,
  strToU8,
  fileBasePrefix,
  ts,
  nowIso,
  zipEntries,
  source = "fiscal/management-daily",
}) {
  const runs = loadSprint4PilotRunsRaw();
  if (runs.length === 0) {
    return { attached: [] };
  }

  /** @type {string[]} */
  const attached = [];
  const pilotPayload = buildSprint4PilotHistoryPayload(nowIso, runs);
  const raw = JSON.stringify(pilotPayload);
  if (raw.length > SPRINT4_ATTACH_MAX_HISTORY_JSON_CHARS) {
    const signedSkip = await buildSignedPayload({
      scope: "SPRINT4_PILOT_HISTORY_ATTACH_SKIPPED",
      generated_at: nowIso,
      source,
      reason: "payload_exceeds_max_chars",
      max_chars: SPRINT4_ATTACH_MAX_HISTORY_JSON_CHARS,
      observed_chars: raw.length,
      runs_count: runs.length,
    });
    zipEntries[`${fileBasePrefix}_SPRINT4_PILOT_HISTORY_ATTACH_SKIPPED_${ts}.json`] = strToU8(JSON.stringify(signedSkip, null, 2));
    attached.push("sprint4_pilot_skipped");
  } else {
    const signedPilot = await buildSignedPayload(pilotPayload);
    zipEntries[`${fileBasePrefix}_SPRINT4_PILOT_HISTORY_ATTACH_${ts}.json`] = strToU8(JSON.stringify(signedPilot, null, 2));
    attached.push("sprint4_pilot_history");
  }

  return { attached };
}

/**
 * Anexa ao ZIP diário (opcional) JSONs assinados da matriz Sprint 4 + histórico de pilotos, se existirem em localStorage.
 * Se o histórico exceder o limite, grava artefato `*_ATTACH_SKIPPED_*` em vez do payload completo.
 *
 * @param {object} opts
 * @param {(p: object) => Promise<object>} opts.buildSignedPayload
 * @param {(s: string) => Uint8Array} opts.strToU8
 * @param {string} opts.fileBasePrefix ex.: ELLAN_FISCAL_DAILY_20260430
 * @param {string} opts.ts
 * @param {string} opts.nowIso
 * @param {Record<string, Uint8Array>} opts.zipEntries
 * @param {string} [opts.source] origem para pilotos SKIPPED (default management-daily)
 * @returns {Promise<{ attached: string[] }>}
 */
export async function appendSprint4OptionalSignedZipEntries({
  buildSignedPayload,
  strToU8,
  fileBasePrefix,
  ts,
  nowIso,
  zipEntries,
  source = "fiscal/management-daily",
}) {
  const matrixStored = loadSprint4MatrixStateRaw();
  const runs = loadSprint4PilotRunsRaw();
  if (!matrixStored && runs.length === 0) {
    return { attached: [] };
  }

  /** @type {string[]} */
  const attached = [];

  if (matrixStored && typeof matrixStored === "object") {
    const matrixPayload = buildSprint4RegressionMatrixPayload(nowIso, matrixStored);
    const signedMatrix = await buildSignedPayload(matrixPayload);
    const name = `${fileBasePrefix}_SPRINT4_REGRESSION_MATRIX_ATTACH_${ts}.json`;
    zipEntries[name] = strToU8(JSON.stringify(signedMatrix, null, 2));
    attached.push("sprint4_matrix");
    const signedGoNoGo = await buildSignedPayload(buildSprint4GoNoGoRegisterSummaryPayload(nowIso, matrixStored));
    zipEntries[`${fileBasePrefix}_SPRINT4_GO_NO_GO_REGISTER_${ts}.json`] = strToU8(JSON.stringify(signedGoNoGo, null, 2));
    attached.push("sprint4_go_no_go_summary");
  }

  if (runs.length > 0) {
    const pilotAttached = await appendSprint4PilotHistoryOptionalSignedZipEntries({
      buildSignedPayload,
      strToU8,
      fileBasePrefix,
      ts,
      nowIso,
      zipEntries,
      source,
    });
    attached.push(...pilotAttached.attached);
  }

  return { attached };
}

/**
 * Resumo executivo Sprint 4: decisão Go/No-Go + UAT KIOSK + progresso da matriz (sem lista completa de itens).
 */
export function buildSprint4GoNoGoRegisterSummaryPayload(nowIso, storedState) {
  const full = buildSprint4RegressionMatrixPayload(nowIso, storedState);
  return {
    scope: "SPRINT4_GO_NO_GO_REGISTER_SUMMARY",
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    storage: { key: SPRINT4_MATRIX_STORAGE_KEY },
    owner: full.owner,
    matrix_progress: full.progress,
    kiosk_uat: full.kiosk_uat.progress,
    go_no_go_register: full.go_no_go_register,
  };
}

/**
 * Payload “fonte” (sem envelope de integridade). O caller costuma embrulhar com `buildSignedPayload`.
 */
export function buildSprint4RegressionMatrixPayload(nowIso, storedState) {
  const rows = mergeSprint4MatrixRows(storedState?.rows || {});
  const kioskUatRows = mergeSprint4KioskUatRows(storedState?.kiosk_uat?.models || {});
  const owner = String(storedState?.owner || "").trim() || "-";
  const progress = computeSprint4MatrixProgress(rows);
  const kioskUatProgress = computeSprint4KioskUatProgress(kioskUatRows);
  const personas = computeSprint4PersonaRollup(rows);
  const goNoGo = storedState?.go_no_go && typeof storedState.go_no_go === "object" ? storedState.go_no_go : {};

  return {
    scope: "SPRINT4_REGRESSION_MATRIX",
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    storage: {
      key: SPRINT4_MATRIX_STORAGE_KEY,
      version: Number(storedState?.version || SPRINT4_MATRIX_VERSION),
      updated_at: String(storedState?.updated_at || ""),
    },
    owner,
    progress,
    personas,
    kiosk_uat: {
      progress: kioskUatProgress,
      models: kioskUatRows.map((item) => ({
        id: item.id,
        label: item.label,
        pass: item.pass,
        note: item.note,
        marked_at: item.marked_at,
      })),
    },
    go_no_go_register: {
      decision: String(goNoGo.decision || "PENDING_REVIEW"),
      residual_risk: String(goNoGo.residual_risk || "MEDIUM"),
      mitigation_plan: String(goNoGo.mitigation_plan || "").trim() || "-",
      owner: String(goNoGo.owner || owner || "-"),
      updated_at: String(goNoGo.updated_at || ""),
      ready_hint: kioskUatProgress.all_pass ? "UAT_KIOSK_OK" : "UAT_KIOSK_PENDING",
    },
    items: rows.map((r) => ({
      id: r.id,
      persona: r.persona,
      area: r.area,
      case: r.case,
      done: r.done,
      note: r.note,
      last_marked_at: r.last_marked_at,
    })),
  };
}
