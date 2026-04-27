import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsTrendKpiCard from "../components/OpsTrendKpiCard";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";
const OPS_AUDIT_PAGE_VERSION = "ops/audit v2.0.0-sprint-audit1";
const AUDIT_COPY_MAX_ITEMS = 30;
const AUDIT_COPY_MAX_CHARS = 12000;

function extractErrorMessage(payload, fallback = "Não foi possível carregar trilha de auditoria.") {
  if (!payload) return fallback;
  if (typeof payload.detail === "string" && payload.detail.trim()) {
    return payload.detail.trim();
  }
  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string" && payload.detail.message.trim()) {
      return payload.detail.message.trim();
    }
    if (typeof payload.detail.type === "string" && payload.detail.type.trim()) {
      return payload.detail.type.trim();
    }
  }
  if (typeof payload.message === "string" && payload.message.trim()) {
    return payload.message.trim();
  }
  return fallback;
}

function toDateTimeLocalInputValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function toIsoOrNull(localDateTimeValue) {
  const raw = String(localDateTimeValue || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

const ACTION_OPTIONS = [
  "",
  "OPS_RECONCILE_ORDER",
  "OPS_RECON_PENDING_LIST",
  "OPS_RECON_PENDING_RUN_ONCE",
  "OPS_AUDIT_LIST",
  "OPS_METRICS_VIEW",
  "OPS_ORDERS_STATUS_AUDIT",
  "OPS_ORDERS_STATUS_AUDIT_RANGE",
  "OPS_ORDERS_STATUS_AUDIT_EXPORT",
  "I1_OUTBOX_MANUAL_REPLAY_BATCH",
];

const RESULT_OPTIONS = ["", "SUCCESS", "ERROR"];
const MAIN_LIMIT_OPTIONS = [20, 50, 100, 200];
const STATUS_LIMIT_OPTIONS = [100, 200, 500, 1000, 2000];

function resolveAuditSeverity(item) {
  const resultValue = String(item?.result || "").toUpperCase();
  const actionValue = String(item?.action || "").toUpperCase();
  if (resultValue === "ERROR") {
    if (actionValue.includes("RECON") || actionValue.includes("FAILED")) return "CRITICAL";
    return "HIGH";
  }
  if (resultValue === "SUCCESS" && actionValue.includes("RECON")) return "MEDIUM";
  return "LOW";
}

function severityEmoji(severity) {
  const normalized = String(severity || "").toUpperCase();
  if (normalized === "CRITICAL") return "🔴";
  if (normalized === "HIGH" || normalized === "ERROR") return "🟠";
  if (normalized === "MEDIUM" || normalized === "WARN") return "🟡";
  return "🟢";
}

function resolveAuditImpactScore(item) {
  const severity = resolveAuditSeverity(item);
  const details = item?.details && typeof item.details === "object" ? item.details : {};
  const hasLocker = Boolean(String(details?.locker_id || "").trim());
  const hasErrorMessage = Boolean(String(item?.error_message || "").trim());
  let score = severity === "CRITICAL" ? 100 : severity === "HIGH" ? 70 : severity === "MEDIUM" ? 35 : 10;
  if (hasLocker) score += 10;
  if (hasErrorMessage) score += 10;
  return score;
}

function resolveAuditCauseCategory(item) {
  const message = String(item?.error_message || "").toUpperCase();
  const action = String(item?.action || "").toUpperCase();
  if (!message && String(item?.result || "").toUpperCase() !== "ERROR") return "OUTROS";
  if (message.includes("TIMEOUT") || message.includes("TIMED OUT") || message.includes("DEADLINE")) return "TIMEOUT";
  if (
    message.includes("VALID") ||
    message.includes("INVALID") ||
    message.includes("CPF") ||
    message.includes("CNPJ") ||
    message.includes("PAYLOAD")
  ) {
    return "VALIDACAO";
  }
  if (
    message.includes("INTEGR") ||
    message.includes("API") ||
    message.includes("HTTP") ||
    message.includes("CONNECTION") ||
    action.includes("OUTBOX")
  ) {
    return "INTEGRACAO";
  }
  if (
    message.includes("DB") ||
    message.includes("DATABASE") ||
    message.includes("REDIS") ||
    message.includes("NETWORK") ||
    message.includes("INFRA")
  ) {
    return "INFRA";
  }
  return "OUTROS";
}

function getAuditSeverityBadgeStyle(severity) {
  const normalized = String(severity || "LOW").toUpperCase();
  if (normalized === "CRITICAL") {
    return {
      border: "1px solid #fecaca",
      background: "#7f1d1d",
      color: "#ffffff",
    };
  }
  if (normalized === "HIGH" || normalized === "ERROR") {
    return {
      border: "1px solid #fdba74",
      background: "#9a3412",
      color: "#ffffff",
    };
  }
  if (normalized === "MEDIUM" || normalized === "WARN") {
    return {
      border: "1px solid #fcd34d",
      background: "#78350f",
      color: "#ffffff",
    };
  }
  if (normalized === "OK") {
    return {
      border: "1px solid #86efac",
      background: "#14532d",
      color: "#ffffff",
    };
  }
  return {
    border: "1px solid #93c5fd",
    background: "#1e3a8a",
    color: "#ffffff",
  };
}

function escapeRegExp(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function renderHighlightedText(text, query) {
  const source = String(text || "");
  const needle = String(query || "").trim();
  if (!needle) return source || "-";
  const regex = new RegExp(`(${escapeRegExp(needle)})`, "ig");
  const parts = source.split(regex);
  return parts.map((part, idx) =>
    regex.test(part) ? (
      <mark key={`hl-${idx}`} style={highlightMarkStyle}>
        {part}
      </mark>
    ) : (
      <React.Fragment key={`txt-${idx}`}>{part}</React.Fragment>
    )
  );
}

function sanitizeText(value) {
  return String(value || "")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function maskMiddle(value, start = 4, end = 4) {
  const source = String(value || "").trim();
  if (!source) return "-";
  if (source.length <= start + end + 3) return `${source.slice(0, 2)}***`;
  return `${source.slice(0, start)}***${source.slice(-end)}`;
}

function redactSensitiveText(value) {
  let text = sanitizeText(value);
  text = text.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted-email]");
  text = text.replace(/\b\d{10,16}\b/g, "[redacted-number]");
  text = text.replace(/\b(bearer|token|secret|password)\s*[:=]\s*[^\s]+/gi, "$1=[redacted]");
  return text;
}

function enforceCopyTextLimit(value, maxChars = AUDIT_COPY_MAX_CHARS) {
  const text = String(value || "");
  if (text.length <= maxChars) {
    return { text, truncated: false };
  }
  return {
    text: `${text.slice(0, maxChars)}\n\n[TRUNCATED] Conteúdo excedeu ${maxChars} caracteres.`,
    truncated: true,
  };
}

export default function OpsAuditPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const now = new Date();
  const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [orderId, setOrderId] = useState("");
  const [lockerId, setLockerId] = useState("");
  const [correlationId, setCorrelationId] = useState("");
  const [errorSearch, setErrorSearch] = useState("");
  const [action, setAction] = useState("");
  const [result, setResult] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [auditFrom, setAuditFrom] = useState(toDateTimeLocalInputValue(last24h));
  const [auditTo, setAuditTo] = useState(toDateTimeLocalInputValue(now));
  const [statusLimit, setStatusLimit] = useState(200);
  const [statusOffset, setStatusOffset] = useState(0);
  const [statusHasMore, setStatusHasMore] = useState(false);
  const [opsHasMore, setOpsHasMore] = useState(false);
  const [statusAuditItems, setStatusAuditItems] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState("24h");
  const [selectedAuditIds, setSelectedAuditIds] = useState({});
  const [copyStatus, setCopyStatus] = useState("");
  const [rankingOpen, setRankingOpen] = useState(false);
  const [rankingSeverityFilter, setRankingSeverityFilter] = useState("");
  const [rankingLimit, setRankingLimit] = useState(8);
  const [groupingOpen, setGroupingOpen] = useState(false);
  const [groupingCauseFilter, setGroupingCauseFilter] = useState("");
  const [groupingRecurrenceFilter, setGroupingRecurrenceFilter] = useState("");
  const [groupingLimit, setGroupingLimit] = useState(6);
  const [timelineOpen, setTimelineOpen] = useState(false);
  const [timelineMarkerFilter, setTimelineMarkerFilter] = useState("");
  const [timelineEntitySearch, setTimelineEntitySearch] = useState("");
  const [timelineLimit, setTimelineLimit] = useState(30);
  const [validationOutcome, setValidationOutcome] = useState("APPROVED");
  const [validationNotes, setValidationNotes] = useState("");
  const didInitialLoadRef = useRef(false);

  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);
  const storageKey = useMemo(() => {
    const suffix = token ? token.slice(0, 16) : "anonymous";
    return `ops-audit-filters:v1:${suffix}`;
  }, [token]);
  const auditKpis = useMemo(() => {
    const scopedByLocker = lockerId
      ? items.filter((item) => String(item?.details?.locker_id || "").trim().toUpperCase().includes(lockerId.toUpperCase()))
      : items;
    const scopedByCorrelation = correlationId
      ? scopedByLocker.filter((item) =>
          String(item?.correlation_id || "")
            .trim()
            .toUpperCase()
            .includes(correlationId.toUpperCase())
        )
      : scopedByLocker;
    const scopedByErrorText = errorSearch
      ? scopedByCorrelation.filter((item) =>
          String(item?.error_message || "")
            .toUpperCase()
            .includes(errorSearch.toUpperCase())
        )
      : scopedByCorrelation;
    const scopedItems = severityFilter
      ? scopedByErrorText.filter((item) => resolveAuditSeverity(item) === severityFilter)
      : scopedByErrorText;
    const successCount = scopedItems.filter((item) => String(item?.result || "").toUpperCase() === "SUCCESS").length;
    const errorCount = scopedItems.filter((item) => String(item?.result || "").toUpperCase() === "ERROR").length;
    return {
      totalRows: total,
      scopedRows: scopedItems.length,
      successRows: successCount,
      errorRows: errorCount,
      statusInconsistencies: statusAuditItems.length,
    };
  }, [items, total, statusAuditItems, severityFilter, lockerId, correlationId, errorSearch]);
  const severityChipCounts = useMemo(() => {
    const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    for (const item of items) {
      const sev = resolveAuditSeverity(item);
      counts[sev] = Number(counts[sev] || 0) + 1;
    }
    return counts;
  }, [items]);
  const filteredItems = useMemo(() => {
    const scopedByLocker = lockerId
      ? items.filter((item) => String(item?.details?.locker_id || "").trim().toUpperCase().includes(lockerId.toUpperCase()))
      : items;
    const scopedByCorrelation = correlationId
      ? scopedByLocker.filter((item) =>
          String(item?.correlation_id || "")
            .trim()
            .toUpperCase()
            .includes(correlationId.toUpperCase())
        )
      : scopedByLocker;
    const scopedByErrorText = errorSearch
      ? scopedByCorrelation.filter((item) =>
          String(item?.error_message || "")
            .toUpperCase()
            .includes(errorSearch.toUpperCase())
        )
      : scopedByCorrelation;
    if (!severityFilter) return scopedByErrorText;
    return scopedByErrorText.filter((item) => resolveAuditSeverity(item) === severityFilter);
  }, [items, severityFilter, lockerId, correlationId, errorSearch]);
  const auditSummary24h = useMemo(() => {
    const nowTs = Date.now();
    const dayAgoTs = nowTs - 24 * 60 * 60 * 1000;
    const rows24h = filteredItems.filter((item) => {
      const createdTs = Date.parse(String(item?.created_at || ""));
      return !Number.isNaN(createdTs) && createdTs >= dayAgoTs && createdTs <= nowTs;
    });
    const totalRows24h = rows24h.length;
    const errorRows24h = rows24h.filter((item) => String(item?.result || "").toUpperCase() === "ERROR").length;
    const errorRate24h = totalRows24h > 0 ? errorRows24h / totalRows24h : 0;
    const severityDominant = totalRows24h > 0 ? (
      errorRate24h > 0.5 ? "CRITICAL" : errorRate24h >= 0.2 ? "HIGH" : errorRate24h >= 0.05 ? "MEDIUM" : "LOW"
    ) : "LOW";
    return {
      totalRows24h,
      errorRows24h,
      errorRate24h,
      severityDominant,
      sourceLabel: `Base atual: página consultada (${filteredItems.length} itens${severityFilter ? `, severidade=${severityFilter}` : ""}${lockerId ? `, locker~${lockerId}` : ""}${correlationId ? `, corr~${correlationId}` : ""}${errorSearch ? `, erro~${errorSearch}` : ""}).`,
    };
  }, [filteredItems, severityFilter, lockerId, correlationId, errorSearch]);
  const criticalRanking = useMemo(() => {
    return [...filteredItems]
      .map((item) => {
        const severity = resolveAuditSeverity(item);
        const impactScore = resolveAuditImpactScore(item);
        const createdTs = Date.parse(String(item?.created_at || ""));
        const lockerId = String(item?.details?.locker_id || "").trim();
        return {
          ...item,
          severity,
          impactScore,
          createdTs: Number.isNaN(createdTs) ? 0 : createdTs,
          lockerId,
        };
      })
      .sort((a, b) => {
        const rank = { CRITICAL: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
        const severityDiff = (rank[a.severity] || 99) - (rank[b.severity] || 99);
        if (severityDiff !== 0) return severityDiff;
        if (b.impactScore !== a.impactScore) return b.impactScore - a.impactScore;
        return b.createdTs - a.createdTs;
      })
      .slice(0, 8);
  }, [filteredItems]);
  const filteredCriticalRanking = useMemo(() => {
    const bySeverity = rankingSeverityFilter
      ? criticalRanking.filter((item) => String(item?.severity || "").toUpperCase() === rankingSeverityFilter)
      : criticalRanking;
    return bySeverity.slice(0, Math.max(Number(rankingLimit || 8), 1));
  }, [criticalRanking, rankingSeverityFilter, rankingLimit]);
  const groupedCauseInsights = useMemo(() => {
    const total = filteredItems.length;
    const causeMap = new Map();
    const correlationMap = new Map();
    for (const item of filteredItems) {
      const cause = resolveAuditCauseCategory(item);
      const corr = String(item?.correlation_id || "").trim() || "-";
      const createdTs = Date.parse(String(item?.created_at || ""));
      const entry = causeMap.get(cause) || {
        cause,
        total: 0,
        errorCount: 0,
        lastSeenTs: 0,
        correlations: new Set(),
      };
      entry.total += 1;
      if (String(item?.result || "").toUpperCase() === "ERROR") entry.errorCount += 1;
      entry.correlations.add(corr);
      if (!Number.isNaN(createdTs) && createdTs > entry.lastSeenTs) entry.lastSeenTs = createdTs;
      causeMap.set(cause, entry);

      const corrEntry = correlationMap.get(corr) || {
        correlationId: corr,
        total: 0,
        errorCount: 0,
        causes: new Set(),
        lastSeenTs: 0,
      };
      corrEntry.total += 1;
      if (String(item?.result || "").toUpperCase() === "ERROR") corrEntry.errorCount += 1;
      corrEntry.causes.add(cause);
      if (!Number.isNaN(createdTs) && createdTs > corrEntry.lastSeenTs) corrEntry.lastSeenTs = createdTs;
      correlationMap.set(corr, corrEntry);
    }

    const groups = [...causeMap.values()]
      .map((entry) => {
        const relatedCorrelations = [...correlationMap.values()]
          .filter((corr) => corr.causes.has(entry.cause))
          .sort((a, b) => b.total - a.total || b.errorCount - a.errorCount || b.lastSeenTs - a.lastSeenTs)
          .slice(0, 5)
          .map((corr) => ({
            correlationId: corr.correlationId,
            total: corr.total,
            errorCount: corr.errorCount,
            recurrenceLevel: corr.total >= 5 ? "ALTA" : corr.total >= 3 ? "MEDIA" : "BAIXA",
            lastSeenLabel: corr.lastSeenTs ? new Date(corr.lastSeenTs).toISOString() : "-",
          }));
        return {
          cause: entry.cause,
          total: entry.total,
          percentage: total > 0 ? (entry.total / total) * 100 : 0,
          errorRate: entry.total > 0 ? entry.errorCount / entry.total : 0,
          recurrenceLevel: entry.total >= 10 ? "ALTA" : entry.total >= 4 ? "MEDIA" : "BAIXA",
          lastSeenLabel: entry.lastSeenTs ? new Date(entry.lastSeenTs).toISOString() : "-",
          correlationCount: entry.correlations.size,
          relatedCorrelations,
        };
      })
      .sort((a, b) => b.total - a.total || b.errorRate - a.errorRate);

    return {
      groups,
      top3Label: groups
        .slice(0, 3)
        .map((item) => `${item.cause} (${item.total})`)
        .join(" · "),
    };
  }, [filteredItems]);
  const filteredGroupedCauseInsights = useMemo(() => {
    const byCause = groupingCauseFilter
      ? groupedCauseInsights.groups.filter((group) => group.cause.includes(groupingCauseFilter.toUpperCase()))
      : groupedCauseInsights.groups;
    const byRecurrence = groupingRecurrenceFilter
      ? byCause.filter((group) => group.recurrenceLevel === groupingRecurrenceFilter)
      : byCause;
    return byRecurrence.slice(0, Math.max(Number(groupingLimit || 6), 1));
  }, [groupedCauseInsights.groups, groupingCauseFilter, groupingRecurrenceFilter, groupingLimit]);
  const timelineInsights = useMemo(() => {
    const sorted = [...filteredItems]
      .map((item) => {
        const createdTs = Date.parse(String(item?.created_at || ""));
        const createdAt = Number.isNaN(createdTs) ? 0 : createdTs;
        const severity = resolveAuditSeverity(item);
        const cause = resolveAuditCauseCategory(item);
        const locker = String(item?.details?.locker_id || "").trim() || "-";
        const corr = String(item?.correlation_id || "").trim() || "-";
        const order = String(item?.order_id || "").trim() || "-";
        const bucket = createdAt > 0 ? new Date(createdAt).toISOString().slice(0, 13) : "unknown-hour";
        return {
          ...item,
          createdAt,
          severity,
          cause,
          locker,
          corr,
          order,
          hourBucket: bucket,
        };
      })
      .sort((a, b) => a.createdAt - b.createdAt);

    const bucketStats = new Map();
    for (const event of sorted) {
      const stats = bucketStats.get(event.hourBucket) || { total: 0, error: 0 };
      stats.total += 1;
      if (String(event?.result || "").toUpperCase() === "ERROR") stats.error += 1;
      bucketStats.set(event.hourBucket, stats);
    }

    const recent = sorted.slice(-80).map((event) => {
      const stats = bucketStats.get(event.hourBucket) || { total: 0, error: 0 };
      const hourErrorRate = stats.total > 0 ? stats.error / stats.total : 0;
      const markers = [];
      if (String(event?.result || "").toUpperCase() === "ERROR") markers.push("ERROR_EVENT");
      if (stats.error >= 3 && hourErrorRate >= 0.5) markers.push("ERROR_SPIKE");
      if (event.severity === "CRITICAL") markers.push("SEVERITY_CRITICAL");
      return {
        ...event,
        hourTotal: stats.total,
        hourError: stats.error,
        hourErrorRate,
        markers,
      };
    });

    return {
      events: recent.reverse(),
      spikes: recent.filter((event) => event.markers.includes("ERROR_SPIKE")).length,
      criticals: recent.filter((event) => event.severity === "CRITICAL").length,
    };
  }, [filteredItems]);
  const filteredTimelineEvents = useMemo(() => {
    const byMarker = timelineMarkerFilter
      ? timelineInsights.events.filter((event) => event.markers.includes(timelineMarkerFilter))
      : timelineInsights.events;
    const needle = timelineEntitySearch.trim().toUpperCase();
    const byEntity = needle
      ? byMarker.filter((event) => {
          const haystack = `${event.locker} ${event.corr} ${event.order} ${event.action} ${event.cause}`.toUpperCase();
          return haystack.includes(needle);
        })
      : byMarker;
    return byEntity.slice(0, Math.max(Number(timelineLimit || 30), 1));
  }, [timelineInsights.events, timelineMarkerFilter, timelineEntitySearch, timelineLimit]);
  const selectedFilteredItems = useMemo(() => {
    return filteredItems.filter((item) => Boolean(selectedAuditIds[item.id]));
  }, [filteredItems, selectedAuditIds]);
  const activeFilterChips = useMemo(() => {
    const chips = [];
    if (orderId) chips.push(`order_id~${orderId}`);
    if (lockerId) chips.push(`locker_id~${lockerId}`);
    if (correlationId) chips.push(`correlation_id~${correlationId}`);
    if (errorSearch) chips.push(`error_search~${errorSearch}`);
    if (action) chips.push(`action=${action}`);
    if (result) chips.push(`result=${result}`);
    if (severityFilter) chips.push(`severity=${severityFilter}`);
    return chips;
  }, [orderId, lockerId, correlationId, errorSearch, action, result, severityFilter]);

  function buildAuditEvidenceMarkdown(item) {
    const severity = resolveAuditSeverity(item);
    const details = item?.details && typeof item.details === "object" ? item.details : {};
    const impactScore = resolveAuditImpactScore(item);
    return [
      `# [OPS-AUDIT] Evidência operacional`,
      ``,
      `- Ação: ${sanitizeText(item?.action || "-")}`,
      `- Resultado: ${sanitizeText(item?.result || "-")}`,
      `- Severidade esperada: ${severity}`,
      `- Impacto sugerido (score): ${impactScore}`,
      `- Locker: ${sanitizeText(details?.locker_id || "-")}`,
      `- Order ID: ${maskMiddle(item?.order_id || "-")}`,
      `- Correlation ID: ${maskMiddle(item?.correlation_id || "-")}`,
      `- Timestamp: ${sanitizeText(item?.created_at || "-")}`,
      `- User ID: ${maskMiddle(item?.user_id || "-")}`,
      ``,
      `## Erro`,
      `${redactSensitiveText(item?.error_message || "Sem mensagem de erro.")}`,
      ``,
      `## Próximos passos`,
      `1. Correlacionar evento no OPS Audit por correlation_id.`,
      `2. Validar impacto em locker/order relacionado.`,
      `3. Acionar runbook e registrar ação corretiva.`,
    ].join("\n");
  }

  function buildAuditEvidencePlain(item) {
    const severity = resolveAuditSeverity(item);
    const details = item?.details && typeof item.details === "object" ? item.details : {};
    const impactScore = resolveAuditImpactScore(item);
    return [
      `OPS-AUDIT EVIDENCIA`,
      `Acao: ${sanitizeText(item?.action || "-")}`,
      `Resultado: ${sanitizeText(item?.result || "-")}`,
      `Severidade esperada: ${severity}`,
      `Impacto sugerido (score): ${impactScore}`,
      `Locker: ${sanitizeText(details?.locker_id || "-")}`,
      `Order ID: ${maskMiddle(item?.order_id || "-")}`,
      `Correlation ID: ${maskMiddle(item?.correlation_id || "-")}`,
      `Timestamp: ${sanitizeText(item?.created_at || "-")}`,
      `User ID: ${maskMiddle(item?.user_id || "-")}`,
      `Erro: ${redactSensitiveText(item?.error_message || "Sem mensagem de erro.")}`,
      `Proximos passos: correlacionar por correlation_id, validar impacto, acionar runbook.`,
    ].join("\n");
  }

  function buildAuditEvidenceSlack(item) {
    const severity = resolveAuditSeverity(item);
    const sevEmoji = severityEmoji(severity);
    const details = item?.details && typeof item.details === "object" ? item.details : {};
    const errorValue = redactSensitiveText(item?.error_message || "");
    const errorSnippet = errorValue ? ` | erro=${errorValue}` : "";
    return [
      `${sevEmoji} [OPS-AUDIT] ${sanitizeText(item?.action || "-")} | ${sanitizeText(item?.result || "-")} | sev=${severity}`,
      `locker=${sanitizeText(details?.locker_id || "-")} | order=${maskMiddle(item?.order_id || "-")} | corr=${maskMiddle(item?.correlation_id || "-")}`,
      `at=${sanitizeText(item?.created_at || "-")} | user=${maskMiddle(item?.user_id || "-")}${errorSnippet}`,
      `next: validar impacto, correlacionar por corr_id, registrar acao corretiva`,
    ].join("\n");
  }

  async function copyToClipboard(text, successMessage) {
    try {
      const bounded = enforceCopyTextLimit(text);
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(bounded.text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = bounded.text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setCopyStatus(`${successMessage}${bounded.truncated ? " (com truncamento de segurança)" : ""}`);
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch (err) {
      setCopyStatus(`Falha ao copiar evidência: ${String(err?.message || err)}`);
    }
  }

  async function copySingleEvidence(item, mode = "md") {
    const text = mode === "plain" ? buildAuditEvidencePlain(item) : buildAuditEvidenceMarkdown(item);
    await copyToClipboard(text, `Evidência ${mode === "plain" ? "texto simples" : "markdown"} copiada.`);
  }

  async function copySingleEvidenceSlack(item) {
    await copyToClipboard(buildAuditEvidenceSlack(item), "Resumo Slack/Teams copiado.");
  }

  async function copyBatchEvidence(mode = "md") {
    if (selectedFilteredItems.length === 0) {
      setCopyStatus("Selecione pelo menos um item para copiar em lote.");
      return;
    }
    const cappedItems = selectedFilteredItems.slice(0, AUDIT_COPY_MAX_ITEMS);
    const sections = cappedItems.map((item, idx) => {
      const block = mode === "plain" ? buildAuditEvidencePlain(item) : buildAuditEvidenceMarkdown(item);
      return `${mode === "plain" ? `--- ITEM ${idx + 1} ---` : `## Item ${idx + 1}\n`}\n${block}`;
    });
    const text = sections.join("\n\n");
    await copyToClipboard(
      text,
      `Evidência em lote (${cappedItems.length}/${selectedFilteredItems.length} itens, ${mode === "plain" ? "texto simples" : "markdown"}) copiada${
        cappedItems.length < selectedFilteredItems.length ? " com limite de segurança" : ""
      }.`
    );
  }

  async function copyBatchEvidenceSlack() {
    if (selectedFilteredItems.length === 0) {
      setCopyStatus("Selecione pelo menos um item para copiar em lote.");
      return;
    }
    const cappedItems = selectedFilteredItems.slice(0, AUDIT_COPY_MAX_ITEMS);
    const sections = cappedItems.map((item, idx) => `--- ITEM ${idx + 1} ---\n${buildAuditEvidenceSlack(item)}`);
    const text = sections.join("\n\n");
    await copyToClipboard(
      text,
      `Resumo Slack/Teams em lote (${cappedItems.length}/${selectedFilteredItems.length} itens) copiado${
        cappedItems.length < selectedFilteredItems.length ? " com limite de segurança" : ""
      }.`
    );
  }

  async function copyAuditDailySlack() {
    const nowIso = new Date().toISOString();
    const rankingTop = filteredCriticalRanking.slice(0, 3);
    const topCauses = filteredGroupedCauseInsights.slice(0, 3).map((group) => `${group.cause}:${group.total}`).join(" | ") || "-";
    const spikes = filteredTimelineEvents.filter((event) => event.markers.includes("ERROR_SPIKE")).length;
    const criticals = filteredTimelineEvents.filter((event) => event.severity === "CRITICAL").length;
    const dominantSeverity = auditSummary24h?.severityDominant || "LOW";
    const dominantEmoji = severityEmoji(dominantSeverity);
    const text = [
      `${dominantEmoji} *OPS Daily (Audit) | ${nowIso}*`,
      `Hoje: sev=${dominantSeverity} ${dominantEmoji} | eventos_filtrados=${filteredItems.length} | ranking_top=${rankingTop.length} | causas_top=${topCauses}`,
      `Bloqueios: sem bloqueios técnicos; pendente validação operacional final de plantão`,
      `Decisão: manter fechamento como concluído em código e anexar evidência operacional incremental`,
      `Sinais: timeline_spikes=${spikes} | timeline_criticos=${criticals}`,
    ].join("\n");
    await copyToClipboard(text, "Daily Slack/Teams (ops/audit) copiado.");
  }

  function buildFinalValidationEvidence(mode = "md") {
    const nowIso = new Date().toISOString();
    const rankingTop = filteredCriticalRanking.slice(0, 3);
    const topCauses = filteredGroupedCauseInsights.slice(0, 3);
    const timelineSpikes = filteredTimelineEvents.filter((event) => event.markers.includes("ERROR_SPIKE")).length;
    const timelineCritical = filteredTimelineEvents.filter((event) => event.severity === "CRITICAL").length;
    const activeFiltersText = activeFilterChips.length > 0 ? activeFilterChips.join(" | ") : "nenhum";
    const notes = sanitizeText(validationNotes || "Sem observações adicionais.");
    if (mode === "plain") {
      return [
        "US-AUDIT-FINAL-VALIDATION",
        `timestamp: ${nowIso}`,
        `outcome: ${validationOutcome}`,
        `filtros_ativos: ${activeFiltersText}`,
        `resumo_24h: total=${auditSummary24h.totalRows24h} | erros=${auditSummary24h.errorRows24h} | taxa=${(auditSummary24h.errorRate24h * 100).toFixed(1)}% | sev=${auditSummary24h.severityDominant}`,
        `ranking_top3: ${rankingTop.map((item) => `${item.severity}:${sanitizeText(item.action || "-")}`).join(" | ") || "-"}`,
        `causas_top3: ${topCauses.map((group) => `${group.cause}:${group.total}(${group.recurrenceLevel})`).join(" | ") || "-"}`,
        `timeline: eventos=${filteredTimelineEvents.length} | spikes=${timelineSpikes} | criticos=${timelineCritical}`,
        `notas: ${notes}`,
        "decisao: registrar evidencia operacional e encerrar sprint ops/audit em codigo",
      ].join("\n");
    }
    return [
      "## US-AUDIT-FINAL-VALIDATION",
      `- Timestamp: ${nowIso}`,
      `- Resultado: ${validationOutcome}`,
      `- Filtros ativos: ${activeFiltersText}`,
      `- Resumo 24h: total=${auditSummary24h.totalRows24h}, erros=${auditSummary24h.errorRows24h}, taxa=${(auditSummary24h.errorRate24h * 100).toFixed(1)}%, severidade=${auditSummary24h.severityDominant}`,
      `- Ranking top 3: ${rankingTop.map((item) => `${item.severity}:${sanitizeText(item.action || "-")}`).join(" | ") || "-"}`,
      `- Causas top 3: ${topCauses.map((group) => `${group.cause}:${group.total}(${group.recurrenceLevel})`).join(" | ") || "-"}`,
      `- Timeline: eventos=${filteredTimelineEvents.length}, spikes=${timelineSpikes}, criticos=${timelineCritical}`,
      `- Notas de validacao: ${notes}`,
      "- Decisao recomendada: encerrar sprint ops/audit como concluido em codigo e anexar validacao operacional.",
    ].join("\n");
  }

  async function copyFinalValidationEvidence(mode = "md") {
    const text = buildFinalValidationEvidence(mode);
    await copyToClipboard(
      text,
      `US-AUDIT-FINAL-VALIDATION (${mode === "plain" ? "texto simples" : "markdown"}) copiado.`
    );
  }

  function toggleSelectAuditItem(id) {
    setSelectedAuditIds((current) => ({
      ...current,
      [id]: !current[id],
    }));
  }

  function toggleSelectAllFiltered() {
    const allSelected = filteredItems.length > 0 && filteredItems.every((item) => Boolean(selectedAuditIds[item.id]));
    if (allSelected) {
      const next = { ...selectedAuditIds };
      for (const item of filteredItems) delete next[item.id];
      setSelectedAuditIds(next);
      return;
    }
    const next = { ...selectedAuditIds };
    for (const item of filteredItems) next[item.id] = true;
    setSelectedAuditIds(next);
  }

  function setSeverityFilterWithUrl(nextSeverity) {
    const normalized = String(nextSeverity || "").toUpperCase();
    const allowed = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
    const finalValue = allowed.includes(normalized) ? normalized : "";
    setSeverityFilter(finalValue);
    const params = new URLSearchParams(location.search || "");
    if (finalValue) {
      params.set("severity", finalValue);
    } else {
      params.delete("severity");
    }
    navigate(
      {
        pathname: location.pathname,
        search: params.toString() ? `?${params.toString()}` : "",
      },
      { replace: true }
    );
  }

  function setLockerIdWithUrl(nextLockerId) {
    const normalized = String(nextLockerId || "").trim();
    setLockerId(normalized);
    const params = new URLSearchParams(location.search || "");
    if (normalized) {
      params.set("locker_id", normalized);
    } else {
      params.delete("locker_id");
    }
    navigate(
      {
        pathname: location.pathname,
        search: params.toString() ? `?${params.toString()}` : "",
      },
      { replace: true }
    );
  }

  function setCorrelationIdWithUrl(nextCorrelationId) {
    const normalized = String(nextCorrelationId || "").trim();
    setCorrelationId(normalized);
    const params = new URLSearchParams(location.search || "");
    if (normalized) {
      params.set("correlation_id", normalized);
    } else {
      params.delete("correlation_id");
    }
    navigate(
      {
        pathname: location.pathname,
        search: params.toString() ? `?${params.toString()}` : "",
      },
      { replace: true }
    );
  }

  function setErrorSearchWithUrl(nextErrorSearch) {
    const normalized = String(nextErrorSearch || "").trim();
    setErrorSearch(normalized);
    const params = new URLSearchParams(location.search || "");
    if (normalized) {
      params.set("error_search", normalized);
    } else {
      params.delete("error_search");
    }
    navigate(
      {
        pathname: location.pathname,
        search: params.toString() ? `?${params.toString()}` : "",
      },
      { replace: true }
    );
  }

  function applyRangePreset(presetId) {
    const referenceNow = new Date();
    let start = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);
    if (presetId === "7d") {
      start = new Date(referenceNow.getTime() - 7 * 24 * 60 * 60 * 1000);
    } else if (presetId === "30d") {
      start = new Date(referenceNow.getTime() - 30 * 24 * 60 * 60 * 1000);
    } else if (presetId === "month") {
      start = new Date(referenceNow.getFullYear(), referenceNow.getMonth(), 1, 0, 0, 0, 0);
    }
    setAuditFrom(toDateTimeLocalInputValue(start));
    setAuditTo(toDateTimeLocalInputValue(referenceNow));
    setStatusOffset(0);
    setSelectedPreset(presetId);
  }

  function resetToShiftDefaults() {
    const confirmation = window.confirm(
      "Resetar todos os filtros para o padrão de plantão (24h e offsets zerados)?"
    );
    if (!confirmation) return;

    const referenceNow = new Date();
    const start24h = new Date(referenceNow.getTime() - 24 * 60 * 60 * 1000);

    setOrderId("");
    setLockerIdWithUrl("");
    setCorrelationIdWithUrl("");
    setErrorSearchWithUrl("");
    setAction("");
    setResult("");
    setLimit(20);
    setOffset(0);

    setAuditFrom(toDateTimeLocalInputValue(start24h));
    setAuditTo(toDateTimeLocalInputValue(referenceNow));
    setStatusLimit(200);
    setStatusOffset(0);
    setSelectedPreset("24h");

    const nextAuditFrom = toDateTimeLocalInputValue(start24h);
    const nextAuditTo = toDateTimeLocalInputValue(referenceNow);
    loadAudit(0, {
      orderId: "",
      lockerId: "",
      correlationId: "",
      errorSearch: "",
      action: "",
      result: "",
      limit: 20,
      offset: 0,
    });
    loadStatusAudit(0, {
      auditFrom: nextAuditFrom,
      auditTo: nextAuditTo,
      statusLimit: 200,
      statusOffset: 0,
    });
  }

  async function loadAudit(nextOffset = null, overrides = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const effectiveOffset = Math.max(Number(nextOffset ?? overrides?.offset ?? offset ?? 0), 0);
      const effectiveLimit = Math.min(Math.max(Number((overrides?.limit ?? limit) ?? 20), 1), 200);
      const effectiveOrderId = String(overrides?.orderId ?? orderId ?? "").trim();
      const effectiveLockerId = String(overrides?.lockerId ?? lockerId ?? "").trim();
      const effectiveCorrelationId = String(overrides?.correlationId ?? correlationId ?? "").trim();
      const effectiveAction = String(overrides?.action ?? action ?? "").trim();
      const effectiveResult = String(overrides?.result ?? result ?? "").trim();
      const params = new URLSearchParams();
      params.set("limit", String(effectiveLimit));
      params.set("offset", String(effectiveOffset));
      if (effectiveOrderId) params.set("order_id", effectiveOrderId);
      if (effectiveLockerId) params.set("locker_id", effectiveLockerId);
      if (effectiveCorrelationId) params.set("correlation_id", effectiveCorrelationId);
      if (effectiveAction) params.set("action", effectiveAction);
      if (effectiveResult) params.set("result", effectiveResult);

      const response = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/ops-audit?${params.toString()}`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          ...authHeaders,
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
      }
      const rows = Array.isArray(payload?.items) ? payload.items : [];
      setItems(rows);
      setTotal(Number(payload?.total || rows.length || 0));
      setOffset(effectiveOffset);
      setOpsHasMore(rows.length >= effectiveLimit);
    } catch (err) {
      setError(String(err?.message || err));
      setItems([]);
      setTotal(0);
      setOpsHasMore(false);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!didInitialLoadRef.current) return;
    loadAudit(0, { lockerId, offset: 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lockerId]);

  async function loadStatusAudit(nextOffset = null, overrides = null) {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(overrides?.auditFrom ?? auditFrom);
      const toIso = toIsoOrNull(overrides?.auditTo ?? auditTo);
      if (!fromIso || !toIso) {
        throw new Error("Preencha from/to com datas válidas.");
      }

      const effectiveOffset = Math.max(Number(nextOffset ?? overrides?.statusOffset ?? statusOffset ?? 0), 0);
      const effectiveLimit = Math.min(Math.max(Number((overrides?.statusLimit ?? statusLimit) ?? 200), 1), 2000);
      const params = new URLSearchParams();
      params.set("from", fromIso);
      params.set("to", toIso);
      params.set("limit", String(effectiveLimit));
      params.set("offset", String(effectiveOffset));
      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/orders-status-audit/range?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
            ...authHeaders,
          },
        }
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload, "Não foi possível carregar auditoria de status."));
      }
      setStatusAuditItems(Array.isArray(payload?.items) ? payload.items : []);
      setStatusHasMore(Boolean(payload?.has_more));
      setStatusOffset(effectiveOffset);
    } catch (err) {
      setError(String(err?.message || err));
      setStatusAuditItems([]);
      setStatusHasMore(false);
    } finally {
      setLoading(false);
    }
  }

  async function exportStatusAuditCsv() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const fromIso = toIsoOrNull(auditFrom);
      const toIso = toIsoOrNull(auditTo);
      if (!fromIso || !toIso) {
        throw new Error("Preencha from/to com datas válidas.");
      }
      const params = new URLSearchParams();
      params.set("from", fromIso);
      params.set("to", toIso);
      params.set("limit", "20000");

      const response = await fetch(
        `${ORDER_PICKUP_BASE}/dev-admin/orders-status-audit/export.csv?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Accept: "text/csv",
            ...authHeaders,
          },
        }
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(extractErrorMessage(payload, "Não foi possível exportar CSV."));
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const downloadLink = document.createElement("a");
      downloadLink.href = objectUrl;
      downloadLink.download = `ops-orders-status-audit-${new Date().toISOString()}.csv`;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function handleMainFiltersKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      loadAudit(0);
    }
  }

  function handleStatusFiltersKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      loadStatusAudit(0);
    }
  }

  useEffect(() => {
    if (!token) return;
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (typeof parsed.orderId === "string") setOrderId(parsed.orderId);
      if (typeof parsed.lockerId === "string") setLockerId(parsed.lockerId);
      if (typeof parsed.correlationId === "string") setCorrelationId(parsed.correlationId);
      if (typeof parsed.errorSearch === "string") setErrorSearch(parsed.errorSearch);
      if (typeof parsed.action === "string") setAction(parsed.action);
      if (typeof parsed.result === "string") setResult(parsed.result);
      if (Number.isFinite(parsed.limit)) setLimit(Math.min(Math.max(Number(parsed.limit), 1), 200));
      if (Number.isFinite(parsed.offset)) setOffset(Math.max(Number(parsed.offset), 0));
      if (typeof parsed.auditFrom === "string" && parsed.auditFrom.trim()) setAuditFrom(parsed.auditFrom);
      if (typeof parsed.auditTo === "string" && parsed.auditTo.trim()) setAuditTo(parsed.auditTo);
      if (Number.isFinite(parsed.statusLimit)) {
        setStatusLimit(Math.min(Math.max(Number(parsed.statusLimit), 1), 2000));
      }
      if (Number.isFinite(parsed.statusOffset)) setStatusOffset(Math.max(Number(parsed.statusOffset), 0));
      if (typeof parsed.selectedPreset === "string" && parsed.selectedPreset.trim()) {
        setSelectedPreset(parsed.selectedPreset);
      }
    } catch (_err) {
      // Ignore corrupted local storage payloads and keep defaults.
    }
  }, [token, storageKey]);

  useEffect(() => {
    if (!token) return;
    const params = new URLSearchParams(location.search || "");
    const actionParam = String(params.get("action") || "").trim();
    const limitParam = Number(params.get("limit"));
    const resultParam = String(params.get("result") || "").trim();
    const orderIdParam = String(params.get("order_id") || "").trim();
    const lockerIdParam = String(params.get("locker_id") || "").trim();
    const correlationIdParam = String(params.get("correlation_id") || "").trim();
    const errorSearchParam = String(params.get("error_search") || "").trim();
    const offsetParam = Number(params.get("offset"));
    const fromParam = String(params.get("from") || "").trim();
    const toParam = String(params.get("to") || "").trim();
    const severityParam = String(params.get("severity") || "").trim().toUpperCase();

    if (actionParam) setAction(actionParam);
    if (Number.isFinite(limitParam) && limitParam > 0) setLimit(Math.min(Math.max(limitParam, 1), 200));
    if (resultParam) setResult(resultParam.toUpperCase());
    if (orderIdParam) setOrderId(orderIdParam);
    if (lockerIdParam) setLockerId(lockerIdParam);
    if (correlationIdParam) setCorrelationId(correlationIdParam);
    if (errorSearchParam) setErrorSearch(errorSearchParam);
    if (Number.isFinite(offsetParam) && offsetParam >= 0) setOffset(Math.max(offsetParam, 0));
    if (fromParam) {
      const parsedFrom = new Date(fromParam);
      if (!Number.isNaN(parsedFrom.getTime())) {
        setAuditFrom(toDateTimeLocalInputValue(parsedFrom));
      }
    }
    if (toParam) {
      const parsedTo = new Date(toParam);
      if (!Number.isNaN(parsedTo.getTime())) {
        setAuditTo(toDateTimeLocalInputValue(parsedTo));
      }
    }
    if (["CRITICAL", "HIGH", "MEDIUM", "LOW"].includes(severityParam)) {
      setSeverityFilter(severityParam);
    } else if (!severityParam) {
      setSeverityFilter("");
    }
  }, [token, location.search]);

  useEffect(() => {
    if (!token) return;
    const payload = {
      orderId,
      lockerId,
      correlationId,
      errorSearch,
      action,
      result,
      limit,
      offset,
      auditFrom,
      auditTo,
      statusLimit,
      statusOffset,
      selectedPreset,
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch (_err) {
      // Ignore storage quota/access errors in restricted browsers.
    }
  }, [
    token,
    storageKey,
    orderId,
    lockerId,
    correlationId,
    errorSearch,
    action,
    result,
    limit,
    offset,
    auditFrom,
    auditTo,
    statusLimit,
    statusOffset,
    selectedPreset,
  ]);

  useEffect(() => {
    if (!token || didInitialLoadRef.current) return;
    didInitialLoadRef.current = true;
    loadAudit(0);
    loadStatusAudit(0);
  }, [token]);

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/ops/reconciliation" style={shortcutLinkStyle}>
            Ir para reconciliação
          </Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>

        <h1 style={{ marginTop: 0 }}>OPS - Trilha de Auditoria</h1>
        <div style={{ marginBottom: 8 }}>
          <span style={pageVersionBadgeStyle}>{OPS_AUDIT_PAGE_VERSION}</span>
        </div>
        <p style={mutedTextStyle}>
          Consulte ações operacionais por order_id, locker, resultado e tipo de ação.
        </p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Order ID
            <input
              type="text"
              value={orderId}
              onChange={(event) => setOrderId(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              placeholder="2dd793dd-..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Locker ID
            <input
              type="text"
              value={lockerId}
              onChange={(event) => setLockerIdWithUrl(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              placeholder="SP-ALPHAVILLE-SHOP-LK-001"
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Correlation ID
            <input
              type="text"
              value={correlationId}
              onChange={(event) => setCorrelationIdWithUrl(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              placeholder="corr-..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Buscar em error_message
            <input
              type="text"
              value={errorSearch}
              onChange={(event) => setErrorSearchWithUrl(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              placeholder="timeout, gateway, integração..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Action
            <select
              value={action}
              onChange={(event) => setAction(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {ACTION_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Result
            <select
              value={result}
              onChange={(event) => setResult(event.target.value)}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {RESULT_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Limit
            <select
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 20))}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            >
              {MAIN_LIMIT_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Offset
            <input
              type="number"
              min={0}
              value={offset}
              onChange={(event) => setOffset(Number(event.target.value || 0))}
              onKeyDown={handleMainFiltersKeyDown}
              style={inputStyle}
            />
          </label>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => loadAudit(0)} style={buttonStyle} disabled={loading}>
            {loading ? "Consultando..." : "Consultar auditoria"}
          </button>
          <button type="button" onClick={resetToShiftDefaults} style={buttonDangerStyle} disabled={loading}>
            Resetar filtros
          </button>
          <button
            type="button"
            onClick={() => loadAudit(0)}
            style={buttonStyle}
            disabled={loading || offset === 0}
          >
            Primeira página
          </button>
          <button
            type="button"
            onClick={() => loadAudit(Math.max(offset - limit, 0))}
            style={buttonStyle}
            disabled={loading || offset === 0}
          >
            Página anterior
          </button>
          <button
            type="button"
            onClick={() => loadAudit(offset + limit)}
            style={buttonStyle}
            disabled={loading || !opsHasMore}
          >
            Próxima página
          </button>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>Total retornado: {total}</span>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>Escopo filtrado: {auditKpis.scopedRows}</span>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>
            Offset atual: {offset} | Itens nesta página: {items.length}
          </span>
        </div>

        <div style={actionsRowStyle}>
          <button type="button" onClick={() => void copyAuditDailySlack()} style={buttonWarnStyle} disabled={loading}>
            Copiar daily Slack/Teams
          </button>
          <button type="button" onClick={toggleSelectAllFiltered} style={buttonWarnStyle} disabled={filteredItems.length === 0}>
            {filteredItems.length > 0 && filteredItems.every((item) => Boolean(selectedAuditIds[item.id]))
              ? "Desmarcar página filtrada"
              : "Selecionar página filtrada"}
          </button>
          <button type="button" onClick={() => void copyBatchEvidence("md")} style={buttonStyle} disabled={selectedFilteredItems.length === 0}>
            Copiar evidência lote (markdown)
          </button>
          <button
            type="button"
            onClick={() => void copyBatchEvidence("plain")}
            style={buttonStyle}
            disabled={selectedFilteredItems.length === 0}
          >
            Copiar evidência lote (texto simples)
          </button>
          <button
            type="button"
            onClick={() => void copyBatchEvidenceSlack()}
            style={buttonStyle}
            disabled={selectedFilteredItems.length === 0}
          >
            Copiar Slack/Teams (lote)
          </button>
          <span style={{ color: "rgba(245,247,250,0.8)" }}>Selecionados: {selectedFilteredItems.length}</span>
          {copyStatus ? <span style={{ color: "#93c5fd", fontWeight: 700 }}>{copyStatus}</span> : null}
        </div>
        <section style={finalValidationSectionStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>US-AUDIT-FINAL-VALIDATION</h3>
            <small style={summary24hHintStyle}>Snapshot auditável para fechamento operacional do sprint</small>
          </div>
          <div style={finalValidationGridStyle}>
            <label style={localFilterFieldStyle}>
              Resultado
              <select value={validationOutcome} onChange={(event) => setValidationOutcome(event.target.value)} style={localFilterInputStyle}>
                <option value="APPROVED">APPROVED</option>
                <option value="APPROVED_WITH_RISK">APPROVED_WITH_RISK</option>
                <option value="REPROVED">REPROVED</option>
              </select>
            </label>
            <label style={localFilterFieldStyle}>
              Notas da validação
              <input
                type="text"
                value={validationNotes}
                onChange={(event) => setValidationNotes(event.target.value)}
                placeholder="tempo de entendimento, observações de plantão..."
                style={localFilterInputStyle}
              />
            </label>
          </div>
          <div style={actionsRowStyle}>
            <button type="button" onClick={() => void copyFinalValidationEvidence("md")} style={buttonStyle}>
              Copiar validação final (markdown)
            </button>
            <button type="button" onClick={() => void copyFinalValidationEvidence("plain")} style={buttonStyle}>
              Copiar validação final (texto simples)
            </button>
          </div>
        </section>
        <div style={activeFiltersWrapStyle}>
          <strong style={{ fontSize: 12, color: "#bfdbfe" }}>Filtros ativos:</strong>
          {activeFilterChips.length > 0 ? (
            activeFilterChips.map((chip) => (
              <span key={chip} style={activeFilterChipStyle}>
                {chip}
              </span>
            ))
          ) : (
            <span style={activeFilterChipStyle}>nenhum (escopo completo da consulta)</span>
          )}
        </div>

        <details style={redactionPolicyDetailsStyle}>
          <summary style={redactionPolicySummaryStyle}>Política de redaction aplicada</summary>
          <section style={redactionPolicySectionStyle}>
            <small style={redactionPolicyHintStyle}>
              Transparência operacional para plantão/auditoria: toda cópia de evidência passa por saneamento e proteção.
            </small>
            <ul style={redactionPolicyListStyle}>
              <li>Campos sensíveis mascarados: `order_id`, `correlation_id`, `user_id`.</li>
              <li>Redaction automática em `error_message`: emails, números longos e padrões `token/secret/password/bearer`.</li>
              <li>Limite de cópia em lote: até {AUDIT_COPY_MAX_ITEMS} itens por operação.</li>
              <li>Limite de payload copiado: até {AUDIT_COPY_MAX_CHARS} caracteres (com truncamento explícito quando excede).</li>
              <li>Saneamento de texto: remoção de caracteres de controle e normalização de espaços.</li>
            </ul>
          </section>
        </details>

        <div style={severityChipRowStyle}>
          <span style={severityChipLabelStyle}>Severidade:</span>
          <button
            type="button"
            onClick={() => setSeverityFilterWithUrl("")}
            style={severityChipStyle(severityFilter === "")}
          >
            Todas ({items.length})
          </button>
          {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => setSeverityFilterWithUrl(sev)}
              style={severityChipStyle(severityFilter === sev, sev)}
            >
              {sev} ({severityChipCounts[sev] || 0})
            </button>
          ))}
        </div>

        <section style={subCardStyle}>
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>Auditoria histórica de status</h3>
          <p style={subtleTextStyle}>
            Investigue períodos longos com paginação por intervalo e exportação CSV.
          </p>

          <div style={filtersGridStyle}>
            <label style={labelStyle}>
              From
              <input
                type="datetime-local"
                value={auditFrom}
                onChange={(event) => setAuditFrom(event.target.value)}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              To
              <input
                type="datetime-local"
                value={auditTo}
                onChange={(event) => setAuditTo(event.target.value)}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
            <label style={labelStyle}>
              Limit
              <select
                value={statusLimit}
                onChange={(event) => setStatusLimit(Number(event.target.value || 200))}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              >
                {STATUS_LIMIT_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label style={labelStyle}>
              Offset
              <input
                type="number"
                min={0}
                value={statusOffset}
                onChange={(event) => setStatusOffset(Number(event.target.value || 0))}
                onKeyDown={handleStatusFiltersKeyDown}
                style={inputStyle}
              />
            </label>
          </div>

          <div style={presetRowStyle}>
            <span style={presetLabelStyle}>Presets globais:</span>
            <button
              type="button"
              onClick={() => applyRangePreset("24h")}
              style={buttonPresetStyle(selectedPreset === "24h")}
              disabled={loading}
            >
              24h
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("7d")}
              style={buttonPresetStyle(selectedPreset === "7d")}
              disabled={loading}
            >
              7d
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("30d")}
              style={buttonPresetStyle(selectedPreset === "30d")}
              disabled={loading}
            >
              30d
            </button>
            <button
              type="button"
              onClick={() => applyRangePreset("month")}
              style={buttonPresetStyle(selectedPreset === "month")}
              disabled={loading}
            >
              Mês atual
            </button>
          </div>

          <div style={actionsRowStyle}>
            <button type="button" onClick={() => loadStatusAudit(0)} style={buttonWarnStyle} disabled={loading}>
              {loading ? "Consultando..." : "Consultar inconsistências"}
            </button>
            <button type="button" onClick={exportStatusAuditCsv} style={buttonStyle} disabled={loading}>
              {loading ? "Exportando..." : "Exportar CSV"}
            </button>
            <button
              type="button"
              onClick={() => loadStatusAudit(Math.max(statusOffset - statusLimit, 0))}
              style={buttonStyle}
              disabled={loading || statusOffset <= 0}
            >
              Página anterior
            </button>
            <button
              type="button"
              onClick={() => loadStatusAudit(statusOffset + statusLimit)}
              style={buttonStyle}
              disabled={loading || !statusHasMore}
            >
              Próxima página
            </button>
            <span style={{ color: "rgba(245,247,250,0.8)" }}>
              Offset atual: {statusOffset} | Itens nesta página: {statusAuditItems.length}
            </span>
          </div>
        </section>

        {error ? <pre style={errorStyle}>{error}</pre> : null}
        {!error ? (
          <div style={kpiGridStyle}>
            <OpsTrendKpiCard label="Total auditoria" value={auditKpis.totalRows} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="SUCCESS (página)" value={auditKpis.successRows} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard label="ERROR (página)" value={auditKpis.errorRows} baseStyle={kpiBoxStyle} showTrend={false} />
            <OpsTrendKpiCard
              label="Inconsistências status"
              value={auditKpis.statusInconsistencies}
              baseStyle={kpiBoxStyle}
              showTrend={false}
            />
          </div>
        ) : null}

        {!error ? (
          <section style={summary24hSectionStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Resumo 24h (US-AUDIT-001)</h3>
              <span style={severityBadgeStyle(auditSummary24h.severityDominant)}>
                Dominante: {auditSummary24h.severityDominant}
              </span>
            </div>
            <div style={summary24hGridStyle}>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{auditSummary24h.totalRows24h}</strong>
                <small style={summary24hLabelStyle}>Eventos (24h)</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{auditSummary24h.errorRows24h}</strong>
                <small style={summary24hLabelStyle}>Erros (24h)</small>
              </article>
              <article style={summary24hItemStyle}>
                <strong style={summary24hValueStyle}>{(auditSummary24h.errorRate24h * 100).toFixed(1)}%</strong>
                <small style={summary24hLabelStyle}>Taxa de erro (24h)</small>
              </article>
            </div>
            <small style={summary24hHintStyle}>{auditSummary24h.sourceLabel}</small>
          </section>
        ) : null}

        {!error && criticalRanking.length > 0 ? (
          <section style={summary24hSectionStyle}>
            <details open={rankingOpen} onToggle={(event) => setRankingOpen(event.currentTarget.open)} style={collapsibleDetailsStyle}>
              <summary style={collapsibleSummaryStyle}>
                Ranking crítico (severidade -> impacto -> recência) · exibindo {filteredCriticalRanking.length}/{criticalRanking.length}
              </summary>
              <div style={localFilterRowStyle}>
                <label style={localFilterFieldStyle}>
                  Severidade
                  <select value={rankingSeverityFilter} onChange={(event) => setRankingSeverityFilter(event.target.value)} style={localFilterInputStyle}>
                    <option value="">Todas</option>
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </label>
                <label style={localFilterFieldStyle}>
                  Limite
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={rankingLimit}
                    onChange={(event) => setRankingLimit(Number(event.target.value || 8))}
                    style={localFilterNumberStyle}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setRankingSeverityFilter("");
                    setRankingLimit(8);
                  }}
                  style={localFilterButtonStyle}
                >
                  Limpar seção
                </button>
              </div>
              <div style={rankingListStyle}>
                {filteredCriticalRanking.map((item, idx) => (
                  <article key={`critical-rank-${item.id}-${idx}`} style={rankingItemStyle}>
                    <div style={rankingHeadStyle}>
                      <strong>#{idx + 1} · {item.action || "-"}</strong>
                      <span style={severityBadgeStyle(item.severity)}>{item.severity}</span>
                    </div>
                    <small style={smallStyle}>
                      impacto: {item.impactScore} · result: {item.result || "-"} · locker: {item.lockerId || "-"}
                    </small>
                    <small style={smallStyle}>
                      correlation_id: {item.correlation_id || "-"} · created_at: {item.created_at || "-"}
                    </small>
                    {item.error_message ? (
                      <small style={smallStyle}>erro: {renderHighlightedText(item.error_message, errorSearch)}</small>
                    ) : null}
                  </article>
                ))}
              </div>
            </details>
          </section>
        ) : null}

        {!error && groupedCauseInsights.groups.length > 0 ? (
          <section style={summary24hSectionStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Agrupamento por causa/correlação (US-AUDIT-004)</h3>
              <small style={summary24hHintStyle}>Top causas: {groupedCauseInsights.top3Label || "-"}</small>
            </div>
            <details open={groupingOpen} onToggle={(event) => setGroupingOpen(event.currentTarget.open)} style={collapsibleDetailsStyle}>
              <summary style={collapsibleSummaryStyle}>
                Grupos por causa · exibindo {filteredGroupedCauseInsights.length}/{groupedCauseInsights.groups.length}
              </summary>
              <div style={localFilterRowStyle}>
                <label style={localFilterFieldStyle}>
                  Causa
                  <input
                    type="text"
                    value={groupingCauseFilter}
                    onChange={(event) => setGroupingCauseFilter(event.target.value)}
                    placeholder="timeout, validacao..."
                    style={localFilterInputStyle}
                  />
                </label>
                <label style={localFilterFieldStyle}>
                  Reincidência
                  <select
                    value={groupingRecurrenceFilter}
                    onChange={(event) => setGroupingRecurrenceFilter(event.target.value)}
                    style={localFilterInputStyle}
                  >
                    <option value="">Todas</option>
                    <option value="ALTA">ALTA</option>
                    <option value="MEDIA">MEDIA</option>
                    <option value="BAIXA">BAIXA</option>
                  </select>
                </label>
                <label style={localFilterFieldStyle}>
                  Limite
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={groupingLimit}
                    onChange={(event) => setGroupingLimit(Number(event.target.value || 6))}
                    style={localFilterNumberStyle}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setGroupingCauseFilter("");
                    setGroupingRecurrenceFilter("");
                    setGroupingLimit(6);
                  }}
                  style={localFilterButtonStyle}
                >
                  Limpar seção
                </button>
              </div>
              <div style={groupedCauseGridStyle}>
                {filteredGroupedCauseInsights.map((group) => (
                  <article key={`cause-group-${group.cause}`} style={groupedCauseItemStyle}>
                    <div style={rankingHeadStyle}>
                      <strong>{group.cause}</strong>
                      <span style={severityBadgeStyle(resolveSeverityByErrorRate(group.errorRate))}>
                        reincidência {group.recurrenceLevel}
                      </span>
                    </div>
                    <small style={smallStyle}>
                      volume: {group.total} ({group.percentage.toFixed(1)}%) · erro: {(group.errorRate * 100).toFixed(1)}%
                    </small>
                    <small style={smallStyle}>
                      correlações: {group.correlationCount} · último evento: {group.lastSeenLabel}
                    </small>
                    {group.relatedCorrelations.length > 0 ? (
                      <details style={groupedCauseDetailsStyle}>
                        <summary style={groupedCauseSummaryStyle}>Ver correlações relacionadas (N2 → N3)</summary>
                        <div style={groupedCauseCorrelationListStyle}>
                          {group.relatedCorrelations.map((corr) => (
                            <small key={`corr-${group.cause}-${corr.correlationId}`} style={smallStyle}>
                              {corr.correlationId} · {corr.errorCount}/{corr.total} erro(s) · reincidência {corr.recurrenceLevel} · último:{" "}
                              {corr.lastSeenLabel}
                            </small>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </article>
                ))}
              </div>
            </details>
          </section>
        ) : null}

        {!error && timelineInsights.events.length > 0 ? (
          <section style={summary24hSectionStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 15 }}>Timeline investigativa (US-AUDIT-005)</h3>
              <small style={summary24hHintStyle}>
                Eventos: {timelineInsights.events.length} · spikes: {timelineInsights.spikes} · críticos: {timelineInsights.criticals}
              </small>
            </div>
            <details open={timelineOpen} onToggle={(event) => setTimelineOpen(event.currentTarget.open)} style={collapsibleDetailsStyle}>
              <summary style={collapsibleSummaryStyle}>
                Stream temporal · exibindo {filteredTimelineEvents.length}/{timelineInsights.events.length}
              </summary>
              <div style={localFilterRowStyle}>
                <label style={localFilterFieldStyle}>
                  Marcador
                  <select value={timelineMarkerFilter} onChange={(event) => setTimelineMarkerFilter(event.target.value)} style={localFilterInputStyle}>
                    <option value="">Todos</option>
                    <option value="ERROR_SPIKE">ERROR_SPIKE</option>
                    <option value="SEVERITY_CRITICAL">SEVERITY_CRITICAL</option>
                    <option value="ERROR_EVENT">ERROR_EVENT</option>
                  </select>
                </label>
                <label style={localFilterFieldStyle}>
                  Entidade
                  <input
                    type="text"
                    value={timelineEntitySearch}
                    onChange={(event) => setTimelineEntitySearch(event.target.value)}
                    placeholder="locker/correlation/order/action"
                    style={localFilterInputStyle}
                  />
                </label>
                <label style={localFilterFieldStyle}>
                  Limite
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={timelineLimit}
                    onChange={(event) => setTimelineLimit(Number(event.target.value || 30))}
                    style={localFilterNumberStyle}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setTimelineMarkerFilter("");
                    setTimelineEntitySearch("");
                    setTimelineLimit(30);
                  }}
                  style={localFilterButtonStyle}
                >
                  Limpar seção
                </button>
              </div>
              <div style={timelineStreamStyle}>
                {filteredTimelineEvents.map((event) => {
                const paramsLocker = new URLSearchParams();
                paramsLocker.set("locker_id", event.locker);
                const fromIso = toIsoOrNull(auditFrom);
                const toIso = toIsoOrNull(auditTo);
                if (fromIso) paramsLocker.set("from", fromIso);
                if (toIso) paramsLocker.set("to", toIso);

                const paramsCorr = new URLSearchParams();
                paramsCorr.set("correlation_id", event.corr);
                if (fromIso) paramsCorr.set("from", fromIso);
                if (toIso) paramsCorr.set("to", toIso);

                return (
                  <article key={`timeline-${event.id}`} style={timelineEventItemStyle}>
                    <div style={timelineHeadStyle}>
                      <span style={severityBadgeStyle(event.severity)}>{event.severity}</span>
                      <strong style={{ fontSize: 12 }}>{event.action || "-"}</strong>
                      <small style={timelineTimestampStyle}>{event.created_at || "-"}</small>
                    </div>
                    <small style={smallStyle}>
                      causa: {event.cause} · result: {event.result || "-"} · hour: {event.hourError}/{event.hourTotal} erro(s) (
                      {(event.hourErrorRate * 100).toFixed(1)}%)
                    </small>
                    {event.markers.length > 0 ? (
                      <div style={timelineMarkersRowStyle}>
                        {event.markers.map((marker) => (
                          <span key={`marker-${event.id}-${marker}`} style={timelineMarkerStyle(marker)}>
                            {marker}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    <div style={timelineLinksRowStyle}>
                      <Link to={`/ops/audit?${paramsLocker.toString()}`} style={timelineShortcutLinkStyle}>
                        Locker
                      </Link>
                      <Link to={`/ops/audit?${paramsCorr.toString()}`} style={timelineShortcutLinkStyle}>
                        Correlation
                      </Link>
                      <Link to="/ops/reconciliation" style={timelineShortcutLinkStyle}>
                        Reconciliação
                      </Link>
                      <Link to="/ops/health" style={timelineShortcutLinkStyle}>
                        Ops Health
                      </Link>
                    </div>
                    {event.error_message ? (
                      <small style={smallStyle}>erro: {renderHighlightedText(event.error_message, errorSearch)}</small>
                    ) : null}
                  </article>
                );
                })}
              </div>
            </details>
          </section>
        ) : null}

        {!error && filteredItems.length > 0 ? (
          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {filteredItems.map((item) => (
              <article key={item.id} style={rowStyle}>
                <div style={rowHeadStyle}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                    <input
                      type="checkbox"
                      checked={Boolean(selectedAuditIds[item.id])}
                      onChange={() => toggleSelectAuditItem(item.id)}
                      aria-label={`Selecionar evento ${item.id}`}
                    />
                    <strong>{item.action || "-"}</strong>
                    <span style={badgeStyle(item.result)}>{item.result || "-"}</span>
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <button type="button" onClick={() => void copySingleEvidence(item, "md")} style={miniActionButtonStyle}>
                      Copiar evidência
                    </button>
                    <button type="button" onClick={() => void copySingleEvidence(item, "plain")} style={miniActionButtonStyle}>
                      Copiar simples
                    </button>
                    <button type="button" onClick={() => void copySingleEvidenceSlack(item)} style={miniActionButtonStyle}>
                      Copiar Slack/Teams
                    </button>
                  </div>
                </div>
                <small style={smallStyle}>order_id: {item.order_id || "-"}</small>
                <small style={smallStyle}>locker_id: {item?.details?.locker_id || "-"}</small>
                <small style={smallStyle}>user_id: {item.user_id || "-"}</small>
                <small style={smallStyle}>correlation_id: {item.correlation_id || "-"}</small>
                <small style={smallStyle}>created_at: {item.created_at || "-"}</small>
                {item.error_message ? (
                  <small style={smallStyle}>error_message: {renderHighlightedText(item.error_message, errorSearch)}</small>
                ) : null}
              </article>
            ))}
          </div>
        ) : null}

        {!error && statusAuditItems.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Inconsistências de status</h3>
            <div style={{ display: "grid", gap: 10 }}>
              {statusAuditItems.map((item) => (
                <article key={`${item.order_id}-${item.reason}`} style={rowStyle}>
                  <div style={rowHeadStyle}>
                    <strong>{item.order_id}</strong>
                    <span style={badgeStyle("ERROR")}>ATENÇÃO</span>
                  </div>
                  <small style={smallStyle}>order_status: {item.order_status || "-"}</small>
                  <small style={smallStyle}>pickup_status: {item.pickup_status || "-"}</small>
                  <small style={smallStyle}>picked_up_at: {item.picked_up_at || "-"}</small>
                  <small style={smallStyle}>reason: {item.reason || "-"}</small>
                </article>
              ))}
            </div>
          </div>
        ) : null}

        {!error && !loading && filteredItems.length === 0 && statusAuditItems.length === 0 ? (
          <p style={{ marginTop: 14 }}>Nenhum evento encontrado com os filtros atuais.</p>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const subCardStyle = {
  marginTop: 16,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.02)",
  padding: 12,
};

const subtleTextStyle = {
  marginTop: 0,
  marginBottom: 8,
  color: "rgba(245,247,250,0.75)",
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const pageVersionBadgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "3px 8px",
  borderRadius: 999,
  border: "1px solid rgba(125,211,252,0.55)",
  background: "rgba(14,116,144,0.16)",
  color: "#bae6fd",
  fontSize: 11,
  fontWeight: 700,
};

const shortcutRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const filtersGridStyle = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const actionsRowStyle = {
  marginTop: 12,
  display: "flex",
  gap: 10,
  alignItems: "center",
  flexWrap: "wrap",
};

const severityChipRowStyle = {
  marginTop: 10,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  alignItems: "center",
};

const severityChipStyle = (active, severity = "") => ({
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "6px 10px",
  borderRadius: 999,
  border: active
    ? "2px solid #bfdbfe"
    : severity
      ? getAuditSeverityBadgeStyle(severity).border
      : "1px solid rgba(148,163,184,0.45)",
  background: active
    ? "#1d4ed8"
    : severity
      ? getAuditSeverityBadgeStyle(severity).background
      : "rgba(15,23,42,0.34)",
  color: active ? "#ffffff" : severity ? getAuditSeverityBadgeStyle(severity).color : "#e2e8f0",
  fontSize: 12,
  fontWeight: 700,
  cursor: "pointer",
  whiteSpace: "nowrap",
  minWidth: 110,
});

const severityChipLabelStyle = {
  color: "#bfdbfe",
  fontSize: 12,
  fontWeight: 700,
};

const activeFiltersWrapStyle = {
  marginTop: 8,
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
  alignItems: "center",
};

const activeFilterChipStyle = {
  display: "inline-flex",
  alignItems: "center",
  padding: "4px 8px",
  borderRadius: 999,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.35)",
  color: "#cbd5e1",
  fontSize: 11,
  fontWeight: 700,
};

const finalValidationSectionStyle = {
  marginTop: 12,
  borderRadius: 12,
  border: "1px solid rgba(125,211,252,0.35)",
  background: "rgba(8,47,73,0.22)",
  padding: 10,
  display: "grid",
  gap: 8,
};

const finalValidationGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
};

const redactionPolicyDetailsStyle = {
  marginTop: 10,
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.25)",
  padding: 8,
};

const redactionPolicySummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 13,
  fontWeight: 700,
};

const redactionPolicySectionStyle = {
  borderRadius: 12,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.2)",
  padding: 10,
  display: "grid",
  gap: 6,
  marginTop: 8,
};

const redactionPolicyHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const redactionPolicyListStyle = {
  margin: 0,
  paddingLeft: 18,
  color: "#e2e8f0",
  fontSize: 12,
  display: "grid",
  gap: 4,
};

const buttonStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const buttonWarnStyle = {
  ...buttonStyle,
  border: "1px solid rgba(245,158,11,0.55)",
  color: "#fde68a",
  background: "rgba(245,158,11,0.12)",
};

const buttonPresetStyle = (isActive) => ({
  ...buttonStyle,
  border: isActive ? "1px solid rgba(59,130,246,0.9)" : "1px solid rgba(96,165,250,0.5)",
  color: isActive ? "#dbeafe" : "#bfdbfe",
  background: isActive ? "rgba(59,130,246,0.28)" : "rgba(96,165,250,0.12)",
  padding: "6px 10px",
  fontSize: 12,
});

const buttonDangerStyle = {
  ...buttonStyle,
  border: "1px solid rgba(248,113,113,0.6)",
  color: "#fecaca",
  background: "rgba(127,29,29,0.25)",
};

const presetRowStyle = {
  marginTop: 8,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  alignItems: "center",
};

const presetLabelStyle = {
  color: "rgba(245,247,250,0.78)",
  fontSize: 12,
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};

const kpiGridStyle = {
  marginTop: 14,
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
};

const kpiBoxStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: "10px 12px",
  display: "grid",
  gap: 4,
};

const summary24hSectionStyle = {
  marginTop: 14,
  borderRadius: 12,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.24)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hGridStyle = {
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
};

const summary24hItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const summary24hValueStyle = {
  color: "#f8fafc",
  fontSize: 18,
  fontWeight: 800,
};

const summary24hLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const collapsibleDetailsStyle = {
  borderRadius: 10,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(2,6,23,0.24)",
  padding: 8,
};

const collapsibleSummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 13,
  fontWeight: 700,
};

const localFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const localFilterLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
  fontWeight: 700,
  marginBottom: 4,
};

const localFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const localFilterInputStyle = {
  ...inputStyle,
  border: "1px solid rgba(148,163,184,0.5)",
  background: "#0b0f14",
  color: "#f5f7fa",
  fontSize: 12,
};

const localFilterNumberStyle = {
  ...localFilterInputStyle,
  fontSize: 12,
  width: "100%",
};

const localFilterButtonStyle = {
  ...buttonStyle,
  alignSelf: "end",
  height: 36,
  fontSize: 12,
  border: "1px solid rgba(248,113,113,0.55)",
  color: "#fecaca",
  background: "rgba(127,29,29,0.2)",
};

const rankingListStyle = {
  display: "grid",
  gap: 8,
};

function resolveSeverityByErrorRate(rate) {
  const value = Number(rate || 0);
  if (value > 0.5) return "CRITICAL";
  if (value >= 0.2) return "HIGH";
  if (value >= 0.05) return "MEDIUM";
  return "LOW";
}

const rankingItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 4,
};

const groupedCauseGridStyle = {
  display: "grid",
  gap: 8,
};

const groupedCauseItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 4,
};

const groupedCauseDetailsStyle = {
  borderRadius: 8,
  border: "1px dashed rgba(148,163,184,0.35)",
  background: "rgba(2,6,23,0.3)",
  padding: 8,
};

const groupedCauseSummaryStyle = {
  cursor: "pointer",
  color: "#bfdbfe",
  fontSize: 12,
  fontWeight: 700,
};

const groupedCauseCorrelationListStyle = {
  marginTop: 8,
  display: "grid",
  gap: 4,
};

const timelineStreamStyle = {
  display: "grid",
  gap: 8,
};

const timelineEventItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 6,
};

const timelineHeadStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const timelineTimestampStyle = {
  color: "#cbd5e1",
  fontSize: 11,
  marginLeft: "auto",
};

const timelineMarkersRowStyle = {
  display: "flex",
  gap: 6,
  flexWrap: "wrap",
};

const timelineMarkerStyle = (marker) => {
  const severity = marker === "SEVERITY_CRITICAL" || marker === "ERROR_SPIKE" ? "CRITICAL" : "MEDIUM";
  const token = getAuditSeverityBadgeStyle(severity);
  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "3px 8px",
    border: token.border,
    background: token.background,
    color: token.color,
    fontSize: 10,
    fontWeight: 800,
    lineHeight: 1.2,
  };
};

const timelineLinksRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const timelineShortcutLinkStyle = {
  color: "#93c5fd",
  fontSize: 12,
  fontWeight: 700,
  textDecoration: "none",
  border: "1px solid rgba(147,197,253,0.4)",
  background: "rgba(30,58,138,0.3)",
  borderRadius: 8,
  padding: "4px 8px",
};

const rankingHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const rowStyle = {
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
  padding: 10,
  display: "grid",
  gap: 4,
};

const rowHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
};

const miniActionButtonStyle = {
  padding: "4px 8px",
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "rgba(15,23,42,0.4)",
  color: "#cbd5e1",
  fontSize: 11,
  fontWeight: 700,
  cursor: "pointer",
};

const smallStyle = {
  color: "rgba(226,232,240,0.9)",
  fontSize: 12,
  wordBreak: "break-word",
};

const highlightMarkStyle = {
  background: "rgba(250,204,21,0.35)",
  color: "#fef9c3",
  borderRadius: 4,
  padding: "0 2px",
};

const badgeStyle = (result) => {
  const ok = String(result || "").toUpperCase() === "SUCCESS";
  return severityBadgeStyle(ok ? "OK" : "HIGH");
};

const severityBadgeStyle = (severity) => {
  const token = getAuditSeverityBadgeStyle(severity);
  return {
    display: "inline-flex",
    alignItems: "center",
    borderRadius: 999,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 800,
    lineHeight: 1.2,
    border: token.border,
    background: token.background,
    color: token.color,
  };
};
