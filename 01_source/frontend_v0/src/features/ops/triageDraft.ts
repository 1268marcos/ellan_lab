
export const OPS_DEV_ERRORS_TRIAGE_DRAFT_KEY = "ellan_ops_dev_errors_triage_draft_v1";

export interface TriageDraft {
  incidentId: string;
  incidentOwner: string;
  incidentEta: string;
  incidentShift: string;
  incidentSeverity: string;
  savedAt?: string;
}

export const INITIAL_TRIAGE_DRAFT: TriageDraft = {
  incidentId: "",
  incidentOwner: "",
  incidentEta: "",
  incidentShift: "",
  incidentSeverity: "HIGH",
};

export function loadTriageDraftFromStorage(storageKey = OPS_DEV_ERRORS_TRIAGE_DRAFT_KEY): TriageDraft {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { ...INITIAL_TRIAGE_DRAFT };
    const parsed = JSON.parse(raw) as Partial<TriageDraft>;
    return {
      incidentId: typeof parsed.incidentId === "string" ? parsed.incidentId : "",
      incidentOwner: typeof parsed.incidentOwner === "string" ? parsed.incidentOwner : "",
      incidentEta: typeof parsed.incidentEta === "string" ? parsed.incidentEta : "",
      incidentShift: typeof parsed.incidentShift === "string" ? parsed.incidentShift : "",
      incidentSeverity: typeof parsed.incidentSeverity === "string" && parsed.incidentSeverity
        ? parsed.incidentSeverity
        : "HIGH",
      savedAt: typeof parsed.savedAt === "string" ? parsed.savedAt : undefined,
    };
  } catch {
    return { ...INITIAL_TRIAGE_DRAFT };
  }
}

export function saveTriageDraftToStorage(
  draft: TriageDraft,
  storageKey = OPS_DEV_ERRORS_TRIAGE_DRAFT_KEY
): void {
  try {
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        ...draft,
        savedAt: new Date().toISOString(),
      })
    );
  } catch {
    // best effort only
  }
}


