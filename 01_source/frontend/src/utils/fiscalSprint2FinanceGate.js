/**
 * Estado do gate financeiro Sprint 2 (v2) persistido pelo cockpit `fiscal/sprint2-finance-gate`.
 * Reutilizado em `fiscal/management-daily` (espelho + anexo ZIP) para evidência única no daily.
 */

export const SPRINT2_FINANCE_GATE_V2_STORAGE_KEY = "fiscal_sprint2_finance_gate_v2";

export const SPRINT2_FINANCE_GATE_V2_THRESHOLDS = Object.freeze({
  fiscal: 50,
  accounting: 40,
  consolidated: 55,
});

export const SPRINT2_FINANCE_GATE_COMMITTEE_REF = "2026-05-01";

export function clampSprint2GatePct(n) {
  const x = Number(n);
  if (Number.isNaN(x)) return 0;
  return Math.min(100, Math.max(0, Math.round(x)));
}

export function loadSprint2FinanceGateV2State() {
  try {
    const raw = window.localStorage.getItem(SPRINT2_FINANCE_GATE_V2_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/**
 * @param {unknown} raw — objeto vindo do localStorage (pode ser null)
 * @returns {null | {
 *   fiscal_percent: number,
 *   accounting_percent: number,
 *   consolidated_percent: number,
 *   p0_evidence_note: string,
 *   p0_evidence_ok: boolean,
 *   fiscal_ok: boolean,
 *   accounting_ok: boolean,
 *   consolidated_ok: boolean,
 *   overall_pass: boolean,
 *   updated_at: string | null,
 * }}
 */
export function summarizeSprint2FinanceGateV2(raw) {
  if (!raw || typeof raw !== "object") return null;
  const fiscal = clampSprint2GatePct(raw.fiscal_percent ?? 26);
  const accounting = clampSprint2GatePct(raw.accounting_percent ?? 15);
  const consolidated = clampSprint2GatePct(raw.consolidated_percent ?? 52);
  const p0Note = String(raw.p0_evidence_note || "");
  const p0Ok = p0Note.trim().length >= 24;
  const fiscalOk = fiscal >= SPRINT2_FINANCE_GATE_V2_THRESHOLDS.fiscal;
  const accountingOk = accounting >= SPRINT2_FINANCE_GATE_V2_THRESHOLDS.accounting;
  const consolidatedOk = consolidated >= SPRINT2_FINANCE_GATE_V2_THRESHOLDS.consolidated;
  return {
    fiscal_percent: fiscal,
    accounting_percent: accounting,
    consolidated_percent: consolidated,
    p0_evidence_note: p0Note,
    p0_evidence_ok: p0Ok,
    fiscal_ok: fiscalOk,
    accounting_ok: accountingOk,
    consolidated_ok: consolidatedOk,
    overall_pass: fiscalOk && accountingOk && consolidatedOk && p0Ok,
    updated_at: raw.updated_at != null ? String(raw.updated_at) : null,
  };
}
