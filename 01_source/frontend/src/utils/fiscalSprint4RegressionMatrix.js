/**
 * Sprint 4 — matriz mínima de regressão (por persona).
 * Estado persistido em localStorage e reutilizado por exportações (página + pacotes executivos).
 */

export const SPRINT4_MATRIX_STORAGE_KEY = "ellan_fiscal_sprint4_regression_matrix_v1";
export const SPRINT4_PILOT_RUNS_STORAGE_KEY = "ellan_fiscal_sprint4_pilot_runs_v1";
export const SPRINT4_MATRIX_VERSION = 4;
export const SPRINT4_MATRIX_PAGE_VERSION = "fiscal/sprint4-regression-matrix v1.12.0-persona-presencial-signoff";
/** Número de casos na matriz mínima Sprint 4 (regressão funcional por persona). */
export const SPRINT4_MATRIX_N_CASES = 21;
export const SPRINT4_REGRESSION_EXPORT_SCHEMA = "sprint4-regression-matrix-v4";
/** Schema do bloco `reference` em `SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST` (JSON assinado). */
export const SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA = "sprint4-persona-functional-checklist-v2-presencial-signoff";

/** Padrões de nome no ZIP executivo / diário (prefixo `ELLAN_FISCAL_DAILY_{YYYYMMDD}_` + sufixo `_{ts}.json`). */
export const SPRINT4_EXEC_ZIP_ATTACHMENT_STEMS = [
  "SPRINT4_EXEC_REGRESSION_MATRIX",
  "SPRINT4_REGRESSION_MATRIX_ATTACH",
  "SPRINT4_GO_NO_GO_REGISTER",
  "SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST",
  "SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D",
  "SPRINT4_PILOT_HISTORY_ATTACH",
  "SPRINT4_PILOT_HISTORY",
];

/** Schema do resumo executivo Go/No-Go (JSON assinado). */
export const SPRINT4_GO_NO_GO_REGISTER_SUMMARY_SCHEMA = "sprint4-go-no-go-register-summary-v1-final";

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
  {
    id: "online-catalog-public-smoke",
    persona: "Comprador ONLINE",
    area: "Catálogo público",
    case: "`/comprar` ou catálogo regional — smoke sem regressão de preço visível + `data-testid` críticos",
  },
  {
    id: "kiosk-touch-models-page-smoke",
    persona: "Comprador KIOSK",
    area: "Cockpit touch",
    case: "`/ops/kiosk-touch-models` — 4 modelos A–D navegáveis + CTAs alinhados a `e2e/kiosk-touch-models.spec.ts`",
  },
  {
    id: "ops-quick-enablement-zip-scope",
    persona: "OPS",
    area: "Treino Sprint 3",
    case: "`/ops/quick-enablement` — checklist + export JSON com scope `SPRINT3_OPS_SUPPORT_QUICK_TRAINING`",
  },
  {
    id: "fiscal-readiness-exec-page-smoke",
    persona: "Fiscal / OPS",
    area: "Readiness execução",
    case: "`/fiscal/readiness-execution` — estado EXEC + export sem regressão de storage keys Sprint 4",
  },
];

/**
 * Checklist por persona: `must_cover` (texto) + `matrix_case_ids` (ligação explícita à matriz).
 * @type {{ persona: string, must_cover: string[], matrix_case_ids: string[] }[]}
 */
export const SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST = [
  {
    persona: "Comprador ONLINE",
    must_cover: ["Checkout feliz + erro acionável", "Rastreabilidade pedido→invoice", "Caminho 4xx/409", "Catálogo / comprar smoke"],
    matrix_case_ids: [
      "online-checkout-payment",
      "online-order-traceability",
      "online-checkout-4xx-path",
      "online-catalog-public-smoke",
    ],
  },
  {
    persona: "Comprador KIOSK",
    must_cover: ["Quick Buy + timeout", "Pickup Fast Lane + fallback de slot", "Cockpit touch A–D + E2E anchors", "UAT 4 modelos (A–D) marcados"],
    matrix_case_ids: ["kiosk-quick-buy", "kiosk-pickup-fast-lane", "kiosk-touch-models-page-smoke"],
  },
  {
    persona: "OPS",
    must_cover: ["Triagem + export evidência", "Reconciliação / health sem regressão de auth", "Treino rápido + ZIP Sprint 3"],
    matrix_case_ids: ["ops-unified-triage", "ops-health-reconciliation-link", "ops-quick-enablement-zip-scope"],
  },
  {
    persona: "Suporte",
    must_cover: ["Console por jornada + playbook + handoff owner/ETA"],
    matrix_case_ids: ["support-journey-console"],
  },
  {
    persona: "Parceiros",
    must_cover: ["Onboarding contrato fiscal mínimo", "Amostra settlement × documento"],
    matrix_case_ids: ["partner-contract-onboarding", "partner-reconciliation-sample"],
  },
  {
    persona: "Fiscal / OPS",
    must_cover: [
      "SLO export JSON/ZIP",
      "E2E audit handoff",
      "Pacote diário assinado",
      "Smoke gap snapshot",
      "Readiness execution smoke",
    ],
    matrix_case_ids: [
      "fiscal-slo-scorecard-export",
      "fiscal-e2e-audit-handoff",
      "fiscal-management-daily-signed",
      "fiscal-gap-snapshot-smoke",
      "fiscal-readiness-exec-page-smoke",
    ],
  },
  {
    persona: "Contábil",
    must_cover: ["ZIP fechamento diário", "Contexto D18 / aprovações"],
    matrix_case_ids: ["contabil-daily-close-zip", "contabil-approvals-d18-context"],
  },
  {
    persona: "Engenharia Plataforma",
    must_cover: ["CI core (Vitest + strict-core) após mudanças na trilha fiscal"],
    matrix_case_ids: ["eng-frontend-ci-core"],
  },
];

/**
 * Normaliza evidência de rodadas presenciais por persona (checklist funcional assinado).
 * @param {unknown} raw
 * @returns {{ session_id: string, facilitator_name: string, session_signed_at: string, persona_signoffs: { persona: string, signer_name: string, signer_role: string, signed_at: string, location: string }[] } | null}
 */
export function normalizePresencialFunctionalChecklist(raw) {
  if (!raw || typeof raw !== "object") return null;
  const session_id = String(raw.session_id || "").trim();
  const facilitator_name = String(raw.facilitator_name || "").trim();
  const session_signed_at = String(raw.session_signed_at || "").trim();
  if (!session_id || !facilitator_name || !session_signed_at) return null;
  const persona_signoffs = Array.isArray(raw.persona_signoffs)
    ? raw.persona_signoffs.map((r) => ({
        persona: String(r?.persona || "").trim(),
        signer_name: String(r?.signer_name || "").trim(),
        signer_role: String(r?.signer_role || "").trim(),
        signed_at: String(r?.signed_at || "").trim(),
        location: String(r?.location || "").trim(),
      }))
    : [];
  return { session_id, facilitator_name, session_signed_at, persona_signoffs };
}

/**
 * UAT touch documentado (manual + âncoras E2E). Espelhado no ZIP `SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D`.
 * @type {{ id: string, label: string, default_note_hint: string, manual_steps: string[], e2e_anchors: string[] }[]}
 */
/** Riscos residuais explícitos (marcação no cockpit + JSON `SPRINT4_GO_NO_GO_REGISTER_SUMMARY`). */
export const SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG = [
  { id: "rr_gate_v2_prod", title: "Gate v2 financeiro não comprovado em produção real" },
  { id: "rr_kiosk_hw", title: "KIOSK touch sem sessão presencial / hardware físico validado" },
  { id: "rr_slo_calibration", title: "SLO fiscal / KPI de saída sem calibragem regional presencial" },
  { id: "rr_partner_edge", title: "Parceiros edge-case (reconciliação, provisões) fora da amostra piloto" },
  { id: "rr_auth_browser_zip", title: "Dependência de token interno / browser para ZIP auditável completo" },
  { id: "rr_p03_stamp", title: "P0-3 / simulação assistida sem evidência anexada ao último daily" },
  {
    id: "rr_legal_committee_rubric",
    title: "Rubrica legal / acta de comité presencial Go/No-Go não arquivada (fora do escopo só digital)",
  },
];

/** Tópicos de mitigação pré-definidos (complementam o texto livre). */
export const SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY = [
  { id: "mt_zip_daily", label: "Anexar pacote diário (ZIP) com P0-1b + Sprint 4 + P0-3 a cada turno crítico" },
  { id: "mt_owner_eta", label: "Owner + ETA explícitos por risco aberto no plano de mitigação (texto livre)" },
  { id: "mt_rollback", label: "Plano de rollback / feature flag documentado para NO_GO" },
  { id: "mt_pilot_extra", label: "Rodadas piloto adicionais com outcome PASS/PARTIAL/FAIL registradas" },
  { id: "mt_ops_handoff", label: "Handoff OPS/Suporte formal (Slack) com correlation_id / order_id" },
  { id: "mt_gate_review", label: "Revisão comité gate v2 antes de promover GO a produção" },
  {
    id: "mt_legal_committee_act",
    label: "Acta / rubrica legal presencial do Go/No-Go arquivada (referência externa ao ZIP)",
  },
];

/**
 * @param {unknown} goNoGo
 * @returns {{
 *   decision: string,
 *   residual_risk: string,
 *   mitigation_plan: string,
 *   owner: string,
 *   updated_at: string,
 *   residual_risk_ids: Record<string, boolean>,
 *   mitigation_topic_ids: Record<string, boolean>,
 * }}
 */
export function normalizeSprint4GoNoGoState(goNoGo) {
  const g = goNoGo && typeof goNoGo === "object" ? goNoGo : {};
  const rr = g.residual_risk_ids && typeof g.residual_risk_ids === "object" ? g.residual_risk_ids : {};
  const mt = g.mitigation_topic_ids && typeof g.mitigation_topic_ids === "object" ? g.mitigation_topic_ids : {};
  return {
    decision: String(g.decision || "PENDING_REVIEW"),
    residual_risk: String(g.residual_risk || "MEDIUM"),
    mitigation_plan: String(g.mitigation_plan || "").trim(),
    owner: String(g.owner || "").trim(),
    updated_at: String(g.updated_at || ""),
    residual_risk_ids: { ...rr },
    mitigation_topic_ids: { ...mt },
  };
}

/**
 * @param {ReturnType<typeof normalizeSprint4GoNoGoState>} norm
 */
export function buildSprint4GoNoGoDerivedBlocks(norm) {
  const residual_risks_documented = SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.map((r) => ({
    id: r.id,
    title: r.title,
    marked: Boolean(norm.residual_risk_ids[r.id]),
  }));
  const selected_from_library = SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.filter((t) =>
    Boolean(norm.mitigation_topic_ids[t.id])
  ).map((t) => t.label);
  return {
    residual_risks_documented,
    mitigation_plan_topics: {
      selected_from_library,
      free_text: norm.mitigation_plan || "-",
    },
  };
}

/**
 * Percentagem de “readiness” da documentação Go/No-Go (0–100), para narrativa Sprint 4.
 * @param {ReturnType<typeof normalizeSprint4GoNoGoState>} norm
 * @param {{ pct: number, total: number, done: number }} matrixProgress
 * @param {{ pct: number, all_pass: boolean }} kioskUatProgress
 */
export function computeSprint4GoNoGoReadinessDocumentationPct(norm, matrixProgress, kioskUatProgress) {
  let s = 0;
  if (norm.decision === "GO" || norm.decision === "NO_GO") s += 20;
  else s += 8;
  const rc = SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.filter((r) => norm.residual_risk_ids[r.id]).length;
  /** Até 7 riscos × 4 p.p. (cap 28) — alinhado ao catálogo `SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG`. */
  s += Math.min(28, rc * 4);
  const tc = SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.filter((t) => norm.mitigation_topic_ids[t.id]).length;
  /** Até 7 tópicos × 4 p.p. (cap 28) — biblioteca `SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY`. */
  s += Math.min(28, tc * 4);
  const len = norm.mitigation_plan.length;
  if (len >= 80) s += 18;
  else if (len >= 40) s += 12;
  else if (len >= 16) s += 6;
  if (matrixProgress.pct >= 50) s += 8;
  if (matrixProgress.pct >= 75) s += 4;
  if (kioskUatProgress.all_pass) s += 12;
  else if (kioskUatProgress.pct >= 50) s += 6;
  if (norm.mitigation_topic_ids.mt_legal_committee_act && norm.residual_risk_ids.rr_legal_committee_rubric) {
    s += 6;
  }
  if (norm.residual_risk !== "MEDIUM" || norm.decision === "NO_GO") s += 4;
  return Math.min(100, Math.round(s));
}

/** Versão do protocolo UAT KIOSK exportado em `SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D`. */
export const SPRINT4_KIOSK_TOUCH_UAT_PROTOCOL_VERSION = "sprint4-kiosk-touch-uat-v2-e2e-presencial";

export const SPRINT4_KIOSK_UAT_MODELS = [
  {
    id: "model_a_quick_buy",
    label: "Modelo A — Quick Buy",
    default_note_hint: "Registar order_id, locker PT, captura catálogo /comprar.",
    manual_steps: [
      "Viewport totem 1080×1920 (retrato); abrir `/ops/kiosk-touch-models` com auth OPS — espelhar `test.describe(\"OPS KIOSK touch — viewport totem\")` quando validar legibilidade.",
      "Modelo A → CTA abre `/comprar`; vitrine com slot selecionável (lab: `installKioskPtLabMocks` + slots AVAILABLE no spec).",
      "Fluxo feliz até pedido criado; validar MB WAY / instrução e ausência de erro de layout em touch.",
      "Simular timeout ou falha de rede leve; confirmar retry seguro sem estado preso.",
    ],
    e2e_anchors: ['Modelo A — CTA primário abre catálogo /comprar', "e2e/kiosk-touch-models.spec.ts"],
    aligned_e2e_tests: ["Modelo A — CTA primário abre catálogo /comprar", "vitrine KIOSK PT legível em retrato 1080×1920 (totem)"],
    hardware_presencial: {
      steps: [
        "Repetir o fluxo A em totem físico (sem mocks de rede) no site piloto; rede e APIs reais.",
        "Validar alvos touch ≥44px nos CTAs críticos do catálogo; registo fotográfico ou vídeo ≤60s.",
        "Anotar `order_id` real e locker_id no campo notas antes de marcar PASS.",
      ],
      evidence_required: ["Identificador do equipamento ou etiqueta do piloto", "Screenshot ou frame de vídeo com order_id ou confirmação visível"],
    },
  },
  {
    id: "model_b_guided_buy",
    label: "Modelo B — Guided Buy",
    default_note_hint: "Registar se checkout inválido sem query é esperado em lab; anexar path guiado.",
    manual_steps: [
      "Modelo B → CTA abre `/checkout` (lab: sem query mínima → `public-checkout-invalid` documentado — alinhar ao teste homónimo).",
      "Com query válida de piloto: percorrer passos guiados até revisão; validar mensagens de validação acionáveis em touch.",
      "Confirmar correlação `order_id` ou bloqueio explícito antes de submit quando aplicável.",
    ],
    e2e_anchors: [
      "Modelo B — CTA primário abre /checkout (laboratório; sem query → checkout inválido)",
      "e2e/kiosk-touch-models.spec.ts",
    ],
    aligned_e2e_tests: ["Modelo B — CTA primário abre /checkout (laboratório; sem query → checkout inválido)"],
    hardware_presencial: {
      steps: [
        "No hardware: abrir checkout guiado com query mínima válida do piloto; percorrer até revisão sem bypass de validação.",
        "Documentar qualquer desvio de copy/layout touch vs lab no campo notas.",
      ],
      evidence_required: ["Screenshot da revisão ou estado bloqueado esperado", "Query string ou order_id de teste utilizado"],
    },
  },
  {
    id: "model_c_pickup_fast_lane",
    label: "Modelo C — Pickup Fast Lane",
    default_note_hint: "Anexar comprovante simulado/impresso, passo identify e redeem-manual.",
    manual_steps: [
      "Modelo C → CTA abre simulador `/ops/pt/kiosk` — alinhar a `Modelo C — CTA primário abre simulador KIOSK OPS (PT)`.",
      "Fluxo completo mock: `Modelo C — KIOSK PT: pedido, pagamento (APPROVED), identificação e retirada manual (mocks)` ou variante `retirada manual isolada` do spec.",
      "Entrada direta `/ops/pt/kiosk`: opcionalmente espelhar `Trilha E — KIOSK PT entrada direta em /ops/pt/kiosk: fluxo completo mockado`.",
      "Validar impressão simulada (lab) ou evidência do comprovante; em totem físico seguir `Trilha E — totem físico: impressão + identificação + retirada (redeem) no mesmo fluxo`.",
    ],
    e2e_anchors: [
      "Modelo C — KIOSK PT: pedido, pagamento (APPROVED), identificação e retirada manual (mocks)",
      "Trilha E — totem físico: impressão + identificação + retirada (redeem) no mesmo fluxo",
      "e2e/kiosk-touch-models.spec.ts",
    ],
    aligned_e2e_tests: [
      "Modelo C — CTA primário abre simulador KIOSK OPS (PT)",
      "Modelo C — KIOSK PT: vitrine, MB WAY e criar pedido (POST mock)",
      "Modelo C — KIOSK PT: retirada manual isolada (mock redeem, sem fluxo de pagamento)",
      "Modelo C — KIOSK PT: pedido, pagamento (APPROVED), identificação e retirada manual (mocks)",
      "Trilha E — KIOSK PT entrada direta em /ops/pt/kiosk: fluxo completo mockado",
      "Trilha E — totem físico: simulação de impressão do comprovante após pagamento aprovado",
      "Trilha E — totem físico: impressão + identificação + retirada (redeem) no mesmo fluxo",
    ],
    hardware_presencial: {
      steps: [
        "Executar fluxo C em hardware com impressora real ou fluxo de comprovante aceite pelo comité.",
        "Validar identify + redeem-manual (ou equivalente operacional) com operador presencial.",
        "Registar incidentes de hardware (papel, rede totem) na nota.",
      ],
      evidence_required: ["Foto do comprovante ou confirmação de impressão", "order_id / pickup reference utilizado no piloto"],
    },
  },
  {
    id: "model_d_partner_allocation",
    label: "Modelo D — Partner Allocation",
    default_note_hint: "Registar slot alvo, SKU e resposta POST alocação (print ou ID de gaveta).",
    manual_steps: [
      "Modelo D → CTA abre `/ops/dev/slots` — alinhar a `Modelo D — CTA primário abre alocação por slot (dev)`.",
      "Grelha de gavetas legível em touch; selecionar slot AVAILABLE; alocar SKU de teste (`Modelo D — dev slots: grelha de gavetas + alocar SKU`).",
      "Confirmar persistência visual e payload de alocação (evidência: HAR, screenshot ou ID de slot).",
    ],
    e2e_anchors: [
      "Modelo D — dev slots: grelha de gavetas + alocar SKU (fluxo físico assistido)",
      "e2e/kiosk-touch-models.spec.ts",
    ],
    aligned_e2e_tests: [
      "Modelo D — CTA primário abre alocação por slot (dev)",
      "Modelo D — dev slots: grelha de gavetas + alocar SKU (fluxo físico assistido)",
    ],
    hardware_presencial: {
      steps: [
        "Em armário físico ou ambiente equivalente: confirmar abertura/após alocação conforme runbook do piloto (sem bypass de segurança).",
        "Dois ciclos touch: seleção de slot + confirmação + leitura do estado da gaveta no UI.",
      ],
      evidence_required: ["ID de slot alocado e SKU", "Foto da grelha ou do estado pós-alocação"],
    },
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
    register_summary_schema: SPRINT4_GO_NO_GO_REGISTER_SUMMARY_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    storage: { key: SPRINT4_MATRIX_STORAGE_KEY },
    owner: full.owner,
    matrix_progress: full.progress,
    kiosk_uat: full.kiosk_uat.progress,
    combined_functional_pct: full.combined_functional_pct,
    kiosk_touch_uat_export_scope: "SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D",
    residual_risks_catalog: SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG,
    mitigation_topics_library: SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY,
    go_no_go_register: full.go_no_go_register,
    readiness_documentation_pct: full.go_no_go_register.readiness_documentation_pct,
    readiness_documentation_pct_formula: {
      version: "sprint4-readiness-doc-v2-final",
      decision_go_no_go_max: 20,
      decision_pending_max: 8,
      residual_risks_marked_points_cap: 28,
      residual_risk_points_per_mark: 4,
      mitigation_topics_marked_points_cap: 28,
      mitigation_topic_points_per_mark: 4,
      mitigation_plan_length_tiers: { gte_80: 18, gte_40: 12, gte_16: 6 },
      matrix_progress_points: { gte_50: 8, gte_75: 4 },
      kiosk_uat_points: { all_pass: 12, gte_50_pct: 6 },
      legal_committee_both_marked_bonus: 6,
      residual_risk_or_no_go_bonus: 4,
      cap: 100,
    },
    presencial_legal_note:
      "readiness_documentation_pct = 100% documental no cockpit; rubrica legal/acta presencial é evidência externa referenciada em `mt_legal_committee_act` + risco `rr_legal_committee_rubric`.",
  };
}

/**
 * Export dedicado: checklist por persona (texto de referência + contagens atuais).
 */
export function buildSprint4PersonaFunctionalChecklistPayload(nowIso, storedState) {
  const full = buildSprint4RegressionMatrixPayload(nowIso, storedState);
  const presencial = normalizePresencialFunctionalChecklist(storedState?.presencial_functional_checklist);
  const expectedPersonas = SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST.map((b) => b.persona);
  const signedPersonaCount = presencial
    ? presencial.persona_signoffs.filter(
        (s) =>
          s.signer_name &&
          s.signed_at &&
          expectedPersonas.includes(s.persona)
      ).length
    : 0;
  const presencial_complete =
    Boolean(presencial) &&
    signedPersonaCount === expectedPersonas.length &&
    full.progress.done === full.progress.total &&
    full.progress.total === SPRINT4_MATRIX_N_CASES;
  return {
    scope: "SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST",
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    checklist_schema: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    reference: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
    matrix_n_cases: SPRINT4_MATRIX_N_CASES,
    matrix_execution_evidence: {
      done: full.progress.done,
      total: full.progress.total,
      pct: full.progress.pct,
      all_matrix_cases_marked: full.progress.done === full.progress.total && full.progress.total === SPRINT4_MATRIX_N_CASES,
    },
    persona_rollups: full.personas,
    matrix_progress: full.progress,
    kiosk_uat: full.kiosk_uat.progress,
    combined_functional_pct: full.combined_functional_pct,
    presencial_functional_signoff: presencial,
    presencial_functional_signoff_complete: presencial_complete,
    presencial_signoff_expected_personas: expectedPersonas,
    presencial_signoff_signed_persona_count: signedPersonaCount,
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
    kiosk_touch_uat_protocol_version: SPRINT4_KIOSK_TOUCH_UAT_PROTOCOL_VERSION,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    presencial_hardware_residual:
      "Checklist cockpit + protocolo v2 = 90% documental; fechamento 100% exige ciclos presenciais em hardware real (notas por modelo + evidência anexa).",
    manual_protocol: SPRINT4_KIOSK_UAT_MODELS.map(
      ({ id, label, manual_steps, e2e_anchors, default_note_hint, aligned_e2e_tests, hardware_presencial }) => ({
        model_id: id,
        label,
        manual_steps,
        e2e_anchors,
        aligned_e2e_tests: aligned_e2e_tests || [],
        default_note_hint,
        hardware_presencial: hardware_presencial || { steps: [], evidence_required: [] },
      })
    ),
    kiosk_uat_execution: full.kiosk_uat,
    combined_functional_pct: full.combined_functional_pct,
    zip_attachment_hint: "ELLAN_FISCAL_DAILY_*_SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D_*.json",
    zip_executive_attachment_hint:
      "ELLAN_FISCAL_DAILY_{YYYYMMDD}_SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D_{ts}.json dentro do ZIP gerado em fiscal/accounting-close (mesmo padrão que management-daily quando appendSprint4OptionalSignedZipEntries corre com estado em localStorage).",
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
  const normGo = normalizeSprint4GoNoGoState(goNoGo);
  const goNoGoDerived = buildSprint4GoNoGoDerivedBlocks(normGo);
  const readinessDocumentationPct = computeSprint4GoNoGoReadinessDocumentationPct(normGo, progress, kioskUatProgress);

  return {
    scope: "SPRINT4_REGRESSION_MATRIX",
    export_schema: SPRINT4_REGRESSION_EXPORT_SCHEMA,
    generated_at: nowIso,
    page_version: SPRINT4_MATRIX_PAGE_VERSION,
    matrix_n_cases: SPRINT4_MATRIX_N_CASES,
    matrix_execution_evidence: {
      done: progress.done,
      total: progress.total,
      pct: progress.pct,
      all_matrix_cases_marked: progress.done === progress.total && progress.total === SPRINT4_MATRIX_N_CASES,
    },
    storage: {
      key: SPRINT4_MATRIX_STORAGE_KEY,
      version: Number(storedState?.version || SPRINT4_MATRIX_VERSION),
      updated_at: String(storedState?.updated_at || ""),
    },
    owner,
    progress,
    combined_functional_pct: combinedPct,
    persona_functional_checklist: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
    persona_functional_checklist_schema: SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_SCHEMA,
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
      decision: normGo.decision,
      residual_risk: normGo.residual_risk,
      mitigation_plan: normGo.mitigation_plan.trim() || "-",
      owner: String(goNoGo.owner || owner || "-").trim() || "-",
      updated_at: String(goNoGo.updated_at || ""),
      ready_hint: kioskUatProgress.all_pass ? "UAT_KIOSK_OK" : "UAT_KIOSK_PENDING",
      residual_risks_documented: goNoGoDerived.residual_risks_documented,
      mitigation_plan_topics: goNoGoDerived.mitigation_plan_topics,
      readiness_documentation_pct: readinessDocumentationPct,
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
