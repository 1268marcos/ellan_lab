import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";

const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const PAGE_VERSION = "fiscal/readiness-execution v1.1.0";
const STORAGE_KEY = "fiscal:readiness:execution:v1";
/** Mesmo storage key do fg1-gate: um sufixo de sessão único para todos os artefatos de handoff FG-1. */
const SESSION_SUFFIX_KEY = "fiscal:fg1:handoff:session_suffix";

function headersJson() {
  return { Accept: "application/json", "X-Internal-Token": INTERNAL_TOKEN };
}

export default function FiscalReadinessExecutionPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copyStatus, setCopyStatus] = useState("");
  const [actionPlan, setActionPlan] = useState(null);
  const [executionMap, setExecutionMap] = useState(() => loadExecutionMap());
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [onlyBlocked, setOnlyBlocked] = useState(true);
  const [exportCopyStatus, setExportCopyStatus] = useState("");

  async function loadData() {
    if (!INTERNAL_TOKEN) {
      setError("Token interno ausente/inválido (422/403). Configure VITE_INTERNAL_TOKEN com o valor correto.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${BILLING_BASE}/admin/fiscal/global/fg1/readiness-action-plan`, { method: "GET", headers: headersJson() });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(String(payload?.detail || "Falha ao carregar plano de execução de readiness."));
      setActionPlan(payload || null);
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
    void loadData();
  }, []);

  useEffect(() => {
    persistExecutionMap(executionMap);
  }, [executionMap]);

  const items = Array.isArray(actionPlan?.items) ? actionPlan.items : [];

  const mergedAll = useMemo(() => {
    return items.map((item) => {
      const code = String(item.country_code || "").toUpperCase();
      const execution = executionMap[code] || {};
      return {
        ...item,
        country_code: code,
        execution_status: String(execution.status || "TODO").toUpperCase(),
        owner: String(execution.owner || ""),
        eta: String(execution.eta || ""),
        notes: String(execution.notes || ""),
      };
    });
  }, [items, executionMap]);

  const brPtSnapshot = useMemo(() => {
    const pick = (code) => mergedAll.find((r) => r.country_code === code) || null;
    return { BR: pick("BR"), PT: pick("PT") };
  }, [mergedAll]);

  const rows = useMemo(() => {
    return mergedAll
      .filter((row) => (onlyBlocked ? Number(row.blocking_reasons_count || 0) > 0 : true))
      .filter((row) => (statusFilter === "ALL" ? true : row.execution_status === statusFilter));
  }, [mergedAll, statusFilter, onlyBlocked]);

  const counts = useMemo(() => {
    const summary = { TODO: 0, IN_PROGRESS: 0, DONE: 0 };
    for (const row of mergedAll) {
      const status = String(row.execution_status || "TODO").toUpperCase();
      if (summary[status] != null) summary[status] += 1;
    }
    return summary;
  }, [mergedAll]);

  function updateExecution(countryCode, patch) {
    const code = String(countryCode || "").toUpperCase();
    setExecutionMap((current) => ({ ...current, [code]: { ...current[code], ...patch } }));
  }

  async function copyExecutionHandoff() {
    const brLine = formatBrPtHandoffLine("BR", brPtSnapshot.BR);
    const ptLine = formatBrPtHandoffLine("PT", brPtSnapshot.PT);
    const text = [
      `[FG-1 readiness execution] ${new Date().toISOString()}`,
      `decision=${String(actionPlan?.decision || "-")}`,
      `status_counts TODO=${counts.TODO} IN_PROGRESS=${counts.IN_PROGRESS} DONE=${counts.DONE}`,
      `Trilha B: ${brLine}`,
      `Trilha B: ${ptLine}`,
      ...rows.slice(0, 10).map(
        (row) =>
          `${row.country_code} status=${row.execution_status} blocking=${Number(row.blocking_reasons_count || 0)} owner=${row.owner || "-"} eta=${row.eta || "-"}`
      ),
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("Resumo de execução copiado para handoff.");
      window.setTimeout(() => setCopyStatus(""), 2200);
    } catch {
      setCopyStatus("Falha ao copiar automaticamente.");
      window.setTimeout(() => setCopyStatus(""), 2400);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/fiscal/fg1-gate" style={shortcutLinkStyle}>
            Abrir fiscal/fg1-gate
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            Abrir fiscal/updates
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Readiness Execution Board" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>Board de execução diária para fechamento dos bloqueios FG-1 com owner, ETA e status por país.</p>

        <div style={filtersRowStyle}>
          <button type="button" style={buttonStyle} onClick={() => void loadData()} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <label style={labelStyle}>
            Status execução
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">ALL</option>
              <option value="TODO">TODO</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="DONE">DONE</option>
            </select>
          </label>
          <button type="button" style={buttonStyle} onClick={() => setOnlyBlocked((v) => !v)}>
            {onlyBlocked ? "Mostrando: somente bloqueados" : "Filtro rápido: somente bloqueados"}
          </button>
          <button type="button" style={buttonStyle} onClick={() => void copyExecutionHandoff()}>
            Copiar resumo handoff
          </button>
        </div>
        {copyStatus ? <small style={mutedTextStyle}>{copyStatus}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        {!error ? (
          <div style={summaryRowStyle}>
            <span style={chipStyle}>Decisão atual: {String(actionPlan?.decision || "-")}</span>
            <span style={chipStyle}>TODO: {counts.TODO}</span>
            <span style={chipStyle}>IN_PROGRESS: {counts.IN_PROGRESS}</span>
            <span style={chipStyle}>DONE: {counts.DONE}</span>
          </div>
        ) : null}

        {!error ? (
          <section style={brPtCardStyle}>
            <div style={brPtHeaderRowStyle}>
              <strong style={brPtTitleStyle}>Trilha B real — BR / PT (readiness FG-1)</strong>
              <div style={brPtLinksRowStyle}>
                <Link to="/ops/fiscal/providers#go-no-go-br" style={shortcutLinkStyle}>
                  Abrir gate BR
                </Link>
                <Link to="/ops/fiscal/providers#go-no-go-pt" style={shortcutLinkStyle}>
                  Abrir gate PT
                </Link>
              </div>
            </div>
            <div style={brPtGridStyle}>
              {(["BR", "PT"]).map((code) => {
                const row = brPtSnapshot[code];
                const blocked = row && Number(row.blocking_reasons_count || 0) > 0;
                if (!row) {
                  return (
                    <div key={code} style={brPtCellMutedStyle}>
                      <span style={brPtCodeStyle}>{code}</span>
                      <span>— não consta no readiness-action-plan desta onda.</span>
                    </div>
                  );
                }
                if (!blocked) {
                  return (
                    <div key={code} style={brPtCellOkStyle}>
                      <span style={brPtCodeStyle}>{code}</span>
                      <span>sem bloqueios no plano atual (readiness {String(row.status || "-")}).</span>
                    </div>
                  );
                }
                return (
                  <div key={code} style={brPtCellBlockedStyle}>
                    <span style={brPtCodeStyle}>{code}</span>
                    <span>
                      {Number(row.blocking_reasons_count)} bloqueio(s) · execução {row.execution_status} · owner{" "}
                      {row.owner || "—"}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>
        ) : null}

        {!error ? (
          <div style={exportRowStyle}>
            <span style={exportLabelStyle}>Handoff (export)</span>
            <button type="button" style={buttonStyle} onClick={() => exportReadinessExecutionJson(actionPlan, mergedAll, brPtSnapshot)}>
              Exportar board (JSON)
            </button>
            <button type="button" style={buttonStyle} onClick={() => exportReadinessExecutionCsv(actionPlan, mergedAll, brPtSnapshot)}>
              Exportar board (CSV)
            </button>
            <button type="button" style={buttonStyle} onClick={() => void copyReadinessExecutionLatestNames(setExportCopyStatus)}>
              Copiar nome latest atual
            </button>
          </div>
        ) : null}
        {exportCopyStatus ? <small style={mutedTextStyle}>{exportCopyStatus}</small> : null}

        {!error ? (
          <div style={tableWrapStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>País</th>
                  <th style={thStyle}>Bloqueios</th>
                  <th style={thStyle}>Status execução</th>
                  <th style={thStyle}>Owner</th>
                  <th style={thStyle}>ETA</th>
                  <th style={thStyle}>Ações recomendadas</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.country_code} style={rowHighlightStyle(row)}>
                    <td style={tdStyle}>{row.country_code}</td>
                    <td style={tdStyle}>{Number(row.blocking_reasons_count || 0)}</td>
                    <td style={tdStyle}>
                      <select
                        value={row.execution_status}
                        onChange={(e) => updateExecution(row.country_code, { status: e.target.value })}
                        style={inputStyle}
                      >
                        <option value="TODO">TODO</option>
                        <option value="IN_PROGRESS">IN_PROGRESS</option>
                        <option value="DONE">DONE</option>
                      </select>
                    </td>
                    <td style={tdStyle}>
                      <input value={row.owner} onChange={(e) => updateExecution(row.country_code, { owner: e.target.value })} style={inputStyle} />
                    </td>
                    <td style={tdStyle}>
                      <input value={row.eta} onChange={(e) => updateExecution(row.country_code, { eta: e.target.value })} style={inputStyle} />
                    </td>
                    <td style={tdStyle}>
                      <ul style={listStyle}>
                        {(row.recommended_actions || []).map((action) => (
                          <li key={`${row.country_code}-${action}`}>{action}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}

function loadExecutionMap() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function persistExecutionMap(value) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value || {}));
  } catch {
    // no-op
  }
}

function formatBrPtHandoffLine(code, row) {
  if (!row) return `${code}: fora do action-plan desta onda`;
  const n = Number(row.blocking_reasons_count || 0);
  if (n === 0) return `${code}: OK (0 bloqueios, readiness ${String(row.status || "-")})`;
  return `${code}: BLOQUEADO (${n}) exec=${row.execution_status} owner=${row.owner || "-"}`;
}

function rowHighlightStyle(row) {
  const code = String(row?.country_code || "").toUpperCase();
  const blocked = Number(row?.blocking_reasons_count || 0) > 0;
  if ((code === "BR" || code === "PT") && blocked) {
    return { background: "rgba(180, 120, 40, 0.12)" };
  }
  return {};
}

function exportReadinessExecutionJson(actionPlan, mergedAll, brPtSnapshot) {
  const sessionSuffix = getStableSessionSuffix();
  const payload = {
    exported_at: new Date().toISOString(),
    scope: "FG-1-READINESS-EXECUTION",
    file_suffix: sessionSuffix,
    wave: actionPlan?.wave ?? null,
    plan_version: actionPlan?.plan_version ?? null,
    decision: actionPlan?.decision ?? null,
    trilha_b_br_pt: buildBrPtExportBlock(brPtSnapshot),
    country_count: mergedAll.length,
    countries: mergedAll.map((row) => ({
      country_code: row.country_code,
      readiness_status: row.status ?? null,
      blocking_reasons_count: Number(row.blocking_reasons_count || 0),
      execution_status: row.execution_status,
      owner: row.owner,
      eta: row.eta,
      notes: row.notes,
      required_env_keys: row.required_env_keys || [],
      recommended_actions: row.recommended_actions || [],
    })),
  };
  downloadTextFile(`fg1_readiness_execution_latest_${sessionSuffix}.json`, JSON.stringify(payload, null, 2), "application/json");
}

function exportReadinessExecutionCsv(actionPlan, mergedAll, brPtSnapshot) {
  const sessionSuffix = getStableSessionSuffix();
  const exportedAt = new Date().toISOString();
  const header = [
    "scope",
    "exported_at",
    "wave",
    "plan_version",
    "global_decision",
    "country_code",
    "readiness_status",
    "blocking_reasons_count",
    "execution_status",
    "owner",
    "eta",
    "notes",
    "required_env_keys",
    "recommended_actions",
  ];
  const brBlock = buildBrPtExportBlock(brPtSnapshot);
  const dataRows = mergedAll.map((row) => [
    "FG-1-READINESS-EXECUTION",
    exportedAt,
    String(actionPlan?.wave ?? ""),
    String(actionPlan?.plan_version ?? ""),
    String(actionPlan?.decision ?? ""),
    row.country_code,
    String(row.status ?? ""),
    String(Number(row.blocking_reasons_count || 0)),
    row.execution_status,
    row.owner,
    row.eta,
    row.notes,
    (row.required_env_keys || []).join(" | "),
    (row.recommended_actions || []).join(" | "),
  ]);
  const prefixRows = [
    [
      "FG-1-READINESS-EXECUTION-BRPT",
      exportedAt,
      String(actionPlan?.wave ?? ""),
      String(actionPlan?.plan_version ?? ""),
      String(actionPlan?.decision ?? ""),
      "BR_SNAPSHOT",
      String(brBlock.BR?.readiness_status ?? ""),
      String(brBlock.BR?.blocking_reasons_count ?? ""),
      String(brBlock.BR?.execution_status ?? ""),
      String(brBlock.BR?.owner ?? ""),
      String(brBlock.BR?.eta ?? ""),
      String(brBlock.BR?.notes ?? ""),
      (brBlock.BR?.required_env_keys || []).join(" | "),
      (brBlock.BR?.recommended_actions || []).join(" | "),
    ],
    [
      "FG-1-READINESS-EXECUTION-BRPT",
      exportedAt,
      String(actionPlan?.wave ?? ""),
      String(actionPlan?.plan_version ?? ""),
      String(actionPlan?.decision ?? ""),
      "PT_SNAPSHOT",
      String(brBlock.PT?.readiness_status ?? ""),
      String(brBlock.PT?.blocking_reasons_count ?? ""),
      String(brBlock.PT?.execution_status ?? ""),
      String(brBlock.PT?.owner ?? ""),
      String(brBlock.PT?.eta ?? ""),
      String(brBlock.PT?.notes ?? ""),
      (brBlock.PT?.required_env_keys || []).join(" | "),
      (brBlock.PT?.recommended_actions || []).join(" | "),
    ],
  ];
  const csv = [header, ...prefixRows, ...dataRows].map((r) => r.map(escapeCsvCell).join(",")).join("\n");
  downloadTextFile(`fg1_readiness_execution_latest_${sessionSuffix}.csv`, csv, "text/csv;charset=utf-8");
}

function buildBrPtExportBlock(brPtSnapshot) {
  const mapRow = (row) =>
    row
      ? {
          country_code: row.country_code,
          readiness_status: row.status ?? null,
          blocking_reasons_count: Number(row.blocking_reasons_count || 0),
          blocked: Number(row.blocking_reasons_count || 0) > 0,
          execution_status: row.execution_status,
          owner: row.owner,
          eta: row.eta,
          notes: row.notes,
          required_env_keys: row.required_env_keys || [],
          recommended_actions: row.recommended_actions || [],
        }
      : null;
  return { BR: mapRow(brPtSnapshot?.BR), PT: mapRow(brPtSnapshot?.PT) };
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
  try {
    const existing = window.sessionStorage.getItem(SESSION_SUFFIX_KEY);
    if (existing) return String(existing);
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const suffix = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
    window.sessionStorage.setItem(SESSION_SUFFIX_KEY, suffix);
    return suffix;
  } catch {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}`;
  }
}

async function copyReadinessExecutionLatestNames(setStatus) {
  const suffix = getStableSessionSuffix();
  const jsonName = `fg1_readiness_execution_latest_${suffix}.json`;
  const csvName = `fg1_readiness_execution_latest_${suffix}.csv`;
  const payload = [jsonName, csvName].join("\n");
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(payload);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = payload;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "absolute";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setStatus(`Nomes latest copiados: ${jsonName} e ${csvName}`);
    window.setTimeout(() => setStatus(""), 2600);
  } catch {
    setStatus("Falha ao copiar automaticamente. Use o padrão fg1_readiness_execution_latest_<sessão>.{json,csv}.");
    window.setTimeout(() => setStatus(""), 3000);
  }
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10 };
const shortcutLinkStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", textDecoration: "none", fontWeight: 700, fontSize: 13 };
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const filtersRowStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "end" };
const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "var(--fiscal-soft-text)", fontWeight: 600 };
const inputStyle = { width: "100%", minWidth: 140, padding: "8px 10px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-surface)", color: "var(--fiscal-text)" };
const buttonStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", cursor: "pointer", fontWeight: 600 };
const errorStyle = { marginTop: 10, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12 };
const summaryRowStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const chipStyle = { display: "inline-flex", padding: "4px 10px", borderRadius: 999, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", fontSize: 12, fontWeight: 700 };
const tableWrapStyle = { marginTop: 10, overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 980 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-table-separator-strong)", padding: "8px 10px", fontSize: 13 };
const tdStyle = { borderBottom: "1px solid var(--fiscal-table-separator-soft)", padding: "8px 10px", verticalAlign: "top", fontSize: 13 };
const listStyle = { margin: 0, paddingLeft: 16, display: "grid", gap: 4, color: "var(--fiscal-soft-text)" };
const exportRowStyle = { marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" };
const exportLabelStyle = { fontSize: 12, fontWeight: 700, color: "var(--fiscal-soft-text)", marginRight: 4 };
const brPtCardStyle = {
  marginTop: 12,
  padding: 12,
  borderRadius: 12,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-surface)",
};
const brPtHeaderRowStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap" };
const brPtTitleStyle = { fontSize: 14, color: "var(--fiscal-text)" };
const brPtLinksRowStyle = { display: "flex", gap: 8, flexWrap: "wrap" };
const brPtGridStyle = { marginTop: 10, display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" };
const brPtCellMutedStyle = { fontSize: 13, color: "var(--fiscal-soft-text)", display: "grid", gap: 4 };
const brPtCellOkStyle = { fontSize: 13, color: "var(--fiscal-soft-text)", display: "grid", gap: 4, padding: 8, borderRadius: 8, border: "1px solid var(--fiscal-table-separator-soft)" };
const brPtCellBlockedStyle = {
  fontSize: 13,
  color: "var(--fiscal-text)",
  display: "grid",
  gap: 4,
  padding: 8,
  borderRadius: 8,
  border: "1px solid rgba(200, 140, 60, 0.55)",
  background: "rgba(200, 140, 60, 0.12)",
};
const brPtCodeStyle = { fontWeight: 800, letterSpacing: "0.04em" };
