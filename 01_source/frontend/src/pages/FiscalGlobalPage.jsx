import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl, FISCAL_API_GROUPS } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const FISCAL_PAGE_VERSION = "fiscal/global v1.1.0";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

export default function FiscalGlobalPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fg1Warning, setFg1Warning] = useState("");
  const [catalog, setCatalog] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [fg1Adapters, setFg1Adapters] = useState(null);
  const [fg1Fixtures, setFg1Fixtures] = useState(null);
  const [apiMethodFilter, setApiMethodFilter] = useState("ALL");
  const [apiGroupFilter, setApiGroupFilter] = useState("ALL");

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

      const [adaptersRes, fixturesRes] = await Promise.all([
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/stub-adapters`, { method: "GET", headers: headersJson() }),
        fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/fixtures-matrix`, { method: "GET", headers: headersJson() }),
      ]);
      const [adaptersPayload, fixturesPayload] = await Promise.all([
        adaptersRes.json().catch(() => ({})),
        fixturesRes.json().catch(() => ({})),
      ]);
      if (adaptersRes.ok && fixturesRes.ok) {
        setFg1Adapters(adaptersPayload || null);
        setFg1Fixtures(fixturesPayload || null);
      } else {
        setFg1Adapters(null);
        setFg1Fixtures(null);
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
          <Link to="/fiscal/readiness-execution" style={shortcutLinkStyle}>
            Abrir fiscal/readiness-execution
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            Abrir fiscal/updates
          </Link>
        </div>

        <OpsPageTitleHeader title="FISCAL - Catálogo Global" versionLabel={FISCAL_PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Visão centralizada do FG-0 com catálogo fiscal multipaís e matriz canônica de cenários obrigatórios.
        </p>

        <div style={toolbarStyle}>
          <button type="button" onClick={() => void loadGlobalFiscalData()} style={buttonStyle} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
        </div>

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
