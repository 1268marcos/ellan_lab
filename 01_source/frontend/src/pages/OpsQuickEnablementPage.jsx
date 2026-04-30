import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  OPS_ENABLEMENT_PAGE_VERSION,
  OPS_ENABLEMENT_STORAGE_KEY,
  buildOpsEnablementTrainingPayload,
  computeOpsEnablementProgress,
  loadOpsEnablementStateRaw,
  mergeOpsEnablementChecklist,
} from "../utils/fiscalSprint3OpsEnablement";

const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";

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

export default function OpsQuickEnablementPage() {
  const [trainee, setTrainee] = useState(() => String(loadOpsEnablementStateRaw()?.trainee || ""));
  const [role, setRole] = useState(() => String(loadOpsEnablementStateRaw()?.role || "OPS"));
  const [sessionNotes, setSessionNotes] = useState(() => String(loadOpsEnablementStateRaw()?.session_notes || ""));
  const [rows, setRows] = useState(() => mergeOpsEnablementChecklist(loadOpsEnablementStateRaw()?.checklist || {}));
  const [statusMsg, setStatusMsg] = useState("");

  useEffect(() => {
    const payload = {
      trainee,
      role,
      session_notes: sessionNotes,
      checklist: Object.fromEntries(
        rows.map((r) => [r.id, { done: r.done, marked_at: r.marked_at }])
      ),
      updated_at: new Date().toISOString(),
    };
    try {
      window.localStorage.setItem(OPS_ENABLEMENT_STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // no-op
    }
  }, [rows, trainee, role, sessionNotes]);

  const progress = useMemo(() => computeOpsEnablementProgress(rows), [rows]);

  function setRow(id, patch) {
    setRows((prev) =>
      prev.map((row) => {
        if (row.id !== id) return row;
        const next = { ...row, ...patch };
        if (Object.prototype.hasOwnProperty.call(patch, "done")) {
          next.marked_at = new Date().toISOString();
        }
        return next;
      })
    );
  }

  async function exportSignedJson() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const body = buildOpsEnablementTrainingPayload(nowIso, { trainee, role, notes: sessionNotes, rows });
    const signed = await buildSignedPayload(body);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_OPS_ENABLEMENT_${ts}.json`, signed);
    setStatusMsg("Treinamento exportado (JSON assinado).");
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  async function exportSignedZip() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const body = buildOpsEnablementTrainingPayload(nowIso, { trainee, role, notes: sessionNotes, rows });
    const signed = await buildSignedPayload(body);
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_OPS_ENABLEMENT_PACKAGE_${ts}.zip`, {
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_OPS_ENABLEMENT_${ts}.json`]: strToU8(JSON.stringify(signed, null, 2)),
    });
    setStatusMsg("Pacote ZIP auditável (treinamento Sprint 3).");
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  async function copySlackHandoff() {
    const nowIso = new Date().toISOString();
    const lines = [
      `*Treinamento rápido OPS/Suporte (Sprint 3) | ${nowIso}*`,
      `Participante: ${String(trainee || "-").trim() || "-"}`,
      `Papel: ${String(role || "-")}`,
      `Checklist: ${progress.done}/${progress.total} (${progress.pct}%)`,
      `Evidência: export JSON/ZIP em ops/quick-enablement (prefixo ${DAILY_AUDIT_PREFIX}).`,
    ];
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setStatusMsg("Handoff Slack copiado.");
    } catch (err) {
      setStatusMsg(`Falha ao copiar: ${String(err?.message || err)}`);
    }
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  function resetLocal() {
    const ok = window.confirm("Limpar rascunho local deste treinamento?");
    if (!ok) return;
    window.localStorage.removeItem(OPS_ENABLEMENT_STORAGE_KEY);
    setTrainee("");
    setRole("OPS");
    setSessionNotes("");
    setRows(mergeOpsEnablementChecklist({}));
    setStatusMsg("Rascunho limpo.");
    window.setTimeout(() => setStatusMsg(""), 2000);
  }

  return (
    <main style={{ maxWidth: 980, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif", color: "#0f172a" }}>
      <header style={{ marginBottom: 16 }}>
        <OpsPageTitleHeader title="OPS + Suporte — Treinamento rápido (Sprint 3)" versionLabel={OPS_ENABLEMENT_PAGE_VERSION} />
        <p style={{ marginTop: 8, color: "#475569", lineHeight: 1.5 }}>
          Roteiro curto (~15 minutos) para OPS e Suporte alinharem ferramentas fiscais e de incidente, com evidência auditável no padrão{" "}
          <code>{DAILY_AUDIT_PREFIX}</code>. Não substitui playbooks completos; acelera o primeiro dia útil em paralelo ao hardening Sprint 3.
        </p>
      </header>

      <section style={cardStyle}>
        <div style={toolbarStyle}>
          <label style={labelStyle}>
            Nome / matrícula
            <input value={trainee} onChange={(e) => setTrainee(e.target.value)} style={inputStyle} placeholder="Quem realizou o treinamento" />
          </label>
          <label style={labelStyle}>
            Papel
            <select value={role} onChange={(e) => setRole(e.target.value)} style={inputStyle}>
              <option value="OPS">OPS</option>
              <option value="SUPORTE_N1">Suporte N1</option>
              <option value="SUPORTE_N2">Suporte N2</option>
              <option value="AUDITORIA">Auditoria</option>
            </select>
          </label>
        </div>
        <label style={{ ...labelStyle, marginTop: 12 }}>
          Notas da sessão (opcional)
          <textarea value={sessionNotes} onChange={(e) => setSessionNotes(e.target.value)} rows={3} style={textareaStyle} placeholder="Tópicos cobertos, dúvidas, follow-up." />
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedJson()}>
            Exportar JSON assinado
          </button>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedZip()}>
            Exportar ZIP auditável
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => void copySlackHandoff()}>
            Copiar handoff Slack
          </button>
          <button type="button" style={buttonSecondaryStyle} onClick={() => resetLocal()}>
            Limpar rascunho
          </button>
        </div>
        <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <span style={chipStyle}>
            Progresso: {progress.done}/{progress.total} ({progress.pct}%)
          </span>
        </div>
        {statusMsg ? <small style={{ color: "#64748b", display: "block", marginTop: 8 }}>{statusMsg}</small> : null}
      </section>

      <section style={{ ...cardStyle, marginTop: 16 }}>
        <h2 style={{ margin: "0 0 10px", fontSize: 16 }}>Checklist guiado</h2>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {rows.map((row) => (
            <li key={row.id} style={rowStyle}>
              <label style={{ display: "flex", gap: 10, alignItems: "flex-start", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={row.done}
                  onChange={(e) => setRow(row.id, { done: e.target.checked })}
                  style={{ marginTop: 4 }}
                  aria-label={row.label}
                />
                <span>
                  <strong>{row.label}</strong>
                  <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>{row.description}</div>
                  <Link to={row.path} style={linkStyle}>
                    Abrir {row.path}
                  </Link>
                </span>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <p style={{ marginTop: 16, fontSize: 13, color: "#64748b" }}>
        Dica: após concluir o checklist, exporte o JSON ou ZIP e anexe ao handoff diário em <Link to="/fiscal/management-daily">fiscal/management-daily</Link> quando for o fechamento do turno.
      </p>
    </main>
  );
}

const cardStyle = { border: "1px solid #e2e8f0", borderRadius: 12, padding: 16, background: "#fff" };
const toolbarStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, fontWeight: 700, color: "#475569" };
const inputStyle = { borderRadius: 8, border: "1px solid #cbd5e1", padding: "8px 10px", fontSize: 14 };
const textareaStyle = { ...inputStyle, resize: "vertical", width: "100%", boxSizing: "border-box" };
const buttonStyle = { padding: "8px 14px", borderRadius: 10, border: "1px solid #0f172a", background: "#0f172a", color: "#fff", fontWeight: 700, cursor: "pointer" };
const buttonSecondaryStyle = { ...buttonStyle, background: "#fff", color: "#0f172a" };
const chipStyle = { display: "inline-flex", padding: "4px 10px", borderRadius: 999, border: "1px solid #cbd5e1", background: "#f8fafc", fontSize: 12, fontWeight: 700 };
const rowStyle = { borderBottom: "1px solid #f1f5f9", padding: "12px 0" };
const linkStyle = { display: "inline-block", marginTop: 6, color: "#2563eb", fontWeight: 700, fontSize: 13 };
