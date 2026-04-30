import { extractIssueNumberFromIncidentId } from "./triageGovernance";

export interface TicketLookupState {
  loading: boolean;
  checkedAt: string;
  status: string;
  owner: string;
  error: string;
  issueNumber: string;
}

export const INITIAL_TICKET_LOOKUP_STATE: TicketLookupState = {
  loading: false,
  checkedAt: "",
  status: "",
  owner: "",
  error: "",
  issueNumber: "",
};

function parseLookupError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const maybePayload = payload as { detail?: unknown; message?: unknown };
  if (typeof maybePayload.detail === "string" && maybePayload.detail.trim()) return maybePayload.detail.trim();
  if (typeof maybePayload.message === "string" && maybePayload.message.trim()) return maybePayload.message.trim();
  if (typeof maybePayload.detail === "object" && maybePayload.detail !== null) {
    const detailObj = maybePayload.detail as { message?: unknown };
    if (typeof detailObj.message === "string" && detailObj.message.trim()) return detailObj.message.trim();
  }
  return fallback;
}

export async function lookupTicketConsistency(params: {
  incidentId: string;
  isIncidentIdValid: boolean;
  trackerApiBaseUrl: string;
}): Promise<TicketLookupState> {
  if (!params.isIncidentIdValid) {
    return {
      ...INITIAL_TICKET_LOOKUP_STATE,
      error: "incident_id inválido para lookup.",
    };
  }

  const issueNumber = extractIssueNumberFromIncidentId(params.incidentId);
  if (!issueNumber) {
    return {
      ...INITIAL_TICKET_LOOKUP_STATE,
      error: "incident_id sem sufixo numérico para lookup.",
    };
  }

  try {
    const response = await fetch(`${params.trackerApiBaseUrl}/${encodeURIComponent(issueNumber)}`, {
      method: "GET",
      headers: { Accept: "application/vnd.github+json" },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(parseLookupError(payload, `Falha no lookup do ticket #${issueNumber}.`));
    }
    const issuePayload = payload as { assignee?: { login?: string }; user?: { login?: string }; state?: string };
    const owner = String(issuePayload.assignee?.login || issuePayload.user?.login || "").trim();
    const status = String(issuePayload.state || "").trim();
    return {
      loading: false,
      checkedAt: new Date().toISOString(),
      status: status || "unknown",
      owner: owner || "unassigned",
      error: "",
      issueNumber,
    };
  } catch (err) {
    return {
      loading: false,
      checkedAt: new Date().toISOString(),
      status: "",
      owner: "",
      error: String((err as Error)?.message || err || "Falha no lookup do ticket."),
      issueNumber,
    };
  }
}

