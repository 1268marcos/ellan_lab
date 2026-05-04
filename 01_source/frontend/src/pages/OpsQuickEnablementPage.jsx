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
    <div style={pageStyle} data-testid="ops-quick-enablement-page">
      <section style={cardStyle}>
        <div style={crossShortcutStyle}>
          <Link to="/ops/health" style={crossShortcutLinkStyle}>
            Ir para saúde operacional
          </Link>
        </div>
        <div style={headerRowStyle}>
          <div>
            <OpsPageTitleHeader
              title="OPS + Suporte — Treinamento rápido (Sprint 3)"
              versionLabel={OPS_ENABLEMENT_PAGE_VERSION}
              versionTo="/ops/auth/policy/versioning"
              containerStyle={{ marginBottom: 0 }}
              titleStyle={{ margin: 0 }}
            />
            <p style={mutedTextStyle}>
              Roteiro curto (~15 minutos) para OPS e Suporte alinharem ferramentas fiscais e de incidente, com evidência auditável no padrão{" "}
              <code style={{ color: "#e2e8f0" }}>{DAILY_AUDIT_PREFIX}</code>. Não substitui playbooks completos; acelera o primeiro dia útil em
              paralelo ao hardening Sprint 3.
            </p>
          </div>
          <div style={toolbarStyle}>
            <button type="button" onClick={() => void exportSignedJson()} style={buttonGhostStyle}>
              Exportar JSON assinado
            </button>
            <button type="button" onClick={() => void exportSignedZip()} style={buttonGhostStyle}>
              Exportar ZIP auditável
            </button>
            <button type="button" onClick={() => void copySlackHandoff()} style={buttonGhostStyle}>
              Copiar handoff Slack
            </button>
            <button type="button" onClick={() => resetLocal()} style={buttonGhostStyle}>
              Limpar rascunho
            </button>
          </div>
        </div>
        {statusMsg ? <small style={predictiveReviewStatusStyle}>{statusMsg}</small> : null}

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Participante e sessão</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              Nome / matrícula
              <input
                value={trainee}
                onChange={(e) => setTrainee(e.target.value)}
                style={healthLocalFilterInputStyle}
                placeholder="Quem realizou o treinamento"
              />
            </label>
            <label style={healthLocalFilterFieldStyle}>
              Papel
              <select value={role} onChange={(e) => setRole(e.target.value)} style={healthLocalFilterInputStyle}>
                <option value="OPS">OPS</option>
                <option value="SUPORTE_N1">Suporte N1</option>
                <option value="SUPORTE_N2">Suporte N2</option>
                <option value="AUDITORIA">Auditoria</option>
              </select>
            </label>
          </div>
          <label style={{ ...healthLocalFilterFieldStyle, gridColumn: "1 / -1" }}>
            Notas da sessão (opcional)
            <textarea
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              rows={3}
              style={enablementTextareaStyle}
              placeholder="Tópicos cobertos, dúvidas, follow-up."
            />
          </label>
          <div style={collectorHealthWrapStyle}>
            <span style={collectorHealthBadgeStyle(progress.pct === 100 ? "ok" : "warn")}>
              Progresso: {progress.done}/{progress.total} ({progress.pct}%)
            </span>
          </div>
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Checklist guiado</h3>
          </div>
          <ul style={checklistUlStyle}>
            {rows.map((row) => (
              <li key={row.id} style={summary24hItemStyle}>
                <label style={checklistLabelStyle}>
                  <input
                    type="checkbox"
                    checked={row.done}
                    onChange={(e) => setRow(row.id, { done: e.target.checked })}
                    aria-label={row.label}
                  />
                  <span>
                    <strong style={{ color: "#f8fafc", fontSize: 14, fontWeight: 700 }}>{row.label}</strong>
                    <small style={{ ...summary24hLabelStyle, display: "block", marginTop: 4 }}>{row.description}</small>
                    <Link to={row.path} style={gateDrilldownLinkStyle}>
                      Abrir {row.path}
                    </Link>
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </section>

        <p style={summary24hHintStyle}>
          Dica: após concluir o checklist, exporte o JSON ou ZIP e anexe ao handoff diário em{" "}
          <Link to="/fiscal/management-daily" style={gateDrilldownLinkStyle}>
            fiscal/management-daily
          </Link>{" "}
          quando for o fechamento do turno.
        </p>
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const headerRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const crossShortcutStyle = {
  display: "flex",
  justifyContent: "flex-end",
  marginBottom: 10,
};

const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

const labelStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "rgba(245,247,250,0.86)",
};

const inputStyle = {
  width: 90,
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

const healthLocalFilterFieldStyle = {
  ...labelStyle,
  color: "#cbd5e1",
};

const healthLocalFilterInputStyle = {
  ...inputStyle,
  width: "100%",
  border: "1px solid rgba(148,163,184,0.5)",
};

const enablementTextareaStyle = {
  ...healthLocalFilterInputStyle,
  minHeight: 80,
  resize: "vertical",
  fontFamily: "inherit",
};

const collectorHealthWrapStyle = {
  marginTop: 10,
  display: "grid",
  gap: 8,
};

const collectorHealthBadgeStyle = (tone) => ({
  display: "inline-flex",
  width: "fit-content",
  padding: "6px 10px",
  borderRadius: 999,
  border:
    tone === "ok"
      ? "1px solid rgba(74,222,128,0.55)"
      : "1px solid rgba(251,191,36,0.55)",
  background:
    tone === "ok"
      ? "rgba(22,101,52,0.22)"
      : "rgba(120,53,15,0.26)",
  color: tone === "ok" ? "#bbf7d0" : "#fde68a",
  fontSize: 12,
  fontWeight: 700,
});

const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const summary24hItemStyle = {
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.3)",
  background: "rgba(15,23,42,0.35)",
  padding: "8px 10px",
  display: "grid",
  gap: 2,
};

const summary24hLabelStyle = {
  color: "#cbd5e1",
  fontSize: 12,
};

const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

const gateDrilldownLinkStyle = {
  marginTop: 8,
  width: "fit-content",
  color: "#93c5fd",
  textDecoration: "underline",
  fontSize: 12,
  fontWeight: 600,
};

const predictiveReviewStatusStyle = {
  color: "#e2e8f0",
  fontSize: 12,
  fontWeight: 700,
};

const checklistUlStyle = {
  listStyle: "none",
  margin: 0,
  padding: 0,
  display: "grid",
  gap: 8,
};

const checklistLabelStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-start",
  cursor: "pointer",
};
