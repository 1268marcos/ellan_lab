import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import "../styles/opsQuickEnablementChrome.css";
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
  const raw = loadOpsEnablementStateRaw();
  const [trainee, setTrainee] = useState(() => String(raw?.trainee || ""));
  const [role, setRole] = useState(() => String(raw?.role || "OPS"));
  const [sessionNotes, setSessionNotes] = useState(() => String(raw?.session_notes || ""));
  const [rows, setRows] = useState(() => mergeOpsEnablementChecklist(raw?.checklist || {}));
  const [statusMsg, setStatusMsg] = useState("");

  useEffect(() => {
    const payload = {
      trainee,
      role,
      session_notes: sessionNotes,
      checklist: Object.fromEntries(rows.map((r) => [r.id, { done: r.done, marked_at: r.marked_at }])),
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
    <main className="ops-quick-enablement-chrome__main" data-testid="ops-quick-enablement-page">
      <header className="ops-quick-enablement-chrome__header">
        <OpsPageTitleHeader title="OPS + Suporte — Treinamento rápido (Sprint 3)" versionLabel={OPS_ENABLEMENT_PAGE_VERSION} />
        <p className="ops-quick-enablement-chrome__intro">
          Roteiro curto (~15 minutos) para OPS e Suporte alinharem ferramentas fiscais e de incidente, com evidência auditável no padrão{" "}
          <code>{DAILY_AUDIT_PREFIX}</code>. Não substitui playbooks completos; acelera o primeiro dia útil em paralelo ao hardening Sprint 3.
        </p>
      </header>

      <section className="ops-quick-enablement-chrome__card">
        <div className="ops-quick-enablement-chrome__toolbar">
          <label className="ops-quick-enablement-chrome__label">
            Nome / matrícula
            <input
              value={trainee}
              onChange={(e) => setTrainee(e.target.value)}
              className="ops-quick-enablement-chrome__input"
              placeholder="Quem realizou o treinamento"
            />
          </label>
          <label className="ops-quick-enablement-chrome__label">
            Papel
            <select value={role} onChange={(e) => setRole(e.target.value)} className="ops-quick-enablement-chrome__input">
              <option value="OPS">OPS</option>
              <option value="SUPORTE_N1">Suporte N1</option>
              <option value="SUPORTE_N2">Suporte N2</option>
              <option value="AUDITORIA">Auditoria</option>
            </select>
          </label>
        </div>
        <label className="ops-quick-enablement-chrome__label ops-quick-enablement-chrome__label--block">
          Notas da sessão (opcional)
          <textarea
            value={sessionNotes}
            onChange={(e) => setSessionNotes(e.target.value)}
            rows={3}
            className="ops-quick-enablement-chrome__textarea"
            placeholder="Tópicos cobertos, dúvidas, follow-up."
          />
        </label>
        <div className="ops-quick-enablement-chrome__actions">
          <button type="button" className="ops-quick-enablement-chrome__btn" onClick={() => void exportSignedJson()}>
            Exportar JSON assinado
          </button>
          <button type="button" className="ops-quick-enablement-chrome__btn" onClick={() => void exportSignedZip()}>
            Exportar ZIP auditável
          </button>
          <button type="button" className="ops-quick-enablement-chrome__btn ops-quick-enablement-chrome__btn--secondary" onClick={() => void copySlackHandoff()}>
            Copiar handoff Slack
          </button>
          <button type="button" className="ops-quick-enablement-chrome__btn ops-quick-enablement-chrome__btn--secondary" onClick={() => resetLocal()}>
            Limpar rascunho
          </button>
        </div>
        <div className="ops-quick-enablement-chrome__status-row">
          <span className="ops-quick-enablement-chrome__chip">
            Progresso: {progress.done}/{progress.total} ({progress.pct}%)
          </span>
        </div>
        {statusMsg ? <small className="ops-quick-enablement-chrome__status-msg">{statusMsg}</small> : null}
      </section>

      <section className="ops-quick-enablement-chrome__card ops-quick-enablement-chrome__card--spaced">
        <h2 className="ops-quick-enablement-chrome__section-title">Checklist guiado</h2>
        <ul className="ops-quick-enablement-chrome__checklist">
          {rows.map((row) => (
            <li key={row.id} className="ops-quick-enablement-chrome__checklist-row">
              <label className="ops-quick-enablement-chrome__checklist-label">
                <input
                  type="checkbox"
                  checked={row.done}
                  onChange={(e) => setRow(row.id, { done: e.target.checked })}
                  aria-label={row.label}
                />
                <span>
                  <strong>{row.label}</strong>
                  <div className="ops-quick-enablement-chrome__row-desc">{row.description}</div>
                  <Link to={row.path} className="ops-quick-enablement-chrome__row-link">
                    Abrir {row.path}
                  </Link>
                </span>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <p className="ops-quick-enablement-chrome__footer-tip">
        Dica: após concluir o checklist, exporte o JSON ou ZIP e anexe ao handoff diário em <Link to="/fiscal/management-daily">fiscal/management-daily</Link> quando for o fechamento do turno.
      </p>
    </main>
  );
}
