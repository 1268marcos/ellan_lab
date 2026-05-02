/**
 * Sprint 4 — matriz mínima de regressão (por persona).
 * Estado persistido em localStorage e reutilizado por exportações (página + pacotes executivos).
 */

export const SPRINT4_MATRIX_STORAGE_KEY = "ellan_fiscal_sprint4_regression_matrix_v1";
export const SPRINT4_PILOT_RUNS_STORAGE_KEY = "ellan_fiscal_sprint4_pilot_runs_v1";
export const SPRINT4_MATRIX_VERSION = 2;
export const SPRINT4_MATRIX_PAGE_VERSION = "fiscal/sprint4-regression-matrix v1.7.0-kiosk-touch-uat-a-d";
export const SPRINT4_REGRESSION_EXPORT_SCHEMA = "sprint4-regression-matrix-v2";

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
  {
    id: "contabil-daily-close-zip",
    persona: "Contábil",
    area: "Fechamento diário",
    case: "`fiscal/accounting-close` — ZIP executivo com blocos D14/D15/D16 + provisões quando aplicável",
  },
  {
    id: "contabil-approvals-d18-context",
    persona: "Contábil",
    area: "Aceite D18",
    case: "Contexto `FISCAL_ACCOUNTING_DAILY_APPROVAL` coerente com histórico e exports assinados",
  },
  {
    id: "fiscal-management-daily-signed",
    persona: "Fiscal / OPS",
    area: "Pacote diário",
    case: "`fiscal/management-daily` — gerar .zip com anexos Sprint 2/3 previstos (gate mirror, SLO, Sprint4 quando gravado)",
  },
  {
    id: "fiscal-gap-snapshot-smoke",
    persona: "Fiscal / OPS",
    area: "Conciliação",
    case: "Smoke `GET /admin/fiscal/fiscal-gap-conciliation-snapshot` + interpretação de agregados por partner",
  },
  {
    id: "online-checkout-4xx-path",
    persona: "Comprador ONLINE",
    area: "Checkout",
    case: "Erro acionável em 4xx/409 (`public-checkout-order-error`) com retry seguro",
  },
  {
    id: "ops-health-reconciliation-link",
    persona: "OPS",
    area: "Reconciliação OPS",
    case: "Atalho `ops/health` → evidência ou `ops/reconciliation` sem regressão de auth",
  },
  {
    id: "eng-frontend-ci-core",
    persona: "Engenharia Plataforma",
    area: "CI / Qualidade",
    case: "`npm test` + `typecheck:strict-core` verdes no frontend após alterações na matriz fiscal",
  },
];

/** Checklist textual por persona (referência executiva; não depende de localStorage). */
export const SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST = [
  {
    persona: "Comprador ONLINE",
    must_cover: ["Checkout feliz + erro acionável", "Rastreabilidade pedido→invoice", "Caminho 4xx/409"],
  },
  {
    persona: "Comprador KIOSK",
    must_cover: ["Quick Buy + timeout", "Pickup Fast Lane + fallback de slot", "UAT 4 modelos (A–D) marcados"],
  },
  { persona: "OPS", must_cover: ["Triagem + export evidência", "Reconciliação / health sem regressão de auth"] },
  { persona: "Suporte", must_cover: ["Console por jornada + playbook + handoff owner/ETA"] },
  {
    persona: "Parceiros",
    must_cover: ["Onboarding contrato fiscal mínimo", "Amostra settlement × documento"],
  },
  {
    persona: "Fiscal / OPS",
    must_cover: ["SLO export JSON/ZIP", "E2E audit handoff", "Pacote diário assinado", "Smoke gap snapshot"],
  },
  { persona: "Contábil", must_cover: ["ZIP fechamento diário", "Contexto D18 / aprovações"] },
  { persona: "Engenharia Plataforma", must_cover: ["CI core (Vitest + strict-core) após mudanças na trilha fiscal"] },
];

/**
 * UAT touch documentado (manual + âncoras E2E). Espelhado no ZIP `SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D`.
 * @type {{ id: string, label: string, default_note_hint: string, manual_steps: string[], e2e_anchors: string[] }[]}
 */
export const SPRINT4_KIOSK_UAT_MODELS = [
  {
    id: "model_a_quick_buy",
    label: "Modelo A — Quick Buy",
    default_note_hint: "Registar order_id, locker PT, captura catálogo /comprar.",
    manual_steps: [
      "Viewport totem 1080×1920; abrir `/ops/kiosk-touch-models` com auth OPS.",
      "Modelo A → CTA abre `/comprar`; vitrine com slot selecionável (lab: mocks conforme `e2e/kiosk-touch-models.spec.ts`).",
      "Fluxo feliz até pedido criado; validar MB WAY / instrução e ausência de erro de layout em touch.",
      "Simular timeout ou falha de rede leve; confirmar retry seguro sem estado preso.",
    ],
    e2e_anchors: ['Modelo A — CTA primário abre catálogo /comprar', "e2e/kiosk-touch-models.spec.ts"],
  },
  {
    id: "model_b_guided_buy",
    label: "Modelo B — Guided Buy",
    default_note_hint: "Registar se checkout inválido sem query é esperado em lab; anexar path guiado.",
    manual_steps: [
      "Modelo B → CTA abre `/checkout` (lab: sem query mínima → `public-checkout-invalid` documentado).",
      "Percorrer passos guiados até revisão; validar mensagens de validação acionáveis em touch.",
      "Confirmar correlação `order_id` ou bloqueio explícito antes de submit quando aplicável.",
    ],
    e2e_anchors: [
      "Modelo B — CTA primário abre /checkout (laboratório; sem query → checkout inválido)",
      "e2e/kiosk-touch-models.spec.ts",
    ],
  },
  {
    id: "model_c_pickup_fast_lane",
    label: "Modelo C — Pickup Fast Lane",
    default_note_hint: "Anexar comprovante simulado/impresso, passo identify e redeem-manual.",
    manual_steps: [
      "Modelo C → `/ops/pt/kiosk`; mocks ou backend: lockers PT, catálogo, slots AVAILABLE.",
      "Criar pedido + gateway APPROVED + payment-approved + identify + `/api/op/totem/pickups/redeem-manual` (ver testes mock completos no spec).",
      "Validar impressão simulada (lab) ou evidência fotográfica do comprovante (campo).",
      "Executar variante só retirada manual isolada quando o turno validar apenas pickup.",
    ],
    e2e_anchors: [
      "Modelo C — KIOSK PT: pedido, pagamento (APPROVED), identificação e retirada manual (mocks)",
      "Trilha E — totem físico: impressão + identificação + retirada (redeem) no mesmo fluxo",
      "e2e/kiosk-touch-models.spec.ts",
    ],
  },
  {
    id: "model_d_partner_allocation",
    label: "Modelo D — Partner Allocation",
    default_note_hint: "Registar slot alvo, SKU e resposta POST alocação (print ou ID de gaveta).",
    manual_steps: [
      "Modelo D → `/ops/dev/slots` via CTA do cockpit (rota dev slots do spec).",
      "Grelha de gavetas legível em touch; selecionar slot AVAILABLE; alocar SKU de teste.",
      "Confirmar persistência visual e payload de alocação (evidência: HAR, screenshot ou ID de slot).",
    ],
    e2e_anchors: [
      "Modelo D — dev slots: grelha de gavetas + alocar SKU (fluxo físico assistido)",
      "e2e/kiosk-touch-models.spec.ts",
    ],
  },
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

/**
 * Cobertura combinada matriz (70%) + UAT KIOSK (30%) para narrativa Sprint 4.
 * @param {{ done: number, total: number }} matrixProgress
 * @param {{ pass: number, total: number }} kioskProgress
 */
export function computeSprint4CombinedFunctionalPct(matrixProgress, kioskProgress) {
  const m = matrixProgress?.total > 0 ? matrixProgress.done / matrixProgress.total : 0;
  const k = kioskProgress?.total > 0 ? kioskProgress.pass / kioskProgress.total : 0;
  return Math.round((m * 0.7 + k * 0.3) * 1000) / 10;
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
 * Anexa ao ZIP diário (opcional) JSONs assinados da matriz Sprint 4 + resumo Go/No-Go + checklist por persona + histórico de pilotos, se existirem em localStorage.
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
    const signedChecklist = await buildSignedPayload(buildSprint4PersonaFunctionalChecklistPayload(nowIso, matrixStored));
    zipEntries[`${fileBasePrefix}_SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_${ts}.json`] = strToU8(JSON.stringify(signedChecklist, null, 2));
    attached.push("sprint4_persona_functional_checklist");
    const signedKioskTouch = await buildSignedPayload(buildSprint4KioskTouchUatModelsPayload(nowIso, matrixStored));
    zipEntries[`${fileBasePrefix}_SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D_${ts}.json`] = strToU8(JSON.stringify(signedKioskTouch, null, 2));
    attached.push("sprint4_kiosk_touch_uat_models");
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
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    storage: { key: SPRINT4_MATRIX_STORAGE_KEY },
    owner: full.owner,
    matrix_progress: full.progress,
    kiosk_uat: full.kiosk_uat.progress,
    combined_functional_pct: full.combined_functional_pct,
    kiosk_touch_uat_export_scope: "SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D",
    go_no_go_register: full.go_no_go_register,
  };
}

/**
 * Export dedicado: checklist por persona (texto de referência + contagens atuais).
 */
export function buildSprint4PersonaFunctionalChecklistPayload(nowIso, storedState) {
  const full = buildSprint4RegressionMatrixPayload(nowIso, storedState);
  return {
    scope: "SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST",
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    reference: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
    persona_rollups: full.personas,
    matrix_progress: full.progress,
    kiosk_uat: full.kiosk_uat.progress,
    combined_functional_pct: full.combined_functional_pct,
  };
}

/**
 * UAT KIOSK touch A–D: protocolo manual documentado + estado PASS/nota por modelo (evidência no ZIP diário/executivo).
 */
export function buildSprint4KioskTouchUatModelsPayload(nowIso, storedState) {
  const full = buildSprint4RegressionMatrixPayload(nowIso, storedState);
  return {
    scope: "SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D",
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    manual_protocol: SPRINT4_KIOSK_UAT_MODELS.map(({ id, label, manual_steps, e2e_anchors, default_note_hint }) => ({
      model_id: id,
      label,
      manual_steps,
      e2e_anchors,
      default_note_hint,
    })),
    kiosk_uat_execution: full.kiosk_uat,
    combined_functional_pct: full.combined_functional_pct,
    zip_attachment_hint: "ELLAN_FISCAL_DAILY_*_SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D_*.json",
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
  const combinedPct = computeSprint4CombinedFunctionalPct(progress, kioskUatProgress);
  const goNoGo = storedState?.go_no_go && typeof storedState.go_no_go === "object" ? storedState.go_no_go : {};

  return {
    scope: "SPRINT4_REGRESSION_MATRIX",
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    storage: {
      key: SPRINT4_MATRIX_STORAGE_KEY,
      version: Number(storedState?.version || SPRINT4_MATRIX_VERSION),
      updated_at: String(storedState?.updated_at || ""),
    },
    owner,
    progress,
    combined_functional_pct: combinedPct,
    persona_functional_checklist: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
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
