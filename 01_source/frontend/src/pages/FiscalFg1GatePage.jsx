import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/fg1-gate v1.5.0";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

export default function FiscalFg1GatePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copyLatestStatus, setCopyLatestStatus] = useState("");
  const [coverageGate, setCoverageGate] = useState(null);
  const [readinessGate, setReadinessGate] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);

  async function loadGate() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [coverageResponse, readinessResponse, actionPlanResponse] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/coverage-gate`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/readiness-gate`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/readiness-action-plan`, { method: "GET", headers: headersJson() }),
      ]);
      const [coveragePayload, readinessPayload, actionPlanPayload] = await Promise.all([
        coverageResponse.json().catch(() => ({})),
        readinessResponse.json().catch(() => ({})),
        actionPlanResponse.json().catch(() => ({})),
      ]);
      if (!coverageResponse.ok || !readinessResponse.ok || !actionPlanResponse.ok) {
        throw new Error(
          String(
            coveragePayload?.detail ||
              readinessPayload?.detail ||
              actionPlanPayload?.detail ||
              "Falha ao carregar gates FG-1 (coverage/readiness/action-plan)."
          )
        );
      }
      setCoverageGate(coveragePayload || null);
      setReadinessGate(readinessPayload || null);
      setActionPlan(actionPlanPayload || null);
    } catch (err) {
      const raw = String(err?.message || err);
      if (raw.toLowerCase().includes("failed to fetch")) {
        setError(`Falha de rede/CORS ao acessar ${BILLING_BASE}. Verifique VITE_BILLING_FISCAL_BASE_URL e se o backend está no ar.`);
      } else {
        setError(raw);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadGate();
  }, []);

  const coverageCountries = Array.isArray(coverageGate?.countries) ? coverageGate.countries : [];
  const readinessCountries = Array.isArray(readinessGate?.countries) ? readinessGate.countries : [];
  const actionPlanItems = Array.isArray(actionPlan?.items) ? actionPlan.items : [];
  const finalDecisionRows = buildFinalDecisionRows(coverageCountries, readinessCountries, actionPlanItems);
  const finalGlobalDecision = finalDecisionRows.every((row) => row.finalDecision === "GO") ? "GO" : "NO_GO";
  const countriesReady = finalDecisionRows.filter((row) => row.finalDecision === "GO").length;
  const countriesBlocked = finalDecisionRows.filter((row) => row.finalDecision !== "GO").length;
  const consolidatedDecision =
    coverageGate?.decision === "GO" && readinessGate?.decision === "GO"
      ? "GO"
      : coverageGate || readinessGate
        ? "NO_GO"
        : "";
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
          <Link to="/fiscal/countries" style={shortcutLinkStyle}>
            Abrir fiscal/countries
          </Link>
        </div>

        <OpsPageTitleHeader title="FISCAL - FG-1 Gate (Coverage + Readiness)" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Gate macro da onda FG-1 para decisão objetiva GO/NO_GO com cobertura canônica e prontidão regulatória/operacional.
        </p>

        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadGate()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar gate"}
          </button>
          <button
            type="button"
            onClick={() => exportFinalDecisionJson(finalDecisionRows, finalGlobalDecision)}
            style={buttonStyle}
            disabled={finalDecisionRows.length === 0}
          >
            Exportar decisão final (JSON)
          </button>
          <button
            type="button"
            onClick={() => exportFinalDecisionCsv(finalDecisionRows, finalGlobalDecision)}
            style={buttonStyle}
            disabled={finalDecisionRows.length === 0}
          >
            Exportar decisão final (CSV)
          </button>
          <button type="button" onClick={() => void handleCopyLatestFileNames(setCopyLatestStatus)} style={buttonStyle}>
            Copiar nome latest atual
          </button>
        </div>
        {copyLatestStatus ? <small style={copyStatusStyle}>{copyLatestStatus}</small> : null}

        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error && (coverageGate || readinessGate) ? (
          <div style={summaryRowStyle}>
            <span style={badgeStyle(consolidatedDecision)}>Decisão consolidada: {consolidatedDecision || "-"}</span>
            <span style={chipStyle}>Coverage: {String(coverageGate?.decision || "-")}</span>
            <span style={chipStyle}>Readiness: {String(readinessGate?.decision || "-")}</span>
            <span style={chipStyle}>Países: {Number(coverageGate?.country_count || readinessGate?.country_count || 0)}</span>
            <span style={chipStyle}>Missing coverage: {Number(coverageGate?.missing_scenarios_total || 0)}</span>
            <span style={chipStyle}>Blocking reasons: {Number(readinessGate?.blocking_reasons_total || 0)}</span>
          </div>
        ) : null}

        {!error && finalDecisionRows.length > 0 ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Painel de decisão final FG-1</h3>
            <div style={summaryRowStyle}>
              <span style={badgeStyle(finalGlobalDecision)}>Decisão final global: {finalGlobalDecision}</span>
              <span style={chipStyle}>Países aptos: {countriesReady}</span>
              <span style={chipStyle}>Países bloqueados: {countriesBlocked}</span>
              <span style={chipStyle}>Critério de saída [x]: 100% países em GO</span>
            </div>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Coverage</th>
                    <th style={thStyle}>Readiness</th>
                    <th style={thStyle}>Ações pendentes</th>
                    <th style={thStyle}>Decisão final país</th>
                    <th style={thStyle}>Critério de saída [x]</th>
                  </tr>
                </thead>
                <tbody>
                  {finalDecisionRows.map((row) => (
                    <tr key={`final-${row.countryCode}`}>
                      <td style={tdStyle}>{row.countryCode}</td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(row.coverageStatus)}>{row.coverageStatus}</span>
                      </td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(row.readinessStatus)}>{row.readinessStatus}</span>
                      </td>
                      <td style={tdStyle}>{row.pendingActions}</td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(row.finalDecision)}>{row.finalDecision}</span>
                      </td>
                      <td style={tdStyle}>
                        {row.finalDecision === "GO"
                          ? "Apto para [x] quando janela controlada validar 30min sem CRITICAL."
                          : "Manter [~]. Fechar bloqueios do action plan antes do go-live."}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {!error && coverageGate ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Coverage Gate ({String(coverageGate?.gate_version || "-")})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Adapter</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Missing</th>
                    <th style={thStyle}>Detalhe por operação</th>
                  </tr>
                </thead>
                <tbody>
                  {coverageCountries.map((item) => (
                    <tr key={item.country_code}>
                      <td style={tdStyle}>{item.country_code}</td>
                      <td style={tdStyle}>{item.adapter_name}</td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(item.coverage_status)}>{item.coverage_status}</span>
                      </td>
                      <td style={tdStyle}>{Number(item.missing_scenarios_count || 0)}</td>
                      <td style={tdStyle}>
                        <ul style={opsListStyle}>
                          {(item.operations || []).map((op) => (
                            <li key={`${item.country_code}-${op.operation}`}>
                              <b>{op.operation}</b>: {op.coverage_status}
                              {Array.isArray(op.missing_scenarios) && op.missing_scenarios.length > 0 ? (
                                <span> (missing: {op.missing_scenarios.join(", ")})</span>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {!error && readinessGate ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Readiness Gate ({String(readinessGate?.gate_version || "-")})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Blocking reasons</th>
                    <th style={thStyle}>Checks</th>
                  </tr>
                </thead>
                <tbody>
                  {readinessCountries.map((item) => (
                    <tr key={item.country_code}>
                      <td style={tdStyle}>{item.country_code}</td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(item.readiness_status)}>{item.readiness_status}</span>
                      </td>
                      <td style={tdStyle}>
                        {Array.isArray(item.blocking_reasons) && item.blocking_reasons.length > 0 ? (
                          <ul style={opsListStyle}>
                            {item.blocking_reasons.map((reason) => (
                              <li key={`${item.country_code}-reason-${reason.code}`}>
                                <b>{reason.code}</b>: {reason.label}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span style={chipStyle}>Sem bloqueios</span>
                        )}
                      </td>
                      <td style={tdStyle}>
                        <ul style={opsListStyle}>
                          {(item.checks || []).map((check) => (
                            <li key={`${item.country_code}-check-${check.code}`}>
                              <b>{check.code}</b>: {check.status}
                            </li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {!error && actionPlan ? (
          <div style={boxStyle}>
            <h3 style={boxTitleStyle}>Readiness Action Plan ({String(actionPlan?.plan_version || "-")})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Bloqueios</th>
                    <th style={thStyle}>ENVs obrigatórias</th>
                    <th style={thStyle}>Ações recomendadas</th>
                  </tr>
                </thead>
                <tbody>
                  {actionPlanItems.map((item) => (
                    <tr key={`action-plan-${item.country_code}`}>
                      <td style={tdStyle}>{item.country_code}</td>
                      <td style={tdStyle}>
                        <span style={badgeStyle(item.status)}>{item.status}</span>
                      </td>
                      <td style={tdStyle}>{Number(item.blocking_reasons_count || 0)}</td>
                      <td style={tdStyle}>
                        {Array.isArray(item.required_env_keys) && item.required_env_keys.length > 0 ? (
                          <ul style={opsListStyle}>
                            {item.required_env_keys.map((envKey) => (
                              <li key={`${item.country_code}-env-${envKey}`}>
                                <code>{envKey}</code>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span style={chipStyle}>Sem pendências de ENV</span>
                        )}
                      </td>
                      <td style={tdStyle}>
                        {Array.isArray(item.recommended_actions) && item.recommended_actions.length > 0 ? (
                          <ul style={opsListStyle}>
                            {item.recommended_actions.map((action) => (
                              <li key={`${item.country_code}-action-${action}`}>{action}</li>
                            ))}
                          </ul>
                        ) : (
                          <span style={chipStyle}>Pronto para go-live</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const toolbarStyle = { display: "flex", gap: 8, marginBottom: 10 };
const buttonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  cursor: "pointer",
  fontWeight: 600,
};
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const boxStyle = {
  marginTop: 12,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 12,
  padding: 12,
  background: "var(--fiscal-box-bg)",
};
const boxTitleStyle = { margin: "0 0 8px", fontSize: 15, color: "var(--fiscal-text)" };
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
  if (status === "GO") {
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
const tableWrapStyle = { overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 940 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-table-separator-strong)", padding: "8px 10px", fontSize: 13 };
const tdStyle = { borderBottom: "1px solid var(--fiscal-table-separator-soft)", padding: "8px 10px", verticalAlign: "top", fontSize: 13 };
const opsListStyle = { margin: 0, paddingLeft: 16, display: "grid", gap: 4, color: "var(--fiscal-soft-text)" };
const copyStatusStyle = { marginTop: 8, display: "inline-flex", color: "var(--fiscal-accent-2)", fontWeight: 700 };

function buildFinalDecisionRows(coverageCountries, readinessCountries, actionPlanItems) {
  const coverageMap = {};
  for (const row of coverageCountries || []) {
    const code = String(row?.country_code || "").toUpperCase();
    if (!code) continue;
    coverageMap[code] = String(row?.coverage_status || "NO_GO").toUpperCase();
  }

  const readinessMap = {};
  for (const row of readinessCountries || []) {
    const code = String(row?.country_code || "").toUpperCase();
    if (!code) continue;
    readinessMap[code] = String(row?.readiness_status || "NO_GO").toUpperCase();
  }

  const actionPlanMap = {};
  for (const row of actionPlanItems || []) {
    const code = String(row?.country_code || "").toUpperCase();
    if (!code) continue;
    actionPlanMap[code] = Number(row?.blocking_reasons_count || 0);
  }

  const countries = Array.from(new Set([...Object.keys(coverageMap), ...Object.keys(readinessMap), ...Object.keys(actionPlanMap)])).sort();
  return countries.map((countryCode) => {
    const coverageStatus = coverageMap[countryCode] || "NO_GO";
    const readinessStatus = readinessMap[countryCode] || "NO_GO";
    const pendingActions = actionPlanMap[countryCode] || 0;
    const finalDecision = coverageStatus === "GO" && readinessStatus === "GO" && pendingActions === 0 ? "GO" : "NO_GO";
    return { countryCode, coverageStatus, readinessStatus, pendingActions, finalDecision };
  });
}

function exportFinalDecisionJson(rows, finalGlobalDecision) {
  const sessionSuffix = getStableSessionSuffix();
  const payload = {
    exported_at: new Date().toISOString(),
    scope: "FG-1-FINAL-DECISION",
    file_suffix: sessionSuffix,
    final_global_decision: finalGlobalDecision,
    country_count: rows.length,
    countries: rows.map((row) => ({
      country_code: row.countryCode,
      coverage_status: row.coverageStatus,
      readiness_status: row.readinessStatus,
      pending_actions: row.pendingActions,
      final_decision: row.finalDecision,
      exit_criteria:
        row.finalDecision === "GO"
          ? "Apto para [x] quando janela controlada validar 30min sem CRITICAL."
          : "Manter [~]. Fechar bloqueios do action plan antes do go-live.",
    })),
  };
  downloadTextFile(
    `fg1_final_decision_latest_${sessionSuffix}.json`,
    JSON.stringify(payload, null, 2),
    "application/json"
  );
}

function exportFinalDecisionCsv(rows, finalGlobalDecision) {
  const sessionSuffix = getStableSessionSuffix();
  const header = [
    "scope",
    "exported_at",
    "final_global_decision",
    "country_code",
    "coverage_status",
    "readiness_status",
    "pending_actions",
    "final_decision",
    "exit_criteria",
  ];
  const exportedAt = new Date().toISOString();
  const dataRows = rows.map((row) => [
    "FG-1-FINAL-DECISION",
    exportedAt,
    finalGlobalDecision,
    row.countryCode,
    row.coverageStatus,
    row.readinessStatus,
    String(row.pendingActions),
    row.finalDecision,
    row.finalDecision === "GO"
      ? "Apto para [x] quando janela controlada validar 30min sem CRITICAL."
      : "Manter [~]. Fechar bloqueios do action plan antes do go-live.",
  ]);
  const csv = [header, ...dataRows].map((row) => row.map(escapeCsvCell).join(",")).join("\n");
  downloadTextFile(
    `fg1_final_decision_latest_${sessionSuffix}.csv`,
    csv,
    "text/csv;charset=utf-8"
  );
}

function downloadTextFile(filename, content, mimeType) {
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

function escapeCsvCell(value) {
  const source = String(value == null ? "" : value);
  if (source.includes(",") || source.includes('"') || source.includes("\n")) {
    return `"${source.replace(/"/g, '""')}"`;
  }
  return source;
}

function getStableSessionSuffix() {
  const storageKey = "fiscal:fg1:handoff:session_suffix";
  try {
    const existing = window.sessionStorage.getItem(storageKey);
    if (existing) return String(existing);
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const suffix = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
    window.sessionStorage.setItem(storageKey, suffix);
    return suffix;
  } catch {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
  }
}

async function handleCopyLatestFileNames(setStatus) {
  const suffix = getStableSessionSuffix();
  const jsonName = `fg1_final_decision_latest_${suffix}.json`;
  const csvName = `fg1_final_decision_latest_${suffix}.csv`;
  const payload = [jsonName, csvName].join("\n");
  try {
    await navigator.clipboard.writeText(payload);
    setStatus(`Nomes latest copiados: ${jsonName} e ${csvName}`);
    window.setTimeout(() => setStatus(""), 2600);
  } catch {
    setStatus("Falha ao copiar automaticamente. Use os nomes latest visíveis no padrão da sessão.");
    window.setTimeout(() => setStatus(""), 3000);
  }
}
