import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import {
  accountingApprovalsToCsvRows,
  buildAccountingApprovalsCsv,
  fetchAccountingApprovalsCompare,
  fetchAccountingApprovalsDivergenceHealth,
  fetchConsolidatedAccountingApprovals,
  postAccountingApprovalsRetention,
} from "../utils/fiscalAccountingApprovalsHistory";
import {
  D18_CHECKLIST_ITEMS,
  D18_CLOSEOUT_STORAGE_KEY,
  buildD18CloseoutPayload as composeD18CloseoutPayload,
  countD18ChecklistDone,
  createInitialP1RiskRows,
  loadD18CloseoutFromStorage,
} from "../utils/fiscalSprint2D18Content";
import { formatOpsDateTime } from "../utils/opsDateTimeFormat";
import { appendP01bSignedZipEntries } from "../utils/fiscalP01bDailyPackage";
import { appendSprint3P03OptionalSignedZipEntries } from "../utils/fiscalSprint3IncidentRunbook";
import { appendSprint4OptionalSignedZipEntries } from "../utils/fiscalSprint4RegressionMatrix";
import {
  loadSprint2FinanceGateV2State,
  summarizeSprint2FinanceGateV2,
  SPRINT2_FINANCE_GATE_V2_THRESHOLDS,
} from "../utils/fiscalSprint2FinanceGate";
import { loadSprint3PartnerAuditMirrorForDaily } from "../utils/fiscalSprint3PartnerAuditMirror";
import { buildD11OrderIdRollupFromGapRows } from "../utils/fiscalD11OrderIdRollup";
import {
  FISCAL_D10_HANDOFF_KEY,
  FISCAL_D10_TRACKER_KEY,
  buildD10ProvidersEvidencePayload,
  parseD10OpsHandoffFromLocalStorageRaw,
  parseD10TrackerFromLocalStorageRaw,
} from "../utils/fiscalD10ProvidersTracker";
import { buildSprint2D12AccountingHandoffEvidence, wrapSprint2D13AccountingAcceptance } from "../utils/fiscalSprint2D12D13Evidence";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/management-daily v1.0.14-d15-revenue-credits-delta";
const APPROVAL_STORAGE_KEY = "fiscal_management_daily:accounting_approval_v1";
const FISCAL_D11_HANDOFF_KEY = "ellan_ops_fiscal_d11_handoff_v1";
const D13_CHECKLIST_STORAGE_KEY = "fiscal_management_daily:d13_critical_checklist_v1";
const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function downloadJsonFile(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

function downloadZipFile(filename, filesMap) {
  const zipped = zipSync(filesMap, { level: 6 });
  const blob = new Blob([zipped], { type: "application/zip" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

function toAuditDayStamp(isoString) {
  return String(isoString || "").slice(0, 10).replaceAll("-", "");
}

async function computeSha256Hex(content) {
  const input = String(content || "");
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(input);
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex;
}

async function buildSignedPayload(payload) {
  const payloadJson = JSON.stringify(payload, null, 2);
  const sha256 = await computeSha256Hex(payloadJson);
  return {
    integrity: {
      algorithm: "SHA-256",
      content_sha256: sha256,
    },
    payload,
  };
}

export default function FiscalManagementDailyPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [catalog, setCatalog] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [stubReadiness, setStubReadiness] = useState(null);
  const [approvalOwner, setApprovalOwner] = useState("");
  const [approvalStatus, setApprovalStatus] = useState("PENDING_REVIEW");
  const [approvalNotes, setApprovalNotes] = useState("");
  const [approvalTimestamp, setApprovalTimestamp] = useState("");
  const [approvalEta, setApprovalEta] = useState("");
  const [d11Handoff, setD11Handoff] = useState(null);
  const [d10Handoff, setD10Handoff] = useState(null);
  const [d13ChecklistState, setD13ChecklistState] = useState({});
  const [historyItems, setHistoryItems] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyOwnerFilter, setHistoryOwnerFilter] = useState("");
  const [historyStatusFilter, setHistoryStatusFilter] = useState("");
  const [historyFromDate, setHistoryFromDate] = useState("");
  const [historyToDate, setHistoryToDate] = useState("");
  const [historyPage, setHistoryPage] = useState(0);
  const [historyLimit] = useState(10);
  const [compareResult, setCompareResult] = useState(null);
  const [d17Health, setD17Health] = useState(null);
  const [d17RetentionOlder, setD17RetentionOlder] = useState(90);
  const [d17RetentionKeep, setD17RetentionKeep] = useState(25);
  const [d17RetentionLast, setD17RetentionLast] = useState(null);
  const [d17RetentionBusy, setD17RetentionBusy] = useState(false);
  const [d15DeltaDate, setD15DeltaDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [d15RevenueCreditsDelta, setD15RevenueCreditsDelta] = useState(null);
  const [d15DeltaLoading, setD15DeltaLoading] = useState(false);
  const [d15DeltaError, setD15DeltaError] = useState("");
  const [d18Checklist, setD18Checklist] = useState({});
  const [d18P1Rows, setD18P1Rows] = useState(() => createInitialP1RiskRows());
  const [d18Certification, setD18Certification] = useState(null);
  const [d18CarimboBy, setD18CarimboBy] = useState("");
  const [d18CarimboNote, setD18CarimboNote] = useState("");
  const [gateMirror, setGateMirror] = useState(() => summarizeSprint2FinanceGateV2(loadSprint2FinanceGateV2State()));
  const [partnerAuditMirror, setPartnerAuditMirror] = useState(() => loadSprint3PartnerAuditMirrorForDaily());

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    function refreshFiscalMirrorsFromStorage() {
      setGateMirror(summarizeSprint2FinanceGateV2(loadSprint2FinanceGateV2State()));
      setPartnerAuditMirror(loadSprint3PartnerAuditMirrorForDaily());
      loadD11Handoff();
      loadD10Handoff();
    }
    window.addEventListener("focus", refreshFiscalMirrorsFromStorage);
    window.addEventListener("storage", refreshFiscalMirrorsFromStorage);
    return () => {
      window.removeEventListener("focus", refreshFiscalMirrorsFromStorage);
      window.removeEventListener("storage", refreshFiscalMirrorsFromStorage);
    };
  }, []);

  useEffect(() => {
    loadD11Handoff();
    loadD10Handoff();
    void loadLatestAccountingApproval();
    void loadAccountingApprovalHistory(0);
    void loadAccountingApprovalComparison();
    void loadD17DivergenceHealth();
  }, []);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(APPROVAL_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      setApprovalOwner(String(parsed?.owner || ""));
      setApprovalStatus(String(parsed?.status || "PENDING_REVIEW"));
      setApprovalNotes(String(parsed?.notes || ""));
      setApprovalTimestamp(String(parsed?.timestamp || ""));
      setApprovalEta(String(parsed?.eta || ""));
    } catch {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(D13_CHECKLIST_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        setD13ChecklistState(parsed);
      }
    } catch {
      // no-op
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(D13_CHECKLIST_STORAGE_KEY, JSON.stringify(d13ChecklistState));
    } catch {
      // no-op
    }
  }, [d13ChecklistState]);

  useEffect(() => {
    const { checklist, p1Risks, certification } = loadD18CloseoutFromStorage();
    setD18Checklist(checklist);
    setD18P1Rows(p1Risks);
    setD18Certification(certification);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        D18_CLOSEOUT_STORAGE_KEY,
        JSON.stringify({ checklist: d18Checklist, p1Risks: d18P1Rows, certification: d18Certification }),
      );
    } catch {
      // no-op
    }
  }, [d18Checklist, d18P1Rows, d18Certification]);

  const readinessChecks = Array.isArray(stubReadiness?.checks) ? stubReadiness.checks : [];
  const passedChecks = readinessChecks.filter((check) => String(check?.status || "").toUpperCase() === "PASS").length;
  const failedChecks = Math.max(readinessChecks.length - passedChecks, 0);
  const decision = String(stubReadiness?.decision || "NO_GO").toUpperCase();
  const countriesNotReady = Number(stubReadiness?.countries_not_ready || 0);
  const riskLevel = decision === "GO" ? "LOW" : countriesNotReady >= 2 ? "HIGH" : "MEDIUM";

  const practicalActions = useMemo(() => {
    if (decision === "GO") {
      return ["Manter execução diária do orquestrador FG-1", "Monitorar desvio de checks por turno"];
    }
    return ["Priorizar países bloqueados no readiness-execution", "Revalidar gates após ações corretivas"];
  }, [decision]);

  const d13CriticalChecklist = useMemo(() => {
    const items = Array.isArray(d11Handoff?.items) ? d11Handoff.items : [];
    return items
      .filter((row) => {
        const sev = String(row?.severity || "UNKNOWN").toUpperCase();
        return sev === "ERROR" || sev === "WARN";
      })
      .slice(0, 20)
      .map((row) => {
        const id = `${row?.id || row?.order_id || "gap"}:${row?.batch_id || "batch"}:${row?.severity || "UNK"}`;
        const severity = String(row?.severity || "UNKNOWN").toUpperCase();
        return {
          id,
          severity,
          order_id: String(row?.order_id || "-"),
          partner_id: String(row?.partner_id || "-"),
          batch_id: String(row?.batch_id || "-"),
          eta: String(approvalEta || "-"),
          owner: String(approvalOwner || "-"),
          title: `[${severity}] ${String(row?.gap_type || "GAP")} | order=${String(row?.order_id || "-")}`,
        };
      });
  }, [d11Handoff, approvalEta, approvalOwner]);

  const d13ChecklistDoneCount = d13CriticalChecklist.filter((item) => Boolean(d13ChecklistState[item.id])).length;

  const d11OrderIdRollup = useMemo(() => {
    if (!d11Handoff) return null;
    const embedded = d11Handoff.order_id_rollup;
    if (embedded && typeof embedded === "object" && Array.isArray(embedded.orders)) {
      return embedded;
    }
    const items = Array.isArray(d11Handoff.items) ? d11Handoff.items : [];
    return buildD11OrderIdRollupFromGapRows(items);
  }, [d11Handoff]);

  async function loadData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [catalogRes, matrixRes, stubRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/catalog`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/scenario-matrix`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-wave-readiness`, { method: "GET", headers: headersJson() }),
      ]);
      const [catalogPayload, matrixPayload, stubPayload] = await Promise.all([
        catalogRes.json().catch(() => ({})),
        matrixRes.json().catch(() => ({})),
        stubRes.json().catch(() => ({})),
      ]);
      if (!catalogRes.ok || !matrixRes.ok || !stubRes.ok) {
        throw new Error(
          String(
            catalogPayload?.detail || matrixPayload?.detail || stubPayload?.detail || "Falha ao carregar dados de gestão fiscal diária."
          )
        );
      }
      setCatalog(catalogPayload || null);
      setMatrix(matrixPayload || null);
      setStubReadiness(stubPayload || null);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function buildFiscalPayload(baseIso) {
    return {
      scope: "FISCAL_MANAGEMENT_DAILY",
      generated_at: baseIso,
      decision_consolidated: decision,
      risk_level: riskLevel,
      checks_pass: `${passedChecks}/${readinessChecks.length}`,
      checks_failed: failedChecks,
      reference: {
        readiness_version: String(stubReadiness?.readiness_version || "-"),
        catalog_count: Number(catalog?.count || 0),
        scenario_matrix_count: Number(matrix?.count || 0),
        countries_not_ready: countriesNotReady,
      },
      practical_actions: practicalActions,
      d11_fiscal_gap_handoff: d11Handoff
        ? {
            generated_at: String(d11Handoff?.generated_at || "-"),
            total_items: Number(d11Handoff?.summary?.total_items || 0),
            severity: d11Handoff?.summary?.severity || {},
            unique_partners: Number(d11Handoff?.summary?.unique_partners || 0),
            unique_batches: Number(d11Handoff?.summary?.unique_batches || 0),
            unique_orders_with_gaps: Number(
              d11Handoff?.summary?.unique_orders_with_gaps ?? d11OrderIdRollup?.unique_orders_with_gaps ?? 0,
            ),
            filters: d11Handoff?.filters || {},
            order_id_rollup_summary: d11OrderIdRollup
              ? {
                  scope: d11OrderIdRollup.scope,
                  generated_at: d11OrderIdRollup.generated_at,
                  unique_orders_with_gaps: d11OrderIdRollup.unique_orders_with_gaps,
                  top_orders: d11OrderIdRollup.orders.slice(0, 15),
                }
              : null,
          }
        : null,
      d10_providers_ops_handoff: d10Handoff
        ? {
            generated_at: String(d10Handoff?.generated_at || "-"),
            source: String(d10Handoff?.source || "-"),
            summary: d10Handoff?.summary || null,
            providers_count: Number(d10Handoff?.summary?.providers_count ?? 0),
          }
        : null,
      d15_revenue_credits_delta: d15RevenueCreditsDelta
        ? {
            snapshot_date: String(d15RevenueCreditsDelta?.snapshot_date || "-"),
            currency_filter: d15RevenueCreditsDelta?.currency_filter ?? null,
            summary: d15RevenueCreditsDelta?.summary || null,
          }
        : null,
    };
  }

  function buildAccountingApprovalPayload(baseIso) {
    return {
      scope: "FISCAL_ACCOUNTING_DAILY_APPROVAL",
      generated_at: baseIso,
      approval: {
        owner: String(approvalOwner || "").trim() || "-",
        status: String(approvalStatus || "PENDING_REVIEW"),
        eta: String(approvalEta || "").trim() || "-",
        notes: String(approvalNotes || "").trim() || "-",
        timestamp: String(approvalTimestamp || baseIso),
      },
      context: {
        decision_consolidated: decision,
        risk_level: riskLevel,
        checks_pass: `${passedChecks}/${readinessChecks.length}`,
        checks_failed: failedChecks,
        readiness_version: String(stubReadiness?.readiness_version || "-"),
        d11_total_items: Number(d11Handoff?.summary?.total_items || 0),
        d11_generated_at: String(d11Handoff?.generated_at || "-"),
        d11_unique_orders_with_gaps: Number(
          d11Handoff?.summary?.unique_orders_with_gaps ?? d11OrderIdRollup?.unique_orders_with_gaps ?? 0,
        ),
        d10_generated_at: String(d10Handoff?.generated_at || "-"),
        d10_progress_pct: Number(d10Handoff?.summary?.d10_progress_pct ?? 0),
        d15_snapshot_date: String(d15RevenueCreditsDelta?.snapshot_date || "-"),
        d15_divergence_residual_pct: Number(d15RevenueCreditsDelta?.summary?.divergence_residual_pct ?? 0),
      },
      d13_critical_checklist: {
        owner: String(approvalOwner || "").trim() || "-",
        eta: String(approvalEta || "").trim() || "-",
        total_items: d13CriticalChecklist.length,
        done_items: d13ChecklistDoneCount,
        items: d13CriticalChecklist.map((item) => ({
          ...item,
          done: Boolean(d13ChecklistState[item.id]),
        })),
      },
    };
  }

  function buildD18CloseoutPayload(baseIso) {
    return composeD18CloseoutPayload({
      generatedAt: baseIso,
      checklistById: d18Checklist,
      p1Rows: d18P1Rows,
      source: "fiscal/management-daily",
      certification: d18Certification,
      context: {
        decision_consolidated: decision,
        risk_level: riskLevel,
        readiness_version: String(stubReadiness?.readiness_version || "-"),
      },
    });
  }

  function stampD18Closeout() {
    const by = String(d18CarimboBy || approvalOwner || "").trim();
    if (!by) {
      setStatus("Informe quem carimba (nome ou sigla) antes de carimbar o D18.");
      window.setTimeout(() => setStatus(""), 3200);
      return;
    }
    const done = countD18ChecklistDone(d18Checklist);
    const total = D18_CHECKLIST_ITEMS.length;
    if (done < total) {
      const ok = window.confirm(
        `Checklist D18 incompleto (${done}/${total}). Carimbar mesmo assim declara revisão humana com ressalva. Continuar?`,
      );
      if (!ok) return;
    }
    const note = String(d18CarimboNote || "").trim();
    setD18Certification({
      certified_at: new Date().toISOString(),
      certified_by: by,
      note,
    });
    setStatus("Closeout D18 carimbado. Incluído em JSON/ZIP no próximo export.");
    window.setTimeout(() => setStatus(""), 3200);
  }

  function revokeD18Certification() {
    if (!d18Certification) return;
    if (!window.confirm("Revogar o carimbo D18? O JSON/ZIP deixará de incluir closeout_certification até novo carimbo.")) return;
    setD18Certification(null);
    setStatus("Carimbo D18 revogado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  function toggleD18Checklist(id) {
    setD18Checklist((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function updateD18P1Row(index, field, value) {
    setD18P1Rows((rows) => rows.map((r, i) => (i === index ? { ...r, [field]: String(value) } : r)));
  }

  function resetD18P1Template() {
    if (!window.confirm("Limpar todas as linhas do template P1?")) return;
    setD18P1Rows(createInitialP1RiskRows());
  }

  async function copyD18CloseoutJson() {
    const nowIso = new Date().toISOString();
    const payload = buildD18CloseoutPayload(nowIso);
    try {
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setStatus("JSON D18 (closeout Sprint 2) copiado.");
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha ao copiar D18: ${String(err?.message || err)}`);
    }
  }

  function downloadD18CloseoutJson() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const payload = buildD18CloseoutPayload(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_D18_SPRINT2_CLOSEOUT_${ts}.json`, payload);
    setStatus("JSON D18 baixado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  function loadD11Handoff() {
    try {
      const raw = window.localStorage.getItem(FISCAL_D11_HANDOFF_KEY);
      if (!raw) {
        setD11Handoff(null);
        return;
      }
      const parsed = JSON.parse(raw);
      setD11Handoff(parsed && typeof parsed === "object" ? parsed : null);
    } catch {
      setD11Handoff(null);
    }
  }

  function loadD10Handoff() {
    try {
      const raw = window.localStorage.getItem(FISCAL_D10_HANDOFF_KEY);
      if (!raw) {
        setD10Handoff(null);
        return;
      }
      setD10Handoff(parseD10OpsHandoffFromLocalStorageRaw(raw));
    } catch {
      setD10Handoff(null);
    }
  }

  async function loadLatestAccountingApproval() {
    if (!INTERNAL_TOKEN) return;
    try {
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/accounting-approvals/latest`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok || !payload?.item) return;
      const item = payload.item;
      setApprovalOwner(String(item?.owner || ""));
      setApprovalStatus(String(item?.status || "PENDING_REVIEW"));
      const etaRaw = String(item?.eta || "");
      setApprovalEta(etaRaw ? etaRaw.slice(0, 16) : "");
      const approvalPayload = item?.payload_json && typeof item.payload_json === "object" ? item.payload_json : {};
      const approvalNode = approvalPayload?.approval && typeof approvalPayload.approval === "object" ? approvalPayload.approval : {};
      const checklistNode =
        approvalPayload?.d13_critical_checklist && typeof approvalPayload.d13_critical_checklist === "object"
          ? approvalPayload.d13_critical_checklist
          : {};
      setApprovalNotes(String(approvalNode?.notes || ""));
      setApprovalTimestamp(String(approvalNode?.timestamp || item?.created_at || ""));
      if (Array.isArray(checklistNode?.items)) {
        const doneMap = checklistNode.items.reduce((acc, row) => {
          const key = String(row?.id || "");
          if (!key) return acc;
          acc[key] = Boolean(row?.done);
          return acc;
        }, {});
        setD13ChecklistState(doneMap);
      }
      setStatus("Aceite contábil central carregado do backend.");
      window.setTimeout(() => setStatus(""), 1800);
    } catch {
      // no-op
    }
  }

  async function loadAccountingApprovalHistory(page = historyPage) {
    if (!INTERNAL_TOKEN) return;
    try {
      const offset = page * historyLimit;
      const params = new URLSearchParams({
        limit: String(historyLimit),
        offset: String(offset),
      });
      if (historyOwnerFilter.trim()) params.set("owner", historyOwnerFilter.trim());
      if (historyStatusFilter.trim()) params.set("status", historyStatusFilter.trim());
      if (historyFromDate.trim()) params.set("date_from", historyFromDate.trim());
      if (historyToDate.trim()) params.set("date_to", historyToDate.trim());
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/accounting-approvals?${params.toString()}`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(String(payload?.detail || "Falha ao carregar histórico D15."));
      setHistoryItems(Array.isArray(payload?.items) ? payload.items : []);
      setHistoryTotal(Number(payload?.total || 0));
      setHistoryPage(page);
    } catch (err) {
      setStatus(`Falha histórico D15: ${String(err?.message || err)}`);
    }
  }

  async function loadAccountingApprovalComparison(currentId = "", previousId = "") {
    if (!INTERNAL_TOKEN) return;
    try {
      const params = new URLSearchParams();
      if (String(currentId || "").trim()) params.set("current_id", String(currentId).trim());
      if (String(previousId || "").trim()) params.set("previous_id", String(previousId).trim());
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/accounting-approvals/compare?${params.toString()}`, {
        method: "GET",
        headers: headersJson(),
      });
      const payload = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(String(payload?.detail || "Falha ao comparar snapshots D15."));
      setCompareResult(payload || null);
    } catch (err) {
      setStatus(`Falha comparação D15: ${String(err?.message || err)}`);
    }
  }

  async function loadD17DivergenceHealth() {
    if (!INTERNAL_TOKEN) return;
    try {
      const data = await fetchAccountingApprovalsDivergenceHealth({
        billingBase: BILLING_BASE,
        getHeaders: headersJson,
      });
      setD17Health(data);
    } catch (err) {
      setD17Health({ ok: false, error: String(err?.message || err) });
    }
  }

  async function loadD15RevenueCreditsDelta() {
    if (!INTERNAL_TOKEN) {
      setD15DeltaError("Token interno ausente para D15.");
      return;
    }
    setD15DeltaLoading(true);
    setD15DeltaError("");
    try {
      const day = String(d15DeltaDate || "").trim() || new Date().toISOString().slice(0, 10);
      const qs = new URLSearchParams({ date: day });
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/accounting/revenue-credits-delta?${qs.toString()}`, {
        method: "GET",
        headers: headersJson(),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(String(data?.detail || "Falha ao carregar delta D15."));
      if (!data?.ok) throw new Error("Resposta D15 inválida.");
      const { ok: _ok, ...rest } = data;
      setD15RevenueCreditsDelta(rest);
      setStatus("Delta D15 (receita / estornos / créditos) carregado.");
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setD15RevenueCreditsDelta(null);
      setD15DeltaError(String(err?.message || err));
    } finally {
      setD15DeltaLoading(false);
    }
  }

  function exportD15RevenueCreditsDeltaJson() {
    if (!d15RevenueCreditsDelta?.scope) {
      setStatus("Carregue o delta D15 antes de exportar.");
      window.setTimeout(() => setStatus(""), 2600);
      return;
    }
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D15_REVENUE_CREDITS_DELTA_${ts}.json`, d15RevenueCreditsDelta);
    setStatus("Export JSON D15 (SPRINT2_D15_REVENUE_CREDITS_DELTA).");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function runD17RetentionPreview() {
    if (!INTERNAL_TOKEN) {
      setStatus("Token interno ausente para retenção D17.");
      return;
    }
    setD17RetentionBusy(true);
    setD17RetentionLast(null);
    try {
      const out = await postAccountingApprovalsRetention({
        billingBase: BILLING_BASE,
        getHeaders: headersJson,
        body: {
          older_than_days: Number(d17RetentionOlder) || 90,
          keep_minimum: Number(d17RetentionKeep) || 25,
          dry_run: true,
        },
      });
      setD17RetentionLast(out);
      setStatus(
        `D17 dry-run: ${out?.selected_for_delete ?? 0} snapshot(s) elegíveis para remoção (total antes=${out?.total_rows_before ?? "-"}).`,
      );
      window.setTimeout(() => setStatus(""), 3200);
    } catch (err) {
      setStatus(`Falha retenção D17: ${String(err?.message || err)}`);
    } finally {
      setD17RetentionBusy(false);
    }
  }

  async function runD17RetentionExecute() {
    if (!INTERNAL_TOKEN) {
      setStatus("Token interno ausente para retenção D17.");
      return;
    }
    const ok = window.confirm(
      "Confirmar remoção permanente dos snapshots mais antigos que o cutoff, respeitando keep_minimum? Esta ação não pode ser desfeita.",
    );
    if (!ok) return;
    setD17RetentionBusy(true);
    setD17RetentionLast(null);
    try {
      const out = await postAccountingApprovalsRetention({
        billingBase: BILLING_BASE,
        getHeaders: headersJson,
        body: {
          older_than_days: Number(d17RetentionOlder) || 90,
          keep_minimum: Number(d17RetentionKeep) || 25,
          dry_run: false,
        },
      });
      setD17RetentionLast(out);
      setStatus(`D17 retenção: ${out?.deleted ?? 0} linha(s) removida(s).`);
      window.setTimeout(() => setStatus(""), 3200);
      void loadAccountingApprovalHistory(historyPage);
      void loadAccountingApprovalComparison();
      void loadD17DivergenceHealth();
    } catch (err) {
      setStatus(`Falha retenção D17: ${String(err?.message || err)}`);
    } finally {
      setD17RetentionBusy(false);
    }
  }

  async function exportConsolidatedHistoryJson() {
    if (!INTERNAL_TOKEN) {
      setStatus("Token interno ausente para export D16.");
      return;
    }
    try {
      const nowIso = new Date().toISOString();
      const ts = nowIso.replace(/[:.]/g, "-");
      const day = toAuditDayStamp(nowIso);
      const bundle = await fetchConsolidatedAccountingApprovals({
        billingBase: BILLING_BASE,
        getHeaders: headersJson,
        filters: {
          owner: historyOwnerFilter,
          status: historyStatusFilter,
          date_from: historyFromDate,
          date_to: historyToDate,
        },
      });
      const payload = {
        scope: "SPRINT2_D16_ACCOUNTING_APPROVALS_HISTORY",
        generated_at: nowIso,
        filters: bundle.filters,
        total: bundle.total,
        items: bundle.items,
      };
      downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_HISTORY_${ts}.json`, payload);
      setStatus(`Export JSON D16: ${bundle.items.length} registro(s).`);
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha export JSON D16: ${String(err?.message || err)}`);
    }
  }

  async function exportConsolidatedHistoryCsv() {
    if (!INTERNAL_TOKEN) {
      setStatus("Token interno ausente para export D16.");
      return;
    }
    try {
      const nowIso = new Date().toISOString();
      const ts = nowIso.replace(/[:.]/g, "-");
      const day = toAuditDayStamp(nowIso);
      const bundle = await fetchConsolidatedAccountingApprovals({
        billingBase: BILLING_BASE,
        getHeaders: headersJson,
        filters: {
          owner: historyOwnerFilter,
          status: historyStatusFilter,
          date_from: historyFromDate,
          date_to: historyToDate,
        },
      });
      const { headers, rows } = accountingApprovalsToCsvRows(bundle.items);
      const csv = buildAccountingApprovalsCsv({ headers, rows });
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_HISTORY_${ts}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setStatus(`Export CSV D16: ${bundle.items.length} linha(s).`);
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha export CSV D16: ${String(err?.message || err)}`);
    }
  }

  function saveAccountingApprovalDraft() {
    const payload = {
      owner: String(approvalOwner || ""),
      status: String(approvalStatus || "PENDING_REVIEW"),
      notes: String(approvalNotes || ""),
      timestamp: String(approvalTimestamp || ""),
      eta: String(approvalEta || ""),
    };
    try {
      window.localStorage.setItem(APPROVAL_STORAGE_KEY, JSON.stringify(payload));
      setStatus("Rascunho da aprovação contábil salvo localmente.");
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha ao salvar rascunho: ${String(err?.message || err)}`);
    }
  }

  async function syncAccountingApprovalToBackend() {
    if (!INTERNAL_TOKEN) {
      setStatus("Token interno ausente para sincronização central.");
      return;
    }
    try {
      const payload = buildAccountingApprovalPayload(new Date().toISOString());
      const r = await fetch(`${BILLING_BASE}/admin/fiscal/accounting-approvals`, {
        method: "POST",
        headers: {
          ...headersJson(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(String(out?.detail || "Falha ao sincronizar aceite no backend."));
      setStatus(`Aceite D13 sincronizado no backend (id=${out?.id || "-"})`);
      await loadAccountingApprovalHistory(0);
      await loadAccountingApprovalComparison();
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha sync backend: ${String(err?.message || err)}`);
    }
  }

  function exportAccountingApprovalJson() {
    const nowIso = new Date().toISOString();
    const inner = buildAccountingApprovalPayload(nowIso);
    const wrapped = wrapSprint2D13AccountingAcceptance(inner, nowIso, "fiscal/management-daily");
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D13_ACCOUNTING_ACCEPTANCE_${ts}.json`, wrapped);
    setStatus("Evidência D13 exportada (SPRINT2_D13_ACCOUNTING_ACCEPTANCE_*.json). POST ao backend continua com o corpo FISCAL_ACCOUNTING_DAILY_APPROVAL.");
    window.setTimeout(() => setStatus(""), 3200);
  }

  function exportD12AccountingHandoffJson() {
    if (!stubReadiness) {
      setStatus("Carregue o readiness FG-1 antes de exportar o handoff D12.");
      window.setTimeout(() => setStatus(""), 3200);
      return;
    }
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const payload = buildSprint2D12AccountingHandoffEvidence({
      generatedAt: nowIso,
      source: "fiscal/management-daily",
      stubReadiness,
      catalog,
      matrix,
      d11Handoff,
      d10Handoff,
    });
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D12_ACCOUNTING_HANDOFF_${ts}.json`, payload);
    setStatus("Evidência D12 exportada (SPRINT2_D12_ACCOUNTING_HANDOFF_*.json).");
    window.setTimeout(() => setStatus(""), 2200);
  }

  function exportD11OrderIdRollupJson() {
    if (!d11OrderIdRollup) {
      setStatus("Sem rollup D11: publique o lote em ops/fiscal/providers e recarregue.");
      window.setTimeout(() => setStatus(""), 3200);
      return;
    }
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D11_ORDER_ID_ROLLUP_${ts}.json`, d11OrderIdRollup);
    setStatus("Export JSON rollup D11 por order_id (evidência Sprint 2).");
    window.setTimeout(() => setStatus(""), 2200);
  }

  function toggleD13ChecklistItem(itemId) {
    setD13ChecklistState((prev) => ({ ...prev, [itemId]: !prev[itemId] }));
  }

  async function copyFiscalPayloadJson() {
    try {
      const payload = buildFiscalPayload(new Date().toISOString());
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setStatus("Payload de gestão fiscal copiado.");
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setStatus(`Falha ao copiar payload: ${String(err?.message || err)}`);
    }
  }

  async function downloadDailyPackageZip() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const fiscalPayload = buildFiscalPayload(nowIso);
    const approvalPayload = buildAccountingApprovalPayload(nowIso);
    const opsPayload = {
      scope: "OPS_HEALTH_DAILY",
      generated_at: nowIso,
      decision,
      checks_pass: `${passedChecks}/${readinessChecks.length}`,
      checks_failed: failedChecks,
      source: "fiscal/management-daily",
      note: "Pacote diário gerado pela página de gestão contábil/fiscal.",
    };
    const signedOpsPayload = await buildSignedPayload(opsPayload);
    const signedFiscalPayload = await buildSignedPayload(fiscalPayload);
    const signedApprovalPayload = await buildSignedPayload(approvalPayload);
    const zipEntries = {
      [`${DAILY_AUDIT_PREFIX}_${day}_OPS_HEALTH_PAYLOAD_${ts}.json`]: strToU8(JSON.stringify(signedOpsPayload, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_MANAGEMENT_PAYLOAD_${ts}.json`]: strToU8(JSON.stringify(signedFiscalPayload, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_ACCOUNTING_APPROVAL_${ts}.json`]: strToU8(JSON.stringify(signedApprovalPayload, null, 2)),
    };
    try {
      if (stubReadiness) {
        const d12Evidence = buildSprint2D12AccountingHandoffEvidence({
          generatedAt: nowIso,
          source: "fiscal/management-daily",
          stubReadiness,
          catalog,
          matrix,
          d11Handoff,
          d10Handoff,
        });
        const signedD12 = await buildSignedPayload(d12Evidence);
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D12_ACCOUNTING_HANDOFF_${ts}.json`] = strToU8(JSON.stringify(signedD12, null, 2));
      }
    } catch {
      // D12 opcional
    }
    try {
      const d13Evidence = wrapSprint2D13AccountingAcceptance(approvalPayload, nowIso, "fiscal/management-daily");
      const signedD13Evidence = await buildSignedPayload(d13Evidence);
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D13_ACCOUNTING_ACCEPTANCE_${ts}.json`] = strToU8(JSON.stringify(signedD13Evidence, null, 2));
    } catch {
      // D13 opcional
    }
    try {
      if (d11Handoff && d11OrderIdRollup) {
        const signedRollup = await buildSignedPayload(d11OrderIdRollup);
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D11_ORDER_ID_ROLLUP_${ts}.json`] = strToU8(JSON.stringify(signedRollup, null, 2));
      }
    } catch {
      // rollup opcional no pacote
    }
    if (INTERNAL_TOKEN) {
      try {
        const historyBundle = await fetchConsolidatedAccountingApprovals({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          filters: {
            owner: historyOwnerFilter,
            status: historyStatusFilter,
            date_from: historyFromDate,
            date_to: historyToDate,
          },
        });
        const signedHistory = await buildSignedPayload({
          scope: "SPRINT2_D16_ACCOUNTING_APPROVALS_HISTORY",
          generated_at: nowIso,
          filters: historyBundle.filters,
          total: historyBundle.total,
          items: historyBundle.items,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_HISTORY_${ts}.json`] = strToU8(JSON.stringify(signedHistory, null, 2));
        try {
          const comparePayload = await fetchAccountingApprovalsCompare({
            billingBase: BILLING_BASE,
            getHeaders: headersJson,
          });
          const signedDiff = await buildSignedPayload({
            scope: "SPRINT2_D16_ACCOUNTING_APPROVALS_DIFF",
            generated_at: nowIso,
            source: "fiscal/management-daily",
            compare: comparePayload,
          });
          zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_DIFF_${ts}.json`] = strToU8(JSON.stringify(signedDiff, null, 2));
        } catch {
          const signedDiffErr = await buildSignedPayload({
            scope: "SPRINT2_D16_ACCOUNTING_APPROVALS_DIFF",
            generated_at: nowIso,
            source: "fiscal/management-daily",
            error: "Histórico D16 anexado, mas diff compare falhou (verifique billing service).",
          });
          zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_DIFF_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedDiffErr, null, 2));
        }
      } catch {
        const signedDiffErr = await buildSignedPayload({
          scope: "SPRINT2_D16_ACCOUNTING_APPROVALS_ATTACH",
          generated_at: nowIso,
          source: "fiscal/management-daily",
          error: "Não foi possível anexar histórico D16 (verifique token e billing service).",
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_APPROVALS_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedDiffErr, null, 2));
      }
    }
    if (INTERNAL_TOKEN) {
      try {
        await appendP01bSignedZipEntries({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          buildSignedPayload,
          strToU8,
          fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
          ts,
          nowIso,
          d11Handoff,
          source: "fiscal/management-daily",
          zipEntries,
        });
      } catch (err) {
        const signedErr = await buildSignedPayload({
          scope: "SPRINT3_P0_1B_E2E_ATTACH_ERROR",
          generated_at: nowIso,
          source: "fiscal/management-daily",
          error: String(err?.message || err),
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_P0_1B_E2E_AUDIT_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
      }
    }
    try {
      await appendSprint4OptionalSignedZipEntries({
        buildSignedPayload,
        strToU8,
        fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
        ts,
        nowIso,
        zipEntries,
        source: "fiscal/management-daily",
      });
    } catch (err) {
      const signedErr = await buildSignedPayload({
        scope: "SPRINT4_DAILY_ATTACH_ERROR",
        generated_at: nowIso,
        source: "fiscal/management-daily",
        error: String(err?.message || err),
      });
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    }
    try {
      await appendSprint3P03OptionalSignedZipEntries({
        buildSignedPayload,
        strToU8,
        fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
        ts,
        nowIso,
        zipEntries,
        source: "fiscal/management-daily",
      });
    } catch (err) {
      const signedErr = await buildSignedPayload({
        scope: "SPRINT3_P03_DAILY_ATTACH_ERROR",
        generated_at: nowIso,
        source: "fiscal/management-daily",
        error: String(err?.message || err),
      });
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_P03_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    }
    try {
      const signedD18 = await buildSignedPayload(buildD18CloseoutPayload(nowIso));
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D18_SPRINT2_CLOSEOUT_${ts}.json`] = strToU8(JSON.stringify(signedD18, null, 2));
    } catch {
      // no-op: closeout D18 é opcional no pacote
    }
    try {
      const rawGate = loadSprint2FinanceGateV2State();
      const mirror = summarizeSprint2FinanceGateV2(rawGate);
      if (mirror) {
        const signedGateMirror = await buildSignedPayload({
          scope: "SPRINT2_GATE_V2_MIRROR_ATTACH",
          generated_at: nowIso,
          source: "fiscal/management-daily",
          committee_reference: "2026-05-01",
          thresholds: SPRINT2_FINANCE_GATE_V2_THRESHOLDS,
          mirror,
          raw_local_storage: rawGate,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_GATE_V2_MIRROR_${ts}.json`] = strToU8(JSON.stringify(signedGateMirror, null, 2));
      }
    } catch {
      // espelho gate opcional
    }
    try {
      const rawPartner = loadSprint3PartnerAuditMirrorForDaily();
      if (rawPartner) {
        const signedPartnerMirror = await buildSignedPayload({
          scope: "SPRINT3_PARTNER_AUDIT_MIRROR_ATTACH",
          generated_at: nowIso,
          source: "fiscal/management-daily",
          saved_snapshot: rawPartner,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_PARTNER_AUDIT_MIRROR_${ts}.json`] = strToU8(
          JSON.stringify(signedPartnerMirror, null, 2),
        );
      }
    } catch {
      // espelho Sprint 3 opcional
    }
    try {
      const rawD10 = window.localStorage.getItem(FISCAL_D10_TRACKER_KEY);
      const d10Tracker = parseD10TrackerFromLocalStorageRaw(rawD10 || "");
      if (d10Tracker) {
        const d10Evidence = buildD10ProvidersEvidencePayload({
          generatedAt: nowIso,
          source: "fiscal/management-daily",
          tracker: d10Tracker,
        });
        const signedD10 = await buildSignedPayload(d10Evidence);
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D10_PROVIDERS_TRACKER_${ts}.json`] = strToU8(JSON.stringify(signedD10, null, 2));
      }
    } catch {
      // D10 opcional no pacote
    }
    try {
      if (d10Handoff) {
        const signedD10Ops = await buildSignedPayload(d10Handoff);
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D10_PROVIDERS_OPS_HANDOFF_${ts}.json`] = strToU8(JSON.stringify(signedD10Ops, null, 2));
      }
    } catch {
      // D10 OPS handoff opcional no pacote
    }
    try {
      if (INTERNAL_TOKEN && d15RevenueCreditsDelta?.scope === "SPRINT2_D15_REVENUE_CREDITS_DELTA") {
        const signedD15 = await buildSignedPayload(d15RevenueCreditsDelta);
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_D15_REVENUE_CREDITS_DELTA_${ts}.json`] = strToU8(JSON.stringify(signedD15, null, 2));
      }
    } catch {
      // D15 opcional no pacote
    }
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_PACKAGE_${ts}.zip`, zipEntries);
    setStatus(
      "Pacote diário (.zip): OPS + FISCAL + APPROVAL + SPRINT2_D12/D13 (quando aplicável) + D10 tracker + D10 OPS handoff + D15 receita/estornos + D11 rollup + D16 + P0-1b + Sprint 4 + carimbo P0-3 + D18 + espelhos gate v2 e Sprint 3 partner-audit quando disponíveis.",
    );
    window.setTimeout(() => setStatus(""), 2200);
  }

  function downloadFiscalPayloadJson() {
    const nowIso = new Date().toISOString();
    const payload = buildFiscalPayload(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_MANAGEMENT_PAYLOAD_${ts}.json`, payload);
    setStatus("Payload JSON da gestão fiscal baixado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/fiscal" style={shortcutLinkStyle}>
            Abrir fiscal/global
          </Link>
          <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>
            Abrir fiscal/sprint2-finance-gate
          </Link>
          <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>
            Abrir fiscal/sprint3-partner-audit
          </Link>
          <Link to="/fiscal/accounting-close" style={shortcutLinkStyle}>
            Abrir fiscal/accounting-close
          </Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Abrir ops/health
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Management Daily" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Cockpit diário do departamento contábil/fiscal para decisão, evidência e anexo operacional.</p>
        <div style={sprint2GateMirrorBoxStyle}>
          <h3 style={boxTitleStyle}>Sprint 2 — gate v2 (espelho)</h3>
          <p style={mutedTextStyle}>
            Os mesmos percentuais e a nota P0 do cockpit{" "}
            <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>
              fiscal/sprint2-finance-gate
            </Link>{" "}
            (<code>localStorage</code> partilhado). Atualiza ao focar esta aba ou ao gravar no outro separador. O pacote diário
            (.zip) inclui <code>SPRINT2_GATE_V2_MIRROR_ATTACH</code> quando existir estado gravado.
          </p>
          {gateMirror ? (
            <>
              <div style={summaryRowStyle}>
                <span style={chipStyle}>
                  Fiscal {gateMirror.fiscal_percent}% {gateMirror.fiscal_ok ? "OK" : "FALTA"} (≥{SPRINT2_FINANCE_GATE_V2_THRESHOLDS.fiscal}%)
                </span>
                <span style={chipStyle}>
                  Contábil {gateMirror.accounting_percent}% {gateMirror.accounting_ok ? "OK" : "FALTA"} (≥
                  {SPRINT2_FINANCE_GATE_V2_THRESHOLDS.accounting}%)
                </span>
                <span style={chipStyle}>
                  Consolidado S2 {gateMirror.consolidated_percent}% {gateMirror.consolidated_ok ? "OK" : "FALTA"} (≥
                  {SPRINT2_FINANCE_GATE_V2_THRESHOLDS.consolidated}%)
                </span>
                <span style={chipStyle}>P0 texto {gateMirror.p0_evidence_ok ? "OK (≥24)" : "FALTA (<24 chars)"}</span>
                {gateMirror.updated_at ? (
                  <span style={chipStyle}>Atualizado: {formatOpsDateTime(gateMirror.updated_at)}</span>
                ) : null}
              </div>
              <div style={{ marginTop: 8 }}>
                <span style={badgeStyle(gateMirror.overall_pass ? "GO" : "NO_GO")}>
                  {gateMirror.overall_pass ? "PASS cumulativo (AND)" : "NO_GO — limiares ou P0 incompletos"}
                </span>
              </div>
              <p style={{ ...mutedTextStyle, marginTop: 10, fontSize: 12 }}>
                Pré-visualização P0:{" "}
                {gateMirror.p0_evidence_note.trim()
                  ? `${gateMirror.p0_evidence_note.trim().slice(0, 200)}${gateMirror.p0_evidence_note.trim().length > 200 ? "…" : ""}`
                  : "(vazio)"}
              </p>
            </>
          ) : (
            <small style={mutedTextStyle}>
              Sem estado gravado. Abra <Link to="/fiscal/sprint2-finance-gate">fiscal/sprint2-finance-gate</Link>, preencha e use
              «Gravar estado local».
            </small>
          )}
        </div>
        <div style={sprint2GateMirrorBoxStyle}>
          <h3 style={boxTitleStyle}>Sprint 3 — auditoria por parceiro (espelho)</h3>
          <p style={mutedTextStyle}>
            Snapshot gravado em{" "}
            <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>
              fiscal/sprint3-partner-audit
            </Link>{" "}
            («Gravar espelho para pacote diário»). O pacote (.zip) inclui <code>SPRINT3_PARTNER_AUDIT_MIRROR_ATTACH</code> quando
            existir.
          </p>
          {partnerAuditMirror ? (
            <div style={summaryRowStyle}>
              <span style={chipStyle}>
                Parceiros na fatia:{" "}
                {Array.isArray(partnerAuditMirror.slice?.partners) ? partnerAuditMirror.slice.partners.length : "—"}
              </span>
              <span style={chipStyle}>D11: {partnerAuditMirror.include_d11 ? "incluído" : "não"}</span>
              {partnerAuditMirror.saved_at ? (
                <span style={chipStyle}>Gravado: {formatOpsDateTime(partnerAuditMirror.saved_at)}</span>
              ) : null}
            </div>
          ) : (
            <small style={mutedTextStyle}>
              Sem espelho. Abra <Link to="/fiscal/sprint3-partner-audit">fiscal/sprint3-partner-audit</Link>, atualize a trilha e
              use «Gravar espelho para pacote diário».
            </small>
          )}
        </div>
        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadData()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button type="button" onClick={() => void copyFiscalPayloadJson()} style={buttonStyle} disabled={!stubReadiness}>
            Copiar payload gestão (JSON)
          </button>
          <button type="button" onClick={() => downloadFiscalPayloadJson()} style={buttonStyle} disabled={!stubReadiness}>
            Baixar payload gestão (.json)
          </button>
          <button type="button" onClick={() => downloadDailyPackageZip()} style={buttonStyle} disabled={!stubReadiness}>
            Baixar pacote diário (.zip)
          </button>
          <button type="button" onClick={() => loadD11Handoff()} style={buttonStyle}>
            Recarregar lote D11
          </button>
          <button type="button" onClick={() => loadD10Handoff()} style={buttonStyle}>
            Recarregar espelho D10
          </button>
          <button type="button" onClick={() => void loadLatestAccountingApproval()} style={buttonStyle}>
            Carregar aceite central
          </button>
          <button type="button" onClick={() => void loadAccountingApprovalHistory(0)} style={buttonStyle}>
            Atualizar histórico D15
          </button>
          <button type="button" onClick={() => void loadAccountingApprovalComparison()} style={buttonStyle}>
            Comparar últimos snapshots
          </button>
          <button type="button" onClick={() => void loadD17DivergenceHealth()} style={buttonStyle} disabled={!INTERNAL_TOKEN}>
            Atualizar saúde D17
          </button>
          <button type="button" onClick={() => void loadD15RevenueCreditsDelta()} style={buttonStyle} disabled={!INTERNAL_TOKEN || d15DeltaLoading}>
            {d15DeltaLoading ? "D15…" : "Carregar delta D15"}
          </button>
        </div>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}
        {!error && stubReadiness ? (
          <div style={summaryRowStyle}>
            <span style={badgeStyle(decision)}>Decisão consolidada: {decision}</span>
            <span style={chipStyle}>{`${passedChecks}/${readinessChecks.length} checks PASS`}</span>
            <span style={chipStyle}>Checks com falha: {failedChecks} / {readinessChecks.length}</span>
            <span style={chipStyle}>Risk level: {riskLevel}</span>
            <span style={chipStyle}>Countries not ready: {countriesNotReady}</span>
            <span style={chipStyle}>Readiness ref: {String(stubReadiness?.readiness_version || "-")}</span>
          </div>
        ) : null}
        {!error && practicalActions.length > 0 ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Ações práticas recomendadas</h3>
            <ul style={listStyle}>
              {practicalActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D10 — Espelho OPS (handoff publicado)</h3>
            {d10Handoff ? (
              <>
                <div style={summaryRowStyle}>
                  <span style={chipStyle}>Publicado: {String(d10Handoff?.generated_at || "-")}</span>
                  <span style={chipStyle}>
                    Checklist D10: {Number(d10Handoff?.summary?.d10_progress_pct ?? 0)}% (
                    {Number(d10Handoff?.summary?.d10_done_count ?? 0)}/{Number(d10Handoff?.summary?.d10_total_tasks ?? 0)})
                  </span>
                  <span style={chipStyle}>Providers (amostra): {Number(d10Handoff?.summary?.providers_count ?? 0)}</span>
                  {d10Handoff?.summary?.go_no_go_br ? (
                    <span style={chipStyle}>GO/NO-GO BR: {String(d10Handoff.summary.go_no_go_br)}</span>
                  ) : null}
                  {d10Handoff?.summary?.go_no_go_pt ? (
                    <span style={chipStyle}>GO/NO-GO PT: {String(d10Handoff.summary.go_no_go_pt)}</span>
                  ) : null}
                </div>
                <small style={mutedTextStyle}>
                  Origem <code>/ops/fiscal/providers</code> — use «Publicar D10 no handoff diário» na OPS. O payload entra em{" "}
                  <code>FISCAL_MANAGEMENT_DAILY</code>, D12/D13 e no ZIP como <code>SPRINT2_D10_PROVIDERS_OPS_HANDOFF_*</code> (assinado).
                </small>
                <div style={{ marginTop: 10 }}>
                  <Link to="/ops/fiscal/providers" style={shortcutLinkStyle}>
                    Abrir ops/fiscal/providers (D10)
                  </Link>
                </div>
              </>
            ) : (
              <small style={mutedTextStyle}>
                Sem espelho D10. Abra <Link to="/ops/fiscal/providers">ops/fiscal/providers</Link> e use «Publicar D10 no handoff diário», depois
                «Recarregar espelho D10».
              </small>
            )}
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D12 - Handoff contábil conectado ao lote D11</h3>
            {d11Handoff ? (
              <>
                <div style={summaryRowStyle}>
                  <span style={chipStyle}>Lote gerado: {String(d11Handoff?.generated_at || "-")}</span>
                  <span style={chipStyle}>Itens D11: {Number(d11Handoff?.summary?.total_items || 0)}</span>
                  <span style={chipStyle}>Partners: {Number(d11Handoff?.summary?.unique_partners || 0)}</span>
                  <span style={chipStyle}>Batches: {Number(d11Handoff?.summary?.unique_batches || 0)}</span>
                </div>
                <div style={summaryRowStyle}>
                  <span style={chipStyle}>ERROR: {Number(d11Handoff?.summary?.severity?.ERROR || 0)}</span>
                  <span style={chipStyle}>WARN: {Number(d11Handoff?.summary?.severity?.WARN || 0)}</span>
                  <span style={chipStyle}>INFO: {Number(d11Handoff?.summary?.severity?.INFO || 0)}</span>
                  <span style={chipStyle}>
                    Pedidos c/ gap: {Number(d11Handoff?.summary?.unique_orders_with_gaps ?? d11OrderIdRollup?.unique_orders_with_gaps ?? 0)}
                  </span>
                </div>
                {d11OrderIdRollup && d11OrderIdRollup.orders.length ? (
                  <>
                    <h4 style={{ ...boxTitleStyle, marginTop: 14, marginBottom: 8, fontSize: 15 }}>D11 — fila por order_id (P0 conciliação)</h4>
                    <div style={toolbarStyle}>
                      <button type="button" onClick={exportD11OrderIdRollupJson} style={buttonStyle}>
                        Exportar rollup order_id (JSON)
                      </button>
                      <Link to="/ops/fiscal/providers" style={shortcutLinkStyle}>
                        Abrir ops/fiscal/providers (D11)
                      </Link>
                    </div>
                    <div style={{ overflowX: "auto", marginTop: 8 }}>
                      <table style={historyTableStyle}>
                        <thead>
                          <tr>
                            <th style={historyThStyle}>order_id</th>
                            <th style={historyThStyle}># gaps</th>
                            <th style={historyThStyle}>ERROR</th>
                            <th style={historyThStyle}>WARN</th>
                            <th style={historyThStyle}>INFO</th>
                          </tr>
                        </thead>
                        <tbody>
                          {d11OrderIdRollup.orders.slice(0, 15).map((o) => (
                            <tr key={o.order_id}>
                              <td style={historyTdStyle}>
                                <code>{o.order_id}</code>
                              </td>
                              <td style={historyTdStyle}>{o.gap_count}</td>
                              <td style={historyTdStyle}>{o.by_severity.ERROR || 0}</td>
                              <td style={historyTdStyle}>{o.by_severity.WARN || 0}</td>
                              <td style={historyTdStyle}>{o.by_severity.INFO || 0}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : null}
                <small style={mutedTextStyle}>
                  Este snapshot D11 já entra automaticamente nos payloads JSON/ZIP do handoff contábil diário. Com rollup por <code>order_id</code>, o ZIP inclui{" "}
                  <code>SPRINT2_D11_ORDER_ID_ROLLUP_*.json</code> assinado (SHA-256). O mesmo padrão de evidência nomeada aplica-se a{" "}
                  <code>SPRINT2_D12_ACCOUNTING_HANDOFF_*</code> (handoff contábil + contexto FG-1) e <code>SPRINT2_D13_ACCOUNTING_ACCEPTANCE_*</code> (aceite + checklist
                  crítico). O pacote .zip inclui também Sprint 3 <strong>P0-1b</strong>: <code>SPRINT3_E2E_AUDIT_TRAIL</code> +{" "}
                  <code>P0_1B_PARTNER_RECONCILIATION</code> (SHA-256), com <code>d11_cross_check</code> quando o lote D11 estiver carregado. Com dados no browser, anexa
                  ainda Sprint 4 (matriz/pilotos) e carimbo P0-3 (<code>SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH</code>) de <code>fiscal/incident-response</code>.
                </small>
              </>
            ) : (
              <small style={mutedTextStyle}>
                Nenhum lote D11 encontrado no navegador. Publique o lote em `ops/fiscal/providers` e clique em "Recarregar lote D11".
              </small>
            )}
            <div style={{ ...toolbarStyle, marginTop: 12 }}>
              <button type="button" onClick={exportD12AccountingHandoffJson} style={buttonStyle} disabled={!stubReadiness}>
                Export handoff D12 (JSON)
              </button>
            </div>
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D15 - Histórico paginado de aceite (owner/status/período)</h3>
            <div style={approvalGridStyle}>
              <label style={labelStyle}>
                owner
                <input value={historyOwnerFilter} onChange={(e) => setHistoryOwnerFilter(e.target.value)} style={inputStyle} placeholder="filtrar owner" />
              </label>
              <label style={labelStyle}>
                status
                <select value={historyStatusFilter} onChange={(e) => setHistoryStatusFilter(e.target.value)} style={inputStyle}>
                  <option value="">ALL</option>
                  <option value="PENDING_REVIEW">PENDING_REVIEW</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="APPROVED_WITH_RESTRICTIONS">APPROVED_WITH_RESTRICTIONS</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </label>
              <label style={labelStyle}>
                período de
                <input type="date" value={historyFromDate} onChange={(e) => setHistoryFromDate(e.target.value)} style={inputStyle} />
              </label>
              <label style={labelStyle}>
                período até
                <input type="date" value={historyToDate} onChange={(e) => setHistoryToDate(e.target.value)} style={inputStyle} />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button type="button" onClick={() => void loadAccountingApprovalHistory(0)} style={buttonStyle}>
                Aplicar filtros
              </button>
              <button type="button" onClick={() => void exportConsolidatedHistoryJson()} style={buttonStyle} disabled={!INTERNAL_TOKEN}>
                Export histórico filtrado (JSON)
              </button>
              <button type="button" onClick={() => void exportConsolidatedHistoryCsv()} style={buttonStyle} disabled={!INTERNAL_TOKEN}>
                Export histórico filtrado (CSV)
              </button>
              <button type="button" onClick={() => void loadAccountingApprovalHistory(Math.max(historyPage - 1, 0))} style={buttonStyle} disabled={historyPage <= 0}>
                Página anterior
              </button>
              <button
                type="button"
                onClick={() => void loadAccountingApprovalHistory(historyPage + 1)}
                style={buttonStyle}
                disabled={(historyPage + 1) * historyLimit >= historyTotal}
              >
                Próxima página
              </button>
              <small style={mutedTextStyle}>
                total={historyTotal} | página={historyPage + 1}
              </small>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={historyTableStyle}>
                <thead>
                  <tr>
                    <th style={historyThStyle}>id</th>
                    <th style={historyThStyle}>owner</th>
                    <th style={historyThStyle}>status</th>
                    <th style={historyThStyle}>eta</th>
                    <th style={historyThStyle}>created_at</th>
                    <th style={historyThStyle}>ações</th>
                  </tr>
                </thead>
                <tbody>
                  {historyItems.length ? (
                    historyItems.map((row) => (
                      <tr key={row?.id}>
                        <td style={historyTdStyle}>{String(row?.id || "-")}</td>
                        <td style={historyTdStyle}>{String(row?.owner || "-")}</td>
                        <td style={historyTdStyle}>{String(row?.status || "-")}</td>
                        <td style={historyTdStyle}>{String(row?.eta || "-")}</td>
                        <td style={historyTdStyle}>{String(row?.created_at || "-")}</td>
                        <td style={historyTdStyle}>
                          <button
                            type="button"
                            onClick={() => void loadAccountingApprovalComparison(String(row?.id || ""), "")}
                            style={smallButtonStyle}
                          >
                            Comparar com anterior
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td style={historyTdStyle} colSpan={6}>
                        Sem snapshots no filtro atual.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
        {!error && INTERNAL_TOKEN ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Contábil Sprint 2 — delta receita / estornos / créditos (D15)</h3>
            <p style={{ ...mutedTextStyle, marginTop: 4 }}>
              Agrega <code>ellanlab_revenue_recognition</code> com <code>financial_ledger</code> (tipos BILLING_REVENUE, BILLING_REVERSAL, CREDIT_NOTE_APPLIED) no dia
              civil. API: <code>GET /admin/fiscal/accounting/revenue-credits-delta</code>.
            </p>
            <div style={{ marginTop: 8, maxWidth: 320 }}>
              <input
                type="date"
                value={d15DeltaDate}
                onChange={(e) => setD15DeltaDate(e.target.value)}
                style={inputStyle}
                data-testid="fiscal-d15-delta-date"
              />
            </div>
            <div style={{ ...toolbarStyle, marginTop: 10 }}>
              <button type="button" onClick={() => void loadD15RevenueCreditsDelta()} style={buttonStyle} disabled={d15DeltaLoading}>
                {d15DeltaLoading ? "A carregar…" : "Atualizar delta"}
              </button>
              <button type="button" onClick={() => exportD15RevenueCreditsDeltaJson()} style={buttonStyle} disabled={!d15RevenueCreditsDelta?.scope}>
                Export JSON (SPRINT2_D15_*)
              </button>
            </div>
            {d15DeltaError ? <div style={errorStyle}>{d15DeltaError}</div> : null}
            {d15RevenueCreditsDelta?.summary ? (
              <div style={{ ...summaryRowStyle, marginTop: 10 }}>
                <span style={chipStyle}>Data: {String(d15RevenueCreditsDelta.snapshot_date || "-")}</span>
                <span style={chipStyle}>Linhas rev.rec.: {Number(d15RevenueCreditsDelta.summary.revenue_recognition_lines || 0)}</span>
                <span style={chipStyle}>Receita reconhecida (¢): {Number(d15RevenueCreditsDelta.summary.recognized_revenue_cents_total || 0)}</span>
                <span style={chipStyle}>Estornos (¢): {Number(d15RevenueCreditsDelta.summary.ledger_reversal_cents || 0)}</span>
                <span style={chipStyle}>Créditos (¢): {Number(d15RevenueCreditsDelta.summary.ledger_credit_note_cents || 0)}</span>
                <span style={chipStyle}>Residual %: {Number(d15RevenueCreditsDelta.summary.divergence_residual_pct || 0)}</span>
              </div>
            ) : (
              <small style={mutedTextStyle}>Use «Carregar delta D15» na barra ou «Atualizar delta» acima.</small>
            )}
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D15 - Comparação entre snapshots de aceite</h3>
            {compareResult?.diff ? (
              <>
                <div style={summaryRowStyle}>
                  <span style={chipStyle}>current={String(compareResult?.current?.id || "-")}</span>
                  <span style={chipStyle}>previous={String(compareResult?.previous?.id || "-")}</span>
                </div>
                <small style={mutedTextStyle}>{String(compareResult?.diff?.summary || "-")}</small>
                <ul style={listStyle}>
                  {(Array.isArray(compareResult?.diff?.changed) ? compareResult.diff.changed : []).map((item) => (
                    <li key={`${item?.field}:${item?.current}:${item?.previous}`}>
                      <strong>{String(item?.field || "-")}</strong>: {String(item?.previous ?? "-")} -&gt; {String(item?.current ?? "-")}
                    </li>
                  ))}
                  {Array.isArray(compareResult?.diff?.changed) && compareResult.diff.changed.length === 0 ? (
                    <li>Sem mudanças relevantes entre os snapshots comparados.</li>
                  ) : null}
                </ul>
              </>
            ) : (
              <small style={mutedTextStyle}>Sem comparação carregada.</small>
            )}
          </div>
        ) : null}
        {!error && INTERNAL_TOKEN ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D17 - Retenção / compactação e alerta de divergência prolongada</h3>
            {d17Health?.ok === false ? (
              <div style={errorStyle}>{String(d17Health?.error || "Falha D17.")}</div>
            ) : d17Health ? (
              <>
                {d17Health?.prolonged_identical_diff ? (
                  <div
                    style={{
                      ...chipStyle,
                      border: "1px solid #c98a2a",
                      background: "#2a2210",
                      color: "#f5d78a",
                      padding: "10px 12px",
                      marginBottom: 10,
                    }}
                  >
                    Alerta: o mesmo diff de governança persiste em {String(d17Health?.prolonged_detail?.consecutive_edges_with_same_diff || "?")} borda(s)
                    consecutiva(s) (limiar {String(d17Health?.prolonged_detail?.threshold_edges || d17Health?.policy?.prolonged_edges || "?")}). Reveja owner/status/ETA ou checklist
                    antes de novos snapshots.
                  </div>
                ) : (
                  <small style={mutedTextStyle}>
                    {d17Health?.latest_pair_has_diff
                      ? "Último par de snapshots tem divergência, mas não atingiu o limiar de repetição prolongada."
                      : "Último par de snapshots sem diff relevante ou dados insuficientes."}
                  </small>
                )}
                <div style={summaryRowStyle}>
                  <span style={chipStyle}>Snapshots analisados: {Number(d17Health?.snapshots_considered || 0)}</span>
                  <span style={chipStyle}>Bordas: {Array.isArray(d17Health?.edges) ? d17Health.edges.length : 0}</span>
                </div>
                {Array.isArray(d17Health?.edges) && d17Health.edges.length ? (
                  <ul style={{ ...listStyle, fontSize: 12 }}>
                    {d17Health.edges.slice(0, 6).map((e, idx) => (
                      <li key={`${e?.newer_id}-${e?.older_id}-${idx}`}>
                        {String(e?.newer_id || "")} vs {String(e?.older_id || "")}: {Number(e?.changed_count || 0)} campo(s) —{" "}
                        {(Array.isArray(e?.fields) ? e.fields : []).join(", ") || "(nenhum)"}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </>
            ) : (
              <small style={mutedTextStyle}>Carregando saúde de divergência…</small>
            )}
            <div style={{ ...approvalGridStyle, marginTop: 12 }}>
              <label style={labelStyle}>
                Retenção: dias mínimos de idade
                <input
                  type="number"
                  min={7}
                  max={3650}
                  value={d17RetentionOlder}
                  onChange={(e) => setD17RetentionOlder(Number(e.target.value) || 90)}
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                Manter no mínimo N linhas
                <input
                  type="number"
                  min={1}
                  max={10000}
                  value={d17RetentionKeep}
                  onChange={(e) => setD17RetentionKeep(Number(e.target.value) || 25)}
                  style={inputStyle}
                />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button type="button" onClick={() => void runD17RetentionPreview()} style={buttonStyle} disabled={d17RetentionBusy}>
                Dry-run retenção
              </button>
              <button type="button" onClick={() => void runD17RetentionExecute()} style={buttonStyle} disabled={d17RetentionBusy}>
                Executar retenção
              </button>
            </div>
            {d17RetentionLast ? (
              <pre style={{ ...mutedTextStyle, fontSize: 11, whiteSpace: "pre-wrap", marginTop: 8 }}>
                {JSON.stringify(d17RetentionLast, null, 2)}
              </pre>
            ) : null}
            <small style={mutedTextStyle}>
              Compactação = poda de linhas antigas acima da idade configurada, sem violar o piso de linhas. Exige billing acessível e token interno.
            </small>
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D13 - Checklist crítico automático (aceite por owner/ETA)</h3>
            <div style={summaryRowStyle}>
              <span style={chipStyle}>Owner aceite: {String(approvalOwner || "-")}</span>
              <span style={chipStyle}>ETA aceite: {String(approvalEta || "-")}</span>
              <span style={chipStyle}>
                Progresso checklist: {d13ChecklistDoneCount}/{d13CriticalChecklist.length}
              </span>
            </div>
            {d13CriticalChecklist.length > 0 ? (
              <div style={{ display: "grid", gap: 6 }}>
                {d13CriticalChecklist.map((item) => (
                  <label key={item.id} style={checkItemStyle}>
                    <input
                      type="checkbox"
                      checked={Boolean(d13ChecklistState[item.id])}
                      onChange={() => toggleD13ChecklistItem(item.id)}
                    />
                    <span>{item.title}</span>
                    <small style={mutedTextStyle}>
                      partner={item.partner_id} | batch={item.batch_id} | owner={item.owner} | ETA={item.eta}
                    </small>
                  </label>
                ))}
              </div>
            ) : (
              <small style={mutedTextStyle}>Sem itens críticos (ERROR/WARN) no snapshot D11 atual.</small>
            )}
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Aprovação Contábil do Dia</h3>
            <div style={approvalGridStyle}>
              <label style={labelStyle}>
                Responsável
                <input
                  type="text"
                  value={approvalOwner}
                  onChange={(event) => setApprovalOwner(event.target.value)}
                  placeholder="Nome do responsável contábil/fiscal"
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                Status
                <select value={approvalStatus} onChange={(event) => setApprovalStatus(event.target.value)} style={inputStyle}>
                  <option value="PENDING_REVIEW">PENDING_REVIEW</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="APPROVED_WITH_RESTRICTIONS">APPROVED_WITH_RESTRICTIONS</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </label>
              <label style={labelStyle}>
                Timestamp (UTC)
                <input
                  type="datetime-local"
                  value={approvalTimestamp}
                  onChange={(event) => setApprovalTimestamp(event.target.value)}
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                ETA de fechamento
                <input
                  type="datetime-local"
                  value={approvalEta}
                  onChange={(event) => setApprovalEta(event.target.value)}
                  style={inputStyle}
                />
              </label>
              <label style={{ ...labelStyle, gridColumn: "1 / -1" }}>
                Observações
                <textarea
                  value={approvalNotes}
                  onChange={(event) => setApprovalNotes(event.target.value)}
                  placeholder="Observações de aprovação e ressalvas do dia"
                  style={textareaStyle}
                />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button type="button" onClick={() => saveAccountingApprovalDraft()} style={buttonStyle}>
                Salvar rascunho local
              </button>
              <button type="button" onClick={() => void syncAccountingApprovalToBackend()} style={buttonStyle}>
                Salvar aceite no backend (multiusuário)
              </button>
              <button type="button" onClick={() => exportAccountingApprovalJson()} style={buttonStyle}>
                Exportar aceite D13 (SPRINT2_D13_*.json)
              </button>
            </div>
          </div>
        ) : null}
        {!error ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>D18 — Fechamento Sprint 2 (checklist + riscos P1 remanescentes)</h3>
            <p style={mutedTextStyle}>
              Conteúdo mínimo para aceite assistido: marcações e template P1 persistem neste navegador (
              <code>{D18_CLOSEOUT_STORAGE_KEY}</code>
              ). Incluído no pacote diário (.zip) como <code>SPRINT2_D18_FINANCE_CLOSEOUT</code>; o ZIP de{" "}
              <Link to="/fiscal/accounting-close">fiscal/accounting-close</Link> reutiliza os mesmos dados com{" "}
              <code>SPRINT2_D18_EXEC_FINANCE_CLOSEOUT</code>.
            </p>
            <div style={summaryRowStyle}>
              <span style={chipStyle}>
                Checklist D18: {countD18ChecklistDone(d18Checklist)}/{D18_CHECKLIST_ITEMS.length}
              </span>
              {d18Certification ? (
                <span style={{ ...chipStyle, borderColor: "rgba(34,197,94,0.55)", background: "rgba(34,197,94,0.12)" }}>
                  Carimbado · {d18Certification.certified_by} ·{" "}
                  {formatOpsDateTime(d18Certification.certified_at, { dateStyle: "short", timeStyle: "medium" })}
                </span>
              ) : (
                <span style={{ ...chipStyle, opacity: 0.85 }}>Sem carimbo de revisão (closeout em rascunho)</span>
              )}
            </div>
            {d18Certification ? (
              <div
                style={{
                  marginBottom: 12,
                  padding: 12,
                  borderRadius: 10,
                  border: "1px solid rgba(34,197,94,0.45)",
                  background: "rgba(34,197,94,0.08)",
                  fontSize: 13,
                }}
              >
                <strong>Revisão registrada.</strong> Por <b>{d18Certification.certified_by}</b> em{" "}
                {formatOpsDateTime(d18Certification.certified_at, { dateStyle: "medium", timeStyle: "medium" })}
                {d18Certification.note ? (
                  <>
                    <br />
                    <span style={{ opacity: 0.92 }}>Nota: {d18Certification.note}</span>
                  </>
                ) : null}
                <div style={{ marginTop: 8 }}>
                  <button type="button" onClick={() => revokeD18Certification()} style={buttonStyle}>
                    Revogar carimbo
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ marginBottom: 12, display: "grid", gap: 8, maxWidth: 480 }}>
                <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
                  Revisor (nome ou sigla) — obrigatório para carimbar
                  <input
                    value={d18CarimboBy}
                    onChange={(e) => setD18CarimboBy(e.target.value)}
                    style={inputStyle}
                    placeholder={String(approvalOwner || "").trim() || "ex.: Marcos / SRE-plantão"}
                  />
                </label>
                <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
                  Nota opcional (contexto da revisão)
                  <textarea
                    value={d18CarimboNote}
                    onChange={(e) => setD18CarimboNote(e.target.value)}
                    rows={2}
                    style={{ ...inputStyle, resize: "vertical", minHeight: 52 }}
                    placeholder="Ex.: Checklist validado com operação; P1 aceitos com ETAs."
                  />
                </label>
                <div>
                  <button type="button" onClick={() => stampD18Closeout()} style={buttonStyle}>
                    Carimbar closeout D18 (revisão humana)
                  </button>
                </div>
              </div>
            )}
            <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
              {D18_CHECKLIST_ITEMS.map((row) => (
                <label key={row.id} style={checkItemStyle}>
                  <input type="checkbox" checked={Boolean(d18Checklist[row.id])} onChange={() => toggleD18Checklist(row.id)} />
                  <span>{row.label}</span>
                </label>
              ))}
            </div>
            <h4 style={{ ...boxTitleStyle, fontSize: 14 }}>Template — riscos P1 remanescentes (5 linhas)</h4>
            <div style={{ overflowX: "auto" }}>
              <table style={historyTableStyle}>
                <thead>
                  <tr>
                    <th style={historyThStyle}>Risco / tema</th>
                    <th style={historyThStyle}>Owner</th>
                    <th style={historyThStyle}>ETA</th>
                    <th style={historyThStyle}>Impacto se não tratar</th>
                  </tr>
                </thead>
                <tbody>
                  {d18P1Rows.map((row, idx) => (
                    <tr key={row.id}>
                      <td style={historyTdStyle}>
                        <input
                          value={row.title}
                          onChange={(e) => updateD18P1Row(idx, "title", e.target.value)}
                          style={{ ...inputStyle, width: "100%", minWidth: 160 }}
                          placeholder="Descrever risco P1"
                        />
                      </td>
                      <td style={historyTdStyle}>
                        <input
                          value={row.owner}
                          onChange={(e) => updateD18P1Row(idx, "owner", e.target.value)}
                          style={inputStyle}
                          placeholder="Owner"
                        />
                      </td>
                      <td style={historyTdStyle}>
                        <input
                          value={row.eta}
                          onChange={(e) => updateD18P1Row(idx, "eta", e.target.value)}
                          style={inputStyle}
                          placeholder="ETA / prazo"
                        />
                      </td>
                      <td style={historyTdStyle}>
                        <input
                          value={row.impact}
                          onChange={(e) => updateD18P1Row(idx, "impact", e.target.value)}
                          style={{ ...inputStyle, width: "100%", minWidth: 140 }}
                          placeholder="Impacto"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={toolbarStyle}>
              <button type="button" onClick={() => void copyD18CloseoutJson()} style={buttonStyle}>
                Copiar JSON D18
              </button>
              <button type="button" onClick={() => downloadD18CloseoutJson()} style={buttonStyle}>
                Baixar JSON D18
              </button>
              <button type="button" onClick={() => resetD18P1Template()} style={buttonStyle}>
                Limpar template P1
              </button>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10 };
const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};
const sprint2GateMirrorBoxStyle = {
  marginTop: 4,
  marginBottom: 14,
  padding: 14,
  borderRadius: 12,
  border: "1px solid rgba(34,197,94,0.4)",
  background: "rgba(22,101,52,0.12)",
};
const toolbarStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 };
const buttonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  cursor: "pointer",
  fontWeight: 600,
};
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const summaryRowStyle = { marginTop: 10, marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const chipStyle = {
  display: "inline-flex",
  padding: "4px 10px",
  borderRadius: 999,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  fontSize: 12,
  fontWeight: 700,
};
const badgeStyle = (status) => {
  if (String(status || "").toUpperCase() === "GO") {
    return {
      display: "inline-flex",
      padding: "4px 10px",
      borderRadius: 999,
      border: "1px solid rgba(34,197,94,0.65)",
      background: "rgba(34,197,94,0.18)",
      color: "#bbf7d0",
      fontSize: 12,
      fontWeight: 700,
    };
  }
  return {
    display: "inline-flex",
    padding: "4px 10px",
    borderRadius: 999,
    border: "1px solid rgba(239,68,68,0.65)",
    background: "rgba(239,68,68,0.18)",
    color: "#fecaca",
    fontSize: 12,
    fontWeight: 700,
  };
};
const boxStyle = {
  marginTop: 12,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 12,
  padding: 12,
  background: "var(--fiscal-box-bg)",
};
const boxTitleStyle = { margin: "0 0 8px", fontSize: 15, color: "var(--fiscal-text)" };
const listStyle = { margin: "6px 0 0", paddingLeft: 18, display: "grid", gap: 4 };
const approvalGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 };
const labelStyle = { display: "grid", gap: 4, color: "var(--fiscal-soft-text)", fontSize: 12, fontWeight: 600 };
const inputStyle = {
  border: "1px solid var(--fiscal-link-border)",
  borderRadius: 8,
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  padding: "8px 10px",
};
const textareaStyle = {
  ...inputStyle,
  minHeight: 88,
  resize: "vertical",
  fontFamily: "inherit",
};
const checkItemStyle = {
  border: "1px solid var(--fiscal-link-border)",
  borderRadius: 10,
  background: "var(--fiscal-link-bg)",
  padding: "8px 10px",
  display: "grid",
  gap: 4,
};
const historyTableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  minWidth: 760,
  marginTop: 8,
};
const historyThStyle = {
  textAlign: "left",
  borderBottom: "1px solid var(--fiscal-link-border)",
  padding: "8px 10px",
  fontSize: 12,
};
const historyTdStyle = {
  borderBottom: "1px solid var(--fiscal-link-border)",
  padding: "8px 10px",
  fontSize: 12,
  verticalAlign: "top",
};
const smallButtonStyle = {
  padding: "6px 8px",
  borderRadius: 8,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  cursor: "pointer",
  fontWeight: 600,
  fontSize: 12,
};
