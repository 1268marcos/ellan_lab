
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import {
  clampSprint2GatePct as clampPct,
  loadSprint2FinanceGateV2State as loadState,
  SPRINT2_FINANCE_GATE_COMMITTEE_REF as COMMITTEE_REF,
  SPRINT2_FINANCE_GATE_V2_STORAGE_KEY as STORAGE_KEY,
  SPRINT2_FINANCE_GATE_V2_THRESHOLDS as THRESHOLDS,
} from "../utils/fiscalSprint2FinanceGate";

const PAGE_VERSION = "fiscal/sprint2-finance-gate v1.0.1-shared-gate-util";
const GATE_VERSION = "v2";

async function computeSha256Hex(text) {
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(String(text || ""));
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function saveState(payload) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

export default function FiscalSprint2FinanceGatePage() {
  const [fiscalPct, setFiscalPct] = useState(26);
  const [accountingPct, setAccountingPct] = useState(15);
  const [consolidatedPct, setConsolidatedPct] = useState(52);
  const [p0Note, setP0Note] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const hydrate = useCallback(() => {
    const s = loadState();
    if (!s) return;
    setFiscalPct(clampPct(s.fiscal_percent ?? 26));
    setAccountingPct(clampPct(s.accounting_percent ?? 15));
    setConsolidatedPct(clampPct(s.consolidated_percent ?? 52));
    setP0Note(String(s.p0_evidence_note || ""));
  }, []);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const p0Ok = useMemo(() => String(p0Note || "").trim().length >= 24, [p0Note]);

  const fiscalOk = fiscalPct >= THRESHOLDS.fiscal;
  const accountingOk = accountingPct >= THRESHOLDS.accounting;
  const consolidatedOk = consolidatedPct >= THRESHOLDS.consolidated;

  const overallPass = fiscalOk && accountingOk && consolidatedOk && p0Ok;

  const nextPhaseLabel = overallPass
    ? "Fase B — Sprint 3 como sprint ideal (expandir hardening / net-new S3 conforme plano)"
    : "Fase A — Sprint 2 dominante; S3/S4 sem net-new (paralelo seguro apenas)";

  function persist() {
    saveState({
      fiscal_percent: clampPct(fiscalPct),
      accounting_percent: clampPct(accountingPct),
      consolidated_percent: clampPct(consolidatedPct),
      p0_evidence_note: String(p0Note || ""),
      updated_at: new Date().toISOString(),
    });
    setStatusMsg("Estado gravado no navegador (localStorage).");
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  async function exportSignedJson() {
    const payload = {
      scope: "SPRINT2_FINANCE_GATE_V2",
      gate_version: GATE_VERSION,
      committee_reference_date: COMMITTEE_REF,
      fiscal_percent: clampPct(fiscalPct),
      accounting_percent: clampPct(accountingPct),
      consolidated_percent: clampPct(consolidatedPct),
      thresholds: THRESHOLDS,
      p0_evidence_note: String(p0Note || ""),
      metrics_pass: {
        fiscal: fiscalOk,
        accounting: accountingOk,
        consolidated: consolidatedOk,
        p0_proof: p0Ok,
      },
      overall_pass: overallPass,
      next_sprint_ideal_hint: nextPhaseLabel,
      exported_at: new Date().toISOString(),
    };
    const body = JSON.stringify(payload, null, 2);
    const signed = {
      integrity: { algorithm: "SHA-256", content_sha256: await computeSha256Hex(body) },
      payload,
    };
    const out = JSON.stringify(signed, null, 2);
    const stamp = new Date().toISOString().slice(0, 10).replaceAll("-", "");
    const blob = new Blob([out], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ELLAN_FISCAL_DAILY_SPRINT2_FINANCE_GATE_${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    setStatusMsg("JSON assinado (SHA-256) descarregado.");
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  async function copySignedJson() {
    const payload = {
      scope: "SPRINT2_FINANCE_GATE_V2",
      gate_version: GATE_VERSION,
      committee_reference_date: COMMITTEE_REF,
      fiscal_percent: clampPct(fiscalPct),
      accounting_percent: clampPct(accountingPct),
      consolidated_percent: clampPct(consolidatedPct),
      thresholds: THRESHOLDS,
      p0_evidence_note: String(p0Note || ""),
      metrics_pass: {
        fiscal: fiscalOk,
        accounting: accountingOk,
        consolidated: consolidatedOk,
        p0_proof: p0Ok,
      },
      overall_pass: overallPass,
      next_sprint_ideal_hint: nextPhaseLabel,
      exported_at: new Date().toISOString(),
    };
    const body = JSON.stringify(payload, null, 2);
    const signed = {
      integrity: { algorithm: "SHA-256", content_sha256: await computeSha256Hex(body) },
      payload,
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(signed, null, 2));
      setStatusMsg("Payload assinado copiado para a área de transferência.");
    } catch {
      setStatusMsg("Não foi possível copiar automaticamente; use Exportar JSON.");
    }
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  const billingBase = import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020";

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <a href={buildFiscalSwaggerUrl(billingBase)} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
          <Link to="/fiscal/management-daily" style={shortcutLinkStyle}>
            Abrir fiscal/management-daily
          </Link>
          <Link to="/fiscal/accounting-close" style={shortcutLinkStyle}>
            Abrir fiscal/accounting-close
          </Link>
          <Link to="/fiscal/updates" style={shortcutLinkStyle}>
            Abrir fiscal/updates
          </Link>
          <Link to="/fiscal/sprint3-partner-audit" style={shortcutLinkStyle}>
            Abrir fiscal/sprint3-partner-audit (Sprint 3 P0-1)
          </Link>
        </div>

        <OpsPageTitleHeader title="FISCAL - Gate financeiro Sprint 2 (comité v2)" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Próximo sprint previsto no plano: enquanto o gate <strong>v2</strong> (comité <strong>{COMMITTEE_REF}</strong>) não
          fechar, a Sprint 2 permanece dominante; após <strong>PASS</strong> cumulativo, a <strong>Sprint 3</strong> torna-se o sprint ideal
          para expansão de hardening. Sprint 4 (Go/No-Go pleno) na fase C, com S3 estável. Fonte:{" "}
          <code>docs/PLANO_30_DIAS_GLOBAL_POR_PERSONA.md</code> (subsecções gate v2 e sequência).
        </p>

        <div style={bannerStyle(overallPass)}>
          <strong>{overallPass ? "PASS — liberar net-new S3/S4 conforme plano" : "NO_GO — manter congelamento de net-new"}</strong>
          <div style={{ marginTop: 6, fontSize: 13 }}>{nextPhaseLabel}</div>
        </div>

        <h2 style={h2Style}>Limiares v2 (AND + comprovação P0)</h2>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Métrica</th>
              <th style={thStyle}>Limiar</th>
              <th style={thStyle}>Valor</th>
              <th style={thStyle}>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={tdStyle}>Fiscal (ELLAN LAB + partners)</td>
              <td style={tdStyle}>≥ {THRESHOLDS.fiscal}%</td>
              <td style={tdStyle}>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={fiscalPct}
                  onChange={(e) => setFiscalPct(clampPct(e.target.value))}
                  style={inputStyle}
                  aria-label="Percentual fiscal"
                />
              </td>
              <td style={tdStyle}>{fiscalOk ? "OK" : "FALTA"}</td>
            </tr>
            <tr>
              <td style={tdStyle}>Contábil (ELLAN LAB + partners)</td>
              <td style={tdStyle}>≥ {THRESHOLDS.accounting}%</td>
              <td style={tdStyle}>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={accountingPct}
                  onChange={(e) => setAccountingPct(clampPct(e.target.value))}
                  style={inputStyle}
                  aria-label="Percentual contábil"
                />
              </td>
              <td style={tdStyle}>{accountingOk ? "OK" : "FALTA"}</td>
            </tr>
            <tr>
              <td style={tdStyle}>Consolidado Sprint 2 (macro)</td>
              <td style={tdStyle}>≥ {THRESHOLDS.consolidated}%</td>
              <td style={tdStyle}>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={consolidatedPct}
                  onChange={(e) => setConsolidatedPct(clampPct(e.target.value))}
                  style={inputStyle}
                  aria-label="Percentual consolidado sprint 2"
                />
              </td>
              <td style={tdStyle}>{consolidatedOk ? "OK" : "FALTA"}</td>
            </tr>
          </tbody>
        </table>

        <label style={labelStyle}>
          Comprovação P0 (mín. 24 caracteres — referência a anexo daily/ZIP ou IDs de trilha)
          <textarea
            value={p0Note}
            onChange={(e) => setP0Note(e.target.value)}
            rows={4}
            style={textareaStyle}
            placeholder="Ex.: Anexo ELLAN_FISCAL_DAILY_* com bloco D11/D13; order_id …"
          />
        </label>
        <p style={mutedTextStyle}>Comprovação P0: {p0Ok ? "OK" : `FALTA (${String(p0Note || "").trim().length}/24 caracteres)`}</p>

        <div style={toolbarStyle}>
          <button type="button" style={buttonStyle} onClick={persist}>
            Gravar estado local
          </button>
          <button
            type="button"
            style={buttonStyle}
            onClick={() => {
              setFiscalPct(26);
              setAccountingPct(15);
              setConsolidatedPct(52);
              setP0Note("");
              setStatusMsg("Valores resetados ao snapshot de referência do plano.");
              window.setTimeout(() => setStatusMsg(""), 2200);
            }}
          >
            Reset referência plano (~26 / ~15 / ~52)
          </button>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedJson()}>
            Exportar JSON assinado
          </button>
          <button type="button" style={buttonStyle} onClick={() => void copySignedJson()}>
            Copiar JSON assinado
          </button>
        </div>
        {statusMsg ? <p style={{ color: "var(--fiscal-text)", marginTop: 8 }}>{statusMsg}</p> : null}
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 12 };
const shortcutLinkStyle = { color: "var(--fiscal-link)", fontWeight: 600 };
const mutedTextStyle = { color: "var(--fiscal-muted)", fontSize: 14, lineHeight: 1.5 };
const h2Style = { fontSize: 16, marginTop: 20, marginBottom: 8 };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 14 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-card-border)", padding: "8px 6px" };
const tdStyle = { borderBottom: "1px solid var(--fiscal-card-border)", padding: "8px 6px", verticalAlign: "middle" };
const inputStyle = { width: 72, padding: 6, borderRadius: 8, border: "1px solid var(--fiscal-card-border)" };
const textareaStyle = { width: "100%", marginTop: 6, padding: 10, borderRadius: 8, border: "1px solid var(--fiscal-card-border)", fontFamily: "inherit" };
const labelStyle = { display: "block", marginTop: 16, fontWeight: 600, fontSize: 14 };
const toolbarStyle = { display: "flex", flexWrap: "wrap", gap: 10, marginTop: 16 };
const buttonStyle = { padding: "8px 14px", borderRadius: 8, border: "1px solid var(--fiscal-card-border)", cursor: "pointer", background: "var(--fiscal-card-bg)" };

function bannerStyle(pass) {
  return {
    marginTop: 12,
    marginBottom: 8,
    padding: 12,
    borderRadius: 12,
    border: `1px solid ${pass ? "#1b7f4a" : "#a61b1b"}`,
    background: pass ? "rgba(27, 127, 74, 0.12)" : "rgba(166, 27, 27, 0.1)",
    color: "var(--fiscal-text)",
  };
}

