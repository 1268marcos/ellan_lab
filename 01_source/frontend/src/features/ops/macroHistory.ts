export interface MacroHistoryEntry {
  id: string;
  createdAt: string;
  kind: string;
  incidentId: string;
  ticketUrl: string;
  ticketStatus: string;
  ticketOwnerLookup: string;
  ticketCheckedAt: string;
  owner: string;
  shift: string;
  eta: string;
  severity: string;
  text: string;
}

function toCsvValue(value: unknown): string {
  const raw = String(value ?? "");
  const escaped = raw.replace(/"/g, "\"\"");
  return `"${escaped}"`;
}

export function buildMacroHistoryJson(history: MacroHistoryEntry[]): string {
  return JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      count: history.length,
      items: history,
    },
    null,
    2
  );
}

export function buildMacroHistoryCsv(history: MacroHistoryEntry[]): string {
  const header = [
    "created_at",
    "kind",
    "incident_id",
    "ticket_url",
    "ticket_status",
    "ticket_owner_lookup",
    "ticket_checked_at",
    "owner",
    "turno",
    "eta",
    "severidade",
    "text",
  ];
  const rows = history.map((entry) => [
    entry.createdAt,
    entry.kind,
    entry.incidentId,
    entry.ticketUrl || "",
    entry.ticketStatus || "",
    entry.ticketOwnerLookup || "",
    entry.ticketCheckedAt || "",
    entry.owner,
    entry.shift,
    entry.eta,
    entry.severity,
    entry.text,
  ]);
  return [header, ...rows].map((row) => row.map((cell) => toCsvValue(cell)).join(",")).join("\n");
}

export function loadMacroHistoryFromStorage(storageKey: string, maxItems: number): MacroHistoryEntry[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as MacroHistoryEntry[]).slice(0, maxItems) : [];
  } catch {
    return [];
  }
}

export function saveMacroHistoryToStorage(storageKey: string, history: MacroHistoryEntry[], maxItems: number): void {
  try {
    localStorage.setItem(storageKey, JSON.stringify(history.slice(0, maxItems)));
  } catch {
    // best effort only
  }
}

