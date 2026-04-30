import React, { useMemo, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  buildTriageMacro as buildTriageMacroText,
  normalizeIncidentId,
  isIncidentIdValid as isIncidentIdValidValue,
} from "../features/ops/triageGovernance";
import {
  INITIAL_TICKET_LOOKUP_STATE,
  lookupTicketConsistency as lookupTicketConsistencyCore,
} from "../features/ops/ticketLookup";
import {
  buildMacroHistoryCsv as buildMacroHistoryCsvText,
  buildMacroHistoryJson as buildMacroHistoryJsonText,
  loadMacroHistoryFromStorage,
  saveMacroHistoryToStorage,
  type MacroHistoryEntry,
} from "../features/ops/macroHistory";
import {
  INITIAL_TRIAGE_DRAFT,
  loadTriageDraftFromStorage,
  saveTriageDraftToStorage,
} from "../features/ops/triageDraft";
import { formatOpsDateTime } from "../utils/opsDateTimeFormat";

const ORDER_PICKUP_BASE = import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const INCIDENT_TRACKER_BASE_URL = import.meta.env.VITE_INCIDENT_TRACKER_BASE_URL || "https://github.com/1268marcos/ellan_lab/issues";
const INCIDENT_TRACKER_API_BASE_URL = import.meta.env.VITE_INCIDENT_TRACKER_API_BASE_URL || "https://api.github.com/repos/1268marcos/ellan_lab/issues";
const OPS_DEV_ERRORS_MACRO_HISTORY_KEY = "ellan_ops_dev_errors_macro_history_v1";
const INCIDENT_RUNBOOKS: Record<string, { label: string; to: string }> = {
  checkout: { label: "Runbook Checkout", to: "/ops/health" },
  kiosk: { label: "Runbook KIOSK", to: "/ops/reconciliation" },
  ops: { label: "Runbook OPS", to: "/ops/audit" },
  global: { label: "Runbook Global", to: "/ops/health" },
};

interface DevErrorItem {
  path?: string;
  status_code?: number;
  method?: string;
  ts?: string;
  trace_id?: string;
  error_type?: string;
  level?: string;
  message?: string;
}

interface UiErrorItem {
  id: string;
  domain: string;
  path: string;
  event_id?: string;
  created_at?: string;
  trace_id?: string;
  message?: string;
}

interface SummaryBucket {
  key: string;
  count: number;
}

interface UiSummaryState {
  total_events: number;
  by_domain: SummaryBucket[];
  by_path: SummaryBucket[];
  by_message: SummaryBucket[];
}

interface DevErrorsApiResponse {
  items: DevErrorItem[];
}

interface UiErrorsApiResponse {
  total: number;
  items: UiErrorItem[];
}

interface UiErrorsSummaryApiResponse {
  total_events: number;
  by_domain: SummaryBucket[];
  by_path: SummaryBucket[];
  by_message: SummaryBucket[];
}

type BackendErrorDetailItem = {
  msg?: unknown;
  message?: unknown;
};

type BackendErrorDetailObject = {
  message?: unknown;
  msg?: unknown;
  error?: unknown;
};

type BackendErrorPayload = {
  detail?: string | BackendErrorDetailObject | BackendErrorDetailItem[];
  message?: unknown;
  error?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function readNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function parseDevErrorItem(value: unknown): DevErrorItem | null {
  if (!isRecord(value)) return null;
  return {
    path: readString(value.path, ""),
    status_code: readNumber(value.status_code, 0),
    method: readString(value.method, ""),
    ts: readString(value.ts, ""),
    trace_id: readString(value.trace_id, ""),
    error_type: readString(value.error_type, ""),
    level: readString(value.level, ""),
    message: readString(value.message, ""),
  };
}

function parseUiErrorItem(value: unknown): UiErrorItem | null {
  if (!isRecord(value)) return null;
  const id = readString(value.id, "");
  const domain = readString(value.domain, "");
  const path = readString(value.path, "");
  if (!id || !domain || !path) return null;
  return {
    id,
    domain,
    path,
    event_id: readString(value.event_id, ""),
    created_at: readString(value.created_at, ""),
    trace_id: readString(value.trace_id, ""),
    message: readString(value.message, ""),
  };
}

function parseSummaryBucket(value: unknown): SummaryBucket | null {
  if (!isRecord(value)) return null;
  const key = readString(value.key, "");
  if (!key) return null;
  return {
    key,
    count: readNumber(value.count, 0),
  };
}

function toList<T>(value: unknown, parser: (entry: unknown) => T | null): T[] {
  if (!Array.isArray(value)) return [];
  const parsed: T[] = [];
  for (const entry of value) {
    const item = parser(entry);
    if (item) parsed.push(item);
  }
  return parsed;
}

function parseDevErrorsApiResponse(payload: unknown): DevErrorsApiResponse {
  if (!isRecord(payload)) return { items: [] };
  return {
    items: toList(payload.items, parseDevErrorItem),
  };
}

function parseUiErrorsApiResponse(payload: unknown): UiErrorsApiResponse {
  if (!isRecord(payload)) return { total: 0, items: [] };
  return {
    total: readNumber(payload.total, 0),
    items: toList(payload.items, parseUiErrorItem),
  };
}

function parseUiErrorsSummaryApiResponse(payload: unknown): UiErrorsSummaryApiResponse {
  if (!isRecord(payload)) return { total_events: 0, by_domain: [], by_path: [], by_message: [] };
  return {
    total_events: readNumber(payload.total_events, 0),
    by_domain: toList(payload.by_domain, parseSummaryBucket),
    by_path: toList(payload.by_path, parseSummaryBucket),
    by_message: toList(payload.by_message, parseSummaryBucket),
  };
}

function readBackendDetailMessage(detail: BackendErrorPayload["detail"]): string {
  if (typeof detail === "string" && detail.trim()) return detail.trim();
  if (Array.isArray(detail)) {
    for (const entry of detail) {
      if (!isRecord(entry)) continue;
      const candidate = readString(entry.message || entry.msg, "").trim();
      if (candidate) return candidate;
    }
    return "";
  }
  if (detail && typeof detail === "object") {
    const candidate = readString(detail.message || detail.msg || detail.error, "").trim();
    if (candidate) return candidate;
  }
  return "";
}

function parseError(payload: unknown, fallback = "Nao foi possivel carregar erros internos."): string {
  if (!isRecord(payload)) return fallback;
  const errorPayload: BackendErrorPayload = {
    detail: payload.detail as BackendErrorPayload["detail"],
    message: payload.message,
    error: payload.error,
  };
  const detailMessage = readBackendDetailMessage(errorPayload.detail);
  if (detailMessage) return detailMessage;
  const message = readString(errorPayload.message, "").trim();
  if (message) return message;
  const error = readString(errorPayload.error, "").trim();
  if (error) return error;
  return fallback;
}

export default function OpsDevErrorsPageBody() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState<DevErrorItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [routeFilter, setRouteFilter] = useState("");
  const [uiErrors, setUiErrors] = useState<UiErrorItem[]>([]);
  const [uiErrorsTotal, setUiErrorsTotal] = useState(0);
  const [uiErrorsOffset, setUiErrorsOffset] = useState(0);
  const [uiErrorsLimit] = useState(20);
  const [summaryHours, setSummaryHours] = useState(24);
  const [uiSummary, setUiSummary] = useState<UiSummaryState>({ total_events: 0, by_domain: [], by_path: [], by_message: [] });
  const [copyStatus, setCopyStatus] = useState("");
  const [incidentId, setIncidentId] = useState(INITIAL_TRIAGE_DRAFT.incidentId);
  const [incidentOwner, setIncidentOwner] = useState(INITIAL_TRIAGE_DRAFT.incidentOwner);
  const [incidentEta, setIncidentEta] = useState(INITIAL_TRIAGE_DRAFT.incidentEta);
  const [incidentSeverity, setIncidentSeverity] = useState(INITIAL_TRIAGE_DRAFT.incidentSeverity);
  const [incidentShift, setIncidentShift] = useState(INITIAL_TRIAGE_DRAFT.incidentShift);
  const [macroHistory, setMacroHistory] = useState<MacroHistoryEntry[]>([]);
  const [ticketLookup, setTicketLookup] = useState(INITIAL_TICKET_LOOKUP_STATE);

  const authHeaders = useMemo<Record<string, string>>(() => {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (INTERNAL_TOKEN) headers["X-Internal-Token"] = INTERNAL_TOKEN;
    return headers;
  }, [token]);

  const routeOptions = useMemo(() => {
    const unique = new Set<string>();
    for (const item of items) {
      const path = String(item?.path || "").trim();
      if (path) unique.add(path);
    }
    return Array.from(unique).sort((a, b) => a.localeCompare(b));
  }, [items]);

  const statusOptions = useMemo(() => {
    const unique = new Set<number>();
    for (const item of items) {
      const value = Number(item?.status_code || 0);
      if (value > 0) unique.add(value);
    }
    return Array.from(unique).sort((a, b) => a - b);
  }, [items]);

  const filteredItems = useMemo(() => {
    const statusCode = Number(statusFilter || 0);
    return items.filter((item) => {
      const matchesStatus = statusCode > 0 ? Number(item?.status_code || 0) === statusCode : true;
      const matchesRoute = routeFilter ? String(item?.path || "") === routeFilter : true;
      return matchesStatus && matchesRoute;
    });
  }, [items, routeFilter, statusFilter]);

  const kpis = useMemo(() => {
    const total = items.length;
    const filtered = filteredItems.length;
    const http4xx = filteredItems.filter((item) => Number(item?.status_code || 0) >= 400 && Number(item?.status_code || 0) < 500).length;
    const http5xx = filteredItems.filter((item) => Number(item?.status_code || 0) >= 500).length;
    return { total, filtered, http4xx, http5xx };
  }, [items, filteredItems]);

  async function loadErrors() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      if (!INTERNAL_TOKEN) {
        throw new Error("VITE_INTERNAL_TOKEN nao configurado no frontend.");
      }
      const [response, uiErrorsResponse, uiSummaryResponse] = await Promise.all([
        fetch(`${ORDER_PICKUP_BASE}/internal/dev/errors`, {
          method: "GET",
          headers: authHeaders,
        }),
        fetch(
          `${ORDER_PICKUP_BASE}/dev-admin/ui-errors?limit=${encodeURIComponent(uiErrorsLimit)}&offset=${encodeURIComponent(uiErrorsOffset)}`,
          {
            method: "GET",
            headers: authHeaders,
          }
        ),
        fetch(
          `${ORDER_PICKUP_BASE}/dev-admin/ui-errors/summary?lookback_hours=${encodeURIComponent(summaryHours)}&top_n=5`,
          {
            method: "GET",
            headers: authHeaders,
          }
        ),
      ]);

      const payload = await response.json().catch(() => ({}));
      const uiPayload = await uiErrorsResponse.json().catch(() => ({}));
      const uiSummaryPayload = await uiSummaryResponse.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseError(payload));
      if (!uiErrorsResponse.ok) throw new Error(parseError(uiPayload, "Nao foi possivel carregar UI errors paginados."));
      if (!uiSummaryResponse.ok) throw new Error(parseError(uiSummaryPayload, "Nao foi possivel carregar summary de UI errors."));
      const devErrorsData = parseDevErrorsApiResponse(payload);
      const uiErrorsData = parseUiErrorsApiResponse(uiPayload);
      const uiSummaryData = parseUiErrorsSummaryApiResponse(uiSummaryPayload);
      setItems(devErrorsData.items);
      setUiErrors(uiErrorsData.items);
      setUiErrorsTotal(uiErrorsData.total);
      setUiSummary(uiSummaryData);
    } catch (err) {
      setError(String((err as Error)?.message || err || "erro desconhecido"));
      setItems([]);
      setUiErrors([]);
      setUiErrorsTotal(0);
      setUiSummary({ total_events: 0, by_domain: [], by_path: [], by_message: [] });
    } finally {
      setLoading(false);
    }
  }

  function nextUiErrorsPage() {
    setUiErrorsOffset((prev) => prev + uiErrorsLimit);
  }

  function prevUiErrorsPage() {
    setUiErrorsOffset((prev) => Math.max(0, prev - uiErrorsLimit));
  }

  const hasNextUiErrorsPage = uiErrorsOffset + uiErrorsLimit < uiErrorsTotal;
  const hasPrevUiErrorsPage = uiErrorsOffset > 0;
  const uiErrorsStart = uiErrorsTotal > 0 ? uiErrorsOffset + 1 : 0;
  const uiErrorsEnd = uiErrorsTotal > 0 ? Math.min(uiErrorsOffset + uiErrorsLimit, uiErrorsTotal) : 0;
  const topDomain = uiSummary.by_domain[0] || null;
  const topPath = uiSummary.by_path[0] || null;
  const topMessage = uiSummary.by_message[0] || null;
  const normalizedIncidentId = normalizeIncidentId(incidentId);
  const isIncidentIdValid = isIncidentIdValidValue(incidentId);
  const incidentTrackerUrl = isIncidentIdValid ? `${INCIDENT_TRACKER_BASE_URL}/${encodeURIComponent(normalizedIncidentId)}` : "";
  const trackerStatus = ticketLookup.status || "nao_verificado";
  const trackerOwner = ticketLookup.owner || "nao_verificado";
  const trackerCheckedAt = ticketLookup.checkedAt || "nao_verificado";

  async function lookupTicketConsistency() {
    setTicketLookup((prev) => ({ ...prev, loading: true, error: "" }));
    const next = await lookupTicketConsistencyCore({
      incidentId: normalizedIncidentId,
      isIncidentIdValid,
      trackerApiBaseUrl: INCIDENT_TRACKER_API_BASE_URL,
    });
    setTicketLookup(next);
    return next.error ? null : next;
  }

  function buildTriageMacro(kind: "INCIDENTE" | "MONITORAMENTO" | "ESCALACAO", lookupSnapshot: typeof ticketLookup | null = null) {
    return buildTriageMacroText({
      kind,
      incidentId: normalizedIncidentId,
      owner: incidentOwner.trim(),
      shift: incidentShift.trim(),
      eta: incidentEta.trim(),
      severity: incidentSeverity,
      ticketUrl: incidentTrackerUrl,
      summaryHours,
      totalEvents: uiSummary.total_events,
      statusFilter,
      routeFilter,
      uiErrorsRange: `${uiErrorsStart}-${uiErrorsEnd} de ${uiErrorsTotal}`,
      topDomain: topDomain ? `${topDomain.key} (${topDomain.count})` : "",
      topPath: topPath ? `${topPath.key} (${topPath.count})` : "",
      topMessage: topMessage ? `${topMessage.key} (${topMessage.count})` : "",
      lookup: lookupSnapshot || {
        status: trackerStatus,
        owner: trackerOwner,
        checkedAt: trackerCheckedAt,
      },
    });
  }

  function recordMacroHistory(kind: string, value: string, lookupSnapshot: typeof ticketLookup | null = null) {
    const resolvedStatus = lookupSnapshot?.status || trackerStatus;
    const resolvedOwner = lookupSnapshot?.owner || trackerOwner;
    const resolvedCheckedAt = lookupSnapshot?.checkedAt || trackerCheckedAt;
    const entry: MacroHistoryEntry = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      createdAt: new Date().toISOString(),
      kind,
      incidentId: normalizedIncidentId || "pendente",
      ticketUrl: incidentTrackerUrl || "",
      ticketStatus: resolvedStatus || "nao_verificado",
      ticketOwnerLookup: resolvedOwner || "nao_verificado",
      ticketCheckedAt: resolvedCheckedAt || "nao_verificado",
      owner: incidentOwner.trim() || "nao_definido",
      shift: incidentShift.trim() || "nao_informado",
      eta: incidentEta.trim() || "nao_informado",
      severity: incidentSeverity,
      text: value,
    };
    setMacroHistory((prev) => [entry, ...prev].slice(0, 20));
  }

  function buildMacroHistoryJson() {
    return buildMacroHistoryJsonText(macroHistory);
  }

  function buildMacroHistoryCsv() {
    return buildMacroHistoryCsvText(macroHistory);
  }

  function downloadText(filename: string, mimeType: string, content: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
  }

  function handleExportMacroHistoryJson() {
    if (!macroHistory.length) {
      setCopyStatus("Sem histórico para exportar.");
      return;
    }
    const timestamp = new Date().toISOString().replaceAll(":", "-");
    downloadText(`ops-dev-errors-macro-history-${timestamp}.json`, "application/json;charset=utf-8", buildMacroHistoryJson());
    setCopyStatus("Export JSON gerado.");
    window.clearTimeout(copyTimerRef.current);
    copyTimerRef.current = window.setTimeout(() => setCopyStatus(""), 2500);
  }

  function handleExportMacroHistoryCsv() {
    if (!macroHistory.length) {
      setCopyStatus("Sem histórico para exportar.");
      return;
    }
    const timestamp = new Date().toISOString().replaceAll(":", "-");
    downloadText(`ops-dev-errors-macro-history-${timestamp}.csv`, "text/csv;charset=utf-8", buildMacroHistoryCsv());
    setCopyStatus("Export CSV gerado.");
    window.clearTimeout(copyTimerRef.current);
    copyTimerRef.current = window.setTimeout(() => setCopyStatus(""), 2500);
  }

  async function handleCopyMacroHistoryJson() {
    if (!macroHistory.length) {
      setCopyStatus("Sem histórico para copiar.");
      return;
    }
    await copyText(buildMacroHistoryJson(), "Histórico JSON copiado.");
  }

  async function handleCopyMacro(kind: "INCIDENTE" | "MONITORAMENTO" | "ESCALACAO") {
    const lookupSnapshot = await lookupTicketConsistency();
    const macroText = buildTriageMacro(kind, lookupSnapshot);
    await copyText(macroText, `Macro ${kind} copiada.`, kind, lookupSnapshot);
  }

  async function copyText(
    value: string,
    successLabel: string,
    kind?: string,
    lookupSnapshot: typeof ticketLookup | null = null
  ) {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        const temp = document.createElement("textarea");
        temp.value = value;
        temp.setAttribute("readonly", "true");
        temp.style.position = "absolute";
        temp.style.left = "-9999px";
        document.body.appendChild(temp);
        temp.select();
        document.execCommand("copy");
        document.body.removeChild(temp);
      }
      if (kind) recordMacroHistory(kind, value, lookupSnapshot);
      setCopyStatus(successLabel);
    } catch {
      setCopyStatus("Falha ao copiar macro.");
    } finally {
      window.clearTimeout(copyTimerRef.current);
      copyTimerRef.current = window.setTimeout(() => setCopyStatus(""), 2500);
    }
  }

  const copyTimerRef = React.useRef(0);

  React.useEffect(() => {
    if (!token) return;
    void loadErrors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, uiErrorsOffset, summaryHours]);

  React.useEffect(() => {
    const draft = loadTriageDraftFromStorage();
    setIncidentId(draft.incidentId);
    setIncidentOwner(draft.incidentOwner);
    setIncidentEta(draft.incidentEta);
    setIncidentShift(draft.incidentShift);
    setIncidentSeverity(draft.incidentSeverity);
  }, []);

  React.useEffect(() => {
    saveTriageDraftToStorage({
      incidentId,
      incidentOwner,
      incidentEta,
      incidentShift,
      incidentSeverity,
    });
  }, [incidentId, incidentOwner, incidentEta, incidentShift, incidentSeverity]);

  React.useEffect(() => {
    setMacroHistory(loadMacroHistoryFromStorage(OPS_DEV_ERRORS_MACRO_HISTORY_KEY, 20));
  }, []);

  React.useEffect(() => {
    saveMacroHistoryToStorage(OPS_DEV_ERRORS_MACRO_HISTORY_KEY, macroHistory, 20);
  }, [macroHistory]);

  React.useEffect(() => () => window.clearTimeout(copyTimerRef.current), []);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Ir para ops/health
          </Link>
          <Link to="/ops/audit" style={shortcutLinkStyle}>
            Ir para ops/audit
          </Link>
        </div>

        <OpsPageTitleHeader title="OPS - Dev Errors" />
        <p style={mutedStyle}>
          Visualizacao interna da rota <code>/internal/dev/errors</code> para diagnostico rapido em desenvolvimento.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={inputStyle}>
              <option value="">Todos</option>
              {statusOptions.map((value) => (
                <option key={value} value={String(value)}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Rota
            <select value={routeFilter} onChange={(event) => setRouteFilter(event.target.value)} style={inputStyle}>
              <option value="">Todas</option>
              {routeOptions.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => void loadErrors()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar erros"}
          </button>
          <button
            type="button"
            onClick={() => {
              setStatusFilter("");
              setRouteFilter("");
            }}
            style={buttonSecondaryStyle}
            disabled={loading}
          >
            Limpar filtros
          </button>
          <span style={{ color: "rgba(226,232,240,0.8)", fontSize: 12 }}>
            Token interno: {INTERNAL_TOKEN ? "configurado" : "nao configurado"}
          </span>
        </div>

        {error ? <pre style={errorStyle}>{error}</pre> : null}

        {!error ? (
          <div style={kpiGridStyle}>
            <OpsTrendKpiCard label="Total eventos" value={kpis.total} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="Apos filtros" value={kpis.filtered} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="HTTP 4xx" value={kpis.http4xx} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="HTTP 5xx" value={kpis.http5xx} baseStyle={kpiBoxStyle} showTrend={false} />
          </div>
        ) : null}

        {!error && filteredItems.length > 0 ? (
          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {filteredItems.map((item, index) => (
              <article key={`${item?.trace_id || "trace"}-${index}`} style={rowStyle}>
                <div style={rowHeadStyle}>
                  <strong>{item?.method || "-"} {item?.path || "-"}</strong>
                  <span style={statusBadgeStyle(Number(item?.status_code || 0))}>{item?.status_code || "-"}</span>
                </div>
                <small style={smallStyle}>ts: {item?.ts || "-"}</small>
                <small style={smallStyle}>trace_id: {item?.trace_id || "-"}</small>
                <small style={smallStyle}>tipo: {item?.error_type || "-"}</small>
                <small style={smallStyle}>nivel: {item?.level || "-"}</small>
                {item?.message ? <small style={smallStyle}>mensagem: {item.message}</small> : null}
              </article>
            ))}
          </div>
        ) : null}

        {!error && !loading && filteredItems.length === 0 ? (
          <p style={{ marginTop: 14, color: "#94a3b8" }}>Nenhum evento encontrado com os filtros atuais.</p>
        ) : null}

        {!error ? (
          <section style={{ marginTop: 20, borderTop: "1px solid rgba(255,255,255,0.12)", paddingTop: 14 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>UI Errors (persistência durável)</h3>
            <p style={{ marginTop: 8, marginBottom: 10, color: "#94a3b8", fontSize: 12 }}>
              Fonte: <code>/dev-admin/ui-errors</code> (paginado).
            </p>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
              <button type="button" onClick={prevUiErrorsPage} disabled={!hasPrevUiErrorsPage || loading} style={buttonSecondaryStyle}>
                ◀ Anterior
              </button>
              <button type="button" onClick={nextUiErrorsPage} disabled={!hasNextUiErrorsPage || loading} style={buttonSecondaryStyle}>
                Próxima ▶
              </button>
              <span style={{ color: "rgba(226,232,240,0.8)", fontSize: 12 }}>
                Exibindo {uiErrorsStart}-{uiErrorsEnd} de {uiErrorsTotal}
              </span>
            </div>
            {uiErrors.length > 0 ? (
              <div style={{ display: "grid", gap: 8 }}>
                {uiErrors.map((item) => (
                  <article key={item.id} style={rowStyle}>
                    <div style={rowHeadStyle}>
                      <strong>{item.domain} - {item.path}</strong>
                      <span style={statusBadgeStyle(500)}>UI</span>
                    </div>
                    <small style={smallStyle}>event_id: {item.event_id}</small>
                    <small style={smallStyle}>created_at: {item.created_at || "-"}</small>
                    <small style={smallStyle}>trace_id: {item.trace_id || "-"}</small>
                    <small style={smallStyle}>mensagem: {item.message || "-"}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p style={{ marginTop: 8, color: "#94a3b8" }}>Nenhum UI error persistido para os filtros atuais.</p>
            )}
          </section>
        ) : null}

        {!error ? (
          <section style={{ marginTop: 20, borderTop: "1px solid rgba(255,255,255,0.12)", paddingTop: 14 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Top incidentes + runbook rápido</h3>
            <div style={{ marginTop: 10, marginBottom: 10, display: "flex", gap: 8, alignItems: "center" }}>
              <label style={{ ...labelStyle, display: "flex", alignItems: "center", gap: 8 }}>
                Janela (h)
                <select
                  value={String(summaryHours)}
                  onChange={(event) => setSummaryHours(Number(event.target.value || 24))}
                  style={inputStyle}
                >
                  <option value="6">6h</option>
                  <option value="12">12h</option>
                  <option value="24">24h</option>
                  <option value="48">48h</option>
                  <option value="168">7d</option>
                </select>
              </label>
              <span style={{ color: "#94a3b8", fontSize: 12 }}>
                Total na janela: {uiSummary.total_events}
              </span>
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {uiSummary.by_domain.map((bucket) => {
                const runbook = INCIDENT_RUNBOOKS[bucket.key] || INCIDENT_RUNBOOKS.global;
                return (
                  <article key={`domain-${bucket.key}`} style={rowStyle}>
                    <div style={rowHeadStyle}>
                      <strong>domain: {bucket.key}</strong>
                      <span style={statusBadgeStyle(500)}>{bucket.count}</span>
                    </div>
                    <Link to={runbook.to} style={shortcutLinkStyle}>
                      {runbook.label}
                    </Link>
                  </article>
                );
              })}
            </div>
            {uiSummary.by_path.length > 0 ? (
              <p style={{ ...smallStyle, marginTop: 10 }}>
                Top rotas com falha: {uiSummary.by_path.map((item) => `${item.key} (${item.count})`).join(" | ")}
              </p>
            ) : null}
          </section>
        ) : null}

        {!error ? (
          <section style={{ marginTop: 20, borderTop: "1px solid rgba(255,255,255,0.12)", paddingTop: 14 }}>
            <h3 style={{ margin: 0, fontSize: 16 }}>Macros de triagem copiáveis (suporte)</h3>
            <p style={{ marginTop: 8, marginBottom: 10, color: "#94a3b8", fontSize: 12 }}>
              Copie e cole no handoff, ticket ou canal Slack/Teams.
            </p>
            <div style={filtersGridStyle}>
              <label style={labelStyle}>
                incident_id
                <input
                  type="text"
                  value={incidentId}
                  onChange={(event) => setIncidentId(event.target.value)}
                  placeholder="INC-2026-0001 ou OPS-1234"
                  style={inputStyle}
                />
                <small style={smallStyle}>Padrão: `ABC-1234` ou `ABC-2026-1` (maiúsculo).</small>
                {incidentId.trim() && !isIncidentIdValid ? (
                  <small style={{ ...smallStyle, color: "#fca5a5" }}>incident_id fora do padrão esperado.</small>
                ) : null}
                {isIncidentIdValid ? (
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <a href={incidentTrackerUrl} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
                      Abrir ticket no tracker
                    </a>
                    <button
                      type="button"
                      onClick={() => void lookupTicketConsistency()}
                      style={buttonSecondaryStyle}
                      disabled={ticketLookup.loading}
                    >
                      {ticketLookup.loading ? "Consultando ticket..." : "Validar ticket no tracker"}
                    </button>
                  </div>
                ) : null}
                {!ticketLookup.loading && ticketLookup.error ? (
                  <small style={{ ...smallStyle, color: "#fca5a5" }}>{ticketLookup.error}</small>
                ) : null}
                {ticketLookup.status ? (
                  <small style={smallStyle}>
                    lookup: status={ticketLookup.status} | owner={ticketLookup.owner || "-"} | checked_at=
                    {ticketLookup.checkedAt ? formatOpsDateTime(ticketLookup.checkedAt) : "-"}
                  </small>
                ) : null}
              </label>
              <label style={labelStyle}>
                owner
                <input
                  type="text"
                  value={incidentOwner}
                  onChange={(event) => setIncidentOwner(event.target.value)}
                  placeholder="marcos"
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                ETA
                <input
                  type="text"
                  value={incidentEta}
                  onChange={(event) => setIncidentEta(event.target.value)}
                  placeholder="2026-04-30T13:00:00-03:00"
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                turno
                <input
                  type="text"
                  value={incidentShift}
                  onChange={(event) => setIncidentShift(event.target.value)}
                  placeholder="manha|tarde|noite"
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                severidade
                <select value={incidentSeverity} onChange={(event) => setIncidentSeverity(event.target.value)} style={inputStyle}>
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </label>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => void handleCopyMacro("INCIDENTE")}
                style={buttonSecondaryStyle}
              >
                Copiar macro INCIDENTE
              </button>
              <button
                type="button"
                onClick={() => void handleCopyMacro("MONITORAMENTO")}
                style={buttonSecondaryStyle}
              >
                Copiar macro MONITORAMENTO
              </button>
              <button
                type="button"
                onClick={() => void handleCopyMacro("ESCALACAO")}
                style={buttonSecondaryStyle}
              >
                Copiar macro ESCALACAO
              </button>
            </div>
            {copyStatus ? <small style={copyStatusStyle}>{copyStatus}</small> : null}
            {macroHistory.length > 0 ? (
              <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
                <small style={{ ...smallStyle, color: "#93c5fd" }}>Histórico local de macros (últimos 20)</small>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button type="button" onClick={handleExportMacroHistoryCsv} style={buttonSecondaryStyle}>
                    Exportar CSV
                  </button>
                  <button type="button" onClick={handleExportMacroHistoryJson} style={buttonSecondaryStyle}>
                    Exportar JSON
                  </button>
                  <button type="button" onClick={() => void handleCopyMacroHistoryJson()} style={buttonSecondaryStyle}>
                    Copiar JSON
                  </button>
                </div>
                {macroHistory.slice(0, 5).map((entry) => (
                  <article key={entry.id} style={rowStyle}>
                    <div style={rowHeadStyle}>
                      <strong>{entry.kind} - {entry.incidentId}</strong>
                      <span style={statusBadgeStyle(entry.severity === "CRITICAL" ? 500 : 400)}>{entry.severity}</span>
                    </div>
                    <small style={smallStyle}>owner: {entry.owner} | turno: {entry.shift} | ETA: {entry.eta}</small>
                    <small style={smallStyle}>copiado em: {formatOpsDateTime(entry.createdAt)}</small>
                    <button
                      type="button"
                      onClick={() => void copyText(entry.text, `Macro ${entry.kind} recopiada.`)}
                      style={buttonSecondaryStyle}
                    >
                      Recopiar macro
                    </button>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle: CSSProperties = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle: CSSProperties = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const mutedStyle: CSSProperties = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const shortcutRowStyle: CSSProperties = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const shortcutLinkStyle: CSSProperties = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const filtersGridStyle: CSSProperties = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
};

const labelStyle: CSSProperties = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle: CSSProperties = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const actionsRowStyle: CSSProperties = {
  marginTop: 12,
  display: "flex",
  gap: 10,
  alignItems: "center",
  flexWrap: "wrap",
};

const buttonStyle: CSSProperties = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const buttonSecondaryStyle: CSSProperties = {
  ...buttonStyle,
  border: "1px solid rgba(96,165,250,0.55)",
  color: "#bfdbfe",
  background: "rgba(30,58,138,0.24)",
};

const errorStyle: CSSProperties = {
  marginTop: 14,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

const kpiGridStyle: CSSProperties = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
};

const kpiBoxStyle: CSSProperties = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: "10px 12px",
  display: "grid",
  gap: 4,
};

const rowStyle: CSSProperties = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const rowHeadStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const smallStyle: CSSProperties = {
  color: "rgba(226,232,240,0.9)",
  fontSize: 12,
  wordBreak: "break-word",
};

const statusBadgeStyle = (status: number | string): CSSProperties => {
  const code = Number(status || 0);
  const is5xx = code >= 500;
  const is4xx = code >= 400 && code < 500;
  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 800,
    lineHeight: 1.2,
    border: is5xx
      ? "1px solid #fecaca"
      : is4xx
        ? "1px solid #fdba74"
        : "1px solid #93c5fd",
    background: is5xx
      ? "#7f1d1d"
      : is4xx
        ? "#9a3412"
        : "#1e3a8a",
    color: "#ffffff",
  };
};

const copyStatusStyle: CSSProperties = {
  marginTop: 10,
  display: "inline-flex",
  color: "#93c5fd",
  fontWeight: 700,
  fontSize: 12,
};

