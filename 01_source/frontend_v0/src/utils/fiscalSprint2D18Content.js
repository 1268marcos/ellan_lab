
/**
 * Sprint 2 — D18 fechamento financeiro: checklist mínimo + linhas template para riscos P1 remanescentes.
 * Persistência partilhada entre `fiscal/management-daily` e ZIP executivo em `fiscal/accounting-close`.
 */

export const D18_CLOSEOUT_STORAGE_KEY = "fiscal_management_daily:sprint2_d18_closeout_v1";

export const D18_CHECKLIST_ITEMS = [
  { id: "d10", label: "Governança D10 (matriz/providers): evidência revisada ou N/A documentado" },
  { id: "d11", label: "Lote D11 publicado em ops/fiscal/providers e refletido no handoff diário" },
  { id: "d12", label: "Handoff D12 contábil conectado ao snapshot D11 no pacote diário" },
  { id: "d13_d14", label: "Aceite D13/D14: owner/ETA/checklist e persistência central quando em uso" },
  { id: "d15", label: "Histórico D15: amostra de compare validada para turno ou justificativa registrada" },
  { id: "d16", label: "Export D16 / ZIP diário ou executivo exercido ou motivo de não-exercício anotado" },
  { id: "d17", label: "D17: dry-run de retenção ou justificativa de volume; divergência prolongada tratada ou escalada" },
  { id: "transition", label: "Comunicação do próximo foco (Sprint 3 / hardening) acordada com o time" },
];

export function createInitialP1RiskRows() {
  return Array.from({ length: 5 }, (_, i) => ({
    id: `p1_${i}`,
    title: "",
    owner: "",
    eta: "",
    impact: "",
  }));
}

export function countD18ChecklistDone(checklistById) {
  const map = checklistById && typeof checklistById === "object" ? checklistById : {};
  return D18_CHECKLIST_ITEMS.filter((row) => Boolean(map[row.id])).length;
}

function normalizeD18Certification(raw) {
  if (!raw || typeof raw !== "object") return null;
  const certified_at = String(raw.certified_at || "").trim();
  const certified_by = String(raw.certified_by || "").trim();
  if (!certified_at || !certified_by) return null;
  return {
    certified_at,
    certified_by,
    note: String(raw.note ?? "").trim(),
  };
}

export function loadD18CloseoutFromStorage() {
  try {
    const raw = window.localStorage.getItem(D18_CLOSEOUT_STORAGE_KEY);
    if (!raw) return { checklist: {}, p1Risks: createInitialP1RiskRows(), certification: null };
    const parsed = JSON.parse(raw);
    const checklist = parsed?.checklist && typeof parsed.checklist === "object" ? parsed.checklist : {};
    const base = createInitialP1RiskRows();
    const p1Risks = Array.isArray(parsed?.p1Risks)
      ? base.map((b, i) => {
          const s = parsed.p1Risks[i];
          if (!s || typeof s !== "object") return b;
          return {
            ...b,
            title: String(s.title ?? ""),
            owner: String(s.owner ?? ""),
            eta: String(s.eta ?? ""),
            impact: String(s.impact ?? ""),
          };
        })
      : base;
    const certification = normalizeD18Certification(parsed?.certification);
    return { checklist, p1Risks, certification };
  } catch {
    return { checklist: {}, p1Risks: createInitialP1RiskRows(), certification: null };
  }
}

/**
 * @param {object} params
 * @param {string} params.generatedAt ISO
 * @param {Record<string, boolean>} params.checklistById
 * @param {Array<{ id: string, title: string, owner: string, eta: string, impact: string }>} params.p1Rows
 * @param {"fiscal/management-daily" | "fiscal/accounting-close"} params.source
 * @param {{ certified_at: string, certified_by: string, note?: string } | null | undefined} params.certification
 * @param {{ decision_consolidated: string, risk_level: string, readiness_version: string }} params.context
 */
export function buildD18CloseoutPayload({ generatedAt, checklistById, p1Rows, source, context, certification }) {
  const checklist_progress = D18_CHECKLIST_ITEMS.map((row) => ({
    id: row.id,
    label: row.label,
    done: Boolean(checklistById?.[row.id]),
  }));
  const doneCount = countD18ChecklistDone(checklistById);
  const total = D18_CHECKLIST_ITEMS.length;
  const scope =
    source === "fiscal/accounting-close" ? "SPRINT2_D18_EXEC_FINANCE_CLOSEOUT" : "SPRINT2_D18_FINANCE_CLOSEOUT";
  const normalizedCert = normalizeD18Certification(certification);
  return {
    scope,
    generated_at: generatedAt,
    source: source || "fiscal/management-daily",
    checklist_progress,
    checklist_done: doneCount,
    checklist_total: total,
    checklist_pass_ratio: total ? `${doneCount}/${total}` : "0/0",
    p1_risks_remaining: (Array.isArray(p1Rows) ? p1Rows : []).map((r) => ({
      id: r.id,
      title: String(r.title || "").trim(),
      owner: String(r.owner || "").trim(),
      eta: String(r.eta || "").trim(),
      impact: String(r.impact || "").trim(),
    })),
    closeout_certification: normalizedCert
      ? {
          certified_at: normalizedCert.certified_at,
          certified_by: normalizedCert.certified_by,
          note: normalizedCert.note || "-",
        }
      : null,
    context: {
      decision_consolidated: String(context?.decision_consolidated || "NO_GO").toUpperCase(),
      risk_level: String(context?.risk_level || "UNKNOWN"),
      readiness_version: String(context?.readiness_version || "-"),
    },
  };
}

