import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const FISCAL_COUNTRIES_PAGE_VERSION = "fiscal/countries v1.0.0";

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

export default function FiscalCountriesPage() {
  const initialFilters = useMemo(() => loadCountriesFilters(), []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copyContextStatus, setCopyContextStatus] = useState("");
  const [items, setItems] = useState([]);
  const [fg1WaveCountrySet, setFg1WaveCountrySet] = useState(() => new Set());
  const [executionStatusMap, setExecutionStatusMap] = useState(() => loadExecutionStatusMap());
  const [regionFilter, setRegionFilter] = useState(initialFilters.region);
  const [priorityFilter, setPriorityFilter] = useState(initialFilters.priority);
  const [authorityFilter, setAuthorityFilter] = useState(initialFilters.authority);
  const [executionFilter, setExecutionFilter] = useState(initialFilters.execution);
  const [onlyInWave, setOnlyInWave] = useState(initialFilters.onlyInWave);

  async function loadCatalog() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${BILLING_BASE}/admin/fiscal/global/catalog`, { method: "GET", headers: headersJson() });
      const waveResponse = await fetch(`${BILLING_BASE}/admin/fiscal/global/fg1-wave-scope`, { method: "GET", headers: headersJson() });
      const payload = await response.json().catch(() => ({}));
      const wavePayload = await waveResponse.json().catch(() => ({}));
      if (!response.ok) throw new Error(String(payload?.detail || "Falha ao carregar catálogo fiscal global."));
      if (!waveResponse.ok) throw new Error(String(wavePayload?.detail || "Falha ao carregar escopo FG-1."));
      setItems(Array.isArray(payload?.items) ? payload.items : []);
      const countries = Array.isArray(wavePayload?.countries) ? wavePayload.countries : [];
      setFg1WaveCountrySet(new Set(countries.map((item) => String(item?.country_code || "").toUpperCase()).filter(Boolean)));
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
    void loadCatalog();
  }, []);

  useEffect(() => {
    persistCountriesFilters({
      region: regionFilter,
      priority: priorityFilter,
      authority: authorityFilter,
      execution: executionFilter,
      onlyInWave,
    });
  }, [regionFilter, priorityFilter, authorityFilter, executionFilter, onlyInWave]);

  const regions = useMemo(() => ["ALL", ...new Set(items.map((item) => String(item.region || "").toUpperCase()).filter(Boolean))], [items]);
  const priorities = useMemo(
    () => ["ALL", ...new Set(items.map((item) => String(item.priority_tier || "").toLowerCase()).filter(Boolean))],
    [items]
  );

  const filteredItems = useMemo(() => {
    const authorityNeedle = authorityFilter.trim().toLowerCase();
    return items.filter((item) => {
      const regionOk = regionFilter === "ALL" || String(item.region || "").toUpperCase() === regionFilter;
      const priorityOk = priorityFilter === "ALL" || String(item.priority_tier || "").toLowerCase() === priorityFilter;
      const authorityOk = !authorityNeedle || String(item.authority || "").toLowerCase().includes(authorityNeedle);
      const executionStatus = resolveExecutionStatus(executionStatusMap, item.country_code);
      const executionOk = executionFilter === "ALL" || executionStatus === executionFilter;
      const inWave = fg1WaveCountrySet.has(String(item.country_code || "").toUpperCase());
      const waveOk = !onlyInWave || inWave;
      return regionOk && priorityOk && authorityOk && executionOk && waveOk;
    });
  }, [items, regionFilter, priorityFilter, authorityFilter, executionFilter, executionStatusMap, fg1WaveCountrySet, onlyInWave]);

  const statusCounts = useMemo(() => {
    const summary = { TODO: 0, IN_PROGRESS: 0, DONE: 0 };
    for (const item of items) {
      const status = resolveExecutionStatus(executionStatusMap, item.country_code);
      if (summary[status] != null) summary[status] += 1;
    }
    return summary;
  }, [items, executionStatusMap]);

  const inWaveCounts = useMemo(() => {
    const summary = { TOTAL: 0, TODO: 0, IN_PROGRESS: 0, DONE: 0 };
    for (const item of items) {
      const inWave = fg1WaveCountrySet.has(String(item.country_code || "").toUpperCase());
      if (!inWave) continue;
      summary.TOTAL += 1;
      const status = resolveExecutionStatus(executionStatusMap, item.country_code);
      if (summary[status] != null) summary[status] += 1;
    }
    return summary;
  }, [items, executionStatusMap, fg1WaveCountrySet]);

  const activePresetLabel = useMemo(() => {
    if (!onlyInWave) return "";
    if (executionFilter === "IN_PROGRESS") return "Preset ativo: Foco FG-1";
    if (executionFilter === "DONE") return "Preset ativo: Fechamento FG-1";
    return "Preset parcial: Somente IN WAVE";
  }, [onlyInWave, executionFilter]);

  function handleExecutionStatusChange(countryCode, newStatus) {
    setExecutionStatusMap((current) => {
      const normalizedCountry = String(countryCode || "").toUpperCase();
      const next = {
        ...current,
        [normalizedCountry]: String(newStatus || "TODO").toUpperCase(),
      };
      persistExecutionStatusMap(next);
      return next;
    });
  }

  function applyStatusToFiltered(newStatus) {
    const normalizedStatus = String(newStatus || "TODO").toUpperCase();
    setExecutionStatusMap((current) => {
      const next = { ...current };
      for (const item of filteredItems) {
        const country = String(item.country_code || "").toUpperCase();
        if (!country) continue;
        next[country] = normalizedStatus;
      }
      persistExecutionStatusMap(next);
      return next;
    });
  }

  function activateFg1FocusPreset() {
    setOnlyInWave(true);
    setExecutionFilter("IN_PROGRESS");
  }

  function activateFg1CloseoutPreset() {
    setOnlyInWave(true);
    setExecutionFilter("DONE");
  }

  function handleResetFilters() {
    setRegionFilter("ALL");
    setPriorityFilter("ALL");
    setAuthorityFilter("");
    setExecutionFilter("ALL");
    setOnlyInWave(false);
  }

  async function handleCopyFilterContext() {
    const contextText = buildFilterContextText({
      regionFilter,
      priorityFilter,
      authorityFilter,
      executionFilter,
      onlyInWave,
      activePresetLabel,
      filteredCount: filteredItems.length,
      totalCount: items.length,
      inWaveCounts,
    });
    try {
      await navigator.clipboard.writeText(contextText);
      setCopyContextStatus("Contexto do filtro copiado para handoff.");
      window.setTimeout(() => setCopyContextStatus(""), 2200);
    } catch {
      setCopyContextStatus("Falha ao copiar automaticamente. Copie manualmente o contexto na tela.");
      window.setTimeout(() => setCopyContextStatus(""), 2600);
    }
  }

  function exportBoardJson() {
    const payload = {
      exported_at: new Date().toISOString(),
      filters: {
        region: regionFilter,
        priority: priorityFilter,
        authority: authorityFilter,
        execution: executionFilter,
        only_in_wave: onlyInWave,
      },
      summary: statusCounts,
      items: filteredItems.map((item) => ({
        country_code: item.country_code,
        region: item.region,
        authority: item.authority,
        priority_tier: item.priority_tier,
        protocol: item.protocol,
        stub_endpoint: item.stub_endpoint,
        execution_status: resolveExecutionStatus(executionStatusMap, item.country_code),
        in_fg1_wave: fg1WaveCountrySet.has(String(item.country_code || "").toUpperCase()),
      })),
    };
    downloadTextFile(
      `fiscal_countries_board_${new Date().toISOString().replace(/[:.]/g, "-")}.json`,
      JSON.stringify(payload, null, 2),
      "application/json"
    );
  }

  function exportBoardCsv() {
    const header = [
      "country_code",
      "region",
      "authority",
      "priority_tier",
      "protocol",
      "stub_endpoint",
      "execution_status",
      "in_fg1_wave",
    ];
    const rows = filteredItems.map((item) => [
      item.country_code,
      item.region,
      item.authority,
      item.priority_tier,
      item.protocol,
      item.stub_endpoint,
      resolveExecutionStatus(executionStatusMap, item.country_code),
      fg1WaveCountrySet.has(String(item.country_code || "").toUpperCase()) ? "true" : "false",
    ]);
    const csv = [header, ...rows].map((row) => row.map(escapeCsvCell).join(",")).join("\n");
    downloadTextFile(
      `fiscal_countries_board_${new Date().toISOString().replace(/[:.]/g, "-")}.csv`,
      csv,
      "text/csv;charset=utf-8"
    );
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal" style={shortcutLinkStyle}>
            Abrir fiscal/global
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            Abrir fiscal/updates
          </Link>
        </div>

        <OpsPageTitleHeader title="FISCAL - Countries Cockpit (FG-1/FG-2)" versionLabel={FISCAL_COUNTRIES_PAGE_VERSION} />
        <p style={mutedTextStyle}>Cockpit operacional para execução FG-1/FG-2 com filtro por região, prioridade e autoridade.</p>

        <div style={filtersGridStyle}>
          <label style={labelStyle}>
            Região
            <select value={regionFilter} onChange={(event) => setRegionFilter(event.target.value)} style={inputStyle}>
              {regions.map((region) => (
                <option key={region} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Prioridade
            <select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)} style={inputStyle}>
              {priorities.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Autoridade
            <input
              type="text"
              value={authorityFilter}
              onChange={(event) => setAuthorityFilter(event.target.value)}
              placeholder="IRS, AT, KSeF, CRA..."
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Execução (board)
            <select value={executionFilter} onChange={(event) => setExecutionFilter(event.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="TODO">TODO</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="DONE">DONE</option>
            </select>
          </label>
          <div style={{ display: "flex", alignItems: "end" }}>
            <div style={actionsRowStyle}>
              <button type="button" onClick={() => void loadCatalog()} style={buttonStyle} disabled={loading}>
                {loading ? "Atualizando..." : "Atualizar"}
              </button>
              <button type="button" onClick={exportBoardCsv} style={buttonStyle} disabled={filteredItems.length === 0}>
                Exportar CSV
              </button>
              <button type="button" onClick={exportBoardJson} style={buttonStyle} disabled={filteredItems.length === 0}>
                Exportar JSON
              </button>
              <button type="button" onClick={() => setOnlyInWave((current) => !current)} style={toggleButtonStyle(onlyInWave)}>
                {onlyInWave ? "Mostrando: somente IN WAVE" : "Filtro rápido: somente IN WAVE"}
              </button>
              <button type="button" onClick={activateFg1FocusPreset} style={focusPresetButtonStyle}>
                Preset foco FG-1 (IN WAVE + IN_PROGRESS)
              </button>
              <button type="button" onClick={activateFg1CloseoutPreset} style={closeoutPresetButtonStyle}>
                Preset fechamento FG-1 (IN WAVE + DONE)
              </button>
              <button type="button" onClick={handleResetFilters} style={buttonStyle}>
                Limpar filtros
              </button>
              <button type="button" onClick={() => void handleCopyFilterContext()} style={buttonStyle}>
                Copiar contexto do filtro
              </button>
            </div>
          </div>
        </div>
        {copyContextStatus ? <small style={copyStatusStyle}>{copyContextStatus}</small> : null}

        {!error ? (
          <div style={boardSummaryStyle}>
            <span style={statusChipStyle("TODO")}>To Do: {statusCounts.TODO}</span>
            <span style={statusChipStyle("IN_PROGRESS")}>In Progress: {statusCounts.IN_PROGRESS}</span>
            <span style={statusChipStyle("DONE")}>Done: {statusCounts.DONE}</span>
            <span style={inWaveSummaryStyle}>
              FG-1 IN WAVE: {inWaveCounts.TOTAL} (T:{inWaveCounts.TODO} | P:{inWaveCounts.IN_PROGRESS} | D:{inWaveCounts.DONE})
            </span>
            {activePresetLabel ? <span style={activePresetStyle}>{activePresetLabel}</span> : null}
          </div>
        ) : null}

        {!error ? (
          <div style={bulkActionsWrapStyle}>
            <strong style={{ fontSize: 12, color: "#cbd5e1" }}>Ação em lote (itens filtrados)</strong>
            <div style={actionsRowStyle}>
              <button type="button" style={buttonStyle} disabled={filteredItems.length === 0} onClick={() => applyStatusToFiltered("TODO")}>
                Marcar filtrados como TODO
              </button>
              <button
                type="button"
                style={inProgressButtonStyle}
                disabled={filteredItems.length === 0}
                onClick={() => applyStatusToFiltered("IN_PROGRESS")}
              >
                Marcar filtrados como IN_PROGRESS
              </button>
              <button type="button" style={doneButtonStyle} disabled={filteredItems.length === 0} onClick={() => applyStatusToFiltered("DONE")}>
                Marcar filtrados como DONE
              </button>
            </div>
          </div>
        ) : null}

        {error ? <div style={errorStyle}>{error}</div> : null}
        {!error ? <small style={summaryStyle}>Países filtrados: {filteredItems.length}</small> : null}

        {!error ? (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>País</th>
                  <th style={thStyle}>Região</th>
                  <th style={thStyle}>Autoridade</th>
                  <th style={thStyle}>Execução</th>
                  <th style={thStyle}>FG-1</th>
                  <th style={thStyle}>Prioridade</th>
                  <th style={thStyle}>Protocolo</th>
                  <th style={thStyle}>Stub Endpoint</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={`${item.country_code}-${item.authority}`}>
                    <td style={tdStyle}>{item.country_code}</td>
                    <td style={tdStyle}>{item.region}</td>
                    <td style={tdStyle}>{item.authority}</td>
                    <td style={tdStyle}>
                      <select
                        value={resolveExecutionStatus(executionStatusMap, item.country_code)}
                        onChange={(event) => handleExecutionStatusChange(item.country_code, event.target.value)}
                        style={statusSelectStyle(resolveExecutionStatus(executionStatusMap, item.country_code))}
                      >
                        <option value="TODO">TODO</option>
                        <option value="IN_PROGRESS">IN_PROGRESS</option>
                        <option value="DONE">DONE</option>
                      </select>
                    </td>
                    <td style={tdStyle}>
                      {fg1WaveCountrySet.has(String(item.country_code || "").toUpperCase()) ? (
                        <span style={inWaveBadgeStyle}>IN WAVE (FG-1)</span>
                      ) : (
                        <span style={outWaveBadgeStyle}>OUT WAVE</span>
                      )}
                    </td>
                    <td style={tdStyle}>{String(item.priority_tier || "-").toUpperCase()}</td>
                    <td style={tdStyle}>{item.protocol}</td>
                    <td style={tdStyle}>
                      <code style={codeStyle}>{item.stub_endpoint}</code>
                    </td>
                  </tr>
                ))}
                {!loading && filteredItems.length === 0 ? (
                  <tr>
                    <td style={tdStyle} colSpan={8}>
                      Nenhum país encontrado para os filtros aplicados.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
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
const filtersGridStyle = { marginTop: 10, display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", alignItems: "end" };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, color: "var(--fiscal-soft-text)", fontWeight: 600 };
const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-surface)",
  color: "var(--fiscal-text)",
};
const boardSummaryStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const buttonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  cursor: "pointer",
  fontWeight: 600,
};
const actionsRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const bulkActionsWrapStyle = {
  marginTop: 8,
  borderRadius: 10,
  border: "1px dashed var(--fiscal-box-border)",
  background: "var(--fiscal-box-bg)",
  padding: 10,
  display: "grid",
  gap: 8,
};
const toggleButtonStyle = (active) => ({
  ...buttonStyle,
  border: active ? "1px solid rgba(56,189,248,0.65)" : buttonStyle.border,
  background: active ? "rgba(14,116,144,0.24)" : buttonStyle.background,
  color: active ? "#bae6fd" : buttonStyle.color,
});
const inProgressButtonStyle = {
  ...buttonStyle,
  border: "1px solid rgba(245,158,11,0.65)",
  background: "rgba(245,158,11,0.18)",
  color: "#fde68a",
};
const doneButtonStyle = {
  ...buttonStyle,
  border: "1px solid rgba(34,197,94,0.65)",
  background: "rgba(34,197,94,0.18)",
  color: "#bbf7d0",
};
const inWaveSummaryStyle = {
  display: "inline-flex",
  padding: "4px 10px",
  borderRadius: 999,
  border: "1px solid rgba(56,189,248,0.65)",
  background: "rgba(14,116,144,0.22)",
  color: "#bae6fd",
  fontSize: 12,
  fontWeight: 700,
};
const activePresetStyle = {
  display: "inline-flex",
  padding: "4px 10px",
  borderRadius: 999,
  border: "1px solid rgba(192,132,252,0.65)",
  background: "rgba(126,34,206,0.18)",
  color: "#e9d5ff",
  fontSize: 12,
  fontWeight: 700,
};
const focusPresetButtonStyle = {
  ...buttonStyle,
  border: "1px solid rgba(217,70,239,0.65)",
  background: "rgba(217,70,239,0.16)",
  color: "#f5d0fe",
};
const closeoutPresetButtonStyle = {
  ...buttonStyle,
  border: "1px solid rgba(16,185,129,0.65)",
  background: "rgba(16,185,129,0.16)",
  color: "#bbf7d0",
};
const statusChipStyle = (status) => {
  if (status === "DONE") {
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
  if (status === "IN_PROGRESS") {
    return {
      display: "inline-flex",
      padding: "4px 10px",
      borderRadius: 999,
      border: "1px solid rgba(245,158,11,0.65)",
      background: "rgba(245,158,11,0.18)",
      color: "#fde68a",
      fontSize: 12,
      fontWeight: 700,
    };
  }
  return {
    display: "inline-flex",
    padding: "4px 10px",
    borderRadius: 999,
    border: "1px solid rgba(148,163,184,0.55)",
    background: "rgba(148,163,184,0.18)",
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: 700,
  };
};
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const summaryStyle = { marginTop: 10, display: "inline-flex", color: "var(--fiscal-accent-2)", fontWeight: 700 };
const copyStatusStyle = { marginTop: 8, display: "inline-flex", color: "var(--fiscal-accent-2)", fontWeight: 700 };
const tableWrapStyle = { marginTop: 10, overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 820 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-table-separator-strong)", padding: "8px 10px", fontSize: 13 };
const tdStyle = { borderBottom: "1px solid var(--fiscal-table-separator-soft)", padding: "8px 10px", verticalAlign: "top", fontSize: 13 };
const codeStyle = { color: "var(--fiscal-text)", background: "var(--fiscal-code-bg)", padding: "2px 6px", borderRadius: 6 };
const inWaveBadgeStyle = {
  display: "inline-flex",
  padding: "3px 8px",
  borderRadius: 999,
  border: "1px solid rgba(56,189,248,0.65)",
  background: "rgba(14,116,144,0.22)",
  color: "#bae6fd",
  fontSize: 11,
  fontWeight: 700,
};
const outWaveBadgeStyle = {
  display: "inline-flex",
  padding: "3px 8px",
  borderRadius: 999,
  border: "1px solid rgba(148,163,184,0.55)",
  background: "rgba(148,163,184,0.18)",
  color: "#cbd5e1",
  fontSize: 11,
  fontWeight: 700,
};

const EXECUTION_STATUS_STORAGE_KEY = "fiscal:countries:execution_status:v1";
const COUNTRIES_FILTERS_STORAGE_KEY = "fiscal:countries:filters:v1";

function loadExecutionStatusMap() {
  try {
    const raw = window.localStorage.getItem(EXECUTION_STATUS_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function persistExecutionStatusMap(mapValue) {
  try {
    window.localStorage.setItem(EXECUTION_STATUS_STORAGE_KEY, JSON.stringify(mapValue || {}));
  } catch {
    // no-op
  }
}

function loadCountriesFilters() {
  const fallback = {
    region: "ALL",
    priority: "ALL",
    authority: "",
    execution: "ALL",
    onlyInWave: false,
  };
  try {
    const raw = window.localStorage.getItem(COUNTRIES_FILTERS_STORAGE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return fallback;
    return {
      region: String(parsed.region || "ALL").toUpperCase(),
      priority: String(parsed.priority || "ALL").toLowerCase(),
      authority: String(parsed.authority || ""),
      execution: String(parsed.execution || "ALL").toUpperCase(),
      onlyInWave: Boolean(parsed.onlyInWave),
    };
  } catch {
    return fallback;
  }
}

function persistCountriesFilters(filtersValue) {
  try {
    window.localStorage.setItem(COUNTRIES_FILTERS_STORAGE_KEY, JSON.stringify(filtersValue || {}));
  } catch {
    // no-op
  }
}

function resolveExecutionStatus(statusMap, countryCode) {
  const normalizedCountry = String(countryCode || "").toUpperCase();
  const normalizedStatus = String(statusMap?.[normalizedCountry] || "TODO").toUpperCase();
  if (normalizedStatus === "IN_PROGRESS" || normalizedStatus === "DONE") return normalizedStatus;
  return "TODO";
}

function statusSelectStyle(status) {
  return {
    ...inputStyle,
    minWidth: 130,
    border:
      status === "DONE"
        ? "1px solid rgba(34,197,94,0.65)"
        : status === "IN_PROGRESS"
          ? "1px solid rgba(245,158,11,0.65)"
          : "1px solid rgba(148,163,184,0.55)",
    color: status === "DONE" ? "#bbf7d0" : status === "IN_PROGRESS" ? "#fde68a" : "#e2e8f0",
  };
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

function buildFilterContextText(input) {
  const authorityValue = String(input?.authorityFilter || "").trim() || "(vazio)";
  const presetValue = String(input?.activePresetLabel || "").trim() || "Preset ativo: Nenhum";
  const inWave = input?.inWaveCounts || { TOTAL: 0, TODO: 0, IN_PROGRESS: 0, DONE: 0 };
  return [
    "[FISCAL handoff] Contexto atual do filtro",
    `timestamp: ${new Date().toISOString()}`,
    `preset: ${presetValue}`,
    `region: ${String(input?.regionFilter || "ALL")}`,
    `priority: ${String(input?.priorityFilter || "ALL")}`,
    `authority: ${authorityValue}`,
    `execution: ${String(input?.executionFilter || "ALL")}`,
    `only_in_wave: ${Boolean(input?.onlyInWave) ? "true" : "false"}`,
    `filtered_items: ${Number(input?.filteredCount || 0)}`,
    `total_items: ${Number(input?.totalCount || 0)}`,
    `in_wave_summary: total=${Number(inWave.TOTAL || 0)} todo=${Number(inWave.TODO || 0)} in_progress=${Number(inWave.IN_PROGRESS || 0)} done=${Number(inWave.DONE || 0)}`,
  ].join("\n");
}
