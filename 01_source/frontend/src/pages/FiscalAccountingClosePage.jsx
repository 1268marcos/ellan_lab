import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import { fetchAccountingApprovalsCompare, fetchConsolidatedAccountingApprovals } from "../utils/fiscalAccountingApprovalsHistory";
import { appendP01bSignedZipEntries } from "../utils/fiscalP01bDailyPackage";
import { buildD18CloseoutPayload, loadD18CloseoutFromStorage } from "../utils/fiscalSprint2D18Content";
import { appendSprint3P03OptionalSignedZipEntries } from "../utils/fiscalSprint3IncidentRunbook";
import {
  appendSprint4PilotHistoryOptionalSignedZipEntries,
  buildSprint4GoNoGoRegisterSummaryPayload,
  buildSprint4RegressionMatrixPayload,
  loadSprint4MatrixStateRaw,
} from "../utils/fiscalSprint4RegressionMatrix";
import {
  loadSprint2FinanceGateV2State,
  summarizeSprint2FinanceGateV2,
  SPRINT2_FINANCE_GATE_V2_THRESHOLDS,
} from "../utils/fiscalSprint2FinanceGate";
import { loadSprint3PartnerAuditMirrorForDaily } from "../utils/fiscalSprint3PartnerAuditMirror";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/accounting-close v1.2.4-s3-partner-mirror-zip";
const APPROVAL_STORAGE_KEY = "fiscal_management_daily:accounting_approval_v1";
const FISCAL_D11_HANDOFF_KEY = "ellan_ops_fiscal_d11_handoff_v1";
const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";
const GO_NO_GO_GATE_VERSION = "go-no-go-gate-v1";
const GO_NO_GO_MIN_SPRINT4_PCT = Number(import.meta.env.VITE_SPRINT4_MIN_REGRESSION_PCT || 70);

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function toAuditDayStamp(isoString) {
  return String(isoString || "").slice(0, 10).replaceAll("-", "");
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

async function computeSha256Hex(content) {
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(String(content || ""));
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function buildSignedPayload(payload) {
  const payloadJson = JSON.stringify(payload, null, 2);
  return {
    integrity: {
      algorithm: "SHA-256",
      content_sha256: await computeSha256Hex(payloadJson),
    },
    payload,
  };
}

function resolvePartnerForCountry(countryCode) {
  const c = String(countryCode || "").toUpperCase();
  if (c === "BR") return "BR_PROVIDER";
  if (c === "PT") return "PT_PROVIDER";
  return "FG1_STUB_ADAPTER";
}

export default function FiscalAccountingClosePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [readinessPlan, setReadinessPlan] = useState(null);
  const [stubReadiness, setStubReadiness] = useState(null);
  const [countryFilter, setCountryFilter] = useState("ALL");
  const [partnerFilter, setPartnerFilter] = useState("ALL");
  const [periodFilter, setPeriodFilter] = useState("7D");
  const [approvalDraft, setApprovalDraft] = useState(null);
  const [sprint4MatrixSnapshot, setSprint4MatrixSnapshot] = useState(null);

  function refreshSprint4MatrixSnapshot() {
    try {
      const stored = loadSprint4MatrixStateRaw();
      if (!stored) {
        setSprint4MatrixSnapshot(null);
        return;
      }
      const payload = buildSprint4RegressionMatrixPayload(new Date().toISOString(), stored);
      setSprint4MatrixSnapshot(payload);
    } catch {
      setSprint4MatrixSnapshot(null);
    }
  }

  useEffect(() => {
    void loadData();
    try {
      const raw = window.localStorage.getItem(APPROVAL_STORAGE_KEY);
      if (raw) setApprovalDraft(JSON.parse(raw));
    } catch {
      setApprovalDraft(null);
    }
    refreshSprint4MatrixSnapshot();
  }, []);

  const planItems = Array.isArray(readinessPlan?.items) ? readinessPlan.items : [];
  const readinessChecks = Array.isArray(stubReadiness?.checks) ? stubReadiness.checks : [];
  const passedChecks = readinessChecks.filter((check) => String(check?.status || "").toUpperCase() === "PASS").length;
  const failedChecks = Math.max(readinessChecks.length - passedChecks, 0);

  const filteredItems = useMemo(() => {
    return planItems.filter((item) => {
      const country = String(item?.country_code || "").toUpperCase();
      const partner = resolvePartnerForCountry(country);
      if (countryFilter !== "ALL" && country !== countryFilter) return false;
      if (partnerFilter !== "ALL" && partner !== partnerFilter) return false;
      return true;
    });
  }, [planItems, countryFilter, partnerFilter]);

  const maxPending = Math.max(...filteredItems.map((item) => Number(item?.blocking_reasons_count || 0)), 1);
  const topPending = [...filteredItems].sort(
    (a, b) => Number(b?.blocking_reasons_count || 0) - Number(a?.blocking_reasons_count || 0)
  );
  const highRiskCount = filteredItems.filter((item) => Number(item?.blocking_reasons_count || 0) >= 2).length;
  const sprint4Progress = sprint4MatrixSnapshot?.progress || { total: 0, done: 0, pct: 0 };
  const gateDecision = String(stubReadiness?.decision || "NO_GO").toUpperCase();
  const goNoGoReady = gateDecision === "GO" && failedChecks === 0 && sprint4Progress.pct >= GO_NO_GO_MIN_SPRINT4_PCT;
  const goNoGoReasons = [
    gateDecision === "GO" ? null : "decision_not_go",
    failedChecks === 0 ? null : "checks_failed",
    sprint4Progress.pct >= GO_NO_GO_MIN_SPRINT4_PCT ? null : "sprint4_regression_below_threshold",
  ].filter(Boolean);

  async function loadData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido. Configure VITE_INTERNAL_TOKEN.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [planRes, stubRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/readiness-action-plan`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-wave-readiness`, { method: "GET", headers: headersJson() }),
      ]);
      const [planPayload, stubPayload] = await Promise.all([
        planRes.json().catch(() => ({})),
        stubRes.json().catch(() => ({})),
      ]);
      if (!planRes.ok || !stubRes.ok) {
        throw new Error(String(planPayload?.detail || stubPayload?.detail || "Falha ao carregar accounting-close."));
      }
      setReadinessPlan(planPayload || null);
      setStubReadiness(stubPayload || null);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function buildClosePayload(nowIso) {
    return {
      scope: "FISCAL_ACCOUNTING_CLOSE",
      generated_at: nowIso,
      filters: {
        country: countryFilter,
        partner: partnerFilter,
        period: periodFilter,
      },
      close_kpis: {
        decision_consolidated: gateDecision,
        checks_pass: `${passedChecks}/${readinessChecks.length}`,
        checks_failed: failedChecks,
        countries_in_scope: filteredItems.length,
        high_risk_countries: highRiskCount,
      },
      go_no_go_gate: {
        version: GO_NO_GO_GATE_VERSION,
        ready: goNoGoReady,
        reasons: goNoGoReasons,
        thresholds: {
          sprint4_min_regression_pct: GO_NO_GO_MIN_SPRINT4_PCT,
          checks_failed_must_equal: 0,
          decision_must_be: "GO",
        },
        current: {
          decision: gateDecision,
          checks_failed: failedChecks,
          sprint4_regression_pct: sprint4Progress.pct,
        },
      },
      pending_by_country: filteredItems.map((item) => {
        const country = String(item?.country_code || "-").toUpperCase();
        return {
          country_code: country,
          partner: resolvePartnerForCountry(country),
          pending_count: Number(item?.blocking_reasons_count || 0),
          required_env_keys: Array.isArray(item?.required_env_keys) ? item.required_env_keys : [],
          readiness_status: String(item?.status || "-"),
        };
      }),
      accounting_approval_snapshot: {
        owner: String(approvalDraft?.owner || "-"),
        status: String(approvalDraft?.status || "PENDING_REVIEW"),
        timestamp: String(approvalDraft?.timestamp || "-"),
      },
      sprint4_regression_matrix_snapshot: sprint4MatrixSnapshot || {
        scope: "SPRINT4_REGRESSION_MATRIX",
        status: "NOT_AVAILABLE",
      },
    };
  }

  async function exportJson() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signed = await buildSignedPayload(buildClosePayload(nowIso));
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_ACCOUNTING_CLOSE_${ts}.json`, signed);
    setStatus("Payload JSON de accounting-close exportado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportZip() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const closePayload = buildClosePayload(nowIso);
    const signedClose = await buildSignedPayload(closePayload);
    const signedGateSummary = await buildSignedPayload({
      scope: "FISCAL_GO_NO_GO_GATE_SUMMARY",
      generated_at: nowIso,
      source: "fiscal/accounting-close",
      gate: closePayload.go_no_go_gate,
      executive_snapshot: {
        decision_consolidated: closePayload.close_kpis.decision_consolidated,
        checks_failed: closePayload.close_kpis.checks_failed,
        sprint4_regression_pct: closePayload.go_no_go_gate?.current?.sprint4_regression_pct,
      },
    });
    const signedApproval = await buildSignedPayload({
      scope: "FISCAL_ACCOUNTING_APPROVAL_SNAPSHOT",
      generated_at: nowIso,
      approval: {
        owner: String(approvalDraft?.owner || "-"),
        status: String(approvalDraft?.status || "PENDING_REVIEW"),
        notes: String(approvalDraft?.notes || "-"),
        timestamp: String(approvalDraft?.timestamp || "-"),
      },
    });
    const zipEntries = {
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_ACCOUNTING_CLOSE_${ts}.json`]: strToU8(JSON.stringify(signedClose, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_GO_NO_GO_GATE_${ts}.json`]: strToU8(JSON.stringify(signedGateSummary, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_ACCOUNTING_APPROVAL_${ts}.json`]: strToU8(JSON.stringify(signedApproval, null, 2)),
    };
    if (INTERNAL_TOKEN) {
      try {
        const end = new Date();
        const start = new Date(end.getTime() - 30 * 86400000);
        const date_from = start.toISOString().slice(0, 10);
        const date_to = end.toISOString().slice(0, 10);
        const historyBundle = await fetchConsolidatedAccountingApprovals({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          filters: { owner: "", status: "", date_from, date_to },
        });
        const signedHistory = await buildSignedPayload({
          scope: "SPRINT2_D16_EXEC_ACCOUNTING_APPROVALS_HISTORY",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          window_days: 30,
          filters: historyBundle.filters,
          total: historyBundle.total,
          items: historyBundle.items,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_EXEC_APPROVALS_HISTORY_${ts}.json`] = strToU8(JSON.stringify(signedHistory, null, 2));
        try {
          const comparePayload = await fetchAccountingApprovalsCompare({
            billingBase: BILLING_BASE,
            getHeaders: headersJson,
          });
          const signedDiff = await buildSignedPayload({
            scope: "SPRINT2_D16_EXEC_ACCOUNTING_APPROVALS_DIFF",
            generated_at: nowIso,
            source: "fiscal/accounting-close",
            compare: comparePayload,
          });
          zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_EXEC_APPROVALS_DIFF_${ts}.json`] = strToU8(JSON.stringify(signedDiff, null, 2));
        } catch {
          const signedDiffErr = await buildSignedPayload({
            scope: "SPRINT2_D16_EXEC_ACCOUNTING_APPROVALS_DIFF",
            generated_at: nowIso,
            source: "fiscal/accounting-close",
            error: "Histórico executivo D16 anexado, mas diff compare falhou.",
          });
          zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_EXEC_APPROVALS_DIFF_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedDiffErr, null, 2));
        }
      } catch {
        const signedErr = await buildSignedPayload({
          scope: "SPRINT2_D16_EXEC_ACCOUNTING_ATTACH",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          error: "Não foi possível anexar histórico D16 ao ZIP executivo (verifique token e billing service).",
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D16_EXEC_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
      }
      try {
        let d11Snapshot = null;
        try {
          const rawD11 = window.localStorage.getItem(FISCAL_D11_HANDOFF_KEY);
          if (rawD11) {
            const parsed = JSON.parse(rawD11);
            d11Snapshot = parsed && typeof parsed === "object" ? parsed : null;
          }
        } catch {
          d11Snapshot = null;
        }
        await appendP01bSignedZipEntries({
          billingBase: BILLING_BASE,
          getHeaders: headersJson,
          buildSignedPayload,
          strToU8,
          fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
          ts,
          nowIso,
          d11Handoff: d11Snapshot,
          source: "fiscal/accounting-close",
          zipEntries,
        });
      } catch (err) {
        const signedErr = await buildSignedPayload({
          scope: "SPRINT3_P0_1B_E2E_ATTACH_ERROR",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          error: String(err?.message || err),
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_P0_1B_EXEC_E2E_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
      }
    }
    try {
      const stored = loadD18CloseoutFromStorage();
      const decision = String(stubReadiness?.decision || "NO_GO").toUpperCase();
      const riskLevel = decision === "GO" ? "LOW" : highRiskCount >= 2 ? "HIGH" : "MEDIUM";
      const d18Payload = buildD18CloseoutPayload({
        generatedAt: nowIso,
        checklistById: stored.checklist,
        p1Rows: stored.p1Risks,
        source: "fiscal/accounting-close",
        certification: stored.certification,
        context: {
          decision_consolidated: decision,
          risk_level: riskLevel,
          readiness_version: String(stubReadiness?.readiness_version || "-"),
        },
      });
      const signedD18 = await buildSignedPayload(d18Payload);
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D18_EXEC_SPRINT2_CLOSEOUT_${ts}.json`] = strToU8(JSON.stringify(signedD18, null, 2));
    } catch {
      try {
        const signedD18Err = await buildSignedPayload({
          scope: "SPRINT2_D18_EXEC_FINANCE_CLOSEOUT",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          error: "Não foi possível montar o closeout D18 para o ZIP executivo.",
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_D18_EXEC_CLOSEOUT_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedD18Err, null, 2));
      } catch {
        // no-op
      }
    }
    try {
      const storedMatrix = loadSprint4MatrixStateRaw();
      const matrixPayload = buildSprint4RegressionMatrixPayload(nowIso, storedMatrix);
      const signedMatrix = await buildSignedPayload(matrixPayload);
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_EXEC_REGRESSION_MATRIX_${ts}.json`] = strToU8(JSON.stringify(signedMatrix, null, 2));
      const signedSprint4GoNoGo = await buildSignedPayload(
        buildSprint4GoNoGoRegisterSummaryPayload(nowIso, storedMatrix && typeof storedMatrix === "object" ? storedMatrix : {})
      );
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_GO_NO_GO_REGISTER_${ts}.json`] = strToU8(JSON.stringify(signedSprint4GoNoGo, null, 2));
    } catch {
      try {
        const signedMatrixErr = await buildSignedPayload({
          scope: "SPRINT4_REGRESSION_MATRIX_ATTACH",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          error: "Não foi possível anexar a matriz Sprint 4 ao ZIP executivo (estado local inválido ou indisponível).",
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_EXEC_REGRESSION_MATRIX_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedMatrixErr, null, 2));
      } catch {
        // no-op
      }
    }
    try {
      await appendSprint4PilotHistoryOptionalSignedZipEntries({
        buildSignedPayload,
        strToU8,
        fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
        ts,
        nowIso,
        zipEntries,
        source: "fiscal/accounting-close",
      });
    } catch (err) {
      const signedErr = await buildSignedPayload({
        scope: "SPRINT4_PILOT_EXEC_ATTACH_ERROR",
        generated_at: nowIso,
        source: "fiscal/accounting-close",
        error: String(err?.message || err),
      });
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_PILOT_EXEC_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    }
    try {
      await appendSprint3P03OptionalSignedZipEntries({
        buildSignedPayload,
        strToU8,
        fileBasePrefix: `${DAILY_AUDIT_PREFIX}_${day}`,
        ts,
        nowIso,
        zipEntries,
        source: "fiscal/accounting-close",
      });
    } catch (err) {
      const signedErr = await buildSignedPayload({
        scope: "SPRINT3_P03_EXEC_ATTACH_ERROR",
        generated_at: nowIso,
        source: "fiscal/accounting-close",
        error: String(err?.message || err),
      });
      zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_P03_EXEC_ATTACH_ERROR_${ts}.json`] = strToU8(JSON.stringify(signedErr, null, 2));
    }
    try {
      const rawGate = loadSprint2FinanceGateV2State();
      const mirror = summarizeSprint2FinanceGateV2(rawGate);
      if (mirror) {
        const signedGateMirror = await buildSignedPayload({
          scope: "SPRINT2_GATE_V2_MIRROR_ATTACH",
          generated_at: nowIso,
          source: "fiscal/accounting-close",
          committee_reference: "2026-05-01",
          thresholds: SPRINT2_FINANCE_GATE_V2_THRESHOLDS,
          mirror,
          raw_local_storage: rawGate,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT2_GATE_V2_MIRROR_EXEC_${ts}.json`] = strToU8(JSON.stringify(signedGateMirror, null, 2));
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
          source: "fiscal/accounting-close",
          saved_snapshot: rawPartner,
        });
        zipEntries[`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_PARTNER_AUDIT_MIRROR_EXEC_${ts}.json`] = strToU8(
          JSON.stringify(signedPartnerMirror, null, 2),
        );
      }
    } catch {
      // espelho Sprint 3 opcional
    }
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_ACCOUNTING_CLOSE_PACKAGE_${ts}.zip`, zipEntries);
    setStatus(
      "Pacote ZIP exportado: close + gate + aprovação + D16 + P0-1b (com token) + D18 + matriz Sprint 4 + resumo Go/No-Go Sprint 4 + pilotos + carimbo P0-3 + espelhos gate v2 e Sprint 3 partner-audit (se gravados) quando houver no browser.",
    );
    window.setTimeout(() => setStatus(""), 2200);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>Abrir fiscal/management-daily</Link>
          <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>Abrir fiscal/sprint2-finance-gate</Link>
          <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>Abrir fiscal/sprint3-partner-audit</Link>
          <Link to="/fiscal/readiness-execution" style={shortcutLinkStyle}>Abrir fiscal/readiness-execution</Link>
          <Link to="/fiscal/sprint4-regression-matrix" style={shortcutLinkStyle}>Abrir fiscal/sprint4-regression-matrix</Link>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>Abrir Swagger FISCAL</a>
        </div>
        <OpsPageTitleHeader title="FISCAL - Accounting Close" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Cockpit de fechamento contábil/fiscal com pendências por país, risco e evidências exportáveis.</p>

        <div style={filtersRowStyle}>
          <label style={labelStyle}>País
            <select value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="US">US</option>
              <option value="AU">AU</option>
              <option value="PL">PL</option>
              <option value="CA">CA</option>
              <option value="FR">FR</option>
            </select>
          </label>
          <label style={labelStyle}>Parceiro
            <select value={partnerFilter} onChange={(e) => setPartnerFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="FG1_STUB_ADAPTER">FG1_STUB_ADAPTER</option>
              <option value="BR_PROVIDER">BR_PROVIDER</option>
              <option value="PT_PROVIDER">PT_PROVIDER</option>
            </select>
          </label>
          <label style={labelStyle}>Período
            <select value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value)} style={inputStyle}>
              <option value="24H">24H</option>
              <option value="7D">7D</option>
              <option value="30D">30D</option>
            </select>
          </label>
        </div>

        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadData()} style={buttonStyle} disabled={loading}>{loading ? "Atualizando..." : "Atualizar"}</button>
          <button type="button" onClick={() => refreshSprint4MatrixSnapshot()} style={buttonStyle} disabled={loading}>Recarregar matriz Sprint 4</button>
          <button type="button" onClick={() => void exportJson()} style={buttonStyle} disabled={loading}>Exportar JSON</button>
          <button type="button" onClick={() => void exportZip()} style={buttonStyle} disabled={loading}>Exportar ZIP auditável</button>
        </div>
        <small style={mutedTextStyle}>
          O ZIP alinha ao handoff único do sprint: com token e dados no browser, inclui P0-1b (E2E + fatia parceiro + D11), matriz Sprint 4 (EXEC), resumo assinado <code>SPRINT4_GO_NO_GO_REGISTER</code> (decisão + UAT KIOSK + % matriz), histórico de pilotos e carimbo P0-3 — alinhado ao pacote diário em management/ops.
        </small>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error ? (
          <>
            <div style={gridStyle}>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Fechamento consolidado</h3>
                <div style={kpiRowStyle}>
                  <span style={badgeStyle(String(stubReadiness?.decision || "NO_GO"))}>Decisão: {String(stubReadiness?.decision || "NO_GO").toUpperCase()}</span>
                  <span style={chipStyle}>Checks: {passedChecks}/{readinessChecks.length}</span>
                  <span style={chipStyle}>Falhas: {failedChecks}</span>
                  <span style={gateBadgeStyle(goNoGoReady)}>Go/No-Go ready: {goNoGoReady ? "SIM" : "NÃO"}</span>
                </div>
                <small style={mutedTextStyle}>
                  Gate {GO_NO_GO_GATE_VERSION}: exige `decision=GO`, `checks_failed=0` e{" "}
                  {`sprint4_pct >= ${GO_NO_GO_MIN_SPRINT4_PCT}`}.
                </small>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Risco de fechamento</h3>
                <div style={kpiRowStyle}>
                  <span style={chipStyle}>Países no filtro: {filteredItems.length}</span>
                  <span style={chipStyle}>Alto risco ({">=2"} pendências): {highRiskCount}</span>
                  <span style={chipStyle}>Aprovação: {String(approvalDraft?.status || "PENDING_REVIEW")}</span>
                </div>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Sprint 4 — Matriz de regressão</h3>
                <div style={kpiRowStyle}>
                  <span style={chipStyle}>Progresso: {sprint4Progress.done}/{sprint4Progress.total}</span>
                  <span style={chipStyle}>Concluído: {sprint4Progress.pct}%</span>
                  <span style={chipStyle}>Owner: {String(sprint4MatrixSnapshot?.owner || "-")}</span>
                </div>
                <small style={mutedTextStyle}>
                  Última atualização local: {String(sprint4MatrixSnapshot?.storage?.updated_at || "não disponível")}.
                </small>
              </section>
            </div>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Pendências por país (gráfico operacional)</h3>
              <div style={{ display: "grid", gap: 8 }}>
                {topPending.map((item) => {
                  const pending = Number(item?.blocking_reasons_count || 0);
                  const pct = Math.max(Math.min((pending / maxPending) * 100, 100), 0);
                  const country = String(item?.country_code || "-").toUpperCase();
                  return (
                    <article key={`close-${country}`} style={barRowStyle}>
                      <strong style={{ width: 60 }}>{country}</strong>
                      <small style={{ width: 140 }}>{resolvePartnerForCountry(country)}</small>
                      <div style={barTrackStyle}><div style={{ ...barFillStyle, width: `${pct}%` }} /></div>
                      <small style={{ minWidth: 36, textAlign: "right" }}>{pending}</small>
                    </article>
                  );
                })}
                {topPending.length === 0 ? <small style={mutedTextStyle}>Sem pendências para os filtros atuais.</small> : null}
              </div>
            </section>
          </>
        ) : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10 };
const shortcutLinkStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", textDecoration: "none", fontWeight: 700, fontSize: 13 };
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const filtersRowStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginTop: 10 };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, fontWeight: 700, color: "var(--fiscal-soft-text)" };
const inputStyle = { borderRadius: 8, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", padding: "8px 10px", fontSize: 13 };
const toolbarStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const buttonStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", cursor: "pointer", fontWeight: 700 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const gridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" };
const boxStyle = { marginTop: 10, border: "1px solid var(--fiscal-box-border)", borderRadius: 12, background: "var(--fiscal-box-bg)", padding: 12 };
const boxTitleStyle = { margin: "0 0 8px", fontSize: 14 };
const kpiRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const chipStyle = { display: "inline-flex", padding: "4px 10px", borderRadius: 999, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", fontSize: 12, fontWeight: 700 };
const badgeStyle = (status) => {
  const ok = String(status || "").toUpperCase() === "GO";
  return {
    ...chipStyle,
    border: ok ? "1px solid rgba(34,197,94,0.65)" : "1px solid rgba(239,68,68,0.65)",
    background: ok ? "rgba(34,197,94,0.18)" : "rgba(239,68,68,0.18)",
    color: ok ? "#bbf7d0" : "#fecaca",
  };
};
const gateBadgeStyle = (ready) => ({
  ...chipStyle,
  border: ready ? "1px solid rgba(34,197,94,0.65)" : "1px solid rgba(239,68,68,0.65)",
  background: ready ? "rgba(34,197,94,0.18)" : "rgba(239,68,68,0.18)",
  color: ready ? "#bbf7d0" : "#fecaca",
});
const barRowStyle = { display: "flex", gap: 8, alignItems: "center" };
const barTrackStyle = { flex: 1, height: 10, borderRadius: 999, background: "rgba(148,163,184,0.25)", overflow: "hidden" };
const barFillStyle = { height: "100%", borderRadius: 999, background: "linear-gradient(90deg, rgba(99,102,241,0.85), rgba(239,68,68,0.85))" };
