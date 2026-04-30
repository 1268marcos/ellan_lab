/**
 * Snapshot gravado em localStorage para o pacote diário / close ZIP
 * (scope SPRINT3_PARTNER_AUDIT_MIRROR_ATTACH), alinhado ao padrão do gate v2.
 */
export const SPRINT3_PARTNER_AUDIT_MIRROR_STORAGE_KEY = "fiscal_sprint3_partner_audit_mirror_v1";

/** @param {Record<string, unknown>} payload */
export function saveSprint3PartnerAuditMirrorForDaily(payload) {
  window.localStorage.setItem(SPRINT3_PARTNER_AUDIT_MIRROR_STORAGE_KEY, JSON.stringify(payload));
}

/** @returns {Record<string, unknown> | null} */
export function loadSprint3PartnerAuditMirrorForDaily() {
  try {
    const raw = window.localStorage.getItem(SPRINT3_PARTNER_AUDIT_MIRROR_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    if (!parsed.slice || typeof parsed.slice !== "object") return null;
    if (typeof parsed.saved_at !== "string") return null;
    return parsed;
  } catch {
    return null;
  }
}
