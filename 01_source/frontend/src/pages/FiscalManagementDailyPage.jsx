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

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/management-daily v1.0.3";
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
  const [d18Checklist, setD18Checklist] = useState({});
  const [d18P1Rows, setD18P1Rows] = useState(() => createInitialP1RiskRows());

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    loadD11Handoff();
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
    const { checklist, p1Risks } = loadD18CloseoutFromStorage();
    setD18Checklist(checklist);
    setD18P1Rows(p1Risks);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(D18_CLOSEOUT_STORAGE_KEY, JSON.stringify({ checklist: d18Checklist, p1Risks: d18P1Rows }));
    } catch {
      // no-op
    }
  }, [d18Checklist, d18P1Rows]);

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
            filters: d11Handoff?.filters || {},
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
      context: {
        decision_consolidated: decision,
        risk_level: riskLevel,
        readiness_version: String(stubReadiness?.readiness_version || "-"),
      },
    });
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
    const payload = buildAccountingApprovalPayload(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_ACCOUNTING_APPROVAL_${ts}.json`, payload);
    setStatus("Aprovação contábil do dia exportada em JSON.");
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
    try {
      const signedD18 = await buildSignedPayload(buildD18CloseoutPayload(nowIso));
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D18_SPRINT2_CLOSEOUT_${ts}.json`] = strToU8(JSON.stringify(signedD18, null, 2));
    } catch {
      // no-op: closeout D18 é opcional no pacote
    }
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_PACKAGE_${ts}.zip`, zipEntries);
    setStatus("Pacote diário (.zip) com OPS + FISCAL + APPROVAL + D16 + D18 (closeout Sprint 2).");
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
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Abrir ops/health
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Management Daily" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Cockpit diário do departamento contábil/fiscal para decisão, evidência e anexo operacional.</p>
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
                </div>
                <small style={mutedTextStyle}>
                  Este snapshot D11 já entra automaticamente nos payloads JSON/ZIP do handoff contábil diário.
                </small>
              </>
            ) : (
              <small style={mutedTextStyle}>
                Nenhum lote D11 encontrado no navegador. Publique o lote em `ops/fiscal/providers` e clique em "Recarregar lote D11".
              </small>
            )}
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
                Exportar aprovação contábil (JSON)
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
            </div>
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
