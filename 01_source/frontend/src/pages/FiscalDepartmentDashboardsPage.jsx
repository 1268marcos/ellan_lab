import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/department-dashboards v1.0.0";
const APPROVAL_STORAGE_KEY = "fiscal_management_daily:accounting_approval_v1";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function resolvePartnerDecision(payload) {
  const candidate = String(
    payload?.final_decision || payload?.decision || payload?.go_no_go || payload?.global_decision || payload?.status || ""
  ).toUpperCase();
  if (candidate.includes("GO")) return "GO";
  if (candidate.includes("NO")) return "NO_GO";
  return "UNKNOWN";
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

export default function FiscalDepartmentDashboardsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [stubReadiness, setStubReadiness] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [partnerBr, setPartnerBr] = useState(null);
  const [partnerPt, setPartnerPt] = useState(null);
  const [approvalDraft, setApprovalDraft] = useState(null);

  useEffect(() => {
    void loadData();
    try {
      const raw = window.localStorage.getItem(APPROVAL_STORAGE_KEY);
      if (raw) setApprovalDraft(JSON.parse(raw));
    } catch {
      setApprovalDraft(null);
    }
  }, []);

  const readinessChecks = Array.isArray(stubReadiness?.checks) ? stubReadiness.checks : [];
  const passedChecks = readinessChecks.filter((check) => String(check?.status || "").toUpperCase() === "PASS").length;
  const failedChecks = Math.max(readinessChecks.length - passedChecks, 0);
  const decision = String(stubReadiness?.decision || "NO_GO").toUpperCase();
  const actionPlanItems = Array.isArray(actionPlan?.items) ? actionPlan.items : [];
  const sortedPending = [...actionPlanItems].sort(
    (a, b) => Number(b?.blocking_reasons_count || 0) - Number(a?.blocking_reasons_count || 0)
  );
  const maxPending = Math.max(...sortedPending.map((item) => Number(item?.blocking_reasons_count || 0)), 1);
  const topPending = sortedPending.slice(0, 6);

  async function loadData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido. Configure VITE_INTERNAL_TOKEN.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [readinessRes, actionPlanRes, brRes, ptRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-wave-readiness`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/readiness-action-plan`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/providers/br-go-no-go?run_connectivity=false`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/providers/pt-go-no-go?run_connectivity=false`, { method: "GET", headers: headersJson() }),
      ]);
      const [readinessPayload, actionPlanPayload, brPayload, ptPayload] = await Promise.all([
        readinessRes.json().catch(() => ({})),
        actionPlanRes.json().catch(() => ({})),
        brRes.json().catch(() => ({})),
        ptRes.json().catch(() => ({})),
      ]);
      if (!readinessRes.ok || !actionPlanRes.ok || !brRes.ok || !ptRes.ok) {
        throw new Error(
          String(
            readinessPayload?.detail || actionPlanPayload?.detail || brPayload?.detail || ptPayload?.detail || "Falha ao carregar dashboard departamental."
          )
        );
      }
      setStubReadiness(readinessPayload || null);
      setActionPlan(actionPlanPayload || null);
      setPartnerBr(brPayload || null);
      setPartnerPt(ptPayload || null);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function exportDashboardSnapshot() {
    const nowIso = new Date().toISOString();
    const payload = {
      scope: "FISCAL_DEPARTMENT_DASHBOARD_SNAPSHOT",
      generated_at: nowIso,
      ellan_fiscal: {
        decision_consolidated: decision,
        checks_pass: `${passedChecks}/${readinessChecks.length}`,
        checks_failed: failedChecks,
        countries_not_ready: Number(stubReadiness?.countries_not_ready || 0),
      },
      ellan_accounting: {
        owner: String(approvalDraft?.owner || "-"),
        status: String(approvalDraft?.status || "PENDING_REVIEW"),
        timestamp: String(approvalDraft?.timestamp || "-"),
      },
      partners: {
        br_decision: resolvePartnerDecision(partnerBr),
        pt_decision: resolvePartnerDecision(partnerPt),
      },
      top_pending_countries: topPending.map((item) => ({
        country_code: String(item?.country_code || "-"),
        pending: Number(item?.blocking_reasons_count || 0),
      })),
    };
    const ts = nowIso.replace(/[:.]/g, "-");
    downloadJsonFile(`ELLAN_FISCAL_DASHBOARD_SNAPSHOT_${ts}.json`, payload);
    setStatus("Snapshot do dashboard departamental exportado em JSON.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>
            Abrir fiscal/management-daily
          </Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Abrir ops/health
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Department Dashboards" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Dashboards práticos para Fiscal e Contábil (ELLAN LAB e parceiros) com foco de decisão diária.</p>
        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadData()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button type="button" onClick={() => exportDashboardSnapshot()} style={buttonStyle} disabled={!stubReadiness}>
            Exportar snapshot dashboard (JSON)
          </button>
        </div>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error ? (
          <div style={gridStyle}>
            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>ELLAN LAB - Fiscal Operacional</h3>
              <div style={kpiRowStyle}>
                <span style={badgeStyle(decision)}>Decisão: {decision}</span>
                <span style={chipStyle}>{`${passedChecks}/${readinessChecks.length} checks PASS`}</span>
                <span style={chipStyle}>Falhas: {failedChecks}</span>
              </div>
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>ELLAN LAB - Contábil</h3>
              <div style={kpiRowStyle}>
                <span style={chipStyle}>Responsável: {String(approvalDraft?.owner || "-")}</span>
                <span style={chipStyle}>Status: {String(approvalDraft?.status || "PENDING_REVIEW")}</span>
                <span style={chipStyle}>Timestamp: {String(approvalDraft?.timestamp || "-")}</span>
              </div>
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Parceiros - BR/PT</h3>
              <div style={kpiRowStyle}>
                <span style={badgeStyle(resolvePartnerDecision(partnerBr))}>BR: {resolvePartnerDecision(partnerBr)}</span>
                <span style={badgeStyle(resolvePartnerDecision(partnerPt))}>PT: {resolvePartnerDecision(partnerPt)}</span>
              </div>
            </section>
          </div>
        ) : null}

        {!error && topPending.length > 0 ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>Top pendências por país (ação diária)</h3>
            <div style={{ display: "grid", gap: 8 }}>
              {topPending.map((item) => {
                const value = Number(item?.blocking_reasons_count || 0);
                const pct = Math.max(Math.min((value / maxPending) * 100, 100), 0);
                return (
                  <article key={`pending-${item.country_code}`} style={barRowStyle}>
                    <strong style={{ width: 48 }}>{String(item?.country_code || "-")}</strong>
                    <div style={barTrackStyle}>
                      <div style={{ ...barFillStyle, width: `${pct}%` }} />
                    </div>
                    <small style={{ minWidth: 36, textAlign: "right" }}>{value}</small>
                  </article>
                );
              })}
            </div>
          </section>
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
const gridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" };
const boxStyle = { border: "1px solid var(--fiscal-box-border)", borderRadius: 12, background: "var(--fiscal-box-bg)", padding: 12 };
const boxTitleStyle = { margin: "0 0 8px", fontSize: 14 };
const kpiRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
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
  const normalized = String(status || "").toUpperCase();
  if (normalized === "GO" || normalized === "APPROVED") {
    return {
      ...chipStyle,
      border: "1px solid rgba(34,197,94,0.65)",
      background: "rgba(34,197,94,0.18)",
      color: "#bbf7d0",
    };
  }
  return {
    ...chipStyle,
    border: "1px solid rgba(239,68,68,0.65)",
    background: "rgba(239,68,68,0.18)",
    color: "#fecaca",
  };
};
const barRowStyle = { display: "flex", gap: 8, alignItems: "center" };
const barTrackStyle = { flex: 1, height: 10, borderRadius: 999, background: "rgba(148,163,184,0.25)", overflow: "hidden" };
const barFillStyle = { height: "100%", borderRadius: 999, background: "linear-gradient(90deg, rgba(239,68,68,0.85), rgba(245,158,11,0.85))" };
