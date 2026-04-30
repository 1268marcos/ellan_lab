import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import { buildP01bPartnerReconciliationSlice } from "../utils/fiscalP01bDailyPackage";
import { saveSprint3PartnerAuditMirrorForDaily } from "../utils/fiscalSprint3PartnerAuditMirror";

const PAGE_VERSION = "fiscal/sprint3-partner-audit v1.2.0-daily-mirror";
const SPRINT3_AUDIT_SESSION_LS = "fiscal:sprint3:partner-audit:handoff:v1";

const SPRINT3_HANDOFF_CHECKLIST = [
  { id: "h1", label: "Trilha E2E atualizada nesta sessão (botão «Atualizar trilha» ou carga inicial)." },
  { id: "h2", label: "Campos de cobertura backend lidos (decision, materialized_rate, raw_rate, total)." },
  { id: "h3", label: "Tabela por partner_id revista (top gaps / severidades)." },
  { id: "h4", label: "Decisão sobre cruzamento D11 documentada (incluir ou não + motivo)." },
  { id: "h5", label: "Slice assinado exportado ou copiado para anexar ao handoff/daily." },
  { id: "h6", label: "Correlação mínima referida no handoff (order_id / partner_id / batch_id quando aplicável)." },
];

function defaultHandoffChecks() {
  return Object.fromEntries(SPRINT3_HANDOFF_CHECKLIST.map((row) => [row.id, false]));
}

function readHandoffChecksFromLs() {
  const base = defaultHandoffChecks();
  try {
    const raw = window.localStorage.getItem(SPRINT3_AUDIT_SESSION_LS);
    if (!raw) return base;
    const parsed = JSON.parse(raw);
    const merged = { ...base };
    for (const row of SPRINT3_HANDOFF_CHECKLIST) {
      if (typeof parsed[row.id] === "boolean") merged[row.id] = parsed[row.id];
    }
    return merged;
  } catch {
    return base;
  }
}

function downloadJsonFile(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
const BILLING_BASE = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";
const FISCAL_D11_HANDOFF_KEY = "ellan_ops_fiscal_d11_handoff_v1";
const E2E_LIMIT = 500;

function headersJson() {
  return {
    Accept: "application/json",
    "X-Internal-Token": INTERNAL_TOKEN,
  };
}

function loadD11Handoff() {
  try {
    const raw = window.localStorage.getItem(FISCAL_D11_HANDOFF_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function computeSha256Hex(text) {
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(String(text || ""));
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export default function FiscalSprint3PartnerAuditPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [auditPayload, setAuditPayload] = useState(null);
  const [slice, setSlice] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [includeD11, setIncludeD11] = useState(true);
  const [handoffChecks, setHandoffChecks] = useState(() => readHandoffChecksFromLs());

  const handoffDone = useMemo(
    () => SPRINT3_HANDOFF_CHECKLIST.filter((row) => handoffChecks[row.id]).length,
    [handoffChecks],
  );

  useEffect(() => {
    try {
      window.localStorage.setItem(SPRINT3_AUDIT_SESSION_LS, JSON.stringify(handoffChecks));
    } catch {
      /* ignore */
    }
  }, [handoffChecks]);

  const recomputeSlice = useCallback((e2e, useD11) => {
    const d11 = useD11 ? loadD11Handoff() : null;
    const built = buildP01bPartnerReconciliationSlice({
      e2ePayload: e2e,
      d11Handoff: d11,
      generatedAt: new Date().toISOString(),
      source: "fiscal/sprint3-partner-audit",
    });
    setSlice(built);
  }, []);

  async function loadAudit() {
    if (!INTERNAL_TOKEN) {
      setError("Configure VITE_INTERNAL_TOKEN.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(
        `${BILLING_BASE}/admin/fiscal/global/sprint3/e2e-audit-trail?status=OPEN&limit=${E2E_LIMIT}`,
        { method: "GET", headers: headersJson() }
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(String(body?.detail || body?.message || "Falha e2e-audit-trail"));
      }
      setAuditPayload(body);
      recomputeSlice(body, includeD11);
    } catch (e) {
      setError(String(e?.message || e));
      setAuditPayload(null);
      setSlice(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAudit();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- carga inicial
  }, []);

  useEffect(() => {
    if (auditPayload) {
      recomputeSlice(auditPayload, includeD11);
    }
  }, [includeD11, auditPayload, recomputeSlice]);

  async function exportSignedSlice() {
    if (!slice) return;
    const json = JSON.stringify(slice, null, 2);
    const signed = {
      integrity: { algorithm: "SHA-256", content_sha256: await computeSha256Hex(json) },
      payload: slice,
    };
    const out = JSON.stringify(signed, null, 2);
    const stamp = new Date().toISOString().slice(0, 10).replaceAll("-", "");
    const blob = new Blob([out], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ELLAN_FISCAL_DAILY_SPRINT3_PARTNER_AUDIT_${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    setStatusMsg("Slice assinado descarregado.");
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  function persistMirrorForDailyZip() {
    if (!slice) return;
    saveSprint3PartnerAuditMirrorForDaily({
      saved_at: new Date().toISOString(),
      source_page: PAGE_VERSION,
      include_d11: includeD11,
      handoff_checks: handoffChecks,
      audit_summary: auditPayload
        ? {
            decision: auditPayload.decision ?? null,
            coverage: auditPayload.coverage ?? null,
          }
        : null,
      slice,
    });
    setStatusMsg("Espelho gravado para pacote diário / close (.zip) — localStorage.");
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  async function copySignedSlice() {
    if (!slice) return;
    const json = JSON.stringify(slice, null, 2);
    const signed = {
      integrity: { algorithm: "SHA-256", content_sha256: await computeSha256Hex(json) },
      payload: slice,
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(signed, null, 2));
      setStatusMsg("Slice assinado copiado.");
    } catch {
      setStatusMsg("Falha ao copiar; use Exportar.");
    }
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  const partners = Array.isArray(slice?.partners) ? slice.partners : [];
  const cov = auditPayload?.coverage || {};

  function toggleHandoff(id) {
    setHandoffChecks((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function exportHandoffSessionJson() {
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    downloadJsonFile(`SPRINT3_PARTNER_AUDIT_HANDOFF_SESSION_${ts}.json`, {
      page: PAGE_VERSION,
      exportedAt: new Date().toISOString(),
      include_d11: includeD11,
      slice_summary: slice
        ? {
            partners_rows: partners.length,
            has_d11_cross: Boolean(slice.d11_cross_check),
            decision: auditPayload?.decision ?? null,
          }
        : null,
      checklist: SPRINT3_HANDOFF_CHECKLIST.map((row) => ({
        id: row.id,
        label: row.label,
        done: Boolean(handoffChecks[row.id]),
      })),
      score: handoffDone,
      total: SPRINT3_HANDOFF_CHECKLIST.length,
    });
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(BILLING_BASE)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Swagger FISCAL
          </a>
          <Link to="/fiscal/slo-alerts" style={shortcutLinkStyle}>
            fiscal/slo-alerts
          </Link>
          <Link to="/fiscal/sprint2-finance-gate" style={shortcutLinkStyle}>
            fiscal/sprint2-finance-gate
          </Link>
          <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>
            fiscal/management-daily
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            fiscal/updates
          </Link>
        </div>

        <OpsPageTitleHeader title="FISCAL - Sprint 3 auditoria por parceiro (P0-1)" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Próximo sprint (Sprint 3): ampliação da <strong>auditoria ponta a ponta</strong> com rollup por <code>partner_id</code> sobre
          <code> GET /admin/fiscal/global/sprint3/e2e-audit-trail</code>, reutilizando o mesmo contrato do anexo P0-1b (<code>buildP01bPartnerReconciliationSlice</code>).
          Cruzamento opcional com snapshot D11 em <code>localStorage</code> (<code>{FISCAL_D11_HANDOFF_KEY}</code>).
        </p>

        <div style={toolbarStyle}>
          <button type="button" style={buttonStyle} onClick={() => void loadAudit()} disabled={loading}>
            {loading ? "A carregar…" : "Atualizar trilha"}
          </button>
          <label style={inlineLabelStyle}>
            <input type="checkbox" checked={includeD11} onChange={(e) => setIncludeD11(e.target.checked)} /> Incluir cruzamento D11
          </label>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedSlice()} disabled={!slice}>
            Exportar slice assinado
          </button>
          <button type="button" style={buttonStyle} onClick={() => void copySignedSlice()} disabled={!slice}>
            Copiar slice assinado
          </button>
          <button type="button" style={buttonStyle} onClick={persistMirrorForDailyZip} disabled={!slice}>
            Gravar espelho para pacote diário
          </button>
        </div>
        {error ? <p style={errStyle}>{error}</p> : null}
        {statusMsg ? <p style={{ marginTop: 8 }}>{statusMsg}</p> : null}

        {auditPayload ? (
          <div style={{ marginTop: 16 }}>
            <h2 style={h2Style}>Cobertura E2E (backend)</h2>
            <ul style={listStyle}>
              <li>
                <strong>decision:</strong> {String(auditPayload.decision ?? "—")}
              </li>
              <li>
                <strong>materialized_rate:</strong> {cov.materialized_rate != null ? Number(cov.materialized_rate).toFixed(4) : "—"}
              </li>
              <li>
                <strong>raw_rate:</strong> {cov.raw_rate != null ? Number(cov.raw_rate).toFixed(4) : "—"}
              </li>
              <li>
                <strong>total linhas:</strong> {cov.total != null ? String(cov.total) : "—"}
              </li>
            </ul>
          </div>
        ) : null}

        {slice ? (
          <div style={{ marginTop: 16 }}>
            <h2 style={h2Style}>Parceiros (ordenado por linhas de gap)</h2>
            {slice.d11_cross_check ? (
              <p style={mutedTextStyle}>
                D11 cross: parceiros distintos E2E <strong>{slice.d11_cross_check.e2e_distinct_partners}</strong> · snapshot parceiros{" "}
                <strong>{slice.d11_cross_check.storage_unique_partners}</strong>
              </p>
            ) : (
              <p style={mutedTextStyle}>Cruzamento D11: desativado ou snapshot ausente.</p>
            )}
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>partner_id</th>
                    <th style={thStyle}>gap_rows</th>
                    <th style={thStyle}>materialized</th>
                    <th style={thStyle}>raw_complete</th>
                    <th style={thStyle}>severidades (top)</th>
                  </tr>
                </thead>
                <tbody>
                  {partners.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={tdStyle}>
                        Sem linhas na amostra (lista vazia ou limite 0).
                      </td>
                    </tr>
                  ) : (
                    partners.map((p) => (
                      <tr key={p.partner_id}>
                        <td style={tdStyle}>
                          <code>{p.partner_id}</code>
                        </td>
                        <td style={tdStyle}>{p.gap_rows}</td>
                        <td style={tdStyle}>{p.materialized_complete}</td>
                        <td style={tdStyle}>{p.raw_complete}</td>
                        <td style={tdStyle}>
                          <code style={{ fontSize: 12 }}>{JSON.stringify(p.severities || {})}</code>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        <section style={handoffSectionStyle} aria-labelledby="sprint3-partner-handoff-h">
          <h2 id="sprint3-partner-handoff-h" style={h2Style}>
            Handoff de sessão — auditoria por parceiro (Sprint 3)
          </h2>
          <p style={mutedTextStyle}>
            Progresso: <strong>{handoffDone}</strong> / {SPRINT3_HANDOFF_CHECKLIST.length}. Estado em{" "}
            <code>{SPRINT3_AUDIT_SESSION_LS}</code>. Exporte JSON para anexar ao daily e fechar o ciclo «trilha + handoff» do
            checklist do plano. Para ZIP em{" "}
            <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>
              fiscal/management-daily
            </Link>
            , use «Gravar espelho para pacote diário» (anexo com scope <code>SPRINT3_PARTNER_AUDIT_MIRROR_ATTACH</code>).
          </p>
          <ul style={handoffListStyle}>
            {SPRINT3_HANDOFF_CHECKLIST.map((row) => (
              <li key={row.id} style={handoffLiStyle}>
                <label style={handoffLabelStyle}>
                  <input
                    type="checkbox"
                    checked={Boolean(handoffChecks[row.id])}
                    onChange={() => toggleHandoff(row.id)}
                    style={handoffInputStyle}
                  />
                  <span>{row.label}</span>
                </label>
              </li>
            ))}
          </ul>
          <button type="button" style={buttonStyle} onClick={exportHandoffSessionJson}>
            Exportar handoff de sessão (JSON)
          </button>
        </section>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 12 };
const shortcutLinkStyle = { color: "var(--fiscal-link)", fontWeight: 600 };
const mutedTextStyle = { color: "var(--fiscal-muted)", fontSize: 14, lineHeight: 1.5 };
const h2Style = { fontSize: 16, marginTop: 12, marginBottom: 8 };
const listStyle = { margin: 0, paddingLeft: 18, fontSize: 14 };
const toolbarStyle = { display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", marginTop: 8 };
const buttonStyle = { padding: "8px 14px", borderRadius: 8, border: "1px solid var(--fiscal-card-border)", cursor: "pointer", background: "var(--fiscal-card-bg)" };
const inlineLabelStyle = { display: "inline-flex", alignItems: "center", gap: 8, fontSize: 14 };
const errStyle = { color: "#c62828", marginTop: 8 };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 13 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-card-border)", padding: "6px 4px" };
const tdStyle = { borderBottom: "1px solid var(--fiscal-card-border)", padding: "6px 4px", verticalAlign: "top" };

const handoffSectionStyle = {
  marginTop: 20,
  padding: 14,
  borderRadius: 12,
  border: "1px solid rgba(129,140,248,0.45)",
  background: "rgba(79,70,229,0.1)",
};

const handoffListStyle = {
  margin: "0 0 12px",
  paddingLeft: 0,
  listStyle: "none",
  display: "grid",
  gap: 10,
};

const handoffLiStyle = { margin: 0 };

const handoffLabelStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-start",
  fontSize: 13,
  lineHeight: 1.45,
  cursor: "pointer",
};

const handoffInputStyle = { marginTop: 3, flexShrink: 0 };
