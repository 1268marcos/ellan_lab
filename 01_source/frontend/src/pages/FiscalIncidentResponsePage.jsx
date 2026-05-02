import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import { buildFiscalSwaggerUrl } from "../constants/fiscalApiCatalog";
import {
  SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO,
  SPRINT3_ASSISTED_SIMULATION_DURATION_MIN,
  SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M,
  SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS,
  SPRINT3_INCIDENT_CHECKLIST,
  SPRINT3_INCIDENT_RESPONSE_STORAGE_KEY,
  SPRINT3_INCIDENT_RUNBOOK_LINKS,
  SPRINT3_INCIDENT_RUNBOOK_VERSION,
  buildSprint3AssistedSimulationStampPayload,
} from "../utils/fiscalSprint3IncidentRunbook";

const PAGE_VERSION = "fiscal/incident-response v1.2.0-15min-sim-v2";
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
const toolbarStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const buttonStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  cursor: "pointer",
  fontWeight: 700,
};
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const errorStyle = { marginTop: 12, background: "#2b1d1d", color: "#ffb4b4", padding: 12, borderRadius: 12, overflow: "auto" };
const gridStyle = { marginTop: 12, display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" };
const boxStyle = { marginTop: 10, border: "1px solid var(--fiscal-box-border)", borderRadius: 12, background: "var(--fiscal-box-bg)", padding: 12 };
const boxTitleStyle = { margin: "0 0 8px", fontSize: 14 };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, fontWeight: 700, color: "var(--fiscal-soft-text)" };
const inputStyle = { borderRadius: 8, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", padding: "8px 10px", fontSize: 13 };
const textareaStyle = { ...inputStyle, minHeight: 120, resize: "vertical" };

export default function FiscalIncidentResponsePage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [incidentId, setIncidentId] = useState("");
  const [owner, setOwner] = useState("");
  const [severity, setSeverity] = useState("MEDIUM");
  const [startedAt, setStartedAt] = useState("");
  const [evidenceNotes, setEvidenceNotes] = useState("");
  const [doneById, setDoneById] = useState({});
  const [simulationScenario, setSimulationScenario] = useState(SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO);
  const [simulationStamps, setSimulationStamps] = useState([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(SPRINT3_INCIDENT_RESPONSE_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        setIncidentId(String(parsed?.incident_id || ""));
        setOwner(String(parsed?.owner || ""));
        setSeverity(String(parsed?.severity || "MEDIUM"));
        setStartedAt(String(parsed?.started_at || ""));
        setEvidenceNotes(String(parsed?.evidence_notes || ""));
        setDoneById(typeof parsed?.done_by_id === "object" && parsed.done_by_id ? parsed.done_by_id : {});
        setSimulationScenario(String(parsed?.simulation_scenario || SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO));
        const stamps = parsed?.simulation_stamps;
        setSimulationStamps(Array.isArray(stamps) ? stamps.slice(-15) : []);
      }
    } catch {
      setError("Falha ao carregar rascunho local.");
    }

    const from = String(searchParams.get("from") || "");
    const preId = String(searchParams.get("incident_id") || "").trim();
    const preSev = String(searchParams.get("severity") || "").trim().toUpperCase();
    if (preId) setIncidentId(preId);
    if (["CRITICAL", "HIGH", "MEDIUM", "LOW"].includes(preSev)) setSeverity(preSev);
    if (from === "ops-health") {
      setStatus("Pré-preenchido a partir de ops/health (query string).");
      window.setTimeout(() => setStatus(""), 2400);
    }
  }, [searchParams]);

  const doneCount = useMemo(() => Object.values(doneById).filter(Boolean).length, [doneById]);
  const totalSteps = SPRINT3_INCIDENT_CHECKLIST.length;

  function persistDraft(nextDone = doneById, nextStamps = simulationStamps) {
    const payload = {
      incident_id: incidentId,
      owner,
      severity,
      started_at: startedAt,
      evidence_notes: evidenceNotes,
      done_by_id: nextDone,
      simulation_scenario: simulationScenario,
      simulation_stamps: nextStamps.slice(-15),
    };
    try {
      window.localStorage.setItem(SPRINT3_INCIDENT_RESPONSE_STORAGE_KEY, JSON.stringify(payload));
      setStatus("Rascunho salvo localmente.");
      window.setTimeout(() => setStatus(""), 2200);
    } catch (err) {
      setError(String(err?.message || err));
    }
  }

  function toggleStep(id) {
    const next = { ...doneById, [id]: !doneById[id] };
    setDoneById(next);
    persistDraft(next);
  }

  function recordAssistedSimulationStamp() {
    const nowIso = new Date().toISOString();
    const stamp = {
      id: `sprint3_sim_${Date.now()}`,
      recorded_at: nowIso,
      scenario: String(simulationScenario || SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO).trim() || SPRINT3_ASSISTED_SIM_DEFAULT_SCENARIO,
      facilitator: String(owner || "").trim() || "-",
      incident_id: String(incidentId || "").trim() || "-",
      checklist_progress_at_stamp: `${doneCount}/${totalSteps}`,
    };
    const next = [...simulationStamps, stamp].slice(-15);
    setSimulationStamps(next);
    persistDraft(doneById, next);
    setStatus(`Carimbo de simulação assistida registrado (${stamp.id}).`);
    window.setTimeout(() => setStatus(""), 2600);
  }

  function buildChecklistPayload(nowIso) {
    const stamps = simulationStamps.slice(-15);
    return {
      scope: "SPRINT3_P0_3_INCIDENT_CHECKLIST",
      runbook_version: SPRINT3_INCIDENT_RUNBOOK_VERSION,
      generated_at: nowIso,
      incident: {
        incident_id: String(incidentId || "").trim() || "-",
        owner: String(owner || "").trim() || "-",
        severity: String(severity || "MEDIUM"),
        started_at: String(startedAt || nowIso),
      },
      checklist_progress: `${doneCount}/${totalSteps}`,
      checklist: SPRINT3_INCIDENT_CHECKLIST.map((step) => ({
        id: step.id,
        label: step.label,
        hint: step.hint,
        done: Boolean(doneById[step.id]),
      })),
      evidence_attachments_text: String(evidenceNotes || "").trim() || "-",
      assisted_simulation: {
        stamps_count: stamps.length,
        last_recorded_at: stamps.length ? stamps[stamps.length - 1].recorded_at : null,
        stamps,
      },
    };
  }

  function buildSimulationStampPayload(nowIso) {
    return buildSprint3AssistedSimulationStampPayload(nowIso, "fiscal/incident-response", {
      incident_id: incidentId,
      owner,
      severity,
      simulation_stamps: simulationStamps,
      simulation_scenario: simulationScenario,
    });
  }

  function buildRunbookRefPayload(nowIso) {
    return {
      scope: "SPRINT3_P0_3_INCIDENT_RUNBOOK_REF",
      runbook_version: SPRINT3_INCIDENT_RUNBOOK_VERSION,
      generated_at: nowIso,
      links: SPRINT3_INCIDENT_RUNBOOK_LINKS,
    };
  }

  function buildEvidencePayload(nowIso) {
    return {
      scope: "SPRINT3_P0_3_INCIDENT_EVIDENCE_ATTACH",
      runbook_version: SPRINT3_INCIDENT_RUNBOOK_VERSION,
      generated_at: nowIso,
      incident: {
        incident_id: String(incidentId || "").trim() || "-",
        owner: String(owner || "").trim() || "-",
        severity: String(severity || "MEDIUM"),
        started_at: String(startedAt || nowIso),
      },
      attachments_text: String(evidenceNotes || "").trim() || "-",
    };
  }

  function copySlackHandoff() {
    const nowIso = new Date().toISOString();
    const lines = [
      "Handoff — Resposta a incidente (Fiscal/OPS) — Sprint 3 P0-3",
      `Incidente: ${String(incidentId || "-").trim() || "-"}`,
      `Owner: ${String(owner || "-").trim() || "-"}`,
      `Severidade: ${severity}`,
      `Checklist: ${doneCount}/${totalSteps} concluídos`,
      `Referência UTC: ${nowIso}`,
      `Evidência (resumo): ${String(evidenceNotes || "").trim().slice(0, 400) || "-"}`,
    ];
    const text = lines.join("\n");
    void navigator.clipboard?.writeText(text).catch(() => {});
    setStatus("Payload Slack/Teams copiado.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportSignedJson() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signed = await buildSignedPayload(buildChecklistPayload(nowIso));
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_INCIDENT_CHECKLIST_${ts}.json`, signed);
    setStatus("Checklist assinado exportado (.json).");
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function copySignedJson() {
    const nowIso = new Date().toISOString();
    const signed = await buildSignedPayload(buildChecklistPayload(nowIso));
    const text = JSON.stringify(signed, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Checklist assinado copiado para a área de transferência.");
    } catch {
      setStatus("Clipboard indisponível; use export .json.");
    }
    window.setTimeout(() => setStatus(""), 2200);
  }

  async function exportSignedZip() {
    const nowIso = new Date().toISOString();
    const day = toAuditDayStamp(nowIso);
    const ts = nowIso.replace(/[:.]/g, "-");
    const signedChecklist = await buildSignedPayload(buildChecklistPayload(nowIso));
    const signedRunbook = await buildSignedPayload(buildRunbookRefPayload(nowIso));
    const signedEvidence = await buildSignedPayload(buildEvidencePayload(nowIso));
    const signedSimStamp = await buildSignedPayload(buildSimulationStampPayload(nowIso));
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_INCIDENT_PACKAGE_${ts}.zip`, {
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_INCIDENT_CHECKLIST_${ts}.json`]: strToU8(JSON.stringify(signedChecklist, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_ASSISTED_SIMULATION_STAMP_${ts}.json`]: strToU8(JSON.stringify(signedSimStamp, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_INCIDENT_RUNBOOK_REF_${ts}.json`]: strToU8(JSON.stringify(signedRunbook, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT3_INCIDENT_EVIDENCE_ATTACH_${ts}.json`]: strToU8(JSON.stringify(signedEvidence, null, 2)),
    });
    setStatus("Pacote auditável (.zip): checklist + carimbo simulação + runbook + anexos.");
    window.setTimeout(() => setStatus(""), 2200);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal/slo-alerts" style={shortcutLinkStyle}>
            Abrir fiscal/slo-alerts
          </Link>
          <Link to="/ops/health" style={shortcutLinkStyle}>
            Abrir ops/health
          </Link>
          <a href={buildFiscalSwaggerUrl(import.meta.env.VITE_BILLING_FISCAL_BASE_URL || "http://localhost:8020")} target="_blank" rel="noreferrer" style={shortcutLinkStyle}>
            Abrir Swagger FISCAL
          </a>
        </div>
        <OpsPageTitleHeader title="FISCAL — Resposta a incidente (Sprint 3 P0-3)" versionLabel={PAGE_VERSION} />
        <p style={mutedTextStyle}>
          Checklist operacional + referência de runbook com exportação auditável (JSON assinado e pacote .zip) para anexar no handoff.
        </p>
        <p style={mutedTextStyle}>
          P0-3: tabletop assistido <strong>{SPRINT3_ASSISTED_SIMULATION_DURATION_MIN} min</strong>; use o carimbo abaixo. Pacote diário/executivo anexa{" "}
          <code>SPRINT3_ASSISTED_SIMULATION_STAMP_ATTACH</code> (payload <code>SPRINT3_P0_3_ASSISTED_SIMULATION_STAMP</code> com <code>stamp_attach_scope</code>).
        </p>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Roteiro 15 min (facilitador)</h3>
          <ol style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--fiscal-text)" }}>
            {SPRINT3_ASSISTED_SIMULATION_TIMELINE_15M.map((block) => (
              <li key={block.phase} style={{ marginBottom: 8 }}>
                <strong>
                  {block.minute_start}–{block.minute_end} min — {block.title}
                </strong>
                <ul style={{ margin: "4px 0 0", paddingLeft: 16 }}>
                  {block.facilitator_actions.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ol>
          <div style={{ marginTop: 10 }}>
            <div style={{ ...labelStyle, marginBottom: 4 }}>Comandos lab (referência)</div>
            <pre
              style={{
                ...inputStyle,
                margin: 0,
                whiteSpace: "pre-wrap",
                fontSize: 12,
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {SPRINT3_ASSISTED_SIMULATION_15MIN_COMMANDS.join("\n")}
            </pre>
          </div>
        </section>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Incident ID
            <input value={incidentId} onChange={(e) => setIncidentId(e.target.value)} style={inputStyle} placeholder="ex.: INC-2026-04-30-001" />
          </label>
          <label style={labelStyle}>
            Owner
            <input value={owner} onChange={(e) => setOwner(e.target.value)} style={inputStyle} placeholder="Responsável no turno" />
          </label>
          <label style={labelStyle}>
            Severidade
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} style={inputStyle}>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </label>
          <label style={labelStyle}>
            Início (UTC / local do browser)
            <input type="datetime-local" value={startedAt} onChange={(e) => setStartedAt(e.target.value)} style={inputStyle} />
          </label>
        </div>

        <label style={{ ...labelStyle, marginTop: 12 }}>
          Evidências anexáveis (texto livre: URLs, order_id, logs, tickets)
          <textarea value={evidenceNotes} onChange={(e) => setEvidenceNotes(e.target.value)} style={textareaStyle} />
        </label>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Simulação assistida — carimbo (Sprint 3 P0-3)</h3>
          <p style={mutedTextStyle}>
            Registros: <strong>{simulationStamps.length}</strong>
            {simulationStamps.length ? ` · último: ${simulationStamps[simulationStamps.length - 1].recorded_at}` : ""}
          </p>
          <label style={{ ...labelStyle, marginTop: 8 }}>
            Cenário / roteiro (curto)
            <input value={simulationScenario} onChange={(e) => setSimulationScenario(e.target.value)} style={inputStyle} />
          </label>
          <div style={{ ...toolbarStyle, marginTop: 10 }}>
            <button type="button" style={buttonStyle} onClick={() => recordAssistedSimulationStamp()}>
              Registrar carimbo de simulação assistida
            </button>
          </div>
        </section>

        <div style={toolbarStyle}>
          <button type="button" style={buttonStyle} onClick={() => persistDraft()}>
            Salvar rascunho local
          </button>
          <button type="button" style={buttonStyle} onClick={() => copySlackHandoff()}>
            Copiar handoff Slack/Teams
          </button>
          <button type="button" style={buttonStyle} onClick={() => void copySignedJson()}>
            Copiar checklist (JSON assinado)
          </button>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedJson()}>
            Exportar checklist (.json assinado)
          </button>
          <button type="button" style={buttonStyle} onClick={() => void exportSignedZip()}>
            Baixar pacote (.zip auditável)
          </button>
        </div>
        {status ? <small style={mutedTextStyle}>{status}</small> : null}
        {error ? <div style={errorStyle}>{error}</div> : null}

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Checklist de resposta ({doneCount}/{totalSteps})</h3>
          <div style={{ display: "grid", gap: 10 }}>
            {SPRINT3_INCIDENT_CHECKLIST.map((step) => (
              <label
                key={step.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: 10,
                  alignItems: "start",
                  padding: 10,
                  borderRadius: 10,
                  border: "1px solid var(--fiscal-link-border)",
                  background: "var(--fiscal-link-bg)",
                }}
              >
                <input type="checkbox" checked={Boolean(doneById[step.id])} onChange={() => toggleStep(step.id)} />
                <span>
                  <strong>{step.label}</strong>
                  <div style={{ ...mutedTextStyle, marginTop: 4 }}>{step.hint}</div>
                </span>
              </label>
            ))}
          </div>
        </section>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Runbook — atalhos ({SPRINT3_INCIDENT_RUNBOOK_VERSION})</h3>
          <ul style={{ margin: 0, paddingLeft: 18, color: "var(--fiscal-soft-text)" }}>
            {SPRINT3_INCIDENT_RUNBOOK_LINKS.map((link) => (
              <li key={link.id} style={{ marginBottom: 8 }}>
                <Link to={link.path} style={{ color: "var(--fiscal-text)", fontWeight: 700 }}>
                  {link.label}
                </Link>
                <div style={{ fontSize: 12 }}>{link.note}</div>
              </li>
            ))}
          </ul>
        </section>
      </section>
    </div>
  );
}
