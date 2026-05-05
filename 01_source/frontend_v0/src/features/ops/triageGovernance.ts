
export const INCIDENT_ID_REGEX = /^[A-Z]+-\d{2,6}(?:-\d{1,6})?$/;

export interface TicketLookupSnapshot {
  status: string;
  owner: string;
  checkedAt: string;
}

export interface TriageMacroContext {
  kind: "INCIDENTE" | "MONITORAMENTO" | "ESCALACAO";
  incidentId: string;
  owner: string;
  shift: string;
  eta: string;
  severity: string;
  ticketUrl: string;
  summaryHours: number;
  totalEvents: number;
  statusFilter: string;
  routeFilter: string;
  uiErrorsRange: string;
  topDomain?: string;
  topPath?: string;
  topMessage?: string;
  lookup?: TicketLookupSnapshot | null;
}

export function normalizeIncidentId(value: string): string {
  return String(value || "").trim().toUpperCase();
}

export function isIncidentIdValid(value: string): boolean {
  const normalized = normalizeIncidentId(value);
  return Boolean(normalized) && INCIDENT_ID_REGEX.test(normalized);
}

export function extractIssueNumberFromIncidentId(value: string): string {
  const normalized = normalizeIncidentId(value);
  const match = normalized.match(/-(\d+)$/);
  return match ? match[1] : "";
}

export function buildTriageMacro(context: TriageMacroContext): string {
  const lines: string[] = [];
  lines.push(`[SUPPORT][TRIAGE][${context.kind}] UI errors`);
  lines.push(`incident_id=${normalizeIncidentId(context.incidentId) || "pendente"}`);
  lines.push(`owner=${context.owner || "nao_definido"}`);
  lines.push(`turno=${context.shift || "nao_informado"}`);
  lines.push(`eta=${context.eta || "nao_informado"}`);
  lines.push(`severidade=${context.severity || "HIGH"}`);
  lines.push(`ticket_url=${context.ticketUrl || "nao_disponivel"}`);
  lines.push(`ticket_status=${context.lookup?.status || "nao_verificado"}`);
  lines.push(`ticket_owner_lookup=${context.lookup?.owner || "nao_verificado"}`);
  lines.push(`ticket_checked_at=${context.lookup?.checkedAt || "nao_verificado"}`);
  lines.push(`janela_horas=${context.summaryHours}`);
  lines.push(`total_eventos=${context.totalEvents}`);
  lines.push(`filtro_status=${context.statusFilter || "todos"}`);
  lines.push(`filtro_rota=${context.routeFilter || "todas"}`);
  lines.push(`pagina_ui_errors=${context.uiErrorsRange}`);
  if (context.topDomain) lines.push(`top_domain=${context.topDomain}`);
  if (context.topPath) lines.push(`top_path=${context.topPath}`);
  if (context.topMessage) lines.push(`top_message=${context.topMessage}`);
  lines.push("rota_runbook=/ops/dev/errors");
  lines.push("acoes_recomendadas=1) validar impacto 2) correlacionar com /ops/health 3) abrir evidência em /ops/audit");
  return lines.join("\n");
}


