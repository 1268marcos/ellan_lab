import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl, FISCAL_API_GROUPS } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const FISCAL_PAGE_VERSION = "fiscal/global v1.3.2-s3-hardening-strip";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function getStubReadinessStats(report) {
  const checks = Array.isArray(report?.checks) ? report.checks : [];
  const failed = checks.filter((check) => String(check?.status || "").toUpperCase() !== "PASS").length;
  const passed = Math.max(checks.length - failed, 0);
  return {
    checks,
    failed,
    passed,
    total: checks.length,
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

export default function FiscalGlobalPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fg1Warning, setFg1Warning] = useState("");
  const [catalog, setCatalog] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [fg1Adapters, setFg1Adapters] = useState(null);
  const [fg1Fixtures, setFg1Fixtures] = useState(null);
  const [fg1StubReadiness, setFg1StubReadiness] = useState(null);
  const [apiMethodFilter, setApiMethodFilter] = useState("ALL");
  const [apiGroupFilter, setApiGroupFilter] = useState("ALL");
  const [managementCopyStatus, setManagementCopyStatus] = useState("");

  async function loadGlobalFiscalData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    setFg1Warning("");
    try {
      const [catalogRes, matrixRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/catalog`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/scenario-matrix`, { method: "GET", headers: headersJson() }),
      ]);
      const [catalogPayload, matrixPayload] = await Promise.all([
        catalogRes.json().catch(() => ({})),
        matrixRes.json().catch(() => ({})),
      ]);
      if (!catalogRes.ok || !matrixRes.ok) {
        const detail = String(catalogPayload?.detail || matrixPayload?.detail || "Falha ao carregar catálogo/matriz fiscal global.");
        throw new Error(detail);
      }
      setCatalog(catalogPayload || null);
      setMatrix(matrixPayload || null);

      const [adaptersRes, fixturesRes, stubReadinessRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-adapters`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/fixtures-matrix`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-wave-readiness`, { method: "GET", headers: headersJson() }),
      ]);
      const [adaptersPayload, fixturesPayload, stubReadinessPayload] = await Promise.all([
        adaptersRes.json().catch(() => ({})),
        fixturesRes.json().catch(() => ({})),
        stubReadinessRes.json().catch(() => ({})),
      ]);
      if (adaptersRes.ok && fixturesRes.ok && stubReadinessRes.ok) {
        setFg1Adapters(adaptersPayload || null);
        setFg1Fixtures(fixturesPayload || null);
        setFg1StubReadiness(stubReadinessPayload || null);
      } else {
        setFg1Adapters(null);
        setFg1Fixtures(null);
        setFg1StubReadiness(null);
        setFg1Warning("Bloco FG-1 indisponível no backend atual (catalog/matrix carregados normalmente).");
      }
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
    void loadGlobalFiscalData();
  }, []);

  const apiGroupOptions = [{ key: "ALL", label: "Todos os grupos" }, ...FISCAL_API_GROUPS.map((group) => ({ key: group.key, label: group.label }))];
  const filteredApiGroups = FISCAL_API_GROUPS.map((group) => {
    if (apiGroupFilter !== "ALL" && group.key !== apiGroupFilter) {
      return null;
    }
    const endpoints = (group.endpoints || []).filter((endpoint) => {
      if (apiMethodFilter === "ALL") return true;
      return String(endpoint || "").toUpperCase().startsWith(`${apiMethodFilter} `);
    });
    if (endpoints.length === 0) return null;
    return { ...group, endpoints };
  }).filter(Boolean);

  async function copyFiscalManagementPayloadJson() {
    try {
      const readinessStats = getStubReadinessStats(fg1StubReadiness);
      const countriesNotReady = Number(fg1StubReadiness?.countries_not_ready || 0);
      const decision = String(fg1StubReadiness?.decision || "NO_GO").toUpperCase();
      const riskLevel = decision === "GO" ? "LOW" : countriesNotReady >= 2 ? "HIGH" : "MEDIUM";
      const actions = [];
      if (decision !== "GO") {
        actions.push("priorizar_paises_bloqueados_no_readiness_execution");
        actions.push("executar_handoff_orchestrator_e_revalidar_gates");
      } else {
        actions.push("manter_ritmo_diario_de_orquestrador");
        actions.push("monitorar_desvio_de_checks_no_turno");
      }
      const nowIso = new Date().toISOString();
      const payload = {
        scope: "FISCAL_MANAGEMENT_DAILY",
        generated_at: nowIso,
        decision_consolidated: decision,
        risk_level: riskLevel,
        checks_pass: `${readinessStats.passed}/${readinessStats.total}`,
        checks_failed: readinessStats.failed,
        reference: {
          readiness_version: String(fg1StubReadiness?.readiness_version || "-"),
          catalog_count: Number(catalog?.count || 0),
          scenario_matrix_count: Number(matrix?.count || 0),
          fixture_matrix_count: Number(fg1Fixtures?.count || 0),
          adapter_count: Number(fg1Adapters?.count || 0),
          countries_not_ready: countriesNotReady,
        },
        practical_actions: actions,
      };
      const text = JSON.stringify(payload, null, 2);
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      const ts = nowIso.replace(/[:.]/g, "-");
      downloadJsonFile(`fiscal_management_daily_payload_${ts}.json`, payload);
      setManagementCopyStatus("Payload executivo FISCAL (JSON) copiado e baixado.");
      window.setTimeout(() => setManagementCopyStatus(""), 2500);
    } catch (err) {
      setManagementCopyStatus(`Falha ao copiar payload executivo: ${String(err?.message || err)}`);
    }
  }

  async function downloadDailyPackageZipFromFiscalGlobal() {
    try {
      if (!fg1StubReadiness) {
        setManagementCopyStatus("Readiness FG-1 indisponível para gerar pacote diário.");
        window.setTimeout(() => setManagementCopyStatus(""), 2500);
        return;
      }
      const nowIso = new Date().toISOString();
      const readinessStats = getStubReadinessStats(fg1StubReadiness);
      const countriesNotReady = Number(fg1StubReadiness?.countries_not_ready || 0);
      const decision = String(fg1StubReadiness?.decision || "NO_GO").toUpperCase();
      const riskLevel = decision === "GO" ? "LOW" : countriesNotReady >= 2 ? "HIGH" : "MEDIUM";
      const fiscalPayload = {
        scope: "FISCAL_MANAGEMENT_DAILY",
        generated_at: nowIso,
        decision_consolidated: decision,
        risk_level: riskLevel,
        checks_pass: `${readinessStats.passed}/${readinessStats.total}`,
        checks_failed: readinessStats.failed,
        reference: {
          readiness_version: String(fg1StubReadiness?.readiness_version || "-"),
          catalog_count: Number(catalog?.count || 0),
          scenario_matrix_count: Number(matrix?.count || 0),
          fixture_matrix_count: Number(fg1Fixtures?.count || 0),
          adapter_count: Number(fg1Adapters?.count || 0),
          countries_not_ready: countriesNotReady,
        },
      };
      const opsPayload = {
        scope: "OPS_HEALTH_DAILY",
        generated_at: nowIso,
        decision,
        checks_pass: `${readinessStats.passed}/${readinessStats.total}`,
        checks_failed: readinessStats.failed,
        source: "fiscal/global",
        note: "Pacote diário gerado a partir do contexto fiscal consolidado.",
        failed_checks: (readinessStats.checks || [])
          .filter((check) => String(check?.status || "").toUpperCase() !== "PASS")
          .map((check) => ({
            code: String(check?.name || "-"),
            detail: String(check?.status || "-"),
          })),
      };
      const ts = nowIso.replace(/[:.]/g, "-");
      downloadZipFile(`daily_management_package_${ts}.zip`, {
        [`ops_health_daily_payload_${ts}.json`]: strToU8(JSON.stringify(opsPayload, null, 2)),
        [`fiscal_management_daily_payload_${ts}.json`]: strToU8(JSON.stringify(fiscalPayload, null, 2)),
      });
      setManagementCopyStatus("Pacote diário (.zip) baixado com payload OPS + FISCAL.");
      window.setTimeout(() => setManagementCopyStatus(""), 2500);
    } catch (err) {
      setManagementCopyStatus(`Falha ao baixar pacote diário: ${String(err?.message || err)}`);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/ops/fiscal/providers" style={shortcutLinkStyle}>
            Abrir ops/fiscal/providers
          </Link>
          <Link to="/fiscal/countries" style={shortcutLinkStyle}>
            Abrir fiscal/countries
          </Link>
          <Link to="/fiscal/fg1-gate" style={shortcutLinkStyle}>
            Abrir fiscal/fg1-gate
          </Link>
          <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>
            Abrir fiscal/sprint2-finance-gate
          </Link>
          <Link to="/fiscal/readiness-execution" style={shortcutLinkStyle}>
            Abrir fiscal/readiness-execution
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            Abrir fiscal/updates
          </Link>
        </div>

        <div style={sprint2GateStripStyle}>
          <div style={sprint2GateTitleStyle}>Sprint 2 — trilha fiscal / contábil (gate v2)</div>
          <div style={sprint2GateLinksStyle}>
            <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>
              fiscal/management-daily
            </Link>
            <Link to="/fiscal/accounting-close" style={shortcutLinkStyle}>
              fiscal/accounting-close
            </Link>
            <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>
              fiscal/sprint2-finance-gate
            </Link>
            <Link to="/fiscal/readiness-execution" style={shortcutLinkStyle}>
              fiscal/readiness-execution
            </Link>
          </div>
          <p style={sprint2GateNoteStyle}>
            Alocação recomendada no plano: <b>~65–75%</b> da capacidade de codificação aqui até o PASS do gate v2 (Fiscal
            ≥50%, Contábil ≥40%, consolidado Sprint 2 ≥55%, comprovação P0). Detalhe:{" "}
            <code>docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md</code> — secções Sprint 2 e «Recomendacao atual — onde codar».
            Runbook FG-0/FG-1: <code>docs/runbooks/FISCAL_CATALOGO_SEM_UI_POR_PAIS.md</code>.
          </p>
        </div>

        <div style={sprint3GateStripStyle}>
          <div style={sprint3GateTitleStyle}>Sprint 3 — hardening (paralelo seguro até gate v2)</div>
          <div style={sprint3GateLinksStyle}>
            <Link to="/fiscal/slo-alerts" style={shortcutLinkStyle}>
              fiscal/slo-alerts
            </Link>
            <Link to="/fiscal/incident-response" style={shortcutLinkStyle}>
              fiscal/incident-response
            </Link>
            <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>
              fiscal/sprint3-partner-audit
            </Link>
            <Link to="/ops/quick-enablement" style={shortcutLinkStyle}>
              ops/quick-enablement
            </Link>
            <Link to="/ops/reconciliation" style={shortcutLinkStyle}>
              ops/reconciliation
            </Link>
          </div>
          <p style={sprint3GateNoteStyle}>
            Checklist Sprint 3 no plano: CSP, TS strict-core, <strong>auditoria E2E</strong>, SLO, P0-3 incidente, quick-enablement.
            Sem <strong>net-new</strong> grande enquanto a <strong>fase A — pré-gate v2</strong> estiver ativa; usar estas rotas em fatias que{" "}
            <b>não</b> roubem capacidade dos P0 financeiros da Sprint 2. Referência:{" "}
            <code>docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md</code> (secção Sprint 3).
          </p>
        </div>

        <OpsPageTitleHeader title="FISCAL - Catálogo Global" versionLabel={FISCAL_PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Visão centralizada do FG-0 com catálogo fiscal multipaís e matriz canônica de cenários obrigatórios.
        </p>

        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadGlobalFiscalData()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button type="button" onClick={() => void copyFiscalManagementPayloadJson()} style={buttonStyle} disabled={!fg1StubReadiness}>
            Copiar payload executivo FISCAL (JSON)
          </button>
          <button type="button" onClick={() => void downloadDailyPackageZipFromFiscalGlobal()} style={buttonStyle} disabled={!fg1StubReadiness}>
            Baixar pacote diário (.zip)
          </button>
        </div>
        {managementCopyStatus ? <small style={mutedTextStyle}>{managementCopyStatus}</small> : null}

        {error ? <div style={errorStyle}>{error}</div> : null}
        {!error && fg1Warning ? <div style={warningStyle}>{fg1Warning}</div> : null}

        {!error && catalog ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>Catálogo Global ({Number(catalog?.count || 0)})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Autoridade</th>
                    <th style={thStyle}>Região</th>
                    <th style={thStyle}>Moeda</th>
                    <th style={thStyle}>Timezone</th>
                    <th style={thStyle}>Protocolo</th>
                  </tr>
                </thead>
                <tbody>
                  {(catalog.items || []).map((item) => (
                    <tr key={`${item.country_code}-${item.authority}`}>
                      <td style={tdStyle}>{item.country_code}</td>
                      <td style={tdStyle}>{item.authority}</td>
                      <td style={tdStyle}>{item.region}</td>
                      <td style={tdStyle}>{item.currency}</td>
                      <td style={tdStyle}>{item.timezone}</td>
                      <td style={tdStyle}>{item.protocol}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {!error && matrix ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>Matriz Canônica de Cenários ({Number(matrix?.count || 0)})</h3>
            <ul style={listStyle}>
              {(matrix.required_scenarios || []).map((row) => (
                <li key={`${row.operation}-${row.scenario}`}>
                  <b>{row.operation}</b> - {row.scenario} - {row.canonical_status}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {!error && fg1Adapters ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>FG-1 Stub Adapters ({Number(fg1Adapters?.count || 0)})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Adapter</th>
                    <th style={thStyle}>Operações</th>
                    <th style={thStyle}>Campos de telemetria</th>
                  </tr>
                </thead>
                <tbody>
                  {(fg1Adapters.items || []).map((item) => (
                    <tr key={`${item.country_code}-${item.adapter_name}`}>
                      <td style={tdStyle}>{item.country_code}</td>
                      <td style={tdStyle}>{item.adapter_name}</td>
                      <td style={tdStyle}>{String((item.operations_supported || []).join(", ") || "-")}</td>
                      <td style={tdStyle}>{String((item.telemetry_fields || []).join(", ") || "-")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {!error && fg1Fixtures ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>FG-1 Fixtures Matrix ({Number(fg1Fixtures?.count || 0)})</h3>
            <div style={tableWrapStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>País</th>
                    <th style={thStyle}>Operação</th>
                    <th style={thStyle}>Cenário</th>
                    <th style={thStyle}>Status canônico</th>
                    <th style={thStyle}>Status autoridade</th>
                    <th style={thStyle}>Fixture path</th>
                  </tr>
                </thead>
                <tbody>
                  {(fg1Fixtures.rows || []).map((row) => (
                    <tr key={`${row.country_code}-${row.operation}-${row.scenario}`}>
                      <td style={tdStyle}>{row.country_code}</td>
                      <td style={tdStyle}>{row.operation}</td>
                      <td style={tdStyle}>{row.scenario}</td>
                      <td style={tdStyle}>{row.canonical_status}</td>
                      <td style={tdStyle}>{row.authority_status}</td>
                      <td style={tdStyle}>
                        <code>{row.fixture_path}</code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {!error && fg1StubReadiness ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>FG-1 Stub Wave Readiness ({String(fg1StubReadiness?.readiness_version || "-")})</h3>
            <div style={summaryRowStyle}>
              <span style={badgeStyle(fg1StubReadiness?.decision)}>Decisão consolidada: {String(fg1StubReadiness?.decision || "-")}</span>
              <span style={chipStyle}>{`${getStubReadinessStats(fg1StubReadiness).passed}/${getStubReadinessStats(fg1StubReadiness).total} checks PASS`}</span>
              <span style={chipStyle}>Checks com falha: {Number(getStubReadinessStats(fg1StubReadiness).failed || 0)}</span>
              <span style={chipStyle}>Referência: {String(fg1StubReadiness?.readiness_version || "-")}</span>
              <span style={chipStyle}>Countries not ready: {Number(fg1StubReadiness?.countries_not_ready || 0)}</span>
              <span style={chipStyle}>Country count: {Number(fg1StubReadiness?.country_count || 0)}</span>
            </div>
            <ul style={listStyle}>
              {(fg1StubReadiness?.checks || []).map((check, idx) => (
                <li key={`${String(check?.name || "check")}-${idx}`}>
                  <b>{String(check?.name || "-")}</b>: {String(check?.status || "-")}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {!error ? (
          <section style={boxStyle}>
            <h3 style={boxTitleStyle}>Catálogo de APIs FISCAL (Swagger)</h3>
            <p style={mutedTextStyle}>
              Hub de endpoints do domínio FISCAL agrupados por responsabilidade, integrado às páginas para reduzir dependência de busca manual no Swagger.
            </p>
            <div style={apiFiltersRowStyle}>
              <label style={apiFilterLabelStyle}>
                Método
                <select value={apiMethodFilter} onChange={(event) => setApiMethodFilter(event.target.value)} style={apiFilterSelectStyle}>
                  <option value="ALL">ALL</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>
              </label>
              <label style={apiFilterLabelStyle}>
                Grupo
                <select value={apiGroupFilter} onChange={(event) => setApiGroupFilter(event.target.value)} style={apiFilterSelectStyle}>
                  {apiGroupOptions.map((option) => (
                    <option key={option.key} value={option.key}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div style={apiGroupsGridStyle}>
              {filteredApiGroups.map((group) => (
                <article key={group.key} style={apiGroupCardStyle}>
                  <strong style={apiGroupTitleStyle}>{group.label}</strong>
                  <ul style={apiListStyle}>
                    {group.endpoints.map((endpoint) => (
                      <li key={`${group.key}-${endpoint}`}>
                        <code>{endpoint}</code>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
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
const sprint2GateStripStyle = {
  marginTop: 10,
  marginBottom: 12,
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(56,189,248,0.45)",
  background: "rgba(14,116,144,0.14)",
};
const sprint2GateTitleStyle = {
  fontSize: 13,
  fontWeight: 800,
  color: "var(--fiscal-accent-2)",
  marginBottom: 8,
};
const sprint2GateLinksStyle = { display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 };
const sprint2GateNoteStyle = {
  margin: 0,
  fontSize: 12,
  lineHeight: 1.45,
  color: "var(--fiscal-soft-text)",
};
const sprint3GateStripStyle = {
  marginTop: 10,
  marginBottom: 12,
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(167,139,250,0.45)",
  background: "rgba(91,33,182,0.12)",
};
const sprint3GateTitleStyle = {
  fontSize: 13,
  fontWeight: 800,
  color: "#ddd6fe",
  marginBottom: 8,
};
const sprint3GateLinksStyle = { display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 };
const sprint3GateNoteStyle = {
  margin: 0,
  fontSize: 12,
  lineHeight: 1.45,
  color: "var(--fiscal-soft-text)",
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
const warningStyle = { marginTop: 12, background: "rgba(245,158,11,0.12)", color: "#fde68a", padding: 12, borderRadius: 12, overflow: "auto" };
const boxStyle = {
  marginTop: 12,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 12,
  background: "var(--fiscal-box-bg)",
  padding: 12,
};
const boxTitleStyle = { marginTop: 0, marginBottom: 8 };
const tableWrapStyle = { overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 740 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-table-separator-strong)", padding: "8px 10px", fontSize: 13 };
const tdStyle = { borderBottom: "1px solid var(--fiscal-table-separator-soft)", padding: "8px 10px", verticalAlign: "top", fontSize: 13 };
const listStyle = { margin: "6px 0 0", paddingLeft: 18, display: "grid", gap: 4 };
const summaryRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 };
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
const badgeStyle = (decision) => {
  const normalized = String(decision || "").toUpperCase();
  if (normalized === "GO" || normalized === "PASS" || normalized === "READY") {
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
const apiGroupsGridStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" };
const apiFiltersRowStyle = { marginTop: 8, marginBottom: 8, display: "flex", gap: 8, flexWrap: "wrap" };
const apiFilterLabelStyle = { display: "grid", gap: 4, fontSize: 12, color: "var(--fiscal-soft-text)", fontWeight: 600 };
const apiFilterSelectStyle = {
  minWidth: 180,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-surface)",
  color: "var(--fiscal-text)",
};
const apiGroupCardStyle = {
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 10,
  background: "var(--fiscal-surface)",
  padding: 10,
};
const apiGroupTitleStyle = { display: "inline-flex", marginBottom: 6, color: "var(--fiscal-accent-2)" };
const apiListStyle = { margin: 0, paddingLeft: 16, display: "grid", gap: 4, color: "var(--fiscal-soft-text)" };
