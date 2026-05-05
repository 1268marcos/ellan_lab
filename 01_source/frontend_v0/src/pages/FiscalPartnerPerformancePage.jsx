
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/partner-performance v1.0.0";
const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";

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

function getGoNoGoStats(payload) {
  const checks = Array.isArray(payload?.checks) ? payload.checks : [];
  const passed = checks.filter((check) => Boolean(check?.ok)).length;
  return {
    decision: String(payload?.go_no_go || "NO_GO").toUpperCase(),
    checks,
    passed,
    failed: Math.max(checks.length - passed, 0),
    checkedAt: String(payload?.checked_at || "-"),
  };
}

export default function FiscalPartnerPerformancePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [providers, setProviders] = useState([]);
  const [brGoNoGo, setBrGoNoGo] = useState(null);
  const [ptGoNoGo, setPtGoNoGo] = useState(null);
  const [countryFilter, setCountryFilter] = useState("ALL");
  const [partnerFilter, setPartnerFilter] = useState("ALL");
  const [periodFilter, setPeriodFilter] = useState("7D");

  useEffect(() => {
    void loadData();
  }, []);

  const partnerOptions = useMemo(() => {
    const set = new Set(["ALL"]);
    for (const row of providers) {
      const name = String(row?.provider_name || "").trim();
      if (name) set.add(name);
    }
    return Array.from(set);
  }, [providers]);

  const filteredRows = useMemo(() => {
    return providers.filter((row) => {
      if (countryFilter !== "ALL" && String(row?.country || "").toUpperCase() !== countryFilter) return false;
      if (partnerFilter !== "ALL" && String(row?.provider_name || "") !== partnerFilter) return false;
      return true;
    });
  }, [providers, countryFilter, partnerFilter]);

  const statusCounts = useMemo(() => {
    const counts = { OK: 0, ERROR: 0, NEVER_TESTED: 0, OTHER: 0 };
    for (const row of filteredRows) {
      const s = String(row?.last_status || "").toUpperCase();
      if (s === "OK") counts.OK += 1;
      else if (s === "ERROR") counts.ERROR += 1;
      else if (s === "NEVER_TESTED") counts.NEVER_TESTED += 1;
      else counts.OTHER += 1;
    }
    return counts;
  }, [filteredRows]);

  const brStats = getGoNoGoStats(brGoNoGo);
  const ptStats = getGoNoGoStats(ptGoNoGo);
  const maxLatency = Math.max(...filteredRows.map((row) => Number(row?.last_latency_ms || 0)), 1);
  const maxStatusCount = Math.max(...Object.values(statusCounts).map((v) => Number(v || 0)), 1);

  async function loadData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido. Configure VITE_INTERNAL_TOKEN.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [statusRes, brRes, ptRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/providers/status`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/providers/br-go-no-go?run_connectivity=false`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/providers/pt-go-no-go?run_connectivity=false`, { method: "GET", headers: headersJson() }),
      ]);
      const [statusPayload, brPayload, ptPayload] = await Promise.all([
        statusRes.json().catch(() => ({})),
        brRes.json().catch(() => ({})),
        ptRes.json().catch(() => ({})),
      ]);
      if (!statusRes.ok || !brRes.ok || !ptRes.ok) {
        throw new Error(String(statusPayload?.detail || brPayload?.detail || ptPayload?.detail || "Falha ao carregar partner performance."));
      }
      setProviders(Array.isArray(statusPayload?.items) ? statusPayload.items : []);
      setBrGoNoGo(brPayload || null);
      setPtGoNoGo(ptPayload || null);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function buildPayload(nowIso) {
    return {
      scope: "FISCAL_PARTNER_PERFORMANCE",
      generated_at: nowIso,
      filters: {
        country: countryFilter,
        partner: partnerFilter,
        period: periodFilter,
      },
      kpis: {
        monitored_rows: filteredRows.length,
        status_distribution: statusCounts,
        br_go_no_go: brStats.decision,
        pt_go_no_go: ptStats.decision,
      },
      providers: filteredRows.map((row) => ({
        country: String(row?.country || "-"),
        partner: String(row?.provider_name || "-"),
        mode: String(row?.mode || "-"),
        enabled: Boolean(row?.enabled),
        last_status: String(row?.last_status || "-"),
        last_latency_ms: row?.last_latency_ms == null ? null : Number(row.last_latency_ms),
        checked_at: String(row?.checked_at || "-"),
      })),
      checklist_summary: [
        { country: "BR", pass: `${brStats.passed}/${brStats.checks.length}`, decision: brStats.decision, checked_at: brStats.checkedAt },
        { country: "PT", pass: `${ptStats.passed}/${ptStats.checks.length}`, decision: ptStats.decision, checked_at: ptStats.checkedAt },
      ],
    };
  }

  async function exportJson() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signed = await buildSignedPayload(buildPayload(nowIso));
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_PARTNER_PERFORMANCE_${ts}.json`, signed);
    setStatus("Payload JSON de partner-performance exportado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportZip() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signedPerformance = await buildSignedPayload(buildPayload(nowIso));
    const signedRaw = await buildSignedPayload({
      scope: "FISCAL_PARTNER_PERFORMANCE_RAW",
      generated_at: nowIso,
      raw: {
        br_go_no_go: brGoNoGo,
        pt_go_no_go: ptGoNoGo,
        providers_status: providers,
      },
    });
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_PARTNER_PERFORMANCE_PACKAGE_${ts}.zip`, {
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_PARTNER_PERFORMANCE_${ts}.json`]: strToU8(JSON.stringify(signedPerformance, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_FISCAL_PARTNER_PERFORMANCE_RAW_${ts}.json`]: strToU8(JSON.stringify(signedRaw, null, 2)),
    });
    setStatus("Pacote ZIP de partner-performance exportado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/ops/fiscal/providers" style={shortcutLinkStyle}>Abrir ops/fiscal/providers</Link>
          <Link to="/fiscal/department-dashboards" style={shortcutLinkStyle}>Abrir fiscal/department-dashboards</Link>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>Abrir Swagger FISCAL</a>
        </div>
        <OpsPageTitleHeader title="FISCAL - Partner Performance" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Gráficos operacionais reais de performance de parceiros (BR/PT) e status de conectividade por país.</p>

        <div style={filtersRowStyle}>
          <label style={labelStyle}>País
            <select value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="BR">BR</option>
              <option value="PT">PT</option>
            </select>
          </label>
          <label style={labelStyle}>Parceiro
            <select value={partnerFilter} onChange={(e) => setPartnerFilter(e.target.value)} style={inputStyle}>
              {partnerOptions.map((item) => <option key={item} value={item}>{item}</option>)}
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
          <button type="button" onClick={() => void exportJson()} style={buttonStyle} disabled={loading}>Exportar JSON</button>
          <button type="button" onClick={() => void exportZip()} style={buttonStyle} disabled={loading}>Exportar ZIP auditável</button>
        </div>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error ? (
          <>
            <div style={gridStyle}>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Checklist GO/NO_GO por parceiro</h3>
                <div style={kpiRowStyle}>
                  <span style={badgeStyle(brStats.decision)}>BR: {brStats.decision} ({brStats.passed}/{brStats.checks.length})</span>
                  <span style={badgeStyle(ptStats.decision)}>PT: {ptStats.decision} ({ptStats.passed}/{ptStats.checks.length})</span>
                </div>
              </section>
              <section style={boxStyle}>
                <h3 style={boxTitleStyle}>Status monitorados</h3>
                <div style={kpiRowStyle}>
                  <span style={chipStyle}>Rows: {filteredRows.length}</span>
                  <span style={chipStyle}>OK: {statusCounts.OK}</span>
                  <span style={chipStyle}>ERROR: {statusCounts.ERROR}</span>
                  <span style={chipStyle}>NEVER_TESTED: {statusCounts.NEVER_TESTED}</span>
                </div>
              </section>
            </div>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Latência por país/parceiro (ms)</h3>
              <div style={{ display: "grid", gap: 8 }}>
                {filteredRows.map((row, idx) => {
                  const latency = Number(row?.last_latency_ms || 0);
                  const pct = Math.max(Math.min((latency / maxLatency) * 100, 100), 0);
                  return (
                    <article key={`${row?.country || "X"}-${idx}`} style={barRowStyle}>
                      <strong style={{ width: 120 }}>{String(row?.country || "-")} / {String(row?.provider_name || "-")}</strong>
                      <div style={barTrackStyle}><div style={{ ...barFillStyle, width: `${pct}%` }} /></div>
                      <small style={{ minWidth: 60, textAlign: "right" }}>{latency} ms</small>
                    </article>
                  );
                })}
                {filteredRows.length === 0 ? <small style={mutedTextStyle}>Sem dados para os filtros atuais.</small> : null}
              </div>
            </section>

            <section style={boxStyle}>
              <h3 style={boxTitleStyle}>Distribuição de status operacionais</h3>
              <div style={{ display: "grid", gap: 8 }}>
                {Object.entries(statusCounts).map(([label, value]) => {
                  const pct = Math.max(Math.min((Number(value || 0) / maxStatusCount) * 100, 100), 0);
                  return (
                    <article key={label} style={barRowStyle}>
                      <strong style={{ width: 120 }}>{label}</strong>
                      <div style={barTrackStyle}><div style={{ ...barFillStyleSecondary, width: `${pct}%` }} /></div>
                      <small style={{ minWidth: 40, textAlign: "right" }}>{value}</small>
                    </article>
                  );
                })}
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
const barRowStyle = { display: "flex", gap: 8, alignItems: "center" };
const barTrackStyle = { flex: 1, height: 10, borderRadius: 999, background: "rgba(148,163,184,0.25)", overflow: "hidden" };
const barFillStyle = { height: "100%", borderRadius: 999, background: "linear-gradient(90deg, rgba(59,130,246,0.85), rgba(16,185,129,0.85))" };
const barFillStyleSecondary = { height: "100%", borderRadius: 999, background: "linear-gradient(90deg, rgba(245,158,11,0.85), rgba(239,68,68,0.85))" };

